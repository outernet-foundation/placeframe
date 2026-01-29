using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;

namespace Outernet.Client
{
    [CustomEditor(typeof(AppSetup))]
    public class AppSetupInspector : Editor
    {
        private static bool foldoutOpen = true;

        public override void OnInspectorGUI()
        {
            DrawDefaultInspector();

            foldoutOpen = EditorGUILayout.Foldout(foldoutOpen, "Env", true);

            if (foldoutOpen)
            {
                EditorGUI.indentLevel++;
                var editorSettings = UnityEnv.GetOrCreateInstance();
                bool wasEnabled = GUI.enabled;
                GUI.enabled = false;
                EditorGUILayout.ObjectField("Instance", editorSettings, typeof(UnityEnv), allowSceneObjects: false);
                GUI.enabled = wasEnabled;
                CreateEditor(editorSettings).DrawDefaultInspector();
                EditorGUI.indentLevel--;
            }
        }
    }
}