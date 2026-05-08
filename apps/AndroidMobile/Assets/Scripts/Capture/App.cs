using FofX.Stateful;
using FofX;
using Nessle;
using ObserveThing;
using Outernet.Logging;
using Placeframe.Core;
using UnityEngine;
using static Placeframe.Client.UIElements;
#if !UNITY_EDITOR
using Placeframe.Core.ARFoundation;
#endif

namespace Placeframe.Client
{
    public class App : AppBase<AppState>
    {
        public SceneReferences sceneReferences;
        public UIPrimitiveSet uiPrimitives;
        public UIElementSet uiElements;
        public LocalizationMapManager localizationMapManager;

        private IControl ui;

        protected override void InitializeState(AppState state)
            => state.Initialize(
                Settings.DefaultObservationContext,
                new UnityLogger() { logLevel = FofX.LogLevel.Trace },
                "root");

        protected override void Awake()
        {
            Logger<LogGroup>.Initialize(labels: new[]
            {
                ("app", "capture-tool"),
#if UNITY_EDITOR
                ("platform", "editor"),
#else
                ("platform", "android-mobile"),
#endif
            });
            sceneReferences.Initialize();

            Application.targetFrameRate = 120;
            UIBuilder.primitives = uiPrimitives;
            UIElements.elements = uiElements;

            base.Awake();
            ui = AppUI();

            App.state.placeframeAuthAudience.value = "placeframe-api";

            Instantiate(localizationMapManager);

#if UNITY_EDITOR
            var cameraProvider = new NoOpCameraProvider();
#else
            var cameraProvider = new CameraProvider(SceneReferences.ARCameraManager, SceneReferences.ARAnchorManager);
#endif

            CaptureManager.Initialize(cameraProvider);
            LocalizationManager.Initialize(cameraProvider);
            AuthManager.Initialize();
            SettingsManager.Initialize();
            CaptureController.Initialize();
        }

        void OnDestroy()
        {
            CaptureController.Shutdown();
            LocalizationManager.Shutdown();
            SettingsManager.Shutdown();
            AuthManager.Shutdown();
            ui?.Dispose();
        }
    }
}
