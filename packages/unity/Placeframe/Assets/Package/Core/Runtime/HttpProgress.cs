using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace Placeframe.Core
{
    // AsyncLocal lets callers attach an IProgress<float> to the implicit request
    // context without threading a parameter through generated API clients. The
    // handler reads Current at send time and wraps the outgoing request body.
    // Percent values are 0..100; -1 signals "in flight, total unknown".
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

    public sealed class ProgressTrackingHandler : DelegatingHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken
        )
        {
            var progress = HttpProgressContext.Current;
            if (progress != null && request.Content != null)
            {
                request.Content = new ProgressWritingContent(request.Content, progress);
            }
            return base.SendAsync(request, cancellationToken);
        }
    }

    internal sealed class ProgressWritingContent : HttpContent
    {
        private readonly HttpContent _inner;
        private readonly IProgress<float> _progress;
        private readonly long? _total;

        public ProgressWritingContent(HttpContent inner, IProgress<float> progress)
        {
            _inner = inner;
            _progress = progress;
            _total = inner.Headers.ContentLength;
            foreach (var header in inner.Headers)
                Headers.TryAddWithoutValidation(header.Key, header.Value);
        }

        // CopyToAsync routes through SerializeToStreamAsync against the target stream directly.
        // ReadAsStreamAsync would instead trigger Mono's HttpContent.LoadIntoBufferAsync — for
        // MultipartFormDataContent in particular this fully materializes every part before
        // yielding, collapsing a streaming passthrough into a phone-side download-then-upload.
        protected override async Task SerializeToStreamAsync(Stream target, TransportContext context)
        {
            _progress.Report(_total.HasValue && _total.Value > 0 ? 0f : -1f);
            using var progressTarget = new ProgressReportingStream(target, _progress, _total);
            await _inner.CopyToAsync(progressTarget, context).ConfigureAwait(false);
            if (_total.HasValue && _total.Value > 0)
                _progress.Report(100f);
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

        private sealed class ProgressReportingStream : Stream
        {
            private static readonly TimeSpan ReportInterval = TimeSpan.FromMilliseconds(200);

            private readonly Stream _inner;
            private readonly IProgress<float> _progress;
            private readonly long? _total;
            private long _written;
            private DateTime _lastReport = DateTime.MinValue;

            public ProgressReportingStream(Stream inner, IProgress<float> progress, long? total)
            {
                _inner = inner;
                _progress = progress;
                _total = total;
            }

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
                if (_total.HasValue && _total.Value > 0)
                    _progress.Report((float)(_written * 100.0 / _total.Value));
                else
                    _progress.Report(-1f);
            }
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
