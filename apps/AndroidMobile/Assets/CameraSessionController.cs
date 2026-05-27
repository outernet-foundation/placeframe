using System;
using ObserveThing;
using PlaceframeApiClient.Model;

namespace Placeframe.Client
{
    public static class CameraSessionController
    {
        private static IDisposable _subscription;

        public static void Initialize()
        {
            _subscription = Observables.ObservableCombineValues(
                App.state.captureStatus,
                App.state.captureMode,
                App.state.mode,
                App.state.localizing,
                CameraNeeded)
                .Subscribe((bool needed) =>
                {
                    var session = SceneReferences.ARSession;
                    if (session == null)
                        return;

                    if (session.enabled == needed)
                        return;

                    session.enabled = needed;
                    Log.Info(LogGroup.Capture, "ARSession {State}", needed ? "enabled" : "disabled");
                });
        }

        public static void Shutdown()
        {
            _subscription?.Dispose();
            _subscription = null;
        }

        private static bool CameraNeeded(
            CaptureStatus captureStatus,
            DeviceType captureMode,
            AppMode mode,
            bool localizing) =>
            (captureStatus != CaptureStatus.Idle && captureMode == DeviceType.ARFoundation)
            || (mode == AppMode.Validation && localizing);
    }
}
