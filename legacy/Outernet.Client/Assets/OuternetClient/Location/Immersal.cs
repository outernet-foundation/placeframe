using UnityEngine;
using System;
using System.Runtime.InteropServices;
using Cysharp.Threading.Tasks;
using AOT;

namespace Outernet.Client.Location
{
    [StructLayout(LayoutKind.Sequential)]
    public struct LocalizeResult
    {
        public int mapId;
        public Vector3 position;
        public Quaternion rotation;
        public int confidence;
    };

    public static class ImmersalNative
    {
#if UNITY_IOS && !UNITY_EDITOR
        private const string Assembly = "__Internal";
#else
        private const string Assembly = "PosePlugin";
#endif

        static private string developerToken = "27ffb72bff36b8b4a2b94d9eec8976b28015e25434cadd6a9d92caa7da1afe0f";

        static object lockObject = new object();

        static public void Initialize()
        {
            icvValidateUser(developerToken);

            LogCallback callback_delegate = new LogCallback(LogImmersal);
            IntPtr intptr_delegate = Marshal.GetFunctionPointerForDelegate(callback_delegate);
            PP_RegisterLogCallback(intptr_delegate);
        }

        static public void SetInteger(string parameter, int value)
        {
            icvSetInteger(parameter, value);
        }

        static public async UniTask<int> LoadMap(byte[] buffer)
        {
            int result = 0;
            await UniTask.RunOnThreadPool(() =>
            {
                lock (lockObject)
                {
                    result = icvLoadMap(buffer);
                }
            });
            return result;
        }

        static public async UniTask FreeMap(int mapHandle)
        {
            await UniTask.RunOnThreadPool(() =>
            {
                lock (lockObject)
                {
                    icvFreeMap(mapHandle);
                }
            });
        }

        static public async UniTask<int> PointsGetCount(int mapHandle)
        {
            int result = 0;
            await UniTask.RunOnThreadPool(() =>
            {
                lock (lockObject)
                {
                    result = icvPointsGetCount(mapHandle);
                }
            });
            return result;
        }

        static public async UniTask<Vector3[]> PointsGet(int mapHandle, int maxCount)
        {
            Vector3[] result = new Vector3[maxCount];
            await UniTask.RunOnThreadPool(() =>
            {
                lock (lockObject)
                {
                    GCHandle vector3ArrayHandle = GCHandle.Alloc(result, GCHandleType.Pinned);
                    icvPointsGet(mapHandle, vector3ArrayHandle.AddrOfPinnedObject(), maxCount);
                    vector3ArrayHandle.Free();
                }
            });
            return result;
        }

        static public async UniTask<LocalizeResult> Localize(int n, IntPtr handles, int width,
            int height, Vector4 intrinsics, IntPtr pixels, int channels, int solverType, Quaternion cameraRotation)
        {
            LocalizeResult result = new LocalizeResult();
            await UniTask.RunOnThreadPool(() =>
            {
                lock (lockObject)
                {
                    result = icvLocalize(n, handles, width, height, ref intrinsics, pixels, channels, solverType, ref cameraRotation);
                }
            });
            return result;
        }

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate void LogCallback(IntPtr msg);

        [MonoPInvokeCallback(typeof(LogCallback))]
        public static void LogImmersal(IntPtr ansiString)
        {
            Log.Debug(LogGroup.Immersal, Marshal.PtrToStringAnsi(ansiString));
        }

        [DllImport(Assembly, CallingConvention = CallingConvention.Cdecl)]
        public static extern void PP_RegisterLogCallback(IntPtr callbackDelegate);

        [DllImport(Assembly, CallingConvention = CallingConvention.Cdecl)]
        private static extern int icvValidateUser([MarshalAs(UnmanagedType.LPStr)] string token);

        /// Available parameters:
        /// "LocalizationMaxPixels" - 0 is no limit (the default), 960*720 or higher.
        /// "NumThreads" - how many CPU cores to use; -1 (system default) or a positive integer.
        /// "ImageCompressionLevel" - 0 (no compression, fastest) to 9 (slowest). Defaults to 4.
        /// </summary>
        /// <param name="parameter">Parameter name</param>
        /// <param name="value">An integer parameter value</param>
        /// <returns>Returns 1 if succeeded, -1 otherwise.</returns>
        [DllImport(Assembly, CallingConvention = CallingConvention.Cdecl)]
        private static extern int icvSetInteger([MarshalAs(UnmanagedType.LPStr)] string parameter, int value);

        [DllImport(Assembly, CallingConvention = CallingConvention.Cdecl)]
        private static extern int icvLoadMap(byte[] buffer);

        [DllImport(Assembly, CallingConvention = CallingConvention.Cdecl)]
        private static extern int icvFreeMap(int mapHandle);

        [DllImport(Assembly, CallingConvention = CallingConvention.Cdecl)]
        private static extern int icvPointsGet(int mapHandle, IntPtr array, int maxCount);

        [DllImport(Assembly, CallingConvention = CallingConvention.Cdecl)]
        private static extern int icvPointsGetCount(int mapHandle);

        [DllImport(Assembly, CallingConvention = CallingConvention.Cdecl)]
        private static extern LocalizeResult icvLocalize(int n, IntPtr handles, int width,
            int height, ref Vector4 intrinsics, IntPtr pixels, int channels, int solverType, ref Quaternion cameraRotation);
    }
}