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
        private readonly AsyncLifecycleGuard _lifecycle = new AsyncLifecycleGuard();
        private ARCameraManager _cameraManager;

        private float _intervalSeconds;
        private float _nextCaptureTime;
        private bool _isCapturing;
        private PinholeCameraConfig _cameraConfig;
        private Func<(Vector3 position, Quaternion rotation)?> _cameraPoseProvider;
        private Func<byte[], PinholeCameraConfig, Vector3, Quaternion, UniTask> _onFrameReceived;

        public ARFoundationCameraProvider(ARCameraManager cameraManager)
        {
            _cameraManager = cameraManager;

            // Auto-focus is actively detrimental for the visual localization use case
            _cameraManager.autoFocusRequested = false;
        }

        public async UniTask<PinholeCameraConfig> Start(
            float intervalSeconds,
            Func<(Vector3 position, Quaternion rotation)?> cameraPoseProvider,
            Func<byte[], PinholeCameraConfig, Vector3, Quaternion, UniTask> onFrameReceived,
            CancellationToken cancellationToken
        ) =>
            await _lifecycle.StartAsync(
                token => StartInternal(intervalSeconds, cameraPoseProvider, onFrameReceived, token),
                cancellationToken
            );

        public async UniTask Stop() => await _lifecycle.StopAsync(StopInternal);

        private async UniTask<PinholeCameraConfig> StartInternal(
            float intervalSeconds,
            Func<(Vector3 position, Quaternion rotation)?> cameraPoseProvider,
            Func<byte[], PinholeCameraConfig, Vector3, Quaternion, UniTask> onFrameReceived,
            CancellationToken sessionToken
        )
        {
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
                    bestConfig = config;
            }

            if (!bestConfig.HasValue)
                throw new Exception("No camera configurations available.");

            if (_cameraManager.currentConfiguration != bestConfig)
            {
                _cameraManager.currentConfiguration = bestConfig;
                Debug.Log(
                    $"Selected camera configuration: {bestConfig.Value.width}x{bestConfig.Value.height} @ {bestConfig.Value.framerate}fps"
                );
            }

            // Wait until intrinsics are available and match the selected configuration
            XRCameraIntrinsics intrinsics = default;
            await UniTask.WaitUntil(
                () =>
                    _cameraManager.TryGetIntrinsics(out intrinsics)
                    && intrinsics.resolution.x == bestConfig.Value.width
                    && intrinsics.resolution.y == bestConfig.Value.height,
                cancellationToken: sessionToken
            );

            // Start capturing frames
            _intervalSeconds = intervalSeconds;
            _nextCaptureTime = Time.realtimeSinceStartup;
            _isCapturing = false;
            _cameraManager.frameReceived += OnCameraFrameReceived;

            _cameraConfig = new PinholeCameraConfig(
                // Our orientation conventions mirrors EXIF's orientation tag
                //
                // ARFoundation on Android Mobile returns images in LEFT_TOP orientation (EXIF Orientation=5):
                //  - 0th row is the visual left edge
                //  - 0th column is the visual top edge
                // To display "normally" (TOP_LEFT), you would apply a transpose (swap X/Y), e.g.:
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

            return _cameraConfig;
        }

        private async UniTask StopInternal()
        {
            await UniTask.WaitUntil(() => !_isCapturing);

            _cameraManager.frameReceived -= OnCameraFrameReceived;
            _cameraManager = null;
            _cameraPoseProvider = null;
            _onFrameReceived = null;
        }

        private void OnCameraFrameReceived(ARCameraFrameEventArgs args)
        {
            // Early out if we stopped capturing but haven't deregistered the event yet
            if (_lifecycle.State != AsyncLifecycleGuard.LifecycleState.Running)
                return;

            // Skip this frame if a previous one is still processing
            if (_isCapturing)
                return;

            // Throttle captures to the requested interval
            if (Time.realtimeSinceStartup < _nextCaptureTime)
                return;

            _isCapturing = true;
            AcquireAndDispatchImage().Forget(Debug.LogException);
        }

        private async UniTask AcquireAndDispatchImage()
        {
            try
            {
                if (!_cameraManager.TryAcquireLatestCpuImage(out var cpuImage))
                    return;

                XRCpuImage.AsyncConversion conversion;
                Vector3 cameraPosition;
                Quaternion cameraRotation;
                float captureTime;
                uint width;
                uint height;
                TextureFormat format;

                try
                {
                    captureTime = Time.realtimeSinceStartup;

                    // Get camera pose at the time of capture
                    var cameraPose = _cameraPoseProvider?.Invoke();
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
                    // Ensure CPU image is always disposed (this is safe to do immediately after starting conversion,
                    // and is optimal memory wise)
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

                var raw = asyncImageConversion.GetData<byte>();

                // Encode to JPG and dispatch callback (on thread pool to avoid blocking main thread)
                await UniTask.RunOnThreadPool(async () =>
                {
                    if (_lifecycle.Token.IsCancellationRequested)
                        return;

                    // Rent from array pool to reduce allocations
                    byte[] rented = ArrayPool<byte>.Shared.Rent(raw.Length);
                    try
                    {
                        raw.CopyTo(rented);
                        var bytes = ImageConversion.EncodeArrayToJPG(
                            rented,
                            (format == TextureFormat.RGB24)
                                ? GraphicsFormat.R8G8B8_UNorm
                                : GraphicsFormat.R8G8B8A8_UNorm,
                            width,
                            height,
                            0,
                            75
                        );

                        if (bytes == null)
                        {
                            Debug.LogWarning("Failed to encode camera image to JPG.");
                            return;
                        }

                        if (_onFrameReceived != null)
                            await _onFrameReceived(bytes, _cameraConfig, cameraPosition, cameraRotation);
                    }
                    finally
                    {
                        ArrayPool<byte>.Shared.Return(rented);
                    }
                });

                // Switch to main thread before updating scheduling variables, to avoid race conditions
                await UniTask.SwitchToMainThread();

                // We have successfully dispatched the frame, schedule the next capture time
                _nextCaptureTime = captureTime + _intervalSeconds;
            }
            finally
            {
                // Always clear the in-flight flag
                _isCapturing = false;
            }
        }
    }
}
