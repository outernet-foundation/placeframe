using UnityEngine;
using UnityEditor;

namespace Placeframe.Client
{
    [CustomEditor(typeof(AppSetup))]
    public class AppSetupEditor : Editor
    {
        private static bool foldoutOpen = true;
        public override void OnInspectorGUI()
        {
            DrawDefaultInspector();

            foldoutOpen = EditorGUILayout.Foldout(foldoutOpen, "Environment", true);

            if (foldoutOpen)
            {
                EditorGUI.indentLevel++;
                var editorSettings = UnityEnv.GetOrCreateInstance();
                bool wasEnabled = GUI.enabled;
                GUI.enabled = false;
                EditorGUILayout.ObjectField("Instance", editorSettings, typeof(EditorSettings), allowSceneObjects: false);
                GUI.enabled = wasEnabled;
                CreateEditor(editorSettings).DrawDefaultInspector();
                EditorGUI.indentLevel--;
            }
        }
    }
}