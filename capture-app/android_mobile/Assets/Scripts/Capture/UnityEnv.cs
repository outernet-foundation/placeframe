using UnityEngine;

#if UNITY_EDITOR
using UnityEditor;
#endif

namespace PlerionClient.Client
{
    [CreateAssetMenu(fileName = "EditorSettings", menuName = "Scriptable Objects/EditorSettings")]
    public class UnityEnv : ScriptableObject
    {
        private static UnityEnv _instance;
        public string plerionBaseURL = "https://api.outernetfoundation.org";
        public bool loginAutomatically;
        public string username;
        public string password;

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
    }
}