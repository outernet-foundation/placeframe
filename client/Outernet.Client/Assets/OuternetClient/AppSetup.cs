using UnityEngine;
using Outernet.Client.Location;
using Cysharp.Threading.Tasks;
using FofX.Serialization;
using Unity.Mathematics;
using SimpleJSON;
using Plerion.Core;

#if AUTHORING_TOOLS_ENABLED
using UnityEngine.InputSystem.UI;
#endif

namespace Outernet.Client
{
    public class AppSetup : MonoBehaviour
    {
        public PrefabSystem prefabSystem;
        public SceneReferences sceneReferences;
        public LocalizationMapManager localizationMapManager;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Initialize()
        {
            Logger.Initialize();

            UnityEnv env = UnityEnv.GetOrCreateInstance();

            Log.enabledLogGroups = env.enabledLogGroups;
            Log.logLevel = env.logLevel;
            Log.stackTraceLevel = env.stackTraceLevel;
        }

        private void Awake()
        {
            AddCustomSerializers();
            sceneReferences.Initialize();

#if AUTHORING_TOOLS_ENABLED
            AuthoringTools.AuthoringToolsPrefabs.Initialize("AuthoringToolsPrefabs");

            Destroy(SceneReferences.XrOrigin);
            Destroy(SceneReferences.ArSession);

            var camera = Instantiate(AuthoringTools.AuthoringToolsPrefabs.Camera);
            var defaultRaycaster = camera.gameObject.AddComponent<AuthoringTools.DefaultRaycaster>();
#endif

            UnityEnv env = UnityEnv.GetOrCreateInstance();
            App.environmentURL = env.environmentURL;
            App.apiUrl = env.plerionApiUrl;
            App.authTokenUrl = env.plerionAuthTokenUrl;
            App.authAudience = env.plerionAuthAudience;

            Instantiate(prefabSystem, transform);

            gameObject.AddComponent<App>();
            gameObject.AddComponent<Platform>();

            PrefabSystem.Create(PrefabSystem.cesiumCreditSystemUI);

            ConnectionManager.Initialize();
            PlaneDetector.Initialize().Forget();

            gameObject.AddComponent<GPSManager>();

#if !AUTHORING_TOOLS_ENABLED
            SceneViewManager.Initialize();
            TilesetManager.Initialize();
            Instantiate(localizationMapManager);
#else
            Auth.Initialize(
                env.plerionAuthTokenUrl,
                env.plerionAuthAudience,
                x => Log.Info(x),
                x => Log.Warn(x),
                x => Log.Error(x)
            );

            Auth.Login("user", "password").Forget();

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
    }
}