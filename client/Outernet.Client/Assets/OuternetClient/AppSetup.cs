using UnityEngine;
using Outernet.Client.Location;
using Cysharp.Threading.Tasks;
using FofX.Serialization;
using Unity.Mathematics;
using SimpleJSON;
using Outernet.Client.AuthoringTools;
using System;


#if AUTHORING_TOOLS_ENABLED
using UnityEngine.InputSystem.UI;
#endif

namespace Outernet.Client
{
    public class AppSetup : MonoBehaviour
    {
        public PrefabSystem prefabSystem;
        public SceneReferences sceneReferences;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Initialize()
        {
            Logger.Initialize();

#if UNITY_EDITOR
            var editorSettings = EditorSettings.GetOrCreateInstance();
            Log.enabledLogGroups = editorSettings.enabledLogGroups;
            Log.logLevel = editorSettings.logLevel;
            Log.stackTraceLevel = editorSettings.stackTraceLevel;
#else
            Log.enabledLogGroups = ~LogGroup.None; // Enable all log groups
            Log.logLevel = LogLevel.Info;
            Log.stackTraceLevel = LogLevel.Warn;
#endif
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

            string plerionAPIBaseUrl = "https://api.outernetfoundation.org";

#if UNITY_EDITOR
            var editorSettings = EditorSettings.GetOrCreateInstance();
            App.environmentURL = editorSettings.environmentURL;
            App.environmentSchema = editorSettings.environmentSchema;

            if (editorSettings.overridePlerionBaseUrl)
                plerionAPIBaseUrl = editorSettings.plerionAPIBaseUrl;
#else
            App.environmentURL = "http://34.196.34.28";
            App.environmentSchema = "dev2";
#endif

            PlerionAPI.Initialize(plerionAPIBaseUrl);

            Instantiate(prefabSystem, transform);

            gameObject.AddComponent<App>();
            gameObject.AddComponent<Platform>();

            PrefabSystem.Create(PrefabSystem.cesiumCreditSystemUI);

            ConnectionManager.Initialize();
            PlaneDetector.Initialize().Forget();
            LocalizedReferenceFrame.Initialize();

#if !AUTHORING_TOOLS_ENABLED
            SceneViewManager.Initialize();
            Localizer.Initialize();
            TilesetManager.Initialize();
#else
            var canvas = Instantiate(AuthoringTools.AuthoringToolsPrefabs.Canvas);
            var systemMenu = Instantiate(AuthoringTools.AuthoringToolsPrefabs.SystemMenu, canvas.transform);

            gameObject.AddComponent<AuthoringTools.AuthoringToolsApp>();
            Instantiate(AuthoringTools.AuthoringToolsPrefabs.UI, canvas.transform);

            systemMenu.transform.SetAsLastSibling();

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
            GetLayersAndPopulate();
            Destroy(this);
        }

        private async void GetLayersAndPopulate()
        {
            App.state.layers.ExecuteActionOrDelay(x =>
            {
                var layer = x.Add(Guid.NewGuid());
                layer.layerName.value = "main";

                layer = x.Add(Guid.NewGuid());
                layer.layerName.value = "other";
            });


            // var layers = await PlerionAPI.api.GetLayersAsync();
            // await UniTask.SwitchToMainThread();

            // if (layers == null)
            return;

            // App.ExecuteActionOrDelay(new SetLayersAction(layers.ToArray()));
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