using System;
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
            try
            {
                var response = await base.SendAsync(request, cancellationToken);
                if (!response.IsSuccessStatusCode)
                    Log.Error(
                        LogGroup.Rest,
                        $"{request.Method} {request.RequestUri} → {(int)response.StatusCode} {response.ReasonPhrase}"
                    );
                return response;
            }
            catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
            {
                throw;
            }
            catch (Exception exception)
            {
                Log.Error(
                    LogGroup.Rest,
                    $"{request.Method} {request.RequestUri} threw {exception.GetType().Name}: {exception.Message}"
                );
                throw;
            }
        }
    }
}
