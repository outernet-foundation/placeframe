using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using FofX.Stateful;
using Plerion.Core;
using UnityEngine;
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

            App.RegisterObserver(HandleAppModeChanged, App.state.mode, App.state.localizing);
            App.RegisterObserver(HandleMapForLocalizationChanged, App.state.mapForLocalization);
        }

        private void HandleAppModeChanged(NodeChangeEventArgs args)
        {
            if (args.initialize)
                return;

            var previousLocalizing =
                GetPreviousValue(App.state.mode, args.changes) == AppMode.Validation
                && GetPreviousValue(App.state.localizing, args.changes);

            var localizing = App.state.mode.value == AppMode.Validation && App.state.localizing.value;

            if (previousLocalizing && !localizing)
            {
                VisualPositioningSystem.StopLocalizing();
            }

            if (localizing && !previousLocalizing)
            {
                VisualPositioningSystem.StartLocalizing();
            }
        }

        private void HandleMapForLocalizationChanged(NodeChangeEventArgs args)
        {
            if (args.initialize)
                return;

            var previousMapForLocalization = GetPreviousValue(App.state.mapForLocalization, args.changes);
            var mapForLocalization = App.state.mapForLocalization.value;

            if (previousMapForLocalization != Guid.Empty)
            {
                VisualPositioningSystem.RemoveLocalizationMap(previousMapForLocalization);
            }

            if (mapForLocalization != Guid.Empty)
            {
                VisualPositioningSystem.AddLocalizationMap(mapForLocalization);
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
