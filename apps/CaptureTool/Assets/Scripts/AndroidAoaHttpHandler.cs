#if !UNITY_EDITOR && UNITY_ANDROID
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using UnityEngine;

namespace Placeframe.Client
{
    public sealed class AndroidAoaHttpHandler : HttpMessageHandler
    {
        private readonly AndroidJavaObject heldActivity;

        public AndroidAoaHttpHandler()
        {
            AndroidJNI.AttachCurrentThread();
            heldActivity = new AndroidJavaClass("com.unity3d.player.UnityPlayer")
                .GetStatic<AndroidJavaObject>("currentActivity");
        }

        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken
        )
        {
            byte[] body = request.Content == null ? null : await request.Content.ReadAsByteArrayAsync();
            return await UniTask.RunOnThreadPool(
                () => SendSync(request, body, cancellationToken),
                cancellationToken: cancellationToken
            );
        }

        private HttpResponseMessage SendSync(HttpRequestMessage request, byte[] body, CancellationToken cancellationToken)
        {
            AndroidJNI.AttachCurrentThread();

            string requestId = Guid.NewGuid().ToString("N");
            request.Headers.TryAddWithoutValidation("X-Request-ID", requestId);

            int bodyLength = body?.Length ?? 0;
            Log.Info(
                LogGroup.Zed,
                "AOA req id={RequestId} {Method} {RequestUri} body={BodyLength}B",
                requestId, request.Method.Method, request.RequestUri, bodyLength
            );

            var stopwatch = Stopwatch.StartNew();
            try
            {
                var httpResponse = ExecuteOverAoa(request, body, cancellationToken);
                int status = (int)httpResponse.StatusCode;
                if (status >= 500)
                    Log.Error(
                        LogGroup.Zed,
                        "AOA res id={RequestId} {Method} {RequestUri} {Status} {ElapsedMs}ms",
                        requestId, request.Method.Method, request.RequestUri, status, stopwatch.ElapsedMilliseconds
                    );
                else
                    Log.Info(
                        LogGroup.Zed,
                        "AOA res id={RequestId} {Method} {RequestUri} {Status} {ElapsedMs}ms",
                        requestId, request.Method.Method, request.RequestUri, status, stopwatch.ElapsedMilliseconds
                    );
                return httpResponse;
            }
            catch (Exception exception)
            {
                if (exception is AndroidJavaException || exception is IOException || exception is OperationCanceledException)
                    Log.Info(
                        LogGroup.Zed, exception,
                        "AOA threw id={RequestId} {Method} {RequestUri} {ElapsedMs}ms",
                        requestId, request.Method.Method, request.RequestUri, stopwatch.ElapsedMilliseconds
                    );
                else
                    Log.Error(
                        LogGroup.Zed, exception,
                        "AOA threw id={RequestId} {Method} {RequestUri} {ElapsedMs}ms",
                        requestId, request.Method.Method, request.RequestUri, stopwatch.ElapsedMilliseconds
                    );
                throw;
            }
        }

        private HttpResponseMessage ExecuteOverAoa(HttpRequestMessage request, byte[] body, CancellationToken cancellationToken)
        {
            string contentType = request.Content?.Headers
                .Where(h => string.Equals(h.Key, "Content-Type", StringComparison.OrdinalIgnoreCase))
                .Select(h => string.Join(", ", h.Value))
                .FirstOrDefault();

            var contentHeaders = request.Content?.Headers
                .Where(h => !string.Equals(h.Key, "Content-Type", StringComparison.OrdinalIgnoreCase))
                ?? Enumerable.Empty<KeyValuePair<string, IEnumerable<string>>>();

            var headerNames = new List<string>();
            var headerValues = new List<string>();
            foreach (var (key, value) in request.Headers
                .Concat(contentHeaders)
                .SelectMany(h => h.Value, (h, v) => (h.Key, v)))
            {
                headerNames.Add(key);
                headerValues.Add(value);
            }

            using var result = AoaJni.Execute(
                heldActivity,
                request.Method.Method,
                request.RequestUri.ToString(),
                headerNames.ToArray(),
                headerValues.ToArray(),
                body,
                contentType
            );

            var response = AoaJni.Response(result);
            var bodyStream = AoaJni.BodyStream(result);
            string[] names = AoaJni.HeaderNames(result);
            string[] values = AoaJni.HeaderValues(result);

            try
            {
                var httpResponse = new HttpResponseMessage((HttpStatusCode)AoaJni.StatusCode(result));
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
                SafeCloseResponse(response);
                response?.Dispose();
                bodyStream?.Dispose();
                throw;
            }
        }

        private static void SafeCloseResponse(AndroidJavaObject response)
        {
            if (response == null) return;
            try { AoaJni.CloseResponse(response); } catch { }
        }

        // okhttp ResponseBody.byteStream() is not safe to call repeatedly
        // (each call wraps the source in a fresh InputStream that races on
        // shared state) — the Java side extracts it once into bodyStream.
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

                byte[] chunk = AoaJni.ReadChunk(bodyStream, count);
                if (chunk == null || chunk.Length == 0) return 0;
                Buffer.BlockCopy(chunk, 0, buffer, offset, chunk.Length);
                return chunk.Length;
            }

            protected override void Dispose(bool disposing)
            {
                if (disposed) return;
                disposed = true;
                SafeCloseResponse(response);
                response?.Dispose();
                bodyStream?.Dispose();
                base.Dispose(disposing);
            }
        }
    }
}
#endif
