using UnityEditor;
using UnityEngine;

namespace Plerion.Core
{
    [CustomEditor(typeof(Anchor))]
    public class AnchorInspector : Editor
    {
        public override void OnInspectorGUI()
        {
            var target = (Anchor)this.target;

            EditorGUILayout.LabelField("ECEF");
            EditorGUI.indentLevel++;
            EditorGUILayout.SelectableLabel(
                $"({target.ecefPosition.x}, {target.ecefPosition.y}, {target.ecefPosition.z})"
            );
            EditorGUI.indentLevel--;
        }
    }
}
