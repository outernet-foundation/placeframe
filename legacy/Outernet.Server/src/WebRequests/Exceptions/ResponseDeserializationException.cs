namespace Outernet.Server
{
    public class ResponseDeserializationException : Exception
    {
        public string Url { get; }
        public string ResponseContent { get; }

        public ResponseDeserializationException(string url, string responseContent, Exception innerException)
            : base($"Failed to deserialize response from {url}", innerException)
        {
            Url = url;
            ResponseContent = responseContent;
        }
    }

}