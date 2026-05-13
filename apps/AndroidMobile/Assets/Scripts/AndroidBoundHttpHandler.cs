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
    // Per-socket network binding via JNI to a vendored okhttp 5.x client (see
    // Plugins/Android/BoundHttpClient.java). ConnectivityManager.bindProcessToNetwork
    // is process-wide and races against any concurrent code that flips it;
    // SocketsHttpHandler.ConnectCallback is absent from Unity 6's Android reference
    // assemblies and IL2CPP forbids reflection workarounds. Whole file compiles out
    // off-device because AndroidJavaObject is a no-op there; editor callers go
    // through InternetBoundHandler.Create() which returns null.
    //
    // One long-lived NetworkRequest per transport via ConnectivityManager.requestNetwork:
    // a bare getAllNetworks() lookup loses non-default networks (USB-ethernet alongside
    // wifi) after first idle on Pixel — the framework tears them down unless an app is
    // actively requesting them. One request per transport because NetworkRequest's
    // transport bits are AND-matched: a single multi-transport request can never be
    // satisfied (no Network is simultaneously wifi AND cellular), so the callback never
    // fulfils and Android keeps neither bearer wanted.
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
    //
    // okhttp 5: peek-FIN isHealthy + idempotent single retry against stale pooled
    // sockets, the failure mode Android's AOSP-bundled com.android.okhttp 2.x fork
    // (the HttpURLConnection backend) silently hits. pingInterval(30s) keeps HTTP/2
    // connections to ngrok fresh. http:// to the ZED stays HTTP/1.1 — okhttp doesn't
    // enable h2_prior_knowledge by default, and uvicorn speaks HTTP/1.1.
    public sealed class AndroidBoundHttpHandler : HttpMessageHandler
    {
        private const string BoundHttpClientClass = "io.placeframe.android.BoundHttpClient";

        // android.net.NetworkCapabilities.TRANSPORT_*: Cellular=0, Wifi=1, Ethernet=3.
        // Bluetooth (2) intentionally omitted.
        private readonly int[] transportInts;

        // The connectivity manager and callbacks must live for the lifetime of the
        // process — releasing any of them lets Android tear down the corresponding
        // network. The inherited HttpMessageHandler.Dispose is a no-op so a
        // transitive HttpClient.Dispose() leaves these fields intact; do not add a
        // Dispose override that releases them, and do not wrap a handler instance
        // in `using` — both paths kill the network mid-session.
        private AndroidJavaObject heldConnectivityManager;
        private AndroidJavaObject heldNetworkCallbacks;

        public AndroidBoundHttpHandler(bool forZedBox = false)
        {
            transportInts = forZedBox ? new[] { 3 } : new[] { 1, 0 };

            AndroidJNI.AttachCurrentThread();
            using var activity = new AndroidJavaClass("com.unity3d.player.UnityPlayer")
                .GetStatic<AndroidJavaObject>("currentActivity");
            heldConnectivityManager = activity.Call<AndroidJavaObject>("getSystemService", "connectivity");

            using var boundClient = new AndroidJavaClass(BoundHttpClientClass);
            heldNetworkCallbacks = boundClient.CallStatic<AndroidJavaObject>(
                "requestNetworks", heldConnectivityManager, transportInts);
        }

        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken
        )
        {
            byte[] body = request.Content == null ? null : await request.Content.ReadAsByteArrayAsync();
            return await Task.Run(() =>
            {
                AndroidJNI.AttachCurrentThread();

                var headerNames = new List<string>();
                var headerValues = new List<string>();
                string contentType = null;
                foreach (var header in request.Headers)
                    foreach (var value in header.Value)
                    {
                        headerNames.Add(header.Key);
                        headerValues.Add(value);
                    }
                if (request.Content != null)
                {
                    foreach (var header in request.Content.Headers)
                    {
                        if (string.Equals(header.Key, "Content-Type", StringComparison.OrdinalIgnoreCase))
                        {
                            contentType = string.Join(", ", header.Value);
                            continue;
                        }
                        foreach (var value in header.Value)
                        {
                            headerNames.Add(header.Key);
                            headerValues.Add(value);
                        }
                    }
                }

                using var boundClient = new AndroidJavaClass(BoundHttpClientClass);
                using var network = boundClient.CallStatic<AndroidJavaObject>(
                    "findMatchingNetwork", heldConnectivityManager, transportInts);
                if (network == null)
                    throw new IOException($"No network available with transports [{string.Join(",", transportInts)}]");

                // Blocks until response headers arrive; body streams lazily through
                // readChunk. AndroidJavaException on transport failure surfaces up
                // through the .NET handler chain as HttpRequestException.
                using var result = boundClient.CallStatic<AndroidJavaObject>(
                    "execute",
                    network, request.Method.Method, request.RequestUri.ToString(),
                    headerNames.ToArray(), headerValues.ToArray(), body, contentType
                );

                var response = result.Get<AndroidJavaObject>("response");
                var bodyStream = result.Get<AndroidJavaObject>("bodyStream");
                string[] names = result.Get<string[]>("headerNames");
                string[] values = result.Get<string[]>("headerValues");

                try
                {
                    var httpResponse = new HttpResponseMessage((HttpStatusCode)result.Get<int>("statusCode"));
                    httpResponse.Content = new StreamContent(new JavaInputStreamWrapper(response, bodyStream, cancellationToken));
                    for (int i = 0; i < names.Length; i++)
                    {
                        if (names[i] == null) continue;
                        HttpHeaders target = (string.Equals(names[i], "Content-Length", StringComparison.OrdinalIgnoreCase)
                            || string.Equals(names[i], "Content-Type", StringComparison.OrdinalIgnoreCase))
                            ? httpResponse.Content.Headers
                            : httpResponse.Headers;
                        target.TryAddWithoutValidation(names[i], values[i]);
                    }
                    return httpResponse;
                }
                catch
                {
                    try { boundClient.CallStatic("closeResponse", response); } catch { }
                    response?.Dispose();
                    bodyStream?.Dispose();
                    throw;
                }
            }, cancellationToken);
        }

        private sealed class JavaInputStreamWrapper : Stream
        {
            private readonly AndroidJavaObject response;
            private readonly AndroidJavaObject bodyStream;
            private readonly CancellationToken cancellationToken;
            private bool disposed;

            public JavaInputStreamWrapper(AndroidJavaObject response, AndroidJavaObject bodyStream, CancellationToken cancellationToken)
            {
                this.response = response;
                this.bodyStream = bodyStream;
                this.cancellationToken = cancellationToken;
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
                if (bodyStream == null) return 0;
                cancellationToken.ThrowIfCancellationRequested();
                AndroidJNI.AttachCurrentThread();

                using var boundClient = new AndroidJavaClass(BoundHttpClientClass);
                byte[] chunk = boundClient.CallStatic<byte[]>("readChunk", bodyStream, count);
                if (chunk == null || chunk.Length == 0) return 0;
                Buffer.BlockCopy(chunk, 0, buffer, offset, chunk.Length);
                return chunk.Length;
            }

            protected override void Dispose(bool disposing)
            {
                if (disposed) return;
                disposed = true;
                try
                {
                    using var boundClient = new AndroidJavaClass(BoundHttpClientClass);
                    boundClient.CallStatic("closeResponse", response);
                }
                catch { }
                response?.Dispose();
                bodyStream?.Dispose();
                base.Dispose(disposing);
            }
        }
    }
}
#endif
