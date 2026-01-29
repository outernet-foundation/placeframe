using Microsoft.Extensions.Configuration;
using Outernet.Shared;
using PlerionApiClient.Api;
using PlerionApiClient.Model;

namespace Outernet.Server
{
    public struct NodesWithinRadiusOfAnyUserRequest
    {
        public double[][] user_positions { get; set; }
        public double radius { get; set; }
        public int limit_count { get; set; }
    }

    public class AuthHttpHandler : DelegatingHandler
    {
        public TokenManager _tokenManager;

        public AuthHttpHandler(TokenManager tokenManager)
        {
            _tokenManager = tokenManager;
        }

        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken
        )
        {
            var token = await _tokenManager.GetTokenAsync();
            request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
            return await base.SendAsync(request, cancellationToken);
        }
    }

    public class PlerionAPI
    {
        public DefaultApi _api;

        public PlerionAPI(TokenManager tokenManager, IConfiguration config)
        {
            var apiUrl = config["API_INTERNAL_URL"] ?? "http://api:8000";
            _api = new DefaultApi(
                new HttpClient(new AuthHttpHandler(tokenManager) { InnerHandler = new HttpClientHandler() })
                {
                    BaseAddress = new Uri(apiUrl),
                },
                apiUrl
            );
        }

        public async Task<List<NodeRead>> GetNodes(IEnumerable<Double3> userPositions, double radius, int limit_count)
        {
            return await _api.GetNodesAsync();
        }
    }
}
