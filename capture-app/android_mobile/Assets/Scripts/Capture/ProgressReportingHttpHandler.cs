

using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

class ProgressReportingHttpClientHandler : HttpClientHandler
{
    private sealed class ProgressHttpContent : HttpContent
    {
        private readonly HttpContent inner;
        private readonly Action<long, long?> onProgress;
        private static readonly TimeSpan ProgressInterval = TimeSpan.FromSeconds(1);

        public ProgressHttpContent(HttpContent inner, Action<long, long?> onProgress)
        {
            this.inner = inner ?? throw new ArgumentNullException(nameof(inner));
            this.onProgress = onProgress ?? ((_, __) => { });
        }

        protected override bool TryComputeLength(out long length)
        {
            if (Headers.ContentLength is long L) { length = L; return true; }
            length = 0; return false;
        }

        protected override async Task SerializeToStreamAsync(Stream target, TransportContext _)
        {
            long? total = Headers.ContentLength; // set by caller above if known
            using var sourceStream = await inner.ReadAsStreamAsync().ConfigureAwait(false);

            var buffer = new byte[81920];
            long sent = 0;

            // Throttling state
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            TimeSpan lastReportAt = TimeSpan.Zero;

            // Initial report (0%) if we know total, otherwise just “started”
            onProgress(0, total);

            for (; ; )
            {
                int readCount = await sourceStream.ReadAsync(buffer, 0, buffer.Length).ConfigureAwait(false);
                if (readCount <= 0) break;

                await target.WriteAsync(buffer, 0, readCount).ConfigureAwait(false);
                sent += readCount;

                // Throttle: only report if at least one second passed
                var now = stopwatch.Elapsed;
                if (now - lastReportAt >= ProgressInterval)
                {
                    onProgress(sent, total);
                    lastReportAt = now;
                }
            }

            // Final report to ensure 100% (or “done” when total unknown)
            onProgress(sent, total);
        }

        protected override void Dispose(bool disposing)
        { if (disposing) inner.Dispose(); base.Dispose(disposing); }
    }

    private readonly IProgress<float> progress;

    public ProgressReportingHttpClientHandler(IProgress<float> progress)
    {
        this.progress = progress;
    }

    protected override async Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request, CancellationToken cancellationToken)
    {
        if (request.Content != null)
        {
            var originalContent = request.Content;
            var contentType = originalContent.Headers.ContentType;
            var contentLength = originalContent.Headers.ContentLength;

            request.Content = new ProgressHttpContent(request.Content, (sent, total) =>
            {
                float? percent = (total.HasValue && total.Value > 0)
                    ? (float)(sent * 100.0 / total.Value)
                    : (float?)null;
                progress.Report(percent ?? -1f);
            });

            if (contentType != null) request.Content.Headers.ContentType = contentType;
            if (contentLength.HasValue) request.Content.Headers.ContentLength = contentLength;
        }

        return await base.SendAsync(request, cancellationToken).ConfigureAwait(false);
    }
}