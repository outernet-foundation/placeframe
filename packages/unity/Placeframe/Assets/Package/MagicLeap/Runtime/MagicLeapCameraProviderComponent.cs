using PlaceframeApiClient.Model;
using R3;

namespace Placeframe.Core.MagicLeap
{
    public class MagicLeapCameraProviderComponent : CameraProviderComponent
    {
#if MAGIC_LEAP
        private MagicLeapCameraProvider _provider;

        private void Awake()
        {
            _provider = new MagicLeapCameraProvider();
        }

        public override Observable<PinholeCameraConfig> CameraConfig()
            => _provider.CameraConfig();

        public override Observable<CameraFrame> Frames(float intervalSeconds, bool useCameraPoseAnchoring = false)
            => _provider.Frames(intervalSeconds, useCameraPoseAnchoring);

#else

        public override Observable<PinholeCameraConfig> CameraConfig()
            => throw new System.NotImplementedException();

        public override Observable<CameraFrame> Frames(float intervalSeconds, bool useCameraPoseAnchoring = false)
            => throw new System.NotImplementedException();
#endif
    }
}