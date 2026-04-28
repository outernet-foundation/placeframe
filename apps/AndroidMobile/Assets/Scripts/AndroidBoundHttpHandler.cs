using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;
#if !UNITY_EDITOR && UNITY_ANDROID
using UnityEngine;
#endif

namespace Placeframe.Client
{
    // Per-socket network binding via JNI to Network.openConnection(url). Avoids
    // ConnectivityManager.bindProcessToNetwork (process-wide, raced when concurrent
    // pipelines flipped it) and SocketsHttpHandler.ConnectCallback (absent from
    // Unity 6's Android reference assemblies; IL2CPP forbids reflection workarounds).
    // Editor falls back to HttpClientHandler because AndroidJavaObject is a no-op
    // off-device; JNI can only be exercised on real hardware. See
    // Assets/Scripts/Harness/HandlerTestRunner for on-device validation.
    //
    // Constructor takes an ordered list of transports — first match wins inside
    // FindNetwork, so callers can express priority (e.g. "wifi if available, else
    // cellular"). The held NetworkRequest is built with all transports OR'd, so
    // ConnectivityManager keeps any of them alive that wouldn't otherwise be.
    //
    // Holds a long-lived NetworkRequest via ConnectivityManager.requestNetwork: a
    // bare getAllNetworks() lookup loses non-default networks (USB-ethernet alongside
    // wifi) after first idle on Pixel — the framework tears them down unless an app
    // is actively requesting them. The retained callback keeps the network up.
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
        // Values from android.net.NetworkCapabilities.TRANSPORT_*. Bluetooth (2)
        // not exposed; not relevant to this app.
        public const int TransportCellular = 0;
        public const int TransportWifi = 1;
        public const int TransportEthernet = 3;

        private readonly int[] transportTypes;
#if !UNITY_EDITOR && UNITY_ANDROID
        // Hold the callback (and its ConnectivityManager) for the lifetime of the
        // process — releasing either lets Android tear down the requested network.
        // We deliberately do NOT override Dispose: the inherited no-op base means
        // a transitive HttpClient.Dispose() leaves these fields intact. Do not
        // add a Dispose override that releases them, and do not wrap a handler
        // instance in `using` — both paths kill the network mid-session.
        private AndroidJavaObject heldConnectivityManager;
        private AndroidJavaObject heldNetworkCallback;
#endif

        public AndroidBoundHttpHandler(int[] transportTypes)
        {
            if (transportTypes == null || transportTypes.Length == 0)
                throw new ArgumentException("transportTypes must contain at least one transport", nameof(transportTypes));
            this.transportTypes = transportTypes;
#if !UNITY_EDITOR && UNITY_ANDROID
            AndroidJNI.AttachCurrentThread();
            using var activity = new AndroidJavaClass("com.unity3d.player.UnityPlayer")
                .GetStatic<AndroidJavaObject>("currentActivity");
            heldConnectivityManager = activity.Call<AndroidJavaObject>("getSystemService", "connectivity");

            using var builder = new AndroidJavaObject("android.net.NetworkRequest$Builder");
            foreach (var transport in transportTypes)
                builder.Call<AndroidJavaObject>("addTransportType", transport).Dispose();
            using var networkRequest = builder.Call<AndroidJavaObject>("build");

            // NetworkCallback is a concrete class with empty default methods; we don't
            // need to override anything. Holding the instance is what matters — the
            // ConnectivityService keys retention off the registered callback object.
            heldNetworkCallback = new AndroidJavaObject("android.net.ConnectivityManager$NetworkCallback");
            heldConnectivityManager.Call("requestNetwork", networkRequest, heldNetworkCallback);
#endif
        }

        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken
        )
        {
#if !UNITY_EDITOR && UNITY_ANDROID
            return await Task.Run(() => SendOnAndroid(request, cancellationToken), cancellationToken);
#else
            using var fallback = new HttpClientHandler();
            using var invoker = new HttpMessageInvoker(fallback);
            return await invoker.SendAsync(request, cancellationToken);
#endif
        }

#if !UNITY_EDITOR && UNITY_ANDROID
        private HttpResponseMessage SendOnAndroid(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            AndroidJNI.AttachCurrentThread();

            using var network = FindNetwork(transportTypes);
            if (network == null)
                throw new IOException($"No network available with transports [{string.Join(",", transportTypes)}]");

            using var urlObj = new AndroidJavaObject("java.net.URL", request.RequestUri.ToString());
            var conn = network.Call<AndroidJavaObject>("openConnection", urlObj);
            try
            {
                conn.Call("setRequestMethod", request.Method.Method);
                conn.Call("setInstanceFollowRedirects", false);
                conn.Call("setDoInput", true);

                ApplyHeaders(conn, request.Headers);

                if (request.Content != null)
                {
                    ApplyHeaders(conn, request.Content.Headers);

                    byte[] bodyBytes = request.Content.ReadAsByteArrayAsync().Result;
                    conn.Call("setDoOutput", true);
                    conn.Call("setFixedLengthStreamingMode", bodyBytes.Length);

                    cancellationToken.ThrowIfCancellationRequested();
                    using var outputStream = conn.Call<AndroidJavaObject>("getOutputStream");
                    WriteBytesToOutputStream(outputStream, bodyBytes);
                    outputStream.Call("close");
                }

                cancellationToken.ThrowIfCancellationRequested();

                int statusCode = conn.Call<int>("getResponseCode");
                var response = new HttpResponseMessage((HttpStatusCode)statusCode);

                AndroidJavaObject bodyStream = statusCode >= 400
                    ? conn.Call<AndroidJavaObject>("getErrorStream")
                    : conn.Call<AndroidJavaObject>("getInputStream");

                response.Content = new StreamContent(new JavaInputStreamWrapper(bodyStream, conn, cancellationToken));
                CopyResponseHeaders(conn, response);
                return response;
            }
            catch
            {
                conn.Call("disconnect");
                conn.Dispose();
                throw;
            }
        }

        private static void ApplyHeaders(AndroidJavaObject conn, HttpHeaders headers)
        {
            foreach (var h in headers)
                foreach (var v in h.Value)
                    conn.Call("setRequestProperty", h.Key, v);
        }

        private static void WriteBytesToOutputStream(AndroidJavaObject outputStream, byte[] bytes)
        {
            IntPtr cls = AndroidJNI.FindClass("java/io/OutputStream");
            IntPtr writeMethod = AndroidJNI.GetMethodID(cls, "write", "([BII)V");
            AndroidJNI.DeleteLocalRef(cls);

            IntPtr javaBuffer = AndroidJNI.ToByteArray(bytes);
            try
            {
                var args = new jvalue[3];
                args[0].l = javaBuffer;
                args[1].i = 0;
                args[2].i = bytes.Length;
                AndroidJNI.CallVoidMethod(outputStream.GetRawObject(), writeMethod, args);
            }
            finally
            {
                AndroidJNI.DeleteLocalRef(javaBuffer);
            }
        }

        // Iterates transports outer, networks inner — first network matching the
        // highest-priority transport wins. Lets callers express e.g. "wifi if up,
        // else cellular" without two handler instances. Caller owns the returned
        // network ref; finally disposes everything else.
        private static AndroidJavaObject FindNetwork(int[] transportTypes)
        {
            using var activity = new AndroidJavaClass("com.unity3d.player.UnityPlayer")
                .GetStatic<AndroidJavaObject>("currentActivity");
            using var cm = activity.Call<AndroidJavaObject>("getSystemService", "connectivity");

            var networks = cm.Call<AndroidJavaObject[]>("getAllNetworks");
            AndroidJavaObject chosen = null;
            try
            {
                foreach (var transport in transportTypes)
                {
                    foreach (var n in networks)
                    {
                        using var caps = cm.Call<AndroidJavaObject>("getNetworkCapabilities", n);
                        if (caps == null) continue;
                        if (caps.Call<bool>("hasTransport", transport))
                        {
                            chosen = n;
                            return chosen;
                        }
                    }
                }
                return null;
            }
            finally
            {
                foreach (var n in networks)
                    if (n != chosen) n.Dispose();
            }
        }

        private static void CopyResponseHeaders(AndroidJavaObject conn, HttpResponseMessage response)
        {
            for (int i = 0; ; i++)
            {
                string key = conn.Call<string>("getHeaderFieldKey", i);
                string value = conn.Call<string>("getHeaderField", i);
                if (key == null && value == null) break;
                if (key == null) continue;

                bool isContentHeader = string.Equals(key, "Content-Length", StringComparison.OrdinalIgnoreCase)
                    || string.Equals(key, "Content-Type", StringComparison.OrdinalIgnoreCase);
                HttpHeaders target = isContentHeader ? response.Content.Headers : response.Headers;
                target.TryAddWithoutValidation(key, value);
            }
        }

        private sealed class JavaInputStreamWrapper : Stream
        {
            private readonly AndroidJavaObject inputStream;
            private readonly AndroidJavaObject connection;
            private readonly IntPtr readMethodId;
            private readonly CancellationToken cancellationToken;
            private bool disposed;

            public JavaInputStreamWrapper(AndroidJavaObject inputStream, AndroidJavaObject connection, CancellationToken cancellationToken)
            {
                this.inputStream = inputStream;
                this.connection = connection;
                this.cancellationToken = cancellationToken;
                if (inputStream != null)
                {
                    IntPtr streamClass = AndroidJNI.FindClass("java/io/InputStream");
                    readMethodId = AndroidJNI.GetMethodID(streamClass, "read", "([BII)I");
                    AndroidJNI.DeleteLocalRef(streamClass);
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

                IntPtr javaBuffer = AndroidJNI.NewByteArray(count);
                try
                {
                    var args = new jvalue[3];
                    args[0].l = javaBuffer;
                    args[1].i = 0;
                    args[2].i = count;
                    int bytesRead = AndroidJNI.CallIntMethod(inputStream.GetRawObject(), readMethodId, args);
                    if (bytesRead <= 0) return 0;

                    byte[] copied = AndroidJNI.FromByteArray(javaBuffer);
                    Buffer.BlockCopy(copied, 0, buffer, offset, bytesRead);
                    return bytesRead;
                }
                finally
                {
                    AndroidJNI.DeleteLocalRef(javaBuffer);
                }
            }

            protected override void Dispose(bool disposing)
            {
                if (disposed) return;
                disposed = true;
                try { inputStream?.Call("close"); } catch { }
                try { inputStream?.Dispose(); } catch { }
                try { connection?.Call("disconnect"); } catch { }
                try { connection?.Dispose(); } catch { }
                base.Dispose(disposing);
            }
        }
#endif
    }
}
