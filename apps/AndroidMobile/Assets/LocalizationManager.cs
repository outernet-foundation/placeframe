using System;
using System.Collections.Generic;
using FofX.Stateful;
using ObserveThing;
using Placeframe.Core;
using UnityEngine;

namespace Placeframe.Client
{
    public class LocalizationManager : MonoBehaviour
    {
        private IDisposable _subscription;
        private bool _intializing;
        public void Initialize(ICameraProvider cameraProvider)
        {
            VisualPositioningSystem.Initialize(
                cameraProvider,
                App.state.placeframeAuthAudience.value,
                message => Log.Info(LogGroup.Localizer, message),
                message => Log.Warn(LogGroup.Localizer, message),
                message => Log.Error(LogGroup.Localizer, message),
                httpHandlerFactory: InternetBoundHandler.Create
            );

            _intializing = true;

            _subscription = new ComposedDisposable(
                Observables.ObservableCombineValues(
                    App.state.mode,
                    App.state.localizing,
                    (mode, localizing) => mode == AppMode.Validation && localizing).Subscribe(localizing =>
                    {
                        if (_intializing)
                            return;

                        if (!localizing)
                        {
                            VisualPositioningSystem.StopLocalizing();
                        }
                        else
                        {
                            VisualPositioningSystem.StartLocalizing(1.0f);
                        }
                    }),
                    App.state.mapForLocalization.ObservableWithPrevious().Subscribe((previous, current) =>
                    {
                        if (_intializing)
                            return;

                        if (previous != Guid.Empty)
                        {
                            VisualPositioningSystem.RemoveLocalizationMap(previous);
                        }

                        if (current != Guid.Empty)
                        {
                            VisualPositioningSystem.AddLocalizationMap(current);
                        }
                    })
            );

            _intializing = false;
        }
    }
}
