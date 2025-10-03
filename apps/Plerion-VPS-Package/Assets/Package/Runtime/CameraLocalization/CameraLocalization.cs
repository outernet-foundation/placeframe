using System;
using System.Threading;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using UnityEngine;

namespace Plerion
{
    public static class CameraLocalization
    {
        public static bool Enabled { get; private set; }

        private static ICameraProvider _cameraProvider;
        private static CancellationTokenSource _cancellationTokenSource;

        public static void SetProvider(ICameraProvider cameraProvider)
        {
            if (Enabled)
                throw new Exception($"Cannot set provider while localization is active. Call {nameof(CameraLocalization)}.{nameof(Stop)} first.");

            _cameraProvider = cameraProvider;
        }

        public static void Start()
        {
            if (Enabled)
                return;

            if (_cameraProvider == null)
                throw new Exception("Camera provider must be set before calling Start.");

            Enabled = true;

            _cancellationTokenSource = new CancellationTokenSource();
            ExecuteCameraLocalization(_cancellationTokenSource.Token).Forget();
        }

        public static void Stop()
        {
            Enabled = false;

            _cancellationTokenSource?.Cancel();
            _cancellationTokenSource?.Dispose();
            _cancellationTokenSource = null;
        }

        private static async UniTask ExecuteCameraLocalization(CancellationToken cancellationToken = default)
        {
            int lastFrameCount = Time.frameCount;

            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    var cameraImage = await _cameraProvider.GetFrame();

                    if (cancellationToken.IsCancellationRequested)
                        break;

                    await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);

                    if (cameraImage.HasValue)
                    {
                        await VisualPositioningSystem.LocalizeFromCameraImage(
                            cameraImage.Value,
                            Camera.main.transform.position,
                            Camera.main.transform.rotation
                        );
                    }

                    // if this process doesn't take at least one frame, 
                    // this loop will become infinite and block the main thread
                    if (Time.frameCount == lastFrameCount)
                        await UniTask.WaitForEndOfFrame();

                    lastFrameCount = Time.frameCount;
                }
                catch (Exception exception)
                {
                    if (exception is TaskCanceledException)
                        break;

                    Log.Error(LogGroup.CameraLocalization, "Exception thrown during localization", exception);
                }
            }
        }
    }
}
