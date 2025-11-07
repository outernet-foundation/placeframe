using System.Net.Http;
using System.Net.Http.Headers;

namespace Plerion.Client
{
    // This class intercepts and modifies HTTP requests to /data endpoints in order
    // to allow for following redirects, as those endpoints redirect to presigned URLs.
    public partial class ApiClient
    {
        partial void InterceptRequest(HttpRequestMessage req)
        {
            if (req.Method == HttpMethod.Put &&
                req.RequestUri != null &&
                req.RequestUri.AbsolutePath.EndsWith("/tar"))
            {
                req.Headers.ExpectContinue = true;
                if (req.Content != null && req.Content.Headers.ContentType == null)
                {
                    req.Content.Headers.ContentType =
                        new MediaTypeHeaderValue("application/octet-stream");
                }
            }
        }
    }
}