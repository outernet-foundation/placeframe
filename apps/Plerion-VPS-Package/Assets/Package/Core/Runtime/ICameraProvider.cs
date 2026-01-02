using System;
using Cysharp.Threading.Tasks;
using UnityEngine;
using PinholeCameraConfig = PlerionApiClient.Model.PinholeCameraConfig;

namespace Plerion.Core
{
    public interface ICameraProvider
    {
        UniTask<PinholeCameraConfig> Start(
            float intervalSeconds,
            Func<(Vector3 position, Quaternion rotation)?> cameraPoseProvider,
            Func<byte[], PinholeCameraConfig, Vector3, Quaternion, UniTask> onFrameReceived
        );
        UniTask Stop();
    }

    public class NoOpCameraProvider : ICameraProvider
    {
        public UniTask<PinholeCameraConfig> Start(
            float intervalSeconds,
            Func<(Vector3 position, Quaternion rotation)?> cameraPoseProvider,
            Func<byte[], PinholeCameraConfig, Vector3, Quaternion, UniTask> onFrameReceived
        ) =>
            UniTask.FromResult(
                new PinholeCameraConfig(
                    orientation: PinholeCameraConfig.OrientationEnum.TOPLEFT,
                    width: 0,
                    height: 0,
                    fx: 0,
                    fy: 0,
                    cx: 0,
                    cy: 0
                )
            );

        public UniTask Stop() => UniTask.CompletedTask;
    }
}
