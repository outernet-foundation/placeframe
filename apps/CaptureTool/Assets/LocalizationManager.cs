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
        private static IDisposable _authSubscription;
        private static ICameraProvider _cameraProvider;
        private static bool _visualPositioningSystemInitialized;
        private static bool _intializing;

        public static void Initialize(ICameraProvider cameraProvider)
        {
            _cameraProvider = cameraProvider;

            // VisualPositioningSystem.Initialize composes the authenticated API client from the
            // discovered server URL plus the handler AuthManager built, so it can only run after
            // a successful login. Initialize throws on a second call, so only the first login
            // initializes it; a same-server re-login keeps the existing client (its handler
            // refreshes tokens on its own).
            _authSubscription = App.state.authStatus.Subscribe(status =>
            {
                if (status != AuthStatus.LoggedIn || _visualPositioningSystemInitialized)
                    return;

                _visualPositioningSystemInitialized = true;
                VisualPositioningSystem.Initialize(
                    App.state.settings.apiUrl.value,
                    _cameraProvider,
                    message => Log.Info(LogGroup.Localizer, message),
                    message => Log.Warn(LogGroup.Localizer, message),
                    message => Log.Error(LogGroup.Localizer, message),
                    httpMessageHandler: AuthManager.HttpMessageHandler
                );
            });

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
            _authSubscription?.Dispose();
            _authSubscription = null;
        }
    }
}
