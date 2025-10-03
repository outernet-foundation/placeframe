using System.Threading.Tasks;
using Cysharp.Threading.Tasks;

namespace Plerion
{
    public class MagicLeapCameraProvider : ICameraProvider
    {
        public bool manageCameraEnabledState;
        private TaskCompletionSource<CameraImage?> _taskCompletionSource;

        public MagicLeapCameraProvider(bool manageCameraEnabledState = true)
        {
            this.manageCameraEnabledState = manageCameraEnabledState;
        }

        private void HandleFrameReceived(CameraImage? cameraImage)
        {
            _taskCompletionSource?.TrySetResult(cameraImage);
            _taskCompletionSource = null;
            MagicLeapCamera.onFrameReceived -= HandleFrameReceived;
        }

        public void Start()
        {
            if (!MagicLeapCamera.initialized)
                MagicLeapCamera.Initialize();

            if (manageCameraEnabledState)
                MagicLeapCamera.Start().Forget();
        }

        public void Stop()
        {
            MagicLeapCamera.onFrameReceived -= HandleFrameReceived;

            if (manageCameraEnabledState)
                MagicLeapCamera.Stop();

            _taskCompletionSource?.TrySetCanceled();
            _taskCompletionSource = null;
        }

        public UniTask<CameraImage?> GetFrame()
        {
            if (_taskCompletionSource == null)
            {
                _taskCompletionSource = new TaskCompletionSource<CameraImage?>();
                MagicLeapCamera.onFrameReceived += HandleFrameReceived;
            }

            return _taskCompletionSource.Task.AsUniTask();
        }
    }
}