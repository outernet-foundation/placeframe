using System;
using System.IO;
using UnityEngine;
using dotenv.net;

#if UNITY_EDITOR
using UnityEditor;
#endif

namespace Outernet.Client
{
    public class UnityEnv : ScriptableObject
    {
        private static UnityEnv _instance;

        public LogGroup enabledLogGroups = ~LogGroup.None; // Enable all log groups
        public LogLevel logLevel = LogLevel.Info;
        public LogLevel stackTraceLevel = LogLevel.Warn;

        public string dotEnvPath;
        public string placeframeApiUrl;
        public string placeframeAuthTokenUrl;
        public string placeframeAuthAudience;

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

                string name = AssetDatabase.GenerateUniqueAssetPath($"Assets/_LocalWorkspace/Resources/{nameof(UnityEnv)}.asset");
                AssetDatabase.CreateAsset(_instance, name);
                AssetDatabase.SaveAssets();
#endif
            }

            return _instance;
        }

#if UNITY_EDITOR
        private void OnValidate()
        {
            // Called when you change fields (like dotEnvPath) in the inspector and hit save.
            if (!Application.isPlaying && _instance != null)
            {
                ReloadFromDotEnv();
                EditorUtility.SetDirty(this);
            }
        }
#endif


        private static void ReloadFromDotEnv()
        {
            if (!string.IsNullOrEmpty(_instance.dotEnvPath))
            {
                try
                {
                    DotEnv.Load(
                        new DotEnvOptions(
                            envFilePaths: new[]
                            {
                                Path.GetFullPath(
                                    Path.Combine(
                                        Directory.GetParent(Application.dataPath)!.FullName,
                                        _instance.dotEnvPath
                                    )
                                ),
                            },
                            ignoreExceptions: false
                        )
                    );

                    var publicDomain = Environment.GetEnvironmentVariable("PUBLIC_DOMAIN");

                    if (string.IsNullOrEmpty(publicDomain))
                    {
                        throw new Exception("PUBLIC_DOMAIN is not set in the .env file.");
                    }

                    var authAudience = Environment.GetEnvironmentVariable("AUTH_AUDIENCE");

                    if (string.IsNullOrEmpty(authAudience))
                    {
                        throw new Exception("AUTH_AUDIENCE is not set in the .env file.");
                    }

                    _instance.placeframeApiUrl = $"https://{publicDomain}";
                    _instance.placeframeAuthTokenUrl =
                        $"{_instance.placeframeApiUrl}/auth/realms/placeframe-dev/protocol/openid-connect/token";
                    _instance.placeframeAuthAudience = authAudience;
                }
                catch (Exception exception)
                {
                    Debug.LogError($"Failed to load .env file at {_instance.dotEnvPath}: {exception.Message}");
                }
            }
        }

        private static void ApplyEnvironmentVariable(string key, ref string field)
        {
            string value = Environment.GetEnvironmentVariable(key);

            if (string.IsNullOrEmpty(value))
            {
                Debug.LogError(
                    $"UnityEnv: required environment variable '{key}' is missing or empty. "
                        + $"Keeping existing value '{field ?? "<null>"}'."
                );
                return;
            }

            field = value;
        }
    }
}