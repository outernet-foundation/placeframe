#if !UNITY_EDITOR && UNITY_ANDROID
using UnityEngine;

namespace Placeframe.Client
{
    // Strongly-typed wrappers over every JNI lookup into
    // io.placeframe.android.AoaAccessoryClient. The stringly-typed method
    // and field names live here exactly once; call sites get compile-checked
    // signatures and a single place to update when the Java contract changes.
    internal static class AoaJni
    {
        private static readonly AndroidJavaClass cls = new("io.placeframe.android.AoaAccessoryClient");

        public static AndroidJavaObject Execute(
            AndroidJavaObject activity,
            string method,
            string url,
            string[] headerNames,
            string[] headerValues,
            byte[] body,
            string contentType
        ) => cls.CallStatic<AndroidJavaObject>(
            "execute", activity, method, url, headerNames, headerValues, body, contentType);

        public static byte[] ReadChunk(AndroidJavaObject stream, int maxSize) =>
            cls.CallStatic<byte[]>("readChunk", stream, maxSize);

        public static void CloseResponse(AndroidJavaObject response) =>
            cls.CallStatic("closeResponse", response);

        public static int StatusCode(AndroidJavaObject result) => result.Get<int>("statusCode");
        public static string[] HeaderNames(AndroidJavaObject result) => result.Get<string[]>("headerNames");
        public static string[] HeaderValues(AndroidJavaObject result) => result.Get<string[]>("headerValues");
        public static AndroidJavaObject Response(AndroidJavaObject result) => result.Get<AndroidJavaObject>("response");
        public static AndroidJavaObject BodyStream(AndroidJavaObject result) => result.Get<AndroidJavaObject>("bodyStream");
    }
}
#endif
