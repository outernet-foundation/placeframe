#if !UNITY_EDITOR && UNITY_ANDROID
using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

namespace Placeframe.Client
{
    // Per-socket network binding via JNI to Network.openConnection(url). Avoids
    // ConnectivityManager.bindProcessToNetwork (process-wide, raced when concurrent
    // pipelines flipped it) and SocketsHttpHandler.ConnectCallback (absent from
    // Unity 6's Android reference assemblies; IL2CPP forbids reflection workarounds).
    // Whole file compiled out off-device because AndroidJavaObject is a no-op there;
    // editor callers go through InternetBoundHandler.Create() which returns null.
    //
    // Holds one long-lived NetworkRequest per transport via ConnectivityManager.requestNetwork:
    // a bare getAllNetworks() lookup loses non-default networks (USB-ethernet alongside wifi)
    // after first idle on Pixel — the framework tears them down unless an app is actively
    // requesting them. The retained callbacks keep each network up. One request per transport
    // because NetworkRequest's transport bits are AND-matched: a single multi-transport
    // request can never be satisfied (no Network is simultaneously wifi AND cellular), so
    // the callback would never fulfil and Android wouldn't keep either bearer wanted.
    //
    // CAVEAT: requestNetwork keeps the network "wanted," which causes Android's
    // NetworkMonitor to repeatedly probe internet-validation endpoints over it.
    // For LAN-only links (no real internet upstream), every probe failure triggers
    // EthernetNetworkFactory to restart IpClient, which kernel-destroys all live TCP
    // sockets bound to the link's IP — silently breaking any in-flight request that
    // takes more than ~1s. The remote end of the link must answer Android's probe
    // (tiny HTTP server returning 204 + DNS override) for this handler to actually
    // work end-to-end on a non-internet network. See docker/zed-capture/CLAUDE.md
    // "Captive-portal spoof" for the ZED-side implementation. Validated wifi/cellular
    // networks aren't subject to the restart loop, so multi-transport instances of
    // this handler used for normal internet traffic don't need a counterpart spoof.
    public sealed class AndroidBoundHttpHandler : HttpMessageHandler
    {
        // Disable HttpURLConnection's KeepAliveCache process-wide. Per-request
        // `Connection: close` (set in ProcessRequest) is necessary but not
        // sufficient: Android's HttpURLConnection (OkHttp under the hood) only
        // honors `Connection: close` on the *response* header, not the request,
        // so if the server or any intermediary doesn't echo it back, the socket
        // stays in KeepAliveCache. The next request grabs the dead socket, sends
        // bytes, then reads EOF — surfaces as
        // `IOException: unexpected end of stream on com.android.okhttp.Address@…`.
        // Setting http.keepAlive=false before any HttpURLConnection is created
        // is the only documented kill-switch for the pool. BeforeSceneLoad fires
        // earlier than any handler instantiation in this app.
        [UnityEngine.RuntimeInitializeOnLoadMethod(UnityEngine.RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void DisableHttpKeepAliveCache()
        {
            AndroidJNI.AttachCurrentThread();
            using var systemClass = new AndroidJavaClass("java.lang.System");
            systemClass.CallStatic("setProperty", "http.keepAlive", "false");
        }

        // RAII wrapper for JNI local refs so callers can `using var` instead of
        // hand-rolling try/finally around DeleteLocalRef.
        private readonly struct LocalRef : IDisposable
        {
            public readonly IntPtr Pointer;
            public LocalRef(IntPtr pointer) { Pointer = pointer; }
            public void Dispose() => AndroidJNI.DeleteLocalRef(Pointer);
        }

        // Mirrors android.net.NetworkCapabilities.TRANSPORT_*. Underlying ints
        // are the Java constants verbatim — passed straight to ConnectivityManager
        // via JNI. Bluetooth (2) intentionally omitted; not relevant to this app.
        private enum Transport
        {
            Cellular = 0,
            Wifi = 1,
            Ethernet = 3,
        }

        // android.net.NetworkCapabilities.NET_CAPABILITY_INTERNET. Filters out
        // sibling networks that share a transport but can't actually carry user
        // traffic (e.g. carrier IMS bearer alongside the LTE/NR internet bearer:
        // both report TRANSPORT_CELLULAR, only one has INTERNET). Without this
        // filter, getAllNetworks ordering is undocumented and the IMS-only
        // network can be picked, causing every DNS lookup on the bound socket
        // to fail with UnknownHostException.
        private const int NetCapabilityInternet = 12;

        private readonly Transport[] transportTypes;

        // Hold the callbacks (and their ConnectivityManager) for the lifetime of the
        // process — releasing any of them lets Android tear down the corresponding network.
        // We deliberately do NOT override Dispose: the inherited no-op base means
        // a transitive HttpClient.Dispose() leaves these fields intact. Do not
        // add a Dispose override that releases them, and do not wrap a handler
        // instance in `using` — both paths kill the network mid-session.
        private AndroidJavaObject heldConnectivityManager;
        private List<AndroidJavaObject> heldNetworkCallbacks;

        public AndroidBoundHttpHandler(bool forZedBox = false)
        {
            transportTypes = forZedBox
                ? new[] { Transport.Ethernet }
                : new[] { Transport.Wifi, Transport.Cellular };

            AndroidJNI.AttachCurrentThread();
            using var activity = new AndroidJavaClass("com.unity3d.player.UnityPlayer")
                .GetStatic<AndroidJavaObject>("currentActivity");
            heldConnectivityManager = activity.Call<AndroidJavaObject>("getSystemService", "connectivity");

            // NetworkCallback is a concrete class with empty default methods; we don't
            // need to override anything. Holding the instance is what matters — the
            // ConnectivityService keys retention off the registered callback object.
            // addCapability(NET_CAPABILITY_INTERNET) mirrors the runtime filter in
            // FindMatchingNetwork so Android keeps the internet-bearing sibling wanted
            // (not the IMS-only cellular sibling that shares TRANSPORT_CELLULAR).
            heldNetworkCallbacks = new List<AndroidJavaObject>();
            foreach (var transport in transportTypes)
            {
                using var builder = new AndroidJavaObject("android.net.NetworkRequest$Builder");
                builder.Call<AndroidJavaObject>("addTransportType", (int)transport).Dispose();
                builder.Call<AndroidJavaObject>("addCapability", NetCapabilityInternet).Dispose();
                using var networkRequest = builder.Call<AndroidJavaObject>("build");

                var callback = new AndroidJavaObject("android.net.ConnectivityManager$NetworkCallback");
                heldConnectivityManager.Call("requestNetwork", networkRequest, callback);
                heldNetworkCallbacks.Add(callback);
            }
        }

        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken
        )
        {
            byte[] body = request.Content == null ? null : await request.Content.ReadAsByteArrayAsync();
            return await Task.Run(() => SendOnAndroid(request, body, cancellationToken), cancellationToken);
        }

        private HttpResponseMessage SendOnAndroid(HttpRequestMessage request, byte[] body, CancellationToken cancellationToken)
        {
            AndroidJNI.AttachCurrentThread();

            using var activity = new AndroidJavaClass("com.unity3d.player.UnityPlayer")
                .GetStatic<AndroidJavaObject>("currentActivity");
            using var connectivityManager = activity.Call<AndroidJavaObject>("getSystemService", "connectivity");
            var networks = connectivityManager.Call<AndroidJavaObject[]>("getAllNetworks");
            AndroidJavaObject network = null;
            try
            {
                network = FindMatchingNetwork(connectivityManager, networks, transportTypes);
                if (network == null)
                    throw new IOException($"No network available with transports [{string.Join(",", transportTypes)}]");
                return ProcessRequest(network, request, body, cancellationToken);
            }
            finally
            {
                network?.Dispose();
            }
        }

        // First network matching the highest-priority transport wins. Lets callers
        // express e.g. "wifi if up, else cellular". Caller owns the returned ref;
        // finally disposes the non-chosen networks.
        private static AndroidJavaObject FindMatchingNetwork(
            AndroidJavaObject connectivityManager,
            AndroidJavaObject[] networks,
            Transport[] transportTypes
        )
        {
            AndroidJavaObject chosen = null;
            try
            {
                foreach (var transport in transportTypes)
                {
                    foreach (var candidateNetwork in networks)
                    {
                        using var capabilities = connectivityManager.Call<AndroidJavaObject>("getNetworkCapabilities", candidateNetwork);
                        if (capabilities == null) continue;
                        if (capabilities.Call<bool>("hasTransport", (int)transport)
                            && capabilities.Call<bool>("hasCapability", NetCapabilityInternet))
                        {
                            chosen = candidateNetwork;
                            return chosen;
                        }
                    }
                }
                return null;
            }
            finally
            {
                foreach (var candidateNetwork in networks)
                    if (candidateNetwork != chosen) candidateNetwork.Dispose();
            }
        }

        private static HttpResponseMessage ProcessRequest(
            AndroidJavaObject network,
            HttpRequestMessage request,
            byte[] body,
            CancellationToken cancellationToken
        )
        {
            // Open the connection (lazy — no TCP yet) and configure verbs/headers.
            using var urlJavaObject = new AndroidJavaObject("java.net.URL", request.RequestUri.ToString());
            var connection = network.Call<AndroidJavaObject>("openConnection", urlJavaObject);
            try
            {
                connection.Call("setRequestMethod", request.Method.Method);
                connection.Call("setInstanceFollowRedirects", false);
                connection.Call("setDoInput", true);

                // Without these, HttpURLConnection waits forever on a stalled connect or
                // read. 15s/60s sized for slow cellular bearers; a hung request must surface
                // as SocketTimeoutException so the caller can fail rather than hang the UI.
                connection.Call("setConnectTimeout", 15000);
                connection.Call("setReadTimeout", 60000);

                // HttpURLConnection's KeepAliveCache keys pooled connections on host:port and
                // ignores the bound Network — a connection opened over wifi can be silently
                // handed back when we later route over cellular, then dies mid-stream because
                // the underlying socket is bound to a torn-down interface. Forcing close per
                // request trades ~50-150ms of TLS handshake for predictability.
                connection.Call("setRequestProperty", "Connection", "close");

                ApplyHeaders(connection, request.Headers);
                if (request.Content != null)
                {
                    ApplyHeaders(connection, request.Content.Headers);

                    // Stream the request body to the server via JNI (TCP connect happens here).
                    connection.Call("setDoOutput", true);
                    connection.Call("setFixedLengthStreamingMode", body.Length);
                    using var outputStream = connection.Call<AndroidJavaObject>("getOutputStream");

                    using var outputStreamClass = new LocalRef(AndroidJNI.FindClass("java/io/OutputStream"));
                    using var javaBuffer = new LocalRef(AndroidJNI.ToByteArray(body));
                    var arguments = new jvalue[3];
                    arguments[0].l = javaBuffer.Pointer;
                    arguments[1].i = 0;
                    arguments[2].i = body.Length;
                    AndroidJNI.CallVoidMethod(outputStream.GetRawObject(), AndroidJNI.GetMethodID(outputStreamClass.Pointer, "write", "([BII)V"), arguments);

                    outputStream.Call("close");
                }

                // Read status; 4xx/5xx bodies come from getErrorStream, others from getInputStream.
                int statusCode = connection.Call<int>("getResponseCode");
                var response = new HttpResponseMessage((HttpStatusCode)statusCode);

                response.Content = new StreamContent(new JavaInputStreamWrapper(
                    statusCode >= 400
                        ? connection.Call<AndroidJavaObject>("getErrorStream")
                        : connection.Call<AndroidJavaObject>("getInputStream"),
                    connection,
                    cancellationToken));

                // Walk numeric header indices until both key and value come back null.
                int index = 0;
                while (true)
                {
                    string key = connection.Call<string>("getHeaderFieldKey", index);
                    string value = connection.Call<string>("getHeaderField", index);
                    index++;
                    if (key == null && value == null) break;
                    if (key == null) continue;

                    HttpHeaders target = (string.Equals(key, "Content-Length", StringComparison.OrdinalIgnoreCase)
                        || string.Equals(key, "Content-Type", StringComparison.OrdinalIgnoreCase))
                        ? response.Content.Headers
                        : response.Headers;
                    target.TryAddWithoutValidation(key, value);
                }

                return response;
            }
            catch
            {
                connection.Call("disconnect");
                connection.Dispose();
                throw;
            }
        }

        private static void ApplyHeaders(AndroidJavaObject connection, HttpHeaders headers)
        {
            foreach (var header in headers)
                foreach (var value in header.Value)
                    connection.Call("setRequestProperty", header.Key, value);
        }


        private sealed class JavaInputStreamWrapper : Stream
        {
            private readonly AndroidJavaObject inputStream;
            private readonly AndroidJavaObject connection;
            private readonly IntPtr readMethodIdentifier;
            private readonly CancellationToken cancellationToken;
            private bool disposed;

            public JavaInputStreamWrapper(AndroidJavaObject inputStream, AndroidJavaObject connection, CancellationToken cancellationToken)
            {
                this.inputStream = inputStream;
                this.connection = connection;
                this.cancellationToken = cancellationToken;
                if (inputStream != null)
                {
                    using var streamClass = new LocalRef(AndroidJNI.FindClass("java/io/InputStream"));
                    readMethodIdentifier = AndroidJNI.GetMethodID(streamClass.Pointer, "read", "([BII)I");
                }
            }

            public override bool CanRead => !disposed;
            public override bool CanSeek => false;
            public override bool CanWrite => false;
            public override long Length => throw new NotSupportedException();
            public override long Position { get => throw new NotSupportedException(); set => throw new NotSupportedException(); }
            public override void Flush() { }
            public override long Seek(long offset, SeekOrigin origin) => throw new NotSupportedException();
            public override void SetLength(long value) => throw new NotSupportedException();
            public override void Write(byte[] buffer, int offset, int count) => throw new NotSupportedException();

            public override int Read(byte[] buffer, int offset, int count)
            {
                if (disposed) throw new ObjectDisposedException(nameof(JavaInputStreamWrapper));
                if (inputStream == null) return 0;
                cancellationToken.ThrowIfCancellationRequested();
                AndroidJNI.AttachCurrentThread();

                using var javaBuffer = new LocalRef(AndroidJNI.NewByteArray(count));
                var arguments = new jvalue[3];
                arguments[0].l = javaBuffer.Pointer;
                arguments[1].i = 0;
                arguments[2].i = count;
                int bytesRead = AndroidJNI.CallIntMethod(inputStream.GetRawObject(), readMethodIdentifier, arguments);

                // JNI Call*Method doesn't auto-rethrow Java exceptions: an IOException
                // thrown mid-body (e.g. okhttp's "unexpected end of stream") returns 0
                // with a pending JNI exception state. The .NET Stream contract maps a
                // 0 return to clean EOF, which silently truncates the body — the JSON
                // deserializer upstream then either fails at a weird offset or, worse,
                // succeeds on a partial document. Surface the real failure instead.
                var pendingException = AndroidJNI.ExceptionOccurred();
                if (pendingException != IntPtr.Zero)
                {
                    AndroidJNI.ExceptionDescribe();
                    AndroidJNI.ExceptionClear();
                    throw new IOException("Java InputStream.read threw mid-body; connection torn down before response completed");
                }

                if (bytesRead <= 0) return 0;

                Buffer.BlockCopy(AndroidJNI.FromByteArray(javaBuffer.Pointer), 0, buffer, offset, bytesRead);
                return bytesRead;
            }

            protected override void Dispose(bool disposing)
            {
                if (disposed) return;
                disposed = true;
                Swallow(() => inputStream?.Call("close"));
                Swallow(() => inputStream?.Dispose());
                Swallow(() => connection?.Call("disconnect"));
                Swallow(() => connection?.Dispose());
                base.Dispose(disposing);
            }

            private static void Swallow(Action action) { try { action(); } catch { } }
        }
    }
}
#endif
