using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace Placeframe.Client
{
    // AsyncLocal lets callers attach an IProgress<float> to the implicit request
    // context without threading a parameter through generated API clients. The
    // handler reads Current at response time and binds it to the returned content
    // stream; uploads read it inside AndroidBoundHttpHandler and bind it to the
    // okhttp request body. Percent values are 0..100; -1 signals "in flight,
    // total unknown".
    public static class HttpProgressContext
    {
        private static readonly AsyncLocal<IProgress<float>> _current = new AsyncLocal<IProgress<float>>();

        public static IProgress<float> Current => _current.Value;

        public static IDisposable Set(IProgress<float> progress)
        {
            var prior = _current.Value;
            _current.Value = progress;
            return new Resetter(prior);
        }

        private sealed class Resetter : IDisposable
        {
            private readonly IProgress<float> _prior;
            public Resetter(IProgress<float> prior) { _prior = prior; }
            public void Dispose() { _current.Value = _prior; }
        }
    }

    // Wraps response Content so the generated client's ReadAsStreamAsync returns
    // a counting stream. Upload progress is handled below the chain because
    // AndroidBoundHttpHandler buffers the request body before handing it to
    // okhttp — observing bytes in this handler would track the local memcpy,
    // not the wire write.
    public sealed class ProgressTrackingHandler : DelegatingHandler
    {
        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken
        )
        {
            var response = await base.SendAsync(request, cancellationToken).ConfigureAwait(false);
            var progress = HttpProgressContext.Current;
            if (progress != null && response.Content != null)
            {
                response.Content = new ProgressReadingContent(response.Content, progress);
            }
            return response;
        }
    }

    internal sealed class ProgressReadingContent : HttpContent
    {
        private readonly HttpContent _inner;
        private readonly IProgress<float> _progress;
        private readonly long? _total;

        public ProgressReadingContent(HttpContent inner, IProgress<float> progress)
        {
            _inner = inner;
            _progress = progress;
            _total = inner.Headers.ContentLength;
            foreach (var h in inner.Headers)
                Headers.TryAddWithoutValidation(h.Key, h.Value);
        }

        protected override Task SerializeToStreamAsync(Stream target, TransportContext context) =>
            _inner.CopyToAsync(target);

        protected override async Task<Stream> CreateContentReadStreamAsync()
        {
            var src = await _inner.ReadAsStreamAsync().ConfigureAwait(false);
            return new ProgressReadingStream(src, _total, _progress);
        }

        protected override bool TryComputeLength(out long length)
        {
            if (_total.HasValue) { length = _total.Value; return true; }
            length = 0;
            return false;
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing) _inner.Dispose();
            base.Dispose(disposing);
        }
    }

    internal sealed class ProgressReadingStream : Stream
    {
        private static readonly TimeSpan ReportInterval = TimeSpan.FromMilliseconds(200);

        private readonly Stream _inner;
        private readonly long? _total;
        private readonly IProgress<float> _progress;
        private long _read;
        private DateTime _lastReport = DateTime.MinValue;
        private bool _disposed;

        public ProgressReadingStream(Stream inner, long? total, IProgress<float> progress)
        {
            _inner = inner;
            _total = total;
            _progress = progress;
            _progress.Report(_total.HasValue && _total.Value > 0 ? 0f : -1f);
        }

        public override bool CanRead => _inner.CanRead;
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
            int n = _inner.Read(buffer, offset, count);
            if (n > 0) Advance(n, done: false);
            return n;
        }

        public override async Task<int> ReadAsync(byte[] buffer, int offset, int count, CancellationToken cancellationToken)
        {
            int n = await _inner.ReadAsync(buffer, offset, count, cancellationToken).ConfigureAwait(false);
            if (n > 0) Advance(n, done: false);
            return n;
        }

        protected override void Dispose(bool disposing)
        {
            if (_disposed) return;
            _disposed = true;
            if (disposing)
            {
                Advance(0, done: true);
                _inner.Dispose();
            }
            base.Dispose(disposing);
        }

        private void Advance(int n, bool done)
        {
            _read += n;
            var now = DateTime.UtcNow;
            if (!done && now - _lastReport < ReportInterval) return;
            _lastReport = now;
            if (_total.HasValue && _total.Value > 0)
                _progress.Report((float)(_read * 100.0 / _total.Value));
            else
                _progress.Report(-1f);
        }
    }
}
