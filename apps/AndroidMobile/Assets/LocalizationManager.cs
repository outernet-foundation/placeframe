using System;
using System.Collections.Generic;
using FofX.Stateful;
using Placeframe.Core;
using UnityEngine;

namespace Placeframe.Client
{
    public class LocalizationManager : MonoBehaviour
    {
        public void Initialize(ICameraProvider cameraProvider)
        {
            VisualPositioningSystem.Initialize(
                cameraProvider,
                App.state.placeframeApiUrl.value,
                App.state.placeframeAuthTokenUrl.value,
                App.state.placeframeAuthAudience.value,
                message => Log.Info(LogGroup.Localizer, message),
                message => Log.Warn(LogGroup.Localizer, message),
                message => Log.Error(LogGroup.Localizer, message)
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
                VisualPositioningSystem.StartLocalizing(1.0f);
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
    }
}
