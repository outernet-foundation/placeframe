using TMPro;
using UnityEditor;
using UnityEngine;

namespace Outernet.Client
{
	[CustomEditor(typeof(ExtrudedTextMeshPro))]
	public class ExtrudedTextEditor : Editor
	{
		ExtrudedTextMeshPro m_handler;

		private void OnEnable()
		{
			m_handler = (ExtrudedTextMeshPro)target;
		}

		public override void OnInspectorGUI()
		{
			EditorGUILayout.PropertyField(serializedObject.FindProperty("defaultDepth"));
			serializedObject.ApplyModifiedProperties();

			var textMeshPro = m_handler.GetComponent<TextMeshPro>();
			var fontAsset = textMeshPro.font;
			EditorGUI.BeginDisabledGroup(fontAsset.material.shader.name.Contains(ExtrudedTextData.SHADER_NAME_SPACE));
			if (GUILayout.Button(new GUIContent("Create 3D Font Asset Variant")))
			{
				Undo.RecordObject(textMeshPro, "Converted Font Asset to 3D");
				var newFont = ExtrudedTextData.ConvertFontAssetTo3D(fontAsset);
				textMeshPro.font = newFont;
			}
			EditorGUI.EndDisabledGroup();
		}
	}
}
