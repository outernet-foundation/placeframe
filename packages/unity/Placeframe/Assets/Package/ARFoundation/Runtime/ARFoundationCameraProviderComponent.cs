using PlaceframeApiClient.Model;
using R3;
using UnityEngine.XR.ARFoundation;

namespace Placeframe.Core.ARFoundation
{
    public class ARFoundationCameraProviderComponent : CameraProviderComponent
    {
        public ARCameraManager _arCameraManager;
        public ARAnchorManager _arAnchorManager;

        private ARFoundationCameraProvider _provider;

        private void Awake()
        {
            _provider = new ARFoundationCameraProvider(_arCameraManager, _arAnchorManager);
        }

        public override Observable<PinholeCameraConfig> CameraConfig()
            => _provider.CameraConfig();

        public override Observable<CameraFrame> Frames(float intervalSeconds, bool useCameraPoseAnchoring = false)
            => _provider.Frames(intervalSeconds, useCameraPoseAnchoring);
    }
}