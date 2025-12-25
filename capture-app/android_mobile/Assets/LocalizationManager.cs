using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using FofX.Stateful;
using Plerion.Core;
using UnityEngine;
using UnityEngine.Android;
#if !UNITY_EDITOR
using Plerion.Core.ARFoundation;
#endif

namespace PlerionClient.Client
{
    public class LocalizationManager : MonoBehaviour
    {
        private void Awake()
        {
            VisualPositioningSystem.Initialize(
                GetCameraProvider(),
                App.state.plerionApiUrl.value,
                App.state.plerionAuthTokenUrl.value,
                App.state.plerionAuthAudience.value,
                message => Log.Info(LogGroup.Localizer, message),
                message => Log.Warn(LogGroup.Localizer, message),
                message => Log.Error(LogGroup.Localizer, message),
                (message, exception) => Log.Error(LogGroup.Localizer, exception, message)
            );

            App.RegisterObserver(HandleAppModeChanged, App.state.mode, App.state.loggedIn);
        }

        private void HandleAppModeChanged(NodeChangeEventArgs args)
        {
            if (!App.state.loggedIn.value || App.state.mode.value != AppMode.Validation)
            {
                App.DeregisterObserver(HandleLocalizationSessionStatusChanged);
                App.DeregisterObserver(HandleLocalizingChanged);

                if (App.state.localizing.value)
                {
                    VisualPositioningSystem.StopLocalizing().Forget();
                }

                return;
            }

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
                    VisualPositioningSystem.AddLocalizationMaps(App.state.mapForLocalization.value);

                return;
            }

            var previousValue = GetPreviousValue(App.state.mapForLocalization, args.changes);
            if (previousValue != App.state.mapForLocalization.value)
            {
                VisualPositioningSystem.RemoveLocalizationMap(previousValue).Forget();
                VisualPositioningSystem.AddLocalizationMaps(App.state.mapForLocalization.value);
            }
        }

        private void HandleLocalizingChanged(NodeChangeEventArgs args)
        {
            if (App.state.localizing.value)
            {
                VisualPositioningSystem.StartLocalizing().Forget();
            }
            else if (!args.initialize)
            {
                VisualPositioningSystem.StopLocalizing().Forget();
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
                await UniTask.SwitchToMainThread();

                await VisualPositioningSystem.StartLocalizationSession();

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
            return new ARFoundationCameraProvider(SceneReferences.ARCameraManager);
#endif
        }
    }
}
