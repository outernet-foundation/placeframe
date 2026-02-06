using FofX.Serialization;
using Placeframe.Core;
using SimpleJSON;
using Unity.Mathematics;
using UnityEngine;

namespace Placeframe.MapRegistrationTool
{
    public class AppSetup : MonoBehaviour
    {
        public SceneReferences sceneReferences;

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

            Prefabs.Initialize("Prefabs");
            var defaultRaycaster = Camera.main.gameObject.AddComponent<DefaultRaycaster>();

            UnityEnv env = UnityEnv.GetOrCreateInstance();
            VisualPositioningSystem.Initialize(
                null,
                env.placeframeAuthAudience,
                message => Debug.Log(message),
                message => Debug.LogWarning(message),
                message => Debug.LogError(message)
            );

            gameObject.AddComponent<App>();

            var creditSystem = Instantiate(Prefabs.CesiumCreditSystem);

            // if this is not the only object loaded into unity with this name (including it's source prefab), the credit system will error
            creditSystem.name = "CesiumCreditSystemDefault";

            var canvas = Instantiate(Prefabs.Canvas);
            var systemUI = Instantiate(Prefabs.SystemMenu, canvas.transform); // system menu must exist first because map registration ui because staticly references it
            var mainUI = Instantiate(Prefabs.MapRegistrationUI, canvas.transform);

            systemUI.transform.SetAsLastSibling();

            Instantiate(Prefabs.LoginScreen, canvas.transform);

            gameObject.AddComponent<LocationContentManager>();
            gameObject.AddComponent<SettingsManager>();
            gameObject.AddComponent<SceneTransformGizmoManager>();
            gameObject.AddComponent<UndoRedoManager>();
            gameObject.AddComponent<PersistenceManager>();

            var sceneViewRoot = Instantiate(Prefabs.SceneViewManager);
            defaultRaycaster.defaultObject = sceneViewRoot.gameObject;

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
