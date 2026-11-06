using System;
using R3;
using UnityEngine;
using PinholeCameraConfig = PlaceframeApiClient.Model.PinholeCameraConfig;

namespace Placeframe.Core
{
    public struct CameraFrame
    {
        public byte[] ImageBytes;
        public Vector3 CameraTranslationUnityWorldFromCamera;
        public Quaternion CameraRotationUnityWorldFromCamera;
        // When the camera exposed the image, on the device's camera clock (the clock of TrackingSample's
        // timestamps); 0 when the provider has no camera timestamp.
        public long TimestampNs;
    }

    // The tracker's camera pose for one camera frame, as the app saw it: unanchored, so a jump after a
    // tracking loss stays visible.
    public struct TrackingSample
    {
        public long TimestampNs;
        public Vector3 CameraTranslationUnityWorldFromCamera;
        public Quaternion CameraRotationUnityWorldFromCamera;
        public string TrackingState;
        public string NotTrackingReason;
    }

    public interface ICameraProvider
    {
        Observable<PinholeCameraConfig> CameraConfig();
        Observable<CameraFrame> Frames(float intervalSeconds, bool useCameraPoseAnchoring = false);
    }

    // A camera provider that can also report the tracker's pose for every camera frame, not only for
    // the frames it hands out as images.
    public interface ITrackingProvider
    {
        Observable<TrackingSample> TrackingSamples();

        // Every camera frame as an image, for recording video-rate runs. A frame that arrives while
        // maxConcurrentEncodes are still being encoded is dropped rather than queued, so a phone that
        // cannot keep up records fewer frames instead of falling ever further behind. downscale divides
        // the image's width and height (1 = full resolution).
        Observable<CameraFrame> EveryFrame(int maxConcurrentEncodes, int downscale);
    }

    public class NoOpCameraProvider : ICameraProvider
    {
        public Observable<PinholeCameraConfig> CameraConfig() => Observable.Empty<PinholeCameraConfig>();

        public Observable<CameraFrame> Frames(float intervalSeconds, bool useCameraPoseAnchoring = false) =>
            Observable.Empty<CameraFrame>();
    }
}
