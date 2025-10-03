using UnityEngine;
using UnityEditor;

namespace Plerion
{
    [CustomEditor(typeof(Anchor))]
    public class AnchorInspector : Editor
    {
        public override void OnInspectorGUI()
        {
            var target = (Anchor)this.target;

            EditorGUILayout.LabelField("ECEF");
            EditorGUI.indentLevel++;
            EditorGUILayout.SelectableLabel($"({target.ecefPosition.x}, {target.ecefPosition.y}, {target.ecefPosition.z})");
            EditorGUI.indentLevel--;
        }
    }
}