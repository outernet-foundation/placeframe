using System;
using System.Net.Http;
using System.Threading;

namespace Placeframe.Auth
{
    public class AnonymousIdentityHttpHandler : DelegatingHandler
    {
        private readonly string _identity;

        public AnonymousIdentityHttpHandler(string identity)
        {
            if (string.IsNullOrEmpty(identity))
                throw new ArgumentException("identity must not be null or empty", nameof(identity));
            _identity = identity;
        }

        protected override System.Threading.Tasks.Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken
        )
        {
            request.Headers.Remove("X-Anonymous-Identity");
            request.Headers.Add("X-Anonymous-Identity", _identity);
            return base.SendAsync(request, cancellationToken);
        }
    }
}
