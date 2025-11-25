using Plerion.VPS;
using UnityEngine;
using UnityEngine.Android;
using Cysharp.Threading.Tasks;
using System.Linq;
using FofX.Stateful;
using System;
using System.Collections.Generic;

#if !UNITY_EDITOR
using Plerion.VPS.ARFoundation;
#endif

namespace PlerionClient.Client
{
    public class LocalizationManager : MonoBehaviour
    {
        public LocalizationMapVisualizer mapVisualizer;

        private void Start()
        {
            CameraLocalization.SetProvider(GetCameraProvider());
            App.RegisterObserver(HandleAppModeChanged, App.state.mode, App.state.loggedIn);
        }

        private void HandleAppModeChanged(NodeChangeEventArgs args)
        {
            if (!App.state.loggedIn.value || App.state.mode.value != AppMode.Validation)
            {
                App.DeregisterObserver(HandleLocalizationSessionStatusChanged);
                App.DeregisterObserver(HandleLocalizingChanged);
                CameraLocalization.Stop();
                mapVisualizer.enabled = false;
                return;
            }

            mapVisualizer.enabled = true;
            App.RegisterObserver(HandleLocalizationSessionStatusChanged, App.state.localizationSessionStatus);
        }

        private void HandleLocalizationSessionStatusChanged(NodeChangeEventArgs args)
        {
            App.DeregisterObserver(HandleMapToValidateChanged);
            App.DeregisterObserver(HandleLocalizingChanged);

            if (App.state.localizationSessionStatus.value == LocalizationSessionStatus.Inactive)
            {
                InitializeLocalizationSession().Forget();
                return;
            }
            else if (App.state.localizationSessionStatus.value == LocalizationSessionStatus.Active)
            {
                App.RegisterObserver(HandleMapToValidateChanged, App.state.mapForLocalization);
                App.RegisterObserver(HandleLocalizingChanged, App.state.localizing);
            }
        }

        private void HandleMapToValidateChanged(NodeChangeEventArgs args)
        {
            if (args.initialize)
            {
                if (App.state.mapForLocalization.value != Guid.Empty)
                    VisualPositioningSystem.LoadLocalizationMaps(App.state.mapForLocalization.value);

                return;
            }

            var previousValue = GetPreviousValue(App.state.mapForLocalization, args.changes);
            if (previousValue != App.state.mapForLocalization.value)
            {
                VisualPositioningSystem.UnloadLocalizationMap(previousValue).Forget();
                VisualPositioningSystem.LoadLocalizationMaps(App.state.mapForLocalization.value);
            }
        }

        private void HandleLocalizingChanged(NodeChangeEventArgs args)
        {
            if (App.state.localizing.value)
            {
                CameraLocalization.Start();
            }
            else
            {
                CameraLocalization.Stop();
            }
        }

        private T GetPreviousValue<T>(ObservablePrimitive<T> primitive, List<NodeChangeData> changes)
        {
            foreach (var change in changes)
            {
                if (change.source == primitive)
                    return (T)change.previousValue;
            }

            return primitive.value;
        }

        private async UniTask InitializeLocalizationSession()
        {
            App.state.localizationSessionStatus.ExecuteSetOrDelay(LocalizationSessionStatus.Starting);

            try
            {
                if (!Permission.HasUserAuthorizedPermission(Permission.Camera))
                    Permission.RequestUserPermission(Permission.Camera);

                UnityEngine.XR.ARSubsystems.XRCameraIntrinsics intrinsics = default;
                while (!SceneReferences.ARCameraManager.TryGetIntrinsics(out intrinsics))
                    await UniTask.WaitForEndOfFrame();

                await UniTask.SwitchToMainThread();

                await VisualPositioningSystem.StartLocalizationSession(new CameraIntrinsics()
                {
                    resolution = intrinsics.resolution,
                    focalLength = intrinsics.focalLength,
                    principlePoint = intrinsics.principalPoint,
                });

                await UniTask.SwitchToMainThread();
                App.state.localizationSessionStatus.ExecuteSetOrDelay(LocalizationSessionStatus.Active);
            }
            catch (Exception exc)
            {
                App.state.localizationSessionStatus.ExecuteSetOrDelay(LocalizationSessionStatus.Error);
                throw exc;
            }
        }

        private ICameraProvider GetCameraProvider()
        {
#if UNITY_EDITOR
            return new NoOpCameraProvider();
#else
            return new ARFoundationCameraProvider(SceneReferences.ARCameraManager, manageCameraEnabledState: false);
#endif
        }
    }
}