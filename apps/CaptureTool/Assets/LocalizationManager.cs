using System;
using System.Net.Http;
using FofX.Stateful;
using ObserveThing;
using Placeframe.Core;

namespace Placeframe.Client
{
    public static class LocalizationManager
    {
        private static IDisposable _subscription;
        private static bool _intializing;

        public static void Initialize(ICameraProvider cameraProvider)
        {
            VisualPositioningSystem.Initialize(
                cameraProvider,
                message => Log.Info(LogGroup.Localizer, message),
                message => Log.Warn(LogGroup.Localizer, message),
                message => Log.Error(LogGroup.Localizer, message),
                httpHandlerFactory: () => new LoggingHttpHandler
                {
                    InnerHandler = new ProgressTrackingHandler { InnerHandler = new HttpClientHandler() }
                }
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
                    App.state.mapForLocalization.ObservableWithPrevious().Subscribe((current, previous) =>
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

        public static void Shutdown()
        {
            _subscription?.Dispose();
            _subscription = null;
        }
    }
}
