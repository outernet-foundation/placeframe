using Nessle;
using Placeframe.Core;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class AppSetup : MonoBehaviour
    {
        public SceneReferences sceneReferences;
        public Prefabs prefabs;
        public UIPrimitiveSet uiPrimitives;

        private void Awake()
        {
            sceneReferences.Initialize();
            prefabs.Initialize();

            VisualPositioningSystem.Initialize(
                GetCameraProvider(),
                "placeframe-api",
                x => Debug.Log(x),
                x => Debug.LogWarning(x),
                x => Debug.LogError(x)
            );

            UIBuilder.primitives = uiPrimitives;

            Instantiate(Prefabs.LocalizationMapManager);

            gameObject.AddComponent<App>();
            gameObject.AddComponent<PhotonConnectionManager>();
            gameObject.AddComponent<SettingsManager>();
            gameObject.AddComponent<AppUI>();

            Destroy(this);
        }

        private ICameraProvider GetCameraProvider()
        {
#if UNITY_EDITOR
            return new NoOpCameraProvider();
#elif MAGIC_LEAP
            return new Placeframe.Core.MagicLeap.MagicLeapCameraProvider();
#elif UNITY_ANDROID
            return new Placeframe.Core.ARFoundation.CameraProvider(SceneReferences.ARCameraManager, SceneReferences.ARAnchorManager);
#else
            return new NoOpCameraProvider();
#endif
        }
    }
}