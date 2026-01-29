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
