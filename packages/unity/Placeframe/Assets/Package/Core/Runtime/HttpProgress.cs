using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;

namespace Placeframe.Core
{
    public readonly struct UploadProgress
    {
        public readonly float? Percent;
        public readonly long BytesSent;
        public readonly long? BytesTotal;
        public readonly double? BytesPerSecond;

        public UploadProgress(float? percent, long bytesSent, long? bytesTotal, double? bytesPerSecond)
        {
            Percent = percent;
            BytesSent = bytesSent;
            BytesTotal = bytesTotal;
            BytesPerSecond = bytesPerSecond;
        }
    }

    // AsyncLocal lets callers attach an IProgress<UploadProgress> to the implicit
    // request context without threading a parameter through generated API clients.
    // The transport handler reads Current at send time and reports the wire write.
    public static class HttpProgressContext
    {
        private static readonly AsyncLocal<IProgress<UploadProgress>> _current = new AsyncLocal<IProgress<UploadProgress>>();

        public static IProgress<UploadProgress> Current => _current.Value;

        public static IDisposable Set(IProgress<UploadProgress> progress)
        {
            var prior = _current.Value;
            _current.Value = progress;
            return new Resetter(prior);
        }

        private sealed class Resetter : IDisposable
        {
            private readonly IProgress<UploadProgress> _prior;
            public Resetter(IProgress<UploadProgress> prior) { _prior = prior; }
            public void Dispose() { _current.Value = _prior; }
        }
    }

    // The internet HTTP transport. Sends request bodies unbuffered over HttpWebRequest so
    // writes block on actual TCP transmission; when an HttpProgressContext is scoped, the
    // body is buffered once, pinned with Content-Length, and copied to the wire in chunks
    // through ProgressReportingStream, so reported progress counts bytes that have left
    // the process. A DelegatingHandler that counts writes into an arbitrary inner
    // transport cannot promise this: every stock handler is entitled to buffer the body
    // (Mono's HttpClientHandler leaves HttpWebRequest.AllowWriteStreamBuffering at its
    // default true), which reduces "progress" to a memory copy that finishes in seconds
    // while the real send proceeds unobserved.
    public sealed class ProgressReportingHttpHandler : HttpMessageHandler
    {
        private const int CopyChunkBytes = 64 * 1024;

        private static readonly HashSet<string> ResponseContentHeaderNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "Allow", "Content-Disposition", "Content-Encoding", "Content-Language",
            "Content-Length", "Content-Location", "Content-MD5", "Content-Range",
            "Content-Type", "Expires", "Last-Modified"
        };

        static ProgressReportingHttpHandler()
        {
            ServicePointManager.Expect100Continue = false;
            ServicePointManager.DefaultConnectionLimit = 16;
        }

        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken
        )
        {
            var progress = HttpProgressContext.Current;
            HttpContent content = request.Content;
            if (progress != null && content != null)
                content = await BufferForProgressAsync(content, progress).ConfigureAwait(false);

            var webRequest = CreateWebRequest(request, content);
            using (cancellationToken.Register(() => webRequest.Abort()))
            {
                if (content != null)
                    await WriteBodyAsync(webRequest, content, progress).ConfigureAwait(false);

                try
                {
                    var webResponse = (HttpWebResponse)await webRequest.GetResponseAsync().ConfigureAwait(false);
                    return BuildResponse(webResponse);
                }
                catch (WebException exception) when (exception.Status == WebExceptionStatus.RequestCanceled)
                {
                    throw new OperationCanceledException(cancellationToken);
                }
                catch (WebException exception) when (exception.Response is HttpWebResponse errorResponse)
                {
                    return BuildResponse(errorResponse);
                }
                catch (WebException exception)
                {
                    throw new HttpRequestException(exception.Message, exception);
                }
            }
        }

        // The body is fully buffered before send so the wire write is a single known-length
        // byte array (incremental multipart streaming stalls on IL2CPP Android builds) and
        // so lazily-streamed sources (the AOA tar fetch) are drained in one deterministic
        // phase before the wire phase begins. Cost: one full copy held for the send.
        private static async Task<HttpContent> BufferForProgressAsync(
            HttpContent content,
            IProgress<UploadProgress> progress
        )
        {
            var bytes = await content.ReadAsByteArrayAsync().ConfigureAwait(false);
            var buffered = new ByteArrayContent(bytes);
            foreach (var header in content.Headers)
                buffered.Headers.TryAddWithoutValidation(header.Key, header.Value);
            content.Dispose();

            var total = buffered.Headers.ContentLength;
            progress.Report(new UploadProgress(
                percent: total.HasValue && total.Value > 0 ? 0f : (float?)null,
                bytesSent: 0,
                bytesTotal: total,
                bytesPerSecond: null));
            return buffered;
        }

        private static HttpWebRequest CreateWebRequest(HttpRequestMessage request, HttpContent content)
        {
            var webRequest = (HttpWebRequest)WebRequest.Create(request.RequestUri);
            webRequest.Method = request.Method.Method;
            webRequest.AllowWriteStreamBuffering = false;
            webRequest.AllowAutoRedirect = true;
            // HttpClient.Timeout governs end-to-end; per-request ceilings would abort
            // long uploads.
            webRequest.Timeout = Timeout.Infinite;
            webRequest.ReadWriteTimeout = Timeout.Infinite;

            foreach (var header in request.Headers)
            {
                // Accept, Referer, and User-Agent are restricted on HttpWebRequest and
                // must go through their dedicated properties; Host, Expect, and
                // Connection are owned by the transport itself.
                if (header.Key == "Accept")
                {
                    webRequest.Accept = string.Join(", ", header.Value);
                    continue;
                }
                if (header.Key == "Referer")
                {
                    webRequest.Referer = string.Join(", ", header.Value);
                    continue;
                }
                if (header.Key == "User-Agent")
                {
                    webRequest.UserAgent = string.Join(", ", header.Value);
                    continue;
                }
                if (header.Key == "Host" || header.Key == "Expect" || header.Key == "Connection" || header.Key == "Transfer-Encoding")
                    continue;

                foreach (var value in header.Value)
                    webRequest.Headers.Add(header.Key, value);
            }

            if (content != null)
            {
                foreach (var header in content.Headers)
                {
                    if (header.Key == "Content-Type")
                        webRequest.ContentType = string.Join(", ", header.Value);
                    else if (header.Key != "Content-Length")
                        foreach (var value in header.Value)
                            webRequest.Headers.Add(header.Key, value);
                }
            }

            return webRequest;
        }

        private static async Task WriteBodyAsync(
            HttpWebRequest webRequest,
            HttpContent content,
            IProgress<UploadProgress> progress
        )
        {
            // Mono requires Content-Length (or SendChunked) before handing out an
            // unbuffered request stream; the buffered body always carries a length.
            var length = content.Headers.ContentLength;
            if (length.HasValue)
                webRequest.ContentLength = length.Value;
            else
                webRequest.SendChunked = true;

            using var requestStream = await webRequest.GetRequestStreamAsync().ConfigureAwait(false);

            if (progress == null)
            {
                await content.CopyToAsync(requestStream).ConfigureAwait(false);
                return;
            }

            // A single whole-body write would surface exactly one tick after the entire
            // transfer; chunked writes tick while the unbuffered stream blocks on the
            // socket.
            using var progressStream = new ProgressReportingStream(requestStream, progress, length);
            var buffer = new byte[CopyChunkBytes];
            using var source = await content.ReadAsStreamAsync().ConfigureAwait(false);
            while (true)
            {
                int read = await source.ReadAsync(buffer, 0, buffer.Length).ConfigureAwait(false);
                if (read == 0)
                    break;
                await progressStream.WriteAsync(buffer, 0, read).ConfigureAwait(false);
            }

            if (length.HasValue && length.Value > 0)
                progress.Report(new UploadProgress(
                    percent: 100f,
                    bytesSent: length.Value,
                    bytesTotal: length,
                    bytesPerSecond: progressStream.LastBytesPerSecond));
        }

        private static HttpResponseMessage BuildResponse(HttpWebResponse webResponse)
        {
            var response = new HttpResponseMessage(webResponse.StatusCode)
            {
                ReasonPhrase = webResponse.StatusDescription,
                Content = new StreamContent(webResponse.GetResponseStream())
            };

            foreach (var key in webResponse.Headers.AllKeys)
            {
                var target = ResponseContentHeaderNames.Contains(key)
                    ? (HttpHeaders)response.Content.Headers
                    : response.Headers;
                target.TryAddWithoutValidation(key, webResponse.Headers.GetValues(key));
            }

            return response;
        }
    }

    internal sealed class ProgressReportingStream : Stream
    {
        private static readonly TimeSpan ReportInterval = TimeSpan.FromMilliseconds(200);
        private static readonly TimeSpan SpeedWindow = TimeSpan.FromSeconds(1);

        private readonly Stream _inner;
        private readonly IProgress<UploadProgress> _progress;
        private readonly long? _total;
        private readonly Queue<(DateTime time, long bytes)> _speedSamples = new Queue<(DateTime, long)>();
        private long _written;
        private DateTime _lastReport = DateTime.MinValue;
        private double? _lastBytesPerSecond;

        public ProgressReportingStream(Stream inner, IProgress<UploadProgress> progress, long? total)
        {
            _inner = inner;
            _progress = progress;
            _total = total;
        }

        public double? LastBytesPerSecond => _lastBytesPerSecond;

        public override bool CanRead => false;
        public override bool CanSeek => false;
        public override bool CanWrite => true;
        public override long Length => throw new NotSupportedException();
        public override long Position { get => throw new NotSupportedException(); set => throw new NotSupportedException(); }
        public override void Flush() => _inner.Flush();
        public override Task FlushAsync(CancellationToken cancellationToken) => _inner.FlushAsync(cancellationToken);
        public override int Read(byte[] buffer, int offset, int count) => throw new NotSupportedException();
        public override long Seek(long offset, SeekOrigin origin) => throw new NotSupportedException();
        public override void SetLength(long value) => throw new NotSupportedException();

        public override void Write(byte[] buffer, int offset, int count)
        {
            _inner.Write(buffer, offset, count);
            _written += count;
            MaybeReport();
        }

        public override async Task WriteAsync(byte[] buffer, int offset, int count, CancellationToken cancellationToken)
        {
            await _inner.WriteAsync(buffer, offset, count, cancellationToken).ConfigureAwait(false);
            _written += count;
            MaybeReport();
        }

        private void MaybeReport()
        {
            var now = DateTime.UtcNow;
            if (now - _lastReport < ReportInterval) return;
            _lastReport = now;

            _speedSamples.Enqueue((now, _written));
            while (_speedSamples.Count > 1 && now - _speedSamples.Peek().time > SpeedWindow)
                _speedSamples.Dequeue();

            var oldest = _speedSamples.Peek();
            var elapsed = (now - oldest.time).TotalSeconds;
            _lastBytesPerSecond = elapsed > 0 ? (_written - oldest.bytes) / elapsed : (double?)null;

            _progress.Report(new UploadProgress(
                percent: _total.HasValue && _total.Value > 0 ? (float?)(_written * 100.0 / _total.Value) : null,
                bytesSent: _written,
                bytesTotal: _total,
                bytesPerSecond: _lastBytesPerSecond));
        }
    }

    // Forward-only stream that advertises a known Length so StreamContent.TryComputeLength
    // sets Content-Length on the multipart request. Position-get tracks bytes read so
    // StreamContent's `Length - Position` arithmetic stays honest after partial consumption;
    // Seek and Position-set throw because the underlying stream is a live wire read.
    public sealed class LengthOnlyStream : Stream
    {
        private readonly Stream _inner;
        private readonly long _length;
        private long _position;

        public LengthOnlyStream(Stream inner, long length)
        {
            _inner = inner;
            _length = length;
        }

        public override bool CanRead => _inner.CanRead;
        public override bool CanSeek => true;
        public override bool CanWrite => false;
        public override long Length => _length;
        public override long Position
        {
            get => _position;
            set => throw new NotSupportedException();
        }

        public override void Flush() { }
        public override long Seek(long offset, SeekOrigin origin) => throw new NotSupportedException();
        public override void SetLength(long value) => throw new NotSupportedException();
        public override void Write(byte[] buffer, int offset, int count) => throw new NotSupportedException();

        public override int Read(byte[] buffer, int offset, int count)
        {
            int n = _inner.Read(buffer, offset, count);
            _position += n;
            return n;
        }

        public override async Task<int> ReadAsync(byte[] buffer, int offset, int count, CancellationToken cancellationToken)
        {
            int n = await _inner.ReadAsync(buffer, offset, count, cancellationToken).ConfigureAwait(false);
            _position += n;
            return n;
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing) _inner.Dispose();
            base.Dispose(disposing);
        }
    }
}
