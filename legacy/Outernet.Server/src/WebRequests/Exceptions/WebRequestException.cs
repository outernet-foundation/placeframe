using System.Net;

namespace Outernet.Server
{
    public class WebRequestException : Exception
    {
        public HttpStatusCode? StatusCode { get; }
        public string ResponseText { get; }

        public WebRequestException(string message, HttpStatusCode? statusCode, string responseText)
            : base(message)
        {
            StatusCode = statusCode;
            ResponseText = responseText;
        }

        public WebRequestException(string message, HttpStatusCode? statusCode, string responseText, Exception innerException)
            : base(message, innerException)
        {
            StatusCode = statusCode;
            ResponseText = responseText;
        }
    }
}