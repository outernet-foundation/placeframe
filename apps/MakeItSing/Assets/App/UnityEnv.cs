using UnityEngine;
using FofX;
using System;

#if UNITY_EDITOR
using UnityEditor;
#endif

namespace Plerion.MakeItSing
{
    public class UnityEnv : ScriptableObject
    {
        private static UnityEnv _instance;
        public string supabaseProjectId;
        public string supabaseApiKey;

        public bool runInOfflineMode;

        [Header("Editor Overrides")]

        public bool overridePlatform;
        [ToggleGroup(nameof(overridePlatform), disable: true)]
        public Platform platform;

        public bool overrideConfig;

        [ToggleGroup(nameof(overrideConfig), disable: true)]
        public LogGroup logGroups;

        [ToggleGroup(nameof(overrideConfig), disable: true)]
        public Outernet.Logging.LogLevel logLevel;

        [ToggleGroup(nameof(overrideConfig), disable: true)]
        public Outernet.Logging.LogLevel stackTraceLevel;

        [ToggleGroup(nameof(overrideConfig), disable: true)]
        public Outernet.Logging.LogLevel notificationLogLevel;

        [ToggleGroup(nameof(overrideConfig), disable: true)]
        public string photonProjectId;

        [ToggleGroup(nameof(overrideConfig), disable: true)]
        public bool loginAutomatically;

        [ToggleGroup(nameof(overrideConfig), disable: true)]
        public string domain;

        [ToggleGroup(nameof(overrideConfig), disable: true)]
        public string username;

        [ToggleGroup(nameof(overrideConfig), disable: true)]
        public string password;

        [ToggleGroup(nameof(overrideConfig), disable: true)]
        public string room;

        [ToggleGroup(nameof(overrideConfig), disable: true)]
        public bool disableSystemUI;

        public static UnityEnv GetOrCreateInstance()
        {
            if (_instance != null)
                return _instance;

            _instance = Resources.Load<UnityEnv>(nameof(UnityEnv));

            if (_instance == null)
            {
                _instance = CreateInstance<UnityEnv>();

#if UNITY_EDITOR
                if (!System.IO.Directory.Exists($"{Application.dataPath}/_LocalWorkspace"))
                    AssetDatabase.CreateFolder("Assets", "_LocalWorkspace");

                if (!System.IO.Directory.Exists($"{Application.dataPath}/_LocalWorkspace/Resources"))
                    AssetDatabase.CreateFolder("Assets/_LocalWorkspace", "Resources");

                string name = AssetDatabase.GenerateUniqueAssetPath(
                    $"Assets/_LocalWorkspace/Resources/{nameof(UnityEnv)}.asset"
                );
                AssetDatabase.CreateAsset(_instance, name);
                AssetDatabase.SaveAssets();
#endif
            }

            return _instance;
        }
    }
}
