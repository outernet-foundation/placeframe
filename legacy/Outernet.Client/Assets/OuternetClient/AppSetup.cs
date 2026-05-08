using UnityEngine;
using Outernet.Client.Location;
using Outernet.Logging;
using Cysharp.Threading.Tasks;
using FofX.Serialization;
using Unity.Mathematics;
using SimpleJSON;
using Placeframe.Core;
using Nessle;
using Outernet.Client.AuthoringTools;

#if AUTHORING_TOOLS_ENABLED
using UnityEngine.InputSystem.UI;
#endif

namespace Outernet.Client
{
    public class AppSetup : MonoBehaviour
    {
        private static readonly string AUTH_AUDIENCE = "placeframe-api";
        public PrefabSystem prefabSystem;
        public SceneReferences sceneReferences;
        public LocalizationMapManager localizationMapManager;
        public UIPrimitiveSet uiPrimitives;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Initialize()
        {
            UnityEngine.Debug.Log($"[BuildInfo] {Application.version}");
            Logger<LogGroup>.Initialize(
                labels: new[]
                {
                    ("app", "outernet-client"),
#if UNITY_EDITOR
                    ("platform", "editor"),
#elif MAGIC_LEAP
                    ("platform", "magic-leap"),
#elif OUTERNET_ANDROID_MOBILE
                    ("platform", "android-mobile"),
#else
                    ("platform", "unknown"),
#endif
                },
                suppressErrors: new[]
                {
                    "Error: MLCamera.InternalGetFramePose failed to get camera frame pose. Reason: MLResult_PoseNotFound",
                    "Error: MLCVCameraGetFramePose in the Magic Leap API failed. Reason: MLResult_PoseNotFound",
                    "Error: XrBeginPlaneDetection in the Magic Leap API failed. Reason: SpaceNotLocatableEXT",
                    "OPENGL NATIVE PLUG-IN ERROR: GL_INVALID_ENUM",
                });

            Log.enabledLogGroups = ~LogGroup.None;
            Log.logLevel = LogLevel.Info;
            Log.stackTraceLevel = LogLevel.Warn;

            Log.Info($"Build {Application.version}");
        }

        private void Awake()
        {
            Nessle.UIBuilder.primitives = uiPrimitives;

            AddCustomSerializers();
            sceneReferences.Initialize();

#if AUTHORING_TOOLS_ENABLED
            AuthoringTools.AuthoringToolsPrefabs.Initialize("AuthoringToolsPrefabs");

            Destroy(SceneReferences.XrOrigin);
            Destroy(SceneReferences.ArSession);

            var camera = Instantiate(AuthoringTools.AuthoringToolsPrefabs.Camera);
            var defaultRaycaster = camera.gameObject.AddComponent<AuthoringTools.DefaultRaycaster>();
#endif

            Instantiate(prefabSystem, transform);

            gameObject.AddComponent<UINavigationHelper>();
            gameObject.AddComponent<App>();
            gameObject.AddComponent<Platform>();

            PrefabSystem.Create(PrefabSystem.cesiumCreditSystemUI);

            ConnectionManager.Initialize();
            PlaneDetector.Initialize().Forget();

            gameObject.AddComponent<GPSManager>();
            gameObject.AddComponent<UserSettingsManager>();

#if !AUTHORING_TOOLS_ENABLED
            SceneViewManager.Initialize();
            TilesetManager.Initialize();
            Instantiate(localizationMapManager);
            gameObject.AddComponent<SystemUI>();
#else
            gameObject.AddComponent<AuthoringTools.AuthoringToolsApp>();

            var canvas = Instantiate(AuthoringTools.AuthoringToolsPrefabs.Canvas);
            var systemUI = Instantiate(AuthoringTools.AuthoringToolsPrefabs.SystemMenu, canvas.transform);
            var mainUI = Instantiate(AuthoringTools.AuthoringToolsPrefabs.UI, canvas.transform);

            systemUI.transform.SetAsLastSibling();

            gameObject.AddComponent<AuthoringTools.LocationContentManager>();
            gameObject.AddComponent<AuthoringTools.SettingsManager>();
            gameObject.AddComponent<AuthoringTools.SceneTransformGizmoManager>();
            gameObject.AddComponent<AuthoringTools.UndoRedoManager>();
            gameObject.AddComponent<AuthoringTools.PersistenceManager>();

            var sceneViewRoot = Instantiate(AuthoringTools.AuthoringToolsPrefabs.SceneViewManager);
            defaultRaycaster.defaultObject = sceneViewRoot.gameObject;

            var inputModuleGO = SceneReferences.InputModule.gameObject;
            Destroy(SceneReferences.InputModule);
            inputModuleGO.AddComponent<InputSystemUIInputModule>();

            // set runtime handles to be a child of the scene view root so input events bubble properly
            var runtimeHandles = new GameObject("RuntimeHandles", typeof(AuthoringTools.RuntimeHandles));
            runtimeHandles.transform.SetParent(sceneViewRoot.transform);
#endif

#if !OUTERNET_MAGIC_LEAP
            Destroy(SceneReferences.GlobalNonNativeKeyboard.gameObject); // prefer system keyboards where ever they are available
#endif

            VisualPositioningSystem.Initialize(
                GetProvider(),
                AUTH_AUDIENCE,
                x => Log.Debug(LogGroup.Default, x),
                x => Log.Warn(LogGroup.Default, x),
                x => Log.Error(LogGroup.Default, x)
            );

            gameObject.AddComponent<LocalizationManager>();

            Destroy(this);
        }

        private void AddCustomSerializers()
        {
            JSONSerialization.AddSerializer(
                json =>
                {
                    if (json == null || json.IsNull)
                        return new double2();

                    var arr = (JSONArray)json;
                    return new double2(arr[0].AsDouble, arr[1].AsDouble);
                },
                value =>
                {
                    var arr = new JSONArray();
                    arr[0] = value.x;
                    arr[1] = value.y;
                    return arr;
                }
            );

            JSONSerialization.AddSerializer<double2?>(
                json =>
                {
                    if (json == null || json.IsNull)
                        return null;

                    var arr = (JSONArray)json;
                    return new double2(arr[0].AsDouble, arr[1].AsDouble);
                },
                value =>
                {
                    if (value == null)
                        JSONNull.CreateOrGet();

                    var arr = new JSONArray();
                    arr[0] = value?.x;
                    arr[1] = value?.y;
                    return arr;
                }
            );

            JSONSerialization.AddSerializer(
                json =>
                {
                    if (json == null || json.IsNull)
                        return new double3();

                    var arr = (JSONArray)json;
                    return new double3(arr[0].AsDouble, arr[1].AsDouble, arr[2].AsDouble);
                },
                value =>
                {
                    var arr = new JSONArray();
                    arr[0] = value.x;
                    arr[1] = value.y;
                    arr[2] = value.z;
                    return arr;
                }
            );

            JSONSerialization.AddSerializer<double3?>(
                json =>
                {
                    if (json == null || json.IsNull)
                        return null;

                    var arr = (JSONArray)json;
                    return new double3(arr[0].AsDouble, arr[1].AsDouble, arr[2].AsDouble);
                },
                value =>
                {
                    if (value == null)
                        JSONNull.CreateOrGet();

                    var arr = new JSONArray();
                    arr[0] = value?.x;
                    arr[1] = value?.y;
                    arr[2] = value?.z;
                    return arr;
                }
            );
        }

        private ICameraProvider GetProvider()
        {
#if UNITY_EDITOR
            return new NoOpCameraProvider();
#elif MAGIC_LEAP
            return new Placeframe.Core.MagicLeap.MagicLeapCameraProvider();
#elif UNITY_ANDROID
            return new Placeframe.Core.ARFoundation.CameraProvider(Camera.main.GetComponent<UnityEngine.XR.ARFoundation.ARCameraManager>(), SceneReferences.AnchorManager);
#else
            return new NoOpCameraProvider();
#endif
        }
    }
}