using System;
using R3;
using UnityEngine;
using PinholeCameraConfig = PlaceframeApiClient.Model.PinholeCameraConfig;

namespace Placeframe.Core
{
    // Diagnostic only — the filter does not gate on this. Unknown is the zero default for providers
    // that do not expose a state.
    public enum CameraTrackingState
    {
        Unknown = 0,
        Tracking = 1,
        Limited = 2,
        Lost = 3,
    }

    public struct CameraFrame
    {
        public byte[] ImageBytes;
        public Vector3 CameraTranslationUnityWorldFromCamera;
        public Quaternion CameraRotationUnityWorldFromCamera;
        public CameraTrackingState TrackingState;
    }

    public interface ICameraProvider
    {
        Observable<PinholeCameraConfig> CameraConfig();
        Observable<CameraFrame> Frames(float intervalSeconds, bool useCameraPoseAnchoring = false);
    }

    public class NoOpCameraProvider : ICameraProvider
    {
        public Observable<PinholeCameraConfig> CameraConfig() => Observable.Empty<PinholeCameraConfig>();

        public Observable<CameraFrame> Frames(float intervalSeconds, bool useCameraPoseAnchoring = false) =>
            Observable.Empty<CameraFrame>();
    }
}
