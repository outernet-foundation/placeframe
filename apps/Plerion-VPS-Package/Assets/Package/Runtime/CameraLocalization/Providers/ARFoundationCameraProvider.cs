using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

namespace Plerion
{
    public class ARFoundationCameraProvider : ICameraProvider
    {
        public ARCameraManager cameraManager;
        public bool manageCameraEnabledState;
        private TaskCompletionSource<CameraImage?> _taskCompletionSource;

        public ARFoundationCameraProvider(ARCameraManager cameraManager, bool manageCameraEnabledState = true)
        {
            this.cameraManager = cameraManager;
            this.manageCameraEnabledState = manageCameraEnabledState;

            if (manageCameraEnabledState)
                cameraManager.enabled = false;
        }

        public void Start()
        {
            if (manageCameraEnabledState)
                cameraManager.enabled = true;
        }

        public void Stop()
        {
            cameraManager.frameReceived -= OnFrameReceived;

            if (manageCameraEnabledState)
                cameraManager.enabled = false;

            _taskCompletionSource?.TrySetCanceled();
            _taskCompletionSource = null;
        }

        public UniTask<CameraImage?> GetFrame()
        {
            if (_taskCompletionSource == null)
            {
                _taskCompletionSource = new TaskCompletionSource<CameraImage?>();
                cameraManager.frameReceived += OnFrameReceived;
            }

            return _taskCompletionSource.Task.AsUniTask();
        }

        private void OnFrameReceived(ARCameraFrameEventArgs args)
        {
            if (!cameraManager.TryAcquireLatestCpuImage(out XRCpuImage image) ||
                !cameraManager.TryGetIntrinsics(out XRCameraIntrinsics intrinsics))
            {
                return;
            }

            var pixelBuffer = image.GetPlane(0).data.ToArray();
            var width = image.width;
            var height = image.height;

            image.Dispose();

            float angle;
            switch (Screen.orientation)
            {
                case ScreenOrientation.Portrait:
                    angle = 90f;
                    break;
                case ScreenOrientation.LandscapeLeft:
                    angle = 180f;
                    break;
                case ScreenOrientation.LandscapeRight:
                    angle = 0f;
                    break;
                case ScreenOrientation.PortraitUpsideDown:
                    angle = -90f;
                    break;
                default:
                    angle = 0f;
                    break;
            }

            _taskCompletionSource.TrySetResult(new CameraImage
            {
                imageWidth = width,
                imageHeight = height,
                pixelBuffer = pixelBuffer,
                focalLength = intrinsics.focalLength,
                principalPoint = intrinsics.principalPoint,
                cameraOrientation = Quaternion.Euler(0f, 0f, angle),
            });
        }
    }
}