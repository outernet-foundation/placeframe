#if MAGIC_LEAP
using System;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using Plerion.Core;
using PlerionApiClient.Model;
using R3;
using UnityEngine;

namespace Plerion.Core.MagicLeap
{
    public class MagicLeapCameraProvider : ICameraProvider
    {
        private TaskCompletionSource<PinholeCameraConfig> _configTaskCompletionSource =
            new TaskCompletionSource<PinholeCameraConfig>();

        public MagicLeapCameraProvider()
        {
            if (!MagicLeapCamera.initialized)
                MagicLeapCamera.Initialize();

            MagicLeapCamera.Start()
                .ContinueWith(() => MagicLeapCamera.onFrameReceived += CompleteCameraConfigTask)
                .Forget();
        }

        private void CompleteCameraConfigTask(MLFrameData data)
        {
            MagicLeapCamera.onFrameReceived -= CompleteCameraConfigTask;
            _configTaskCompletionSource.SetResult(
                new PinholeCameraConfig(
                    (int)data.intrinsics.Width,
                    (int)data.intrinsics.Height,
                    PinholeCameraConfig.OrientationEnum.BOTTOMLEFT,
                    data.intrinsics.FocalLength.X,
                    data.intrinsics.FocalLength.Y,
                    data.intrinsics.PrincipalPoint.X,
                    data.intrinsics.PrincipalPoint.Y
                )
            );
        }

        public Observable<PinholeCameraConfig> CameraConfig()
        {
            return Observable.FromAsync(
                async cancellationToken =>
                {
                    cancellationToken.Register(() => _configTaskCompletionSource.TrySetCanceled(cancellationToken));
                    return await _configTaskCompletionSource.Task;
                }
            );
        }

        public Observable<CameraFrame> Frames(float intervalSeconds, bool useCameraPoseAnchoring = false)
        {
            return Observable
                .FromEvent<MLFrameData>(
                    x => MagicLeapCamera.onFrameReceived += x,
                    x => MagicLeapCamera.onFrameReceived -= x
                )
                .ThrottleLast(TimeSpan.FromSeconds(intervalSeconds))
                .SelectAwait(async (frame, cancellationToken) => await UniTask.RunOnThreadPool(
                    () => ImageConversion.EncodeArrayToJPG(
                        frame.imageBytes,
                        UnityEngine.Experimental.Rendering.GraphicsFormat.R8G8B8A8_UNorm,
                        frame.intrinsics.Width,
                        frame.intrinsics.Height,
                        0,
                        75
                    ),
                    cancellationToken: cancellationToken
                ))
                .Select(jpgBytes => new CameraFrame()
                {
                    ImageBytes = jpgBytes,
                    CameraTranslationUnityWorldFromCamera = Camera.main.transform.position,
                    CameraRotationUnityWorldFromCamera = Camera.main.transform.rotation
                });
        }
    }
}
#endif
