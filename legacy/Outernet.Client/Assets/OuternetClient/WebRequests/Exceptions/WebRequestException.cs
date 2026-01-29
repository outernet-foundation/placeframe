using System;
using UnityEngine.Networking;

namespace Outernet.Client
{
    public class WebRequestException : Exception
    {
        public UnityWebRequest.Result UnityWebRequestResult { get; private set; }
        public long StatusCode { get; private set; }
        public string Response { get; private set; }

        public WebRequestException(UnityWebRequest.Result unityWebRequestResult, string message, long statusCode, string response) : base(message)
        {
            UnityWebRequestResult = unityWebRequestResult;
            StatusCode = statusCode;
            Response = response;
        }
    }
}