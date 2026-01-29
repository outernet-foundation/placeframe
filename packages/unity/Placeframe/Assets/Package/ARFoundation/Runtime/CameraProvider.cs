using System;
using System.Buffers;
using System.Threading;
using Cysharp.Threading.Tasks;
using PlerionApiClient.Model;
using R3;
using Unity.Collections;
using UnityEngine;
using UnityEngine.Android;
using UnityEngine.Experimental.Rendering;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;
using TrackingState = UnityEngine.XR.ARSubsystems.TrackingState;

namespace Plerion.Core.ARFoundation
{
    public class CameraProvider : ICameraProvider
    {
        private readonly ARCameraManager _cameraManager;
        private readonly ARAnchorManager _anchorManager;

        public CameraProvider(ARCameraManager cameraManager, ARAnchorManager anchorManager)
        {
            _cameraManager = cameraManager;
            _anchorManager = anchorManager;

            // Auto-focus is actively detrimental for the visual localization use case
            _cameraManager.autoFocusRequested = false;
        }

        public Observable<PinholeCameraConfig> CameraConfig() =>
            Observable.FromAsync(async cancellationToken => await PrepareCamera(cancellationToken));

        public Observable<CameraFrame> Frames(float intervalSeconds, bool useCameraPoseAnchoring = false)
        {
            return (
                // If anchoring is requested, asynchronously prepare an anchor
                useCameraPoseAnchoring
                    ? Observable.FromAsync(async cancellationToken => await PrepareAnchor(cancellationToken))
                    : Observable.Return<ARAnchor>(null)
            ).SelectMany(anchor =>
                Observable
                    // Observe ARCameraManager frameReceived events
                    .FromEvent<ARCameraFrameEventArgs>(
                        h => _cameraManager.frameReceived += h,
                        h => _cameraManager.frameReceived -= h
                    )
                    // Throttle frame events to the requested interval
                    .ThrottleLast(TimeSpan.FromSeconds(intervalSeconds))
                    // Emit a CameraFrame event for each new ARCameraManager frameReceived event
                    .SelectAwait(
                        async (_, cancellationToken) => await CreateCameraFrame(anchor, cancellationToken),
                        // Skip frames if they pile up
                        AwaitOperation.Drop
                    )
                    // Filter out null CameraFrame results (happens when TryAcquireLatestCpuImage fails)
                    .WhereNotNull()
                    // When a subscription on this observable is disposed
                    .Do(onDispose: () =>
                    {
                        // If anchoring was requested, dispose the anchor
                        if (useCameraPoseAnchoring)
                            DisposeAnchor(anchor);
                    })
            );
        }

        public async UniTask<PinholeCameraConfig> PrepareCamera(CancellationToken cancellationToken)
        {
            // Ensure we have camera permission (this should be requested at the app level)
            if (!Permission.HasUserAuthorizedPermission(Permission.Camera))
                throw new Exception("Camera permission not granted");

            // Select the best available camera configuration (highest resolution)
            XRCameraConfiguration? bestConfig = null;
            using (var configs = _cameraManager.GetConfigurations(Allocator.Temp))
            {
                foreach (var config in configs)
                {
                    if (
                        bestConfig == null
                        || (config.width * config.height) > (bestConfig.Value.width * bestConfig.Value.height)
                    )
                        bestConfig = config;
                }
            }

            if (!bestConfig.HasValue)
                throw new Exception("No camera configurations available");

            if (_cameraManager.currentConfiguration != bestConfig)
                _cameraManager.currentConfiguration = bestConfig;

            // Wait until intrinsics are available and match the selected configuration
            XRCameraIntrinsics intrinsics = default;
            await UniTask.WaitUntil(
                () =>
                    _cameraManager.TryGetIntrinsics(out intrinsics)
                    && intrinsics.resolution.x == bestConfig.Value.width
                    && intrinsics.resolution.y == bestConfig.Value.height,
                cancellationToken: cancellationToken
            );

            return new PinholeCameraConfig(
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
        }

        private async UniTask<ARAnchor> PrepareAnchor(CancellationToken cancellationToken)
        {
            await UniTask.WaitUntil(
                () => ARSession.state == ARSessionState.SessionTracking,
                cancellationToken: cancellationToken
            );

            var result = await _anchorManager.TryAddAnchorAsync(
                new Pose(
                    _cameraManager.transform.position,
                    Quaternion.Euler(0f, _cameraManager.transform.eulerAngles.y, 0f)
                )
            );

            return result.value;
        }

        private void DisposeAnchor(ARAnchor anchor) =>
            UniTask.Post(() => UnityEngine.Object.Destroy(anchor.gameObject));

        private async UniTask<CameraFrame?> CreateCameraFrame(ARAnchor anchor, CancellationToken cancellationToken)
        {
            XRCpuImage.AsyncConversion conversion;
            TextureFormat textureFormat;
            uint width;
            uint height;

            // Try to acquire the latest CPU image from ARFoundation
            if (!_cameraManager.TryAcquireLatestCpuImage(out var cpuImage))
                // This is an expected case; ARFoundation does not guarantee that the native buffer is accessible even when frameReceived fires
                return null;

            try
            {
                width = (uint)cpuImage.width;
                height = (uint)cpuImage.height;
                textureFormat = cpuImage.FormatSupported(TextureFormat.RGB24)
                    ? TextureFormat.RGB24
                    : TextureFormat.RGBA32;

                // Start image conversion
                conversion = cpuImage.ConvertAsync(new XRCpuImage.ConversionParams(cpuImage, textureFormat));
            }
            finally
            {
                // Dispose XRCpuImage immediately after starting conversion (safe, and optimal memory management)
                cpuImage.Dispose();
            }

            // Create a temporary variable for conversion with 'using' keyword to ensure conversion is disposed
            using var conversionHandle = conversion;

            // Get camera pose at the moment of capture
            (Vector3 cameraPosition, Quaternion cameraRotation) = GetCameraPose(anchor);

            // Await conversion completion
            while (!conversionHandle.status.IsDone())
                await UniTask.Yield(PlayerLoopTiming.Update, cancellationToken);

            // Throw if conversion failed
            if (conversionHandle.status != XRCpuImage.AsyncConversionStatus.Ready)
                throw new Exception($"Image conversion failed: {conversionHandle.status}");

            var bytes = await EncodeToJpg(
                conversionHandle.GetData<byte>(),
                textureFormat,
                width,
                height,
                cancellationToken
            );

            return new CameraFrame
            {
                ImageBytes = bytes,
                CameraTranslationUnityWorldFromCamera = cameraPosition,
                CameraRotationUnityWorldFromCamera = cameraRotation,
            };
        }

        private async UniTask<byte[]> EncodeToJpg(
            NativeArray<byte> bytes,
            TextureFormat textureFormat,
            uint width,
            uint height,
            CancellationToken cancellationToken
        )
        {
            var graphicsFormat =
                textureFormat == TextureFormat.RGB24 ? GraphicsFormat.R8G8B8_UNorm : GraphicsFormat.R8G8B8A8_UNorm;

            byte[] buffer = ArrayPool<byte>.Shared.Rent(bytes.Length);

            try
            {
                bytes.CopyTo(buffer);

                var jpgBytes = await UniTask.RunOnThreadPool(
                    () => ImageConversion.EncodeArrayToJPG(buffer, graphicsFormat, width, height, 0, 75),
                    cancellationToken: cancellationToken
                );

                if (jpgBytes == null || jpgBytes.Length == 0)
                    throw new Exception("Image encoding failed");

                return jpgBytes;
            }
            finally
            {
                ArrayPool<byte>.Shared.Return(buffer);
            }
        }

        private (Vector3 position, Quaternion rotation) GetCameraPose(ARAnchor anchor)
        {
            if (Camera.main == null)
                throw new Exception("Camera not available");

            if (anchor == null)
            {
                return (Camera.main.transform.position, Camera.main.transform.rotation);
            }

            if (ARSession.state != ARSessionState.SessionTracking || anchor.trackingState == TrackingState.None)
            {
                throw new Exception("Anchor tracking lost");
            }

            return (
                anchor.transform.InverseTransformPoint(Camera.main.transform.position),
                Quaternion.Inverse(anchor.transform.rotation) * Camera.main.transform.rotation
            );
        }
    }
}
