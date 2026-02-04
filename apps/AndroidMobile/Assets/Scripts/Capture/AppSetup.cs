using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using FofX.Stateful;
using Nessle;
using Placeframe.Core;
using R3;
using UnityEngine;
#if !UNITY_EDITOR
using Placeframe.Core.ARFoundation;
#endif

namespace Placeframe.Client
{
    public class AppSetup : MonoBehaviour
    {
        public SceneReferences sceneReferences;
        public LocalizationManager localizationManager;
        public UIPrimitiveSet uiPrimitives;
        public UIElementSet uiElements;
        public LocalizationMapManager localizationMapManager;

        private void Awake()
        {
            UniTaskScheduler.UnobservedTaskException += (exception) =>
                Log.Error(LogGroup.UncaughtException, $"Unobserved task exception: {exception}");

            TaskScheduler.UnobservedTaskException += (sender, args) =>
                Log.Error(LogGroup.UncaughtException, $"Unobserved task exception: {args.Exception}");

            ObservableSystem.RegisterUnhandledExceptionHandler(exception =>
                Log.Error(LogGroup.UncaughtException, $"R3 unhandled exception: {exception}")
            );

            sceneReferences.Initialize();

            Application.targetFrameRate = 120;
            UIBuilder.primitives = uiPrimitives;
            UIElements.elements = uiElements;

            gameObject.AddComponent<App>();

            var env = UnityEnv.GetOrCreateInstance();
            App.state.placeframeAuthAudience.ExecuteSet(env.placeframeAuthAudience);

            Instantiate(localizationManager);
            Instantiate(localizationMapManager);

#if UNITY_EDITOR
            var cameraProvider = new NoOpCameraProvider();
#else
            var cameraProvider = new CameraProvider(SceneReferences.ARCameraManager, SceneReferences.ARAnchorManager);
            CaptureManager.Initialize(cameraProvider);
#endif

            localizationManager.Initialize(cameraProvider);
            ZedCaptureController.Initialize();

            gameObject.AddComponent<AuthManager>();
            gameObject.AddComponent<SettingsManager>();
            gameObject.AddComponent<CaptureController>();

            Destroy(this);
        }
    }
}
