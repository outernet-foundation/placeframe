using System.Net.Http;

namespace Placeframe.Client
{
    // Factory for the "wifi or cellular, never the ZED USB-ethernet link" handler
    // shape used by every internet-bound HttpClient in the app. Returns null off
    // Android-device so callers can fall through to the default HttpClientHandler.
    public static class InternetBoundHandler
    {
        public static HttpMessageHandler Create()
        {
#if !UNITY_EDITOR && UNITY_ANDROID
            return new AndroidBoundHttpHandler();
#else
            return null;
#endif
        }
    }
}
