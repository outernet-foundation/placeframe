// #if UNITY_LUMIN
#pragma warning disable CS0618
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Threading;
using AOT;
using Cysharp.Threading.Tasks;
using UnityEngine;
using UnityEngine.XR.MagicLeap;
using UnityEngine.XR.MagicLeap.Native;
using static Plerion.NativeBindings;

namespace Plerion
{
    public static class MagicLeapCamera
    {
        public static bool initialized { get; private set; }
        private static bool permissionGranted = false;
        private static readonly MLPermissions.Callbacks permissionCallbacks = new MLPermissions.Callbacks();
        private static ulong nativeHandle = ulong.MaxValue;
        private static byte[] pixelBuffer;

        private static MLCameraDeviceAvailabilityStatusCallbacks deviceAvailabilityStatusCallbacks = new()
        {
            Version = 1u,
            OnDeviceAvailable = OnDeviceAvailable,
            OnDeviceUnavailable = OnDeviceUnavailable
        };

        private static MLCameraCaptureCallbacks captureCallbacks = new()
        {
            Version = 1u,
            OnCaptureFailed = OnCaptureFailedCallback,
            OnCaptureAborted = OnCaptureAbortedCallback,
            OnCaptureCompleted = OnCaptureCompletedCallback,
            OnImageBufferAvailable = OnImageBufferAvailableCallback,
            OnVideoBufferAvailable = OnVideoBufferAvailableCallback,
            OnPreviewBufferAvailable = OnPreviewBufferAvailableCallback
        };

        private static MLCameraDeviceStatusCallbacks deviceStatusCallbacks = new()
        {
            Version = 1u,
            OnDeviceStreaming = OnDeviceStreamingCallback,
            OnDeviceIdle = OnDeviceIdleCallback,
            OnDeviceDisconnected = OnDeviceDisconnectedCallback,
            OnDeviceError = OnDeviceErrorCallback
        };

        private static MLCameraConnectContext connectContext = new()
        {
            Version = 1u,
            CamId = Identifier.CV,
            Flags = ConnectFlag.CamOnly,
            EnableVideoStab = true,

            // We don't use this, but omitting it will result in MLCameraPrepareCapture failing
            MrInfo = new()
            {
                MrQuality = MRQuality._1440x1080,
                MrBlendType = MRBlendType.Additive,
                FrameRate = CaptureFrameRate._15FPS
            }
        };

        private static MLCameraCaptureConfig captureConfig = new()
        {
            Version = 1u,
            CaptureFrameRate = CaptureFrameRate._15FPS,
            NumStreams = 1,

            // The native API will return an "invalid param" error if there is only one element in this array
            StreamConfig = new MLCameraCaptureStreamConfig[2]
            {
                new ()
                {
                    CaptureType = CaptureType.Video,
                    Width = 3840,
                    Height = 2160,
                    OutputFormat = OutputFormat.YUV_420_888,
                    MediaRecorderSurfaceHandle = ulong.MaxValue
                },
                default,
            }
        };

        public static event Action<CameraImage?> onFrameReceived;

        public static void Initialize()
        {
            permissionCallbacks.OnPermissionGranted += (string permission) =>
            {
                if (permission != MLPermission.Camera) return;

                if (MLPermissions.CheckPermission(MLPermission.Camera).IsOk)
                {
                    Log.Info(LogGroup.Permissions, "Magic Leap Camera Permission Granted");
                    permissionGranted = true;
                }
                else
                {
                    Log.Warn(LogGroup.Permissions, "Magic Leap Camera Permission Denied");
                    permissionGranted = false;
                }
            };

            MLPermissions.RequestPermission(MLPermission.Camera, permissionCallbacks);
        }

        public static async UniTask Start()
        {
            if (!permissionGranted)
            {
                Log.Warn(LogGroup.MagicLeapCamera, "Magic Leap Camera Permission not granted yet?");
            }

            await UniTask.WaitUntil(() => permissionGranted);

            Check(MLCameraInit(ref deviceAvailabilityStatusCallbacks, IntPtr.Zero), "MLCameraInit");

            await UniTask.WaitUntil(() =>
            {
                MLResult.Code code = MLCameraGetDeviceAvailabilityStatus(Identifier.CV, out bool deviceAvailable);
                return code == 0 && deviceAvailable;
            });

            Check(MLCameraConnect(ref connectContext, out nativeHandle), "MLCameraConnect");
            Check(MLCameraSetCaptureCallbacks(nativeHandle, ref captureCallbacks, IntPtr.Zero), "MLCameraSetCaptureCallbacks");
            Check(MLCameraSetDeviceStatusCallbacks(nativeHandle, ref deviceStatusCallbacks, IntPtr.Zero), "MLCameraSetDeviceStatusCallbacks");
            Check(MLCameraPrepareCapture(nativeHandle, ref captureConfig, out var _), "MLCameraPrepareCapture");
            Check(MLCameraPreCaptureAEAWB(nativeHandle), "MLCameraPreCaptureAEAWB");

            await UniTask.NextFrame(); // Omitting this will result in a crash, couldn't figure out a callback to wait for instead

            Check(MLCameraCaptureVideoStart(nativeHandle), "MLCameraCaptureVideoStart");
        }

        public static void Stop()
        {
            Check(MLCameraCaptureVideoStop(nativeHandle), "MLCameraCaptureVideoStop");
            Check(MLCameraDisconnect(nativeHandle), "MLCameraDisconnect");
        }

        [MonoPInvokeCallback(typeof(MLCameraCaptureCallbacks.OnVideoBufferAvailableDelegate))]
        public static void OnVideoBufferAvailableCallback(ref MLCameraOutput output, ulong _, ref MLCameraResultExtras extra, IntPtr __)
        {
            if (extra.Intrinsics == IntPtr.Zero || onFrameReceived == null)
                return;

            var mLCameraIntrinsicCalibrationParameters = Marshal.PtrToStructure<MLCameraIntrinsicCalibrationParameters>(extra.Intrinsics);

            IntPtr data = output.Planes[0].Data;
            int width = (int)output.Planes[0].Width;
            int height = (int)output.Planes[0].Height;
            int pixelStride = (int)output.Planes[0].PixelsStride;
            int size = width * height * pixelStride;

            if (pixelBuffer is null || pixelBuffer.Length != size)
                pixelBuffer = new byte[size];

            Marshal.Copy(data, pixelBuffer, 0, size);

            onFrameReceived.Invoke(new CameraImage
            {
                imageWidth = width,
                imageHeight = height,
                pixelBuffer = pixelBuffer,
                focalLength = MLConvert.ToUnity(mLCameraIntrinsicCalibrationParameters.FocalLength),
                principalPoint = MLConvert.ToUnity(mLCameraIntrinsicCalibrationParameters.PrincipalPoint),
                cameraOrientation = Quaternion.Euler(0f, 0f, 180.0f)
            });
        }

        static void Check(MLResult.Code code, string functionName)
        {
            if (code != 0) throw new Exception($"{functionName} errored: {MLResult.CodeToString(code)}");
        }

        [MonoPInvokeCallback(typeof(MLCameraDeviceAvailabilityStatusCallbacks.DeviceAvailabilityStatusDelegate))]
        public static void OnDeviceAvailable(ref MLCameraDeviceAvailabilityInfo _)
        {
            Log.Info(LogGroup.MagicLeapCamera, "Magic Leap Camera Device Available");
        }

        [MonoPInvokeCallback(typeof(MLCameraDeviceAvailabilityStatusCallbacks.DeviceAvailabilityStatusDelegate))]
        public static void OnDeviceUnavailable(ref MLCameraDeviceAvailabilityInfo _)
        {
            Log.Warn(LogGroup.MagicLeapCamera, "Magic Leap Camera Device Unavailable");
        }

        [MonoPInvokeCallback(typeof(MLCameraCaptureCallbacks.OnCaptureFailedDelegate))]
        public static void OnCaptureFailedCallback(ref MLCameraResultExtras _, IntPtr __)
        {
            Log.Error(LogGroup.MagicLeapCamera, "Magic Leap Camera Capture Failed");
        }

        [MonoPInvokeCallback(typeof(MLCameraCaptureCallbacks.OnCaptureAbortedDelegate))]
        public static void OnCaptureAbortedCallback(IntPtr _)
        {
            Log.Error(LogGroup.MagicLeapCamera, "Magic Leap Camera Capture Aborted");
        }

        [MonoPInvokeCallback(typeof(MLCameraCaptureCallbacks.OnCaptureCompletedDelegate))]
        public static void OnCaptureCompletedCallback(ulong _, ref MLCameraResultExtras __, IntPtr ___)
        {
            Log.Trace(LogGroup.MagicLeapCamera, "Magic Leap Camera Capture Completed");
        }

        [MonoPInvokeCallback(typeof(MLCameraCaptureCallbacks.OnImageBufferAvailableDelegate))]
        public static void OnImageBufferAvailableCallback(ref MLCameraOutput _, ulong __, ref MLCameraResultExtras ___, IntPtr ____)
        {
            Log.Error(LogGroup.MagicLeapCamera, "Magic Leap Camera Image Buffer Available");
        }

        [MonoPInvokeCallback(typeof(MLCameraCaptureCallbacks.OnPreviewBufferAvailableDelegate))]
        public static void OnPreviewBufferAvailableCallback(ulong _, ulong __, ref MLCameraResultExtras ___, IntPtr ____)
        {
            Log.Error(LogGroup.MagicLeapCamera, "Magic Leap Camera Preview Buffer Available");
        }

        [MonoPInvokeCallback(typeof(MLCameraDeviceStatusCallbacks.OnDeviceStreamingDelegate))]
        public static void OnDeviceStreamingCallback(IntPtr _)
        {
            Log.Info(LogGroup.MagicLeapCamera, "Magic Leap Camera Device Streaming");
        }

        [MonoPInvokeCallback(typeof(MLCameraDeviceStatusCallbacks.OnDeviceIdleDelegate))]
        public static void OnDeviceIdleCallback(IntPtr _)
        {
            Log.Info(LogGroup.MagicLeapCamera, "Magic Leap Camera Device Idle");
        }

        [MonoPInvokeCallback(typeof(MLCameraDeviceStatusCallbacks.OnDeviceDisconnectedDelegate))]
        public static void OnDeviceDisconnectedCallback(DisconnectReason disconnectReason, IntPtr __)
        {
            Log.Warn(LogGroup.MagicLeapCamera, $"Magic Leap Camera Device Disconnected: {disconnectReason}");

            // async UniTask Reconnect()
            // {
            //     await UniTask.SwitchToMainThread();
            //     await UniTask.WaitForSeconds(1);

            //     Log.Info(LogGroup.MagicLeapCamera, "Reconnecting Magic Leap Camera");
            //     await StartCameraCapture();
            // }

            // UniTask
            //     .Create(Reconnect)
            //     .Forget();
        }

        [MonoPInvokeCallback(typeof(MLCameraDeviceStatusCallbacks.OnDeviceErrorDelegate))]
        public static void OnDeviceErrorCallback(ErrorType errorType, IntPtr __)
        {
            Log.Warn(LogGroup.MagicLeapCamera, $"Magic Leap Camera Device Error: {errorType}");
        }
    }
}
// #endif