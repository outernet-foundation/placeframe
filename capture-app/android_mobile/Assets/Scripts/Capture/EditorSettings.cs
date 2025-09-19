#if UNITY_EDITOR
using UnityEngine;
using UnityEditor;

namespace PlerionClient.Client
{
    [CreateAssetMenu(fileName = "EditorSettings", menuName = "Scriptable Objects/EditorSettings")]
    public class EditorSettings : ScriptableObject
    {
        private static EditorSettings _instance;


        public static EditorSettings GetOrCreateInstance()
        {
            if (_instance != null)
                return _instance;

            var instances = AssetDatabase.FindAssets($"t:{nameof(EditorSettings)}", new string[] { "Assets/_LocalWorkspace" });

            if (instances.Length == 0)
            {
                _instance = CreateInstance<EditorSettings>();

                if (!System.IO.Directory.Exists($"{Application.dataPath}/_LocalWorkspace"))
                    AssetDatabase.CreateFolder("Assets", "_LocalWorkspace");

                string name = AssetDatabase.GenerateUniqueAssetPath("Assets/_LocalWorkspace/EditorSettings.asset");
                AssetDatabase.CreateAsset(_instance, name);
                AssetDatabase.SaveAssets();
                return _instance;
            }

            _instance = AssetDatabase.LoadAssetAtPath<EditorSettings>(AssetDatabase.GUIDToAssetPath(instances[0]));
            return _instance;
        }
    }
}
#endif