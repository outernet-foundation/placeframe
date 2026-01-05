using System;
using System.Buffers;
using System.Threading;
using Cysharp.Threading.Tasks;
using PlerionApiClient.Model;
using Unity.Collections;
using UnityEngine;
using UnityEngine.Android;
using UnityEngine.Experimental.Rendering;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

namespace Plerion.Core.ARFoundation
{
    public class ARFoundationCameraProvider : ICameraProvider
    {
        private SystemState _systemState = SystemState.Idle;
        private ARCameraManager _cameraManager;
        private float _intervalSeconds;
        private float _nextCaptureTime;
        private int _captureInFlight;

        private Func<(Vector3 position, Quaternion rotation)?> _cameraPoseProvider;
        private Func<byte[], Vector3, Quaternion, UniTask> _onFrameReceived;

        public ARFoundationCameraProvider(ARCameraManager cameraManager)
        {
            _cameraManager = cameraManager;

            // Auto-focus is unhelpful for our use case
            _cameraManager.autoFocusRequested = false;
        }

        public async UniTask<PinholeCameraConfig> Start(
            float intervalSeconds,
            Func<(Vector3 position, Quaternion rotation)?> cameraPoseProvider,
            Func<byte[], Vector3, Quaternion, UniTask> onFrameReceived
        )
        {
            if (_systemState != SystemState.Idle)
                throw new InvalidOperationException("Camera provider is already started");

            _systemState = SystemState.Starting;

            _cameraPoseProvider = cameraPoseProvider;
            _onFrameReceived = onFrameReceived;

            // Ensure we have camera permission (this should be requested at the app level)
            if (!Permission.HasUserAuthorizedPermission(Permission.Camera))
                throw new Exception("Camera permission not granted.");

            // Select the best available camera configuration (highest resolution)
            XRCameraConfiguration? bestConfig = null;
            using var configs = _cameraManager.GetConfigurations(Allocator.Temp);
            foreach (var config in configs)
            {
                if (
                    bestConfig == null
                    || (config.width * config.height) > (bestConfig.Value.width * bestConfig.Value.height)
                )
                {
                    bestConfig = config;
                }
            }

            if (!bestConfig.HasValue)
            {
                throw new Exception("No camera configurations available.");
            }

            if (_cameraManager.currentConfiguration != bestConfig)
            {
                _cameraManager.currentConfiguration = bestConfig;
                Debug.Log(
                    $"Selected camera configuration: {bestConfig.Value.width}x{bestConfig.Value.height} @ {bestConfig.Value.framerate}fps"
                );
            }

            // Wait until intrinsics are available and match the selected configuration
            XRCameraIntrinsics intrinsics = default;
            await UniTask.WaitUntil(() =>
                _cameraManager.TryGetIntrinsics(out intrinsics)
                && intrinsics.resolution.x == bestConfig.Value.width
                && intrinsics.resolution.y == bestConfig.Value.height
            );

            // Start capturing frames
            _intervalSeconds = intervalSeconds;
            _nextCaptureTime = Time.realtimeSinceStartup;
            _cameraManager.frameReceived += OnCameraFrameReceived;

            _systemState = SystemState.Running;

            // Return camera intrinsics
            return new PinholeCameraConfig(
                // ARFoundation on Android Mobile returns images in LEFT_TOP orientation (EXIF/TIFF Orientation=5):
                //  - 0th row is the visual left edge
                //  - 0th column is the visual top edge
                // To display canonically (TOP_LEFT), apply a transpose (swap X/Y), e.g.:
                //  - rotate 90° CW, then flip left↔right, OR
                //  - flip top↔bottom, then rotate 90° CW
                orientation: PinholeCameraConfig.OrientationEnum.LEFTTOP,
                width: intrinsics.resolution.x,
                height: intrinsics.resolution.y,
                fx: intrinsics.focalLength.x,
                fy: intrinsics.focalLength.y,
                cx: intrinsics.principalPoint.x,
                cy: intrinsics.principalPoint.y
            );
        }

        public async UniTask Stop()
        {
            if (_systemState != SystemState.Running)
                throw new InvalidOperationException("Camera provider is not running");

            _systemState = SystemState.Stopping;

            // Wait for any in-flight capture to complete before unsubscribing
            await UniTask.WaitUntil(() => Interlocked.CompareExchange(ref _captureInFlight, 0, 0) == 0);

            _cameraManager.frameReceived -= OnCameraFrameReceived;
            _cameraManager = null;
            _cameraPoseProvider = null;
            _onFrameReceived = null;
            _systemState = SystemState.Idle;
        }

        private void OnCameraFrameReceived(ARCameraFrameEventArgs args)
        {
            // Throttle captures to the requested interval, and ensure only one capture is in-flight at a time
            if (
                Time.realtimeSinceStartup < _nextCaptureTime
                || Interlocked.CompareExchange(ref _captureInFlight, 1, 0) != 0
            )
                return;

            AcquireAndDispatchImage().Forget(Debug.LogException);
        }

        private async UniTask AcquireAndDispatchImage()
        {
            try
            {
                Vector3 cameraPosition;
                Quaternion cameraRotation;
                float captureTime;
                uint width;
                uint height;
                TextureFormat format;
                XRCpuImage.AsyncConversion conversion;

                // Try to acquire the latest CPU image
                if (!_cameraManager.TryAcquireLatestCpuImage(out var cpuImage))
                    return;

                try
                {
                    // Record capture time
                    captureTime = Time.realtimeSinceStartup;

                    // Get camera pose at capture time
                    var cameraPose = _cameraPoseProvider();
                    if (cameraPose == null)
                    {
                        Debug.LogWarning("Camera pose unavailable; skipping frame.");
                        return;
                    }
                    (cameraPosition, cameraRotation) = cameraPose.Value;

                    // Start image conversion
                    width = (uint)cpuImage.width;
                    height = (uint)cpuImage.height;
                    format = cpuImage.FormatSupported(TextureFormat.RGB24) ? TextureFormat.RGB24 : TextureFormat.RGBA32;
                    conversion = cpuImage.ConvertAsync(new XRCpuImage.ConversionParams(cpuImage, format));
                }
                finally
                {
                    // Ensure CPU image is always disposed (this is safe and optimal to do immediately after starting conversion)
                    cpuImage.Dispose();
                }

                // Temporary variable to ensure conversion is disposed
                using var asyncImageConversion = conversion;

                // Await conversion completion
                while (!asyncImageConversion.status.IsDone())
                    await UniTask.Yield(PlayerLoopTiming.Update);

                // Throw if conversion failed
                if (asyncImageConversion.status != XRCpuImage.AsyncConversionStatus.Ready)
                    throw new Exception($"XRCpuImage conversion failed: {asyncImageConversion.status}");

                // Encode to JPG and dispatch callback (on thread pool to avoid blocking main thread)
                var raw = asyncImageConversion.GetData<byte>();
                await UniTask.RunOnThreadPool(async () =>
                {
                    // Rent from array pool to reduce allocations
                    byte[] rented = ArrayPool<byte>.Shared.Rent(raw.Length);
                    byte[] bytes;
                    try
                    {
                        raw.CopyTo(rented);
                        bytes = ImageConversion.EncodeArrayToJPG(
                            rented,
                            (format == TextureFormat.RGB24)
                                ? GraphicsFormat.R8G8B8_UNorm
                                : GraphicsFormat.R8G8B8A8_UNorm,
                            width,
                            height,
                            rowBytes: 0,
                            quality: 75
                        );
                    }
                    finally
                    {
                        ArrayPool<byte>.Shared.Return(rented);
                    }

                    await _onFrameReceived(bytes, cameraPosition, cameraRotation);
                });

                // We have successfully dispatched the frame, schedule the next capture time
                _nextCaptureTime = captureTime + _intervalSeconds;
            }
            finally
            {
                // Always clear the in-flight flag
                Interlocked.Exchange(ref _captureInFlight, 0);
            }
        }
    }
}
