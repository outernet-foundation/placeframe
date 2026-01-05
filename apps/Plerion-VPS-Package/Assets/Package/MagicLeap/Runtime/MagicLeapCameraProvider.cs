#if UNITY_LUMIN
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using Plerion.Core;

namespace Plerion.Core.MagicLeap
{
    public class MagicLeapCameraProvider : ICameraProvider
    {
        public bool manageCameraEnabledState;
        private TaskCompletionSource<byte[]> _taskCompletionSource;

        public MagicLeapCameraProvider(bool manageCameraEnabledState = true)
        {
            this.manageCameraEnabledState = manageCameraEnabledState;
        }

        private void HandleFrameReceived(byte[] cameraImage)
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

        public UniTask<byte[]> GetFrame()
        {
            if (_taskCompletionSource == null)
            {
                _taskCompletionSource = new TaskCompletionSource<byte[]>();
                MagicLeapCamera.onFrameReceived += HandleFrameReceived;
            }

            return _taskCompletionSource.Task.AsUniTask();
        }
    }
}
#endif
