using UnityEngine;
using UnityEditor;

namespace Plerion.MakeItSing
{
    [CustomPropertyDrawer(typeof(ToggleGroupAttribute))]
    public class ToggleGroupPropertyDrawer : PropertyDrawer
    {
        public override void OnGUI(Rect position, SerializedProperty property, GUIContent label)
        {
            var toggleAttribute = (ToggleGroupAttribute)attribute;
            var toggleProperty = property.serializedObject.FindProperty(toggleAttribute.toggleProperty);
            bool show = toggleProperty.boolValue;

            if (toggleAttribute.invert)
                show = !show;

            if (!show && !toggleAttribute.disable)
                return;

            bool wasEnabled = GUI.enabled;

            if (toggleAttribute.disable)
                GUI.enabled = show && wasEnabled;

            EditorGUI.PropertyField(position, property, label, true);

            GUI.enabled = wasEnabled;
        }

        public override float GetPropertyHeight(SerializedProperty property, GUIContent label)
        {
            var toggleAttribute = (ToggleGroupAttribute)attribute;
            var toggleProperty = property.serializedObject.FindProperty(toggleAttribute.toggleProperty);
            bool show = toggleProperty.boolValue;

            if (toggleAttribute.invert)
                show = !show;

            if (toggleAttribute.disable)
                show = true;

            return show ? EditorGUI.GetPropertyHeight(property, label, true) : 0;
        }
    }
}