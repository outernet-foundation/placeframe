using FofX.Stateful;
using Nessle;
using Outernet.Logging;
using Placeframe.Core;
using UnityEngine;
#if !UNITY_EDITOR
using Placeframe.Core.ARFoundation;
#endif

namespace Placeframe.Client
{
    public class AppSetup : MonoBehaviour
    {
        public SceneReferences sceneReferences;
        public UIPrimitiveSet uiPrimitives;
        public UIElementSet uiElements;
        public LocalizationMapManager localizationMapManager;

        private void Awake()
        {
            Logger<LogGroup>.Initialize();

            sceneReferences.Initialize();

            Application.targetFrameRate = 120;
            UIBuilder.primitives = uiPrimitives;
            UIElements.elements = uiElements;

            gameObject.AddComponent<App>();

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

            Destroy(this);
        }
    }
}
