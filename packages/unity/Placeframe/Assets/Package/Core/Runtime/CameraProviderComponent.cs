using PlaceframeApiClient.Model;
using R3;
using UnityEngine;

namespace Placeframe.Core
{
    public abstract class CameraProviderComponent : MonoBehaviour, ICameraProvider
    {
        public abstract Observable<PinholeCameraConfig> CameraConfig();
        public abstract Observable<CameraFrame> Frames(float intervalSeconds, bool useCameraPoseAnchoring = false);
    }
}