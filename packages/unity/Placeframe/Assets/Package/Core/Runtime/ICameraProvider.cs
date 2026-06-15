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

    // The device's own GNSS fix at capture time. Diagnostic only — the one geodetic independent of
    // the filter's belief, so it can be cross-checked against a hypothesis's implied position to tell
    // which of two competing locks matches the real world. Absent on providers without GNSS (Magic
    // Leap 2, editor) and before the first fix arrives.
    public readonly struct GnssFix
    {
        public readonly CartographicCoordinates Coordinates;
        public readonly float HorizontalAccuracyMeters;
        public readonly double TimestampSeconds;

        public GnssFix(CartographicCoordinates coordinates, float horizontalAccuracyMeters, double timestampSeconds)
        {
            Coordinates = coordinates;
            HorizontalAccuracyMeters = horizontalAccuracyMeters;
            TimestampSeconds = timestampSeconds;
        }
    }

    public struct CameraFrame
    {
        public byte[] ImageBytes;
        public Vector3 CameraTranslationUnityWorldFromCamera;
        public Quaternion CameraRotationUnityWorldFromCamera;
        public CameraTrackingState TrackingState;
        public GnssFix? DeviceLocation;
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
