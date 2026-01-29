using System;

namespace Outernet.Client
{
    public class ResponseDeserializationException : Exception
    {
        public string Url { get; private set; }
        public string Json { get; private set; }

        public ResponseDeserializationException(string url, string json, Exception innerException)
            : base("Response failed to deserialize", innerException)
        {
            Url = url;
            Json = json;
        }
    }
}