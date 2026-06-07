using System;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace Placeframe.Client
{
    public sealed class LoggingHttpHandler : DelegatingHandler
    {
        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken
        )
        {
            string requestId = Guid.NewGuid().ToString("N");
            request.Headers.TryAddWithoutValidation("X-Request-ID", requestId);

            long bodyLength = request.Content?.Headers.ContentLength ?? -1;
            Log.Info(
                LogGroup.Rest,
                "req id={RequestId} {Method} {RequestUri} body={BodyLength}B",
                requestId, request.Method.Method, request.RequestUri, bodyLength
            );

            var stopwatch = Stopwatch.StartNew();
            try
            {
                var response = await base.SendAsync(request, cancellationToken);
                int status = (int)response.StatusCode;
                if (status >= 500)
                    Log.Error(
                        LogGroup.Rest,
                        "res id={RequestId} {Method} {RequestUri} {Status} {ElapsedMs}ms",
                        requestId, request.Method.Method, request.RequestUri, status, stopwatch.ElapsedMilliseconds
                    );
                else
                    Log.Info(
                        LogGroup.Rest,
                        "res id={RequestId} {Method} {RequestUri} {Status} {ElapsedMs}ms",
                        requestId, request.Method.Method, request.RequestUri, status, stopwatch.ElapsedMilliseconds
                    );
                return response;
            }
            catch (Exception exception)
            {
                if (exception is OperationCanceledException || exception is IOException || exception is HttpRequestException)
                    Log.Info(
                        LogGroup.Rest, exception,
                        "threw id={RequestId} {Method} {RequestUri} {ElapsedMs}ms",
                        requestId, request.Method.Method, request.RequestUri, stopwatch.ElapsedMilliseconds
                    );
                else
                    Log.Error(
                        LogGroup.Rest, exception,
                        "threw id={RequestId} {Method} {RequestUri} {ElapsedMs}ms",
                        requestId, request.Method.Method, request.RequestUri, stopwatch.ElapsedMilliseconds
                    );
                throw;
            }
        }
    }
}
