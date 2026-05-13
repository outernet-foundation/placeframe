using UnityEditor;
using UnityEngine;

namespace Placeframe.Core
{
    [CustomEditor(typeof(GeoPose))]
    public class GeoPoseInspector : Editor
    {
        public override void OnInspectorGUI()
        {
            var target = (GeoPose)this.target;

            EditorGUILayout.LabelField("ECEF");
            EditorGUI.indentLevel++;
            EditorGUILayout.SelectableLabel(
                $"({target.ecefPosition.x}, {target.ecefPosition.y}, {target.ecefPosition.z})"
            );
            EditorGUI.indentLevel--;
        }
    }
}
