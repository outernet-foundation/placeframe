using Cysharp.Threading.Tasks;
using System.Net.Http;

namespace Placeframe.Auth
{
    public class TokenServerAuthorizationProvider : AuthorizationProvider
    {
        public override bool authorized => _authorized;
        public override HttpMessageHandler httpMessageHandler => _httpMessageHandler;

        public bool loginAutomatically;
        public string tokenUrl;
        public string clientId;
        public string username;
        public string password;

        private bool _authorized;
        private HttpMessageHandler _httpMessageHandler;

        private void Awake()
        {
            if (loginAutomatically)
                Login(tokenUrl, clientId, username, password).Forget();
        }

        public async UniTask Login(string tokenUrl, string clientId, string username, string password)
        {
            var httpHandler = new TokenServerHttpHandler();
            await httpHandler.Login(tokenUrl, clientId, username, password);
            _httpMessageHandler = httpHandler;
            _authorized = true;
        }
    }
}