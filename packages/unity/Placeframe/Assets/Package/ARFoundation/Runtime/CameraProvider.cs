using System;
using System.Buffers;
using System.Collections.Generic;
using System.Threading;
using Cysharp.Threading.Tasks;
using PlaceframeApiClient.Model;
using R3;
using Unity.Collections;
using UnityEngine;
using UnityEngine.Android;
using UnityEngine.Experimental.Rendering;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;
using TrackingState = UnityEngine.XR.ARSubsystems.TrackingState;

namespace Placeframe.Core.ARFoundation
{
    public class CameraProvider : ICameraProvider
    {
        private class AnchorChain
        {
            // Inside ARCore's good-tracking radius; smaller multiplies handovers and cumulative drift, larger degrades the cached transform.
            private const float HandoverDistanceMeters = 4f;

            private readonly ARAnchorManager _anchorManager;
            private readonly List<ARAnchor> _allAnchors = new();

            private ARAnchor _active;
            private Vector3 _originFromActivePosition;
            private Quaternion _originFromActiveRotation;

            public AnchorChain(ARAnchorManager anchorManager, ARAnchor origin)
            {
                _anchorManager = anchorManager;
                _active = origin;
                _originFromActivePosition = Vector3.zero;
                _originFromActiveRotation = Quaternion.identity;
                _allAnchors.Add(origin);
            }

            public async UniTask<(Vector3 position, Quaternion rotation)> SampleCameraPose(Camera camera)
            {
                if (NeedsHandover(camera.transform.position))
                    await Handover(camera);

                // Limited still emits; the reconstructor's truth-alignment gate catches captures that drifted too far to use.
                if (_active.trackingState == TrackingState.None)
                    throw new Exception("Active anchor tracking lost");

                Vector3 activeFromCameraPosition = _active.transform.InverseTransformPoint(camera.transform.position);
                Quaternion activeFromCameraRotation = Quaternion.Inverse(_active.transform.rotation) * camera.transform.rotation;

                Vector3 originFromCameraPosition = _originFromActiveRotation * activeFromCameraPosition + _originFromActivePosition;
                Quaternion originFromCameraRotation = _originFromActiveRotation * activeFromCameraRotation;

                return (originFromCameraPosition, originFromCameraRotation);
            }

            public void Dispose() => UniTask.Post(DestroyAllAnchors);

            private void DestroyAllAnchors()
            {
                foreach (var anchor in _allAnchors)
                {
                    if (anchor != null)
                        UnityEngine.Object.Destroy(anchor.gameObject);
                }
            }

            private bool NeedsHandover(Vector3 cameraWorldPosition)
            {
                if (_active.trackingState != TrackingState.Tracking)
                    return true;

                return Vector3.Distance(cameraWorldPosition, _active.transform.position) > HandoverDistanceMeters;
            }

            private async UniTask Handover(Camera camera)
            {
                var result = await _anchorManager.TryAddAnchorAsync(new Pose(camera.transform.position, camera.transform.rotation));

                if (result.value == null)
                    return;

                var newAnchor = result.value;
                _allAnchors.Add(newAnchor);

                // Skip if either anchor is degraded; a sloppy cached transform poisons every future frame.
                if (_active.trackingState != TrackingState.Tracking || newAnchor.trackingState != TrackingState.Tracking)
                    return;

                Vector3 activeFromNewPosition = _active.transform.InverseTransformPoint(newAnchor.transform.position);
                Quaternion activeFromNewRotation = Quaternion.Inverse(_active.transform.rotation) * newAnchor.transform.rotation;

                _originFromActivePosition = _originFromActiveRotation * activeFromNewPosition + _originFromActivePosition;
                _originFromActiveRotation = _originFromActiveRotation * activeFromNewRotation;
                _active = newAnchor;
            }
        }

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
                // If anchoring is requested, asynchronously prepare an anchor chain
                useCameraPoseAnchoring
                    ? Observable.FromAsync(async cancellationToken => await PrepareAnchorChain(cancellationToken))
                    : Observable.Return<AnchorChain>(null)
            ).SelectMany(chain =>
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
                        async (_, cancellationToken) => await CreateCameraFrame(chain, cancellationToken),
                        // Drop also serializes handover so SampleCameraPose is not re-entered during TryAddAnchorAsync.
                        AwaitOperation.Drop
                    )
                    // Filter out null CameraFrame results (happens when TryAcquireLatestCpuImage fails)
                    .WhereNotNull()
                    // When a subscription on this observable is disposed
                    .Do(onDispose: () =>
                    {
                        // If anchoring was requested, dispose all anchors in the chain
                        if (useCameraPoseAnchoring)
                            chain.Dispose();
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
                for (var index = 0; index < configs.Length; index++)
                {
                    var config = configs[index];

                    // Diagnostic: the device's full config menu with frame rates, so a Loki query can
                    // tell whether selecting max resolution forces a lower frame rate than an alternative.
                    var framerate = config.framerate?.ToString() ?? "null";
                    VisualPositioningSystem.LogDebug(
                        $"step=camera.config.available index={index} width={config.width} height={config.height} framerate={framerate}"
                    );

                    if (
                        bestConfig == null
                        || (config.width * config.height) > (bestConfig.Value.width * bestConfig.Value.height)
                    )
                        bestConfig = config;
                }
            }

            if (bestConfig.HasValue)
            {
                var selectedFramerate = bestConfig.Value.framerate?.ToString() ?? "null";
                VisualPositioningSystem.LogDebug(
                    $"step=camera.config.selected width={bestConfig.Value.width} height={bestConfig.Value.height} framerate={selectedFramerate}"
                );
            }

            XRCameraIntrinsics intrinsics = default;

            if (bestConfig.HasValue)
            {
                if (_cameraManager.currentConfiguration != bestConfig)
                {
                    try
                    {
                        _cameraManager.currentConfiguration = bestConfig;
                    }
                    catch (Exception exc)
                    {
                        // no-op, platform doesn't support setting config
                    }
                }

                // Wait until intrinsics are available and match the selected configuration
                await UniTask.WaitUntil(
                    () =>
                        _cameraManager.TryGetIntrinsics(out intrinsics)
                        && intrinsics.resolution.x == bestConfig.Value.width
                        && intrinsics.resolution.y == bestConfig.Value.height,
                    cancellationToken: cancellationToken
                );
            }
            else
            {
                // Wait until intrinsics are available
                await UniTask.WaitUntil(
                    () => _cameraManager.TryGetIntrinsics(out intrinsics),
                    cancellationToken: cancellationToken
                );
            }

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

        private async UniTask<AnchorChain> PrepareAnchorChain(CancellationToken cancellationToken)
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

            if (result.value == null)
                throw new Exception("Failed to add origin anchor");

            return new AnchorChain(_anchorManager, result.value);
        }

        private async UniTask<CameraFrame?> CreateCameraFrame(AnchorChain chain, CancellationToken cancellationToken)
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
            (Vector3 cameraPosition, Quaternion cameraRotation) = await GetCameraPose(chain);

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
                TrackingState = SampleTrackingState(),
            };
        }

        // Lost frames do not reach this method (the anchored path throws in GetCameraPose), so the
        // non-Tracking case here is "session degraded but still emitting" — Limited, not Lost.
        private static CameraTrackingState SampleTrackingState() =>
            ARSession.state == ARSessionState.SessionTracking ? CameraTrackingState.Tracking : CameraTrackingState.Limited;

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

        private async UniTask<(Vector3 position, Quaternion rotation)> GetCameraPose(AnchorChain chain)
        {
            if (Camera.main == null)
                throw new Exception("Camera not available");

            if (chain == null)
            {
                return (Camera.main.transform.position, Camera.main.transform.rotation);
            }

            if (ARSession.state != ARSessionState.SessionTracking)
            {
                throw new Exception("AR session not tracking");
            }

            return await chain.SampleCameraPose(Camera.main);
        }
    }
}
