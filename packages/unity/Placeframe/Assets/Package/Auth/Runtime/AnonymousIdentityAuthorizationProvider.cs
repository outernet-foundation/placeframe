using System.Net.Http;

namespace Placeframe.Auth
{
    public class AnonymousIdentityAuthorizationProvider : AuthorizationProvider
    {
        public override bool authorized => true;
        public override HttpMessageHandler httpMessageHandler => _httpMessageHandler;

        public string identity;

        private HttpMessageHandler _httpMessageHandler;

        private void Awake()
        {
            _httpMessageHandler = new AnonymousIdentityHttpHandler(identity);
        }
    }
}
