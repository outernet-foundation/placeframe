using System;
using FofX.Serialization;
using Nessle;
using Placeframe.Core;
using SimpleJSON;
using Unity.Mathematics;
using UnityEngine;
using ObserveThing;
using Cysharp.Threading.Tasks;
using UnityEngine.Splines;
using Outernet.Logging;
using System.Linq;

namespace Plerion.MakeItSing
{
    [Flags]
    public enum LogGroup
    {
        None = 0,
        UnhandledExceptions = 1,
        Stateful = 2,
        PhotonConnection = 4
    }

    public class AppSetup : MonoBehaviour
    {
        public SceneReferences sceneReferences;
        public Prefabs prefabs;
        public UIPrimitiveSet uiPrimitives;
        public UIElementSet uiElements;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Initialize()
        {
            UnityEngine.Debug.Log($"[BuildInfo] {Application.version}");

            Logger<LogGroup>.Initialize();

            var env = UnityEnv.GetOrCreateInstance();

            Log<LogGroup>.enabledLogGroups = env.logGroups;
            Log<LogGroup>.logLevel = env.logLevel;
            Log<LogGroup>.stackTraceLevel = env.stackTraceLevel;

            Log<LogGroup>.Info($"Build {Application.version}");

            Settings.DefaultExceptionHandler = exc => Log<LogGroup>.Error(LogGroup.UnhandledExceptions, exc);
        }

        private void Awake()
        {
            var env = UnityEnv.GetOrCreateInstance();

            Application.targetFrameRate = -1;
            SupabaseAPI.ProjectId = env.supabaseProjectId;
            SupabaseAPI.ApiKey = env.supabaseApiKey;

            sceneReferences.Initialize();
            prefabs.Initialize();

            AddSerializers();

            VisualPositioningSystem.Initialize(
                GetCameraProvider(),
                "placeframe-api",
                x => Debug.Log(x),
                x => Debug.LogWarning(x),
                x => Debug.LogError(x)
            );

            UIBuilder.primitives = uiPrimitives;
            UIElements.elements = uiElements;

            Instantiate(Prefabs.LocalizationMapManager);

            // #if !PLERION_MAGIC_LEAP
            //             foreach (var controller in SceneReferences.Controllers)
            //                 controller.SetActive(false);
            // #endif

            gameObject.AddComponent<App>();

#if UNITY_EDITOR
            App.state.platform.value = env.overridePlatform ? env.platform : GetPlatform();
#else
            App.state.platform.value = GetPlatform();
#endif

            App.state.version.value = Application.version;

            gameObject.AddComponent<PhotonConnectionManager>();
            gameObject.AddComponent<SettingsManager>();
            gameObject.AddComponent<AppUI>();
            gameObject.AddComponent<LocalizationManager>();
            gameObject.AddComponent<SupabaseContentHelper>();
            gameObject.AddComponent<NotificationManager>();

#if UNITY_EDITOR
            if (env.overrideConfig)
            {
                App.ExecuteTransaction(state =>
                {
                    state.config.logGroups.value = env.logGroups;
                    state.config.logLevel.value = env.logLevel;
                    state.config.stackTraceLevel.value = env.stackTraceLevel;
                    state.config.notificationLogLevel.value = env.notificationLogLevel;
                    state.nameServerConnection.connectionString.value = env.photonProjectId;
                    state.userSettings.domain.value = env.domain;
                    state.userSettings.username.value = env.username;
                    state.userSettings.password.value = env.password;
                    state.roomID.value = string.IsNullOrEmpty(env.room) ? Guid.Empty : new Guid(env.room);

                    if (env.loginAutomatically)
                        state.loginStatus.value = LoginStatus.LoginRequested;

                    state.config.disableSystemUI.value = env.disableSystemUI;
                });
            }
            else
            {
                InitializeConfig();
            }
#else
            InitializeConfig();
#endif

            //TODO: Remove this!
            // App.state.loginStatus.value = LoginStatus.LoggedIn;

            Destroy(this);
        }

        private void InitializeConfig()
        {
            SupabaseAPI.GetPrioritizedConfig(
                SystemInfo.deviceUniqueIdentifier,
                App.state.version.value,
                App.state.platform.value.ToString()
            ).ContinueWith(config => App.ExecuteTransaction(state =>
            {
                if (config.log_groups != null)
                    App.state.config.logGroups.value = config.log_groups.Value == -1 ? ((LogGroup)~0) : (LogGroup)config.log_groups.Value;

                if (config.log_level != null)
                    App.state.config.logLevel.value = config.log_level.Value;

                if (config.stack_trace_level != null)
                    App.state.config.stackTraceLevel.value = config.stack_trace_level.Value;

                if (config.notification_log_level != null)
                    App.state.config.notificationLogLevel.value = config.notification_log_level.Value;

                if (config.photon_project_id != null)
                    App.state.nameServerConnection.connectionString.value = config.photon_project_id;

                if (config.login_automatically ?? false)
                    App.state.loginStatus.value = LoginStatus.LoginRequested;

                if (config.domain != null)
                    App.state.userSettings.domain.value = config.domain;

                if (config.username != null)
                    App.state.userSettings.username.value = config.username;

                if (config.password != null)
                    App.state.userSettings.password.value = config.password;

                if (config.room.HasValue)
                    App.state.roomID.value = config.room.Value;

                if (config.disable_system_ui != null)
                    App.state.config.disableSystemUI.value = config.disable_system_ui.Value;

            })).Forget();
        }

        private void AddSerializers()
        {
            JSONSerialization.AddSerializer(
                new SerializationPair<double2>(
                    JSONSerializers.ToDouble2,
                    JSONSerializers.ToJSON
                )
            );

            JSONSerialization.AddSerializer(
                new SerializationPair<double3>(
                    JSONSerializers.ToDouble3,
                    JSONSerializers.ToJSON
                )
            );

            JSONSerialization.AddSerializer(
                new SerializationPair<Vector2>(
                    JSONSerializers.ToVector2,
                    JSONSerializers.ToJSON
                )
            );

            JSONSerialization.AddSerializer(
                new SerializationPair<Vector3>(
                    JSONSerializers.ToVector3,
                    JSONSerializers.ToJSON
                )
            );

            JSONSerialization.AddSerializer(
                new SerializationPair<Vector4>(
                    JSONSerializers.ToVector4,
                    JSONSerializers.ToJSON
                )
            );

            JSONSerialization.AddSerializer(
                new SerializationPair<Quaternion>(
                    JSONSerializers.ToQuaternion,
                    JSONSerializers.ToJSON
                )
            );


            JSONSerialization.AddSerializer(
                new SerializationPair<Color>(
                    JSONSerializers.ToColor,
                    JSONSerializers.ToJSON
                )
            );

            JSONSerialization.AddSerializer(
                new SerializationPair<SceneObjectId>(
                    json => new SceneObjectId(json.AsInt),
                    value => value.value
                )
            );

            JSONSerialization.AddSerializer(
                new SerializationPair<HighFrequencyPrimitiveId>(
                    json => new HighFrequencyPrimitiveId(json.AsInt),
                    value => value.value
                )
            );

            JSONSerialization.AddSerializer(
                new SerializationPair<DateTime>(
                    json => DateTime.Parse(json.Value),
                    value => value.ToUniversalTime().ToString("O")
                )
            );

            JSONSerialization.AddSerializer(
                new SerializationPair<BezierKnot>(
                    json =>
                    {
                        var vec3Serializer = JSONSerialization.GetSerializer<Vector3>();
                        var quatSerializer = JSONSerialization.GetSerializer<Quaternion>();
                        return new BezierKnot(
                            vec3Serializer.fromJSON(json["position"]),
                            vec3Serializer.fromJSON(json["tangentIn"]),
                            vec3Serializer.fromJSON(json["tangentOut"]),
                            quatSerializer.fromJSON(json["rotation"])
                        );
                    },
                    value =>
                    {
                        var json = new JSONObject();
                        var vec3Serializer = JSONSerialization.GetSerializer<Vector3>();
                        var quatSerializer = JSONSerialization.GetSerializer<Quaternion>();
                        json["position"] = vec3Serializer.toJSON(value.Position);
                        json["tangentIn"] = vec3Serializer.toJSON(value.TangentIn);
                        json["tangentOut"] = vec3Serializer.toJSON(value.TangentOut);
                        json["rotation"] = quatSerializer.toJSON(value.Rotation);
                        return json;
                    }
                )
            );

            PhotonSerialization.AddSerializer(new Serializer<SceneObjectId>((writer, id) => writer.Write(id.value), reader => new SceneObjectId(reader.ReadInt32())));
            PhotonSerialization.AddSerializer(new Serializer<HighFrequencyPrimitiveId>((writer, id) => writer.Write(id.value), reader => new HighFrequencyPrimitiveId(reader.ReadInt32())));
            PhotonSerialization.AddSerializer(new Serializer<BezierKnot>(
                (writer, knot) =>
                {
                    writer.Write(knot.Position.x);
                    writer.Write(knot.Position.y);
                    writer.Write(knot.Position.z);
                    writer.Write(knot.TangentIn.x);
                    writer.Write(knot.TangentIn.y);
                    writer.Write(knot.TangentIn.z);
                    writer.Write(knot.TangentOut.x);
                    writer.Write(knot.TangentOut.y);
                    writer.Write(knot.TangentOut.z);
                    writer.Write(knot.Rotation.value.x);
                    writer.Write(knot.Rotation.value.y);
                    writer.Write(knot.Rotation.value.z);
                    writer.Write(knot.Rotation.value.w);
                },
                reader =>
                {
                    return new BezierKnot(
                        new float3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle()),
                        new float3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle()),
                        new float3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle()),
                        new quaternion(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle())
                    );
                }
            ));
        }

        private Platform GetPlatform()
        {
#if UNITY_STANDALONE_WIN
            return Platform.Windows;
#elif UNITY_STANDALONE_OSX
            return Platform.OSX;
#elif UNITY_STANDALONE_LINUX
            return Platform.Linux;
#elif UNITY_ANDROID
#if PLERION_MAGIC_LEAP
            return Platform.MagicLeap;
#elif PLERION_ANDROID_MOBILE
            return Platform.AndroidMobile;
#endif
#endif
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