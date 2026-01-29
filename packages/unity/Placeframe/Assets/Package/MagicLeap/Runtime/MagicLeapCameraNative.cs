#if MAGIC_LEAP
using System;
using System.Runtime.InteropServices;
using UnityEngine.XR.MagicLeap;
using UnityEngine.XR.MagicLeap.Native;

namespace Placeframe.Core.MagicLeap
{
    public class NativeBindings : MagicLeapNativeBindings
    {
        public enum ErrorType
        {
            None,
            Invalid,
            Disabled,
            DeviceFailed,
            ServiceFailed,
            CaptureFailed,
        }

        public enum Identifier
        {
            Main,
            CV,
        }

        public enum DisconnectReason
        {
            DeviceLost,
            PriorityLost,
        }

        public enum MRQuality
        {
            _648x720 = 1,
            _972x1080,
            _1944x2160,
            _960x720,
            _1440x1080,
            _2880x2160,
        }

        public struct MLCameraMRConnectInfo
        {
            public MRQuality MrQuality;
            public MRBlendType MrBlendType;
            public CaptureFrameRate FrameRate;
        }

        public enum MRBlendType
        {
            Additive = 1,
        }

        public enum CaptureFrameRate
        {
            None,
            _15FPS,
            _30FPS,
            _60FPS,
        }

        public enum ConnectFlag
        {
            CamOnly,
            VirtualOnly,
            MR,
        }

        public enum OutputFormat
        {
            YUV_420_888 = 1,
            JPEG,
            RGBA_8888,
        }

        public enum CaptureType
        {
            Image,
            Video,
            Preview,
        }

        public struct MLCameraConnectContext
        {
            public uint Version;

            public Identifier CamId;

            public ConnectFlag Flags;

            [MarshalAs(UnmanagedType.I1)]
            public bool EnableVideoStab;

            public MLCameraMRConnectInfo MrInfo;
        }

        public struct MLCameraCaptureStreamConfig
        {
            public CaptureType CaptureType;
            public int Width;
            public int Height;
            public OutputFormat OutputFormat;
            public ulong MediaRecorderSurfaceHandle;
        }

        public struct MLCameraCaptureConfig
        {
            public uint Version;

            public CaptureFrameRate CaptureFrameRate;

            public uint NumStreams;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 2)]
            public MLCameraCaptureStreamConfig[] StreamConfig;
        }

        public struct MLCameraPlaneInfo
        {
            public uint Version;
            public uint Width;
            public uint Height;
            public uint Stride;
            public uint BytesPerPixel;
            public uint PixelsStride;
            public IntPtr Data;
            public uint Size;
        }

        public struct MLCameraOutput
        {
            public uint Version;

            public byte PlaneCount;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 3)]
            public MLCameraPlaneInfo[] Planes;

            public OutputFormat Format;
        }

        public readonly struct MLCameraIntrinsicCalibrationParameters
        {
            public readonly uint Version;
            public readonly uint Width;
            public readonly uint Height;
            public readonly MLVec2f FocalLength;
            public readonly MLVec2f PrincipalPoint;
            public readonly float FOV;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 5)]
            public readonly double[] Distortion;
        }

        public readonly struct MLCameraResultExtras
        {
            public readonly uint Version;
            public readonly long FrameNumber;
            public readonly long VcamTimestamp;
            public readonly IntPtr Intrinsics;
        }

        public readonly struct MLCameraDeviceAvailabilityInfo
        {
            public readonly Identifier CamId;
            public readonly IntPtr UserData;
        }

        public struct MLCameraDeviceAvailabilityStatusCallbacks
        {
            public delegate void DeviceAvailabilityStatusDelegate(ref MLCameraDeviceAvailabilityInfo info);

            public uint Version;
            public DeviceAvailabilityStatusDelegate OnDeviceAvailable;
            public DeviceAvailabilityStatusDelegate OnDeviceUnavailable;
        }

        public struct MLCameraDeviceStatusCallbacks
        {
            public delegate void OnDeviceStreamingDelegate(IntPtr data);
            public delegate void OnDeviceIdleDelegate(IntPtr data);
            public delegate void OnDeviceDisconnectedDelegate(DisconnectReason reason, IntPtr data);
            public delegate void OnDeviceErrorDelegate(ErrorType error, IntPtr data);

            public uint Version;
            public OnDeviceStreamingDelegate OnDeviceStreaming;
            public OnDeviceIdleDelegate OnDeviceIdle;
            public OnDeviceDisconnectedDelegate OnDeviceDisconnected;
            public OnDeviceErrorDelegate OnDeviceError;
        }

        public struct MLCameraCaptureCallbacks
        {
            public delegate void OnCaptureFailedDelegate(ref MLCameraResultExtras extra, IntPtr data);
            public delegate void OnCaptureAbortedDelegate(IntPtr data);
            public delegate void OnCaptureCompletedDelegate(
                ulong metadataHandle,
                ref MLCameraResultExtras extra,
                IntPtr data
            );
            public delegate void OnImageBufferAvailableDelegate(
                ref MLCameraOutput output,
                ulong metadataHandle,
                ref MLCameraResultExtras extra,
                IntPtr data
            );
            public delegate void OnVideoBufferAvailableDelegate(
                ref MLCameraOutput output,
                ulong metadataHandle,
                ref MLCameraResultExtras extra,
                IntPtr data
            );
            public delegate void OnPreviewBufferAvailableDelegate(
                ulong bufferHandle,
                ulong metadataHandle,
                ref MLCameraResultExtras extra,
                IntPtr data
            );

            public uint Version;
            public OnCaptureFailedDelegate OnCaptureFailed;
            public OnCaptureAbortedDelegate OnCaptureAborted;
            public OnCaptureCompletedDelegate OnCaptureCompleted;
            public OnImageBufferAvailableDelegate OnImageBufferAvailable;
            public OnVideoBufferAvailableDelegate OnVideoBufferAvailable;
            public OnPreviewBufferAvailableDelegate OnPreviewBufferAvailable;
        }

        [DllImport("ml_sdk_loader", CallingConvention = CallingConvention.Cdecl)]
        public static extern MLResult.Code MLCameraInit(
            ref MLCameraDeviceAvailabilityStatusCallbacks deviceAvailabilityStatusCallback,
            IntPtr userData
        );

        [DllImport("ml_sdk_loader", CallingConvention = CallingConvention.Cdecl)]
        public static extern MLResult.Code MLCameraConnect(ref MLCameraConnectContext inputContext, out ulong handle);

        [DllImport("ml_sdk_loader", CallingConvention = CallingConvention.Cdecl)]
        public static extern MLResult.Code MLCameraDisconnect(ulong contextHandle);

        [DllImport("ml_sdk_loader", CallingConvention = CallingConvention.Cdecl)]
        internal static extern MLResult.Code MLCameraPreCaptureAEAWB(ulong contextHandle);

        [DllImport("ml_sdk_loader", CallingConvention = CallingConvention.Cdecl)]
        public static extern MLResult.Code MLCameraPrepareCapture(
            ulong contextHandle,
            ref MLCameraCaptureConfig config,
            out ulong metadataHandle
        );

        [DllImport("ml_sdk_loader", CallingConvention = CallingConvention.Cdecl)]
        internal static extern MLResult.Code MLCameraSetCaptureCallbacks(
            ulong handle,
            ref MLCameraCaptureCallbacks captureCallbacks,
            IntPtr data
        );

        [DllImport("ml_sdk_loader", CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi)]
        public static extern MLResult.Code MLCameraCaptureImage(ulong contextHandle, uint numImages);

        [DllImport("ml_sdk_loader", CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi)]
        public static extern MLResult.Code MLCameraCaptureVideoStart(ulong contextHandle);

        [DllImport("ml_sdk_loader", CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi)]
        public static extern MLResult.Code MLCameraCaptureVideoStop(ulong contextHandle);

        [DllImport("ml_sdk_loader", CallingConvention = CallingConvention.Cdecl)]
        public static extern MLResult.Code MLCameraSetDeviceStatusCallbacks(
            ulong contextHandle,
            ref MLCameraDeviceStatusCallbacks deviceStatusCallbacks,
            IntPtr data
        );

        [DllImport("ml_sdk_loader", CallingConvention = CallingConvention.Cdecl)]
        internal static extern MLResult.Code MLCameraGetDeviceAvailabilityStatus(
            Identifier camId,
            [MarshalAs(UnmanagedType.I1)] out bool deviceAvailabilityStatus
        );
    }
}
#endif
