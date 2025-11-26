using UnityEngine;

using UnityEditor;

[CustomPropertyDrawer(typeof(ConditionalPropertyAttribute))]
public class ConditionalPropertyDrawer : PropertyDrawer
{
    public override void OnGUI(Rect position, SerializedProperty property, GUIContent label)
    {
        if (ShouldDraw(property, (ConditionalPropertyAttribute)attribute))
            EditorGUI.PropertyField(position, property, label);
    }

    public override float GetPropertyHeight(SerializedProperty property, GUIContent label)
    {
        return ShouldDraw(property, (ConditionalPropertyAttribute)attribute) ? EditorGUI.GetPropertyHeight(property, label) : 0;
    }

    private bool ShouldDraw(SerializedProperty property, ConditionalPropertyAttribute attribute)
    {
        var obj = property.serializedObject;
        var targetProp = obj.FindProperty(attribute.propertyName);

        if (targetProp.propertyType == SerializedPropertyType.Enum)
            return Equals(attribute.value, System.Enum.ToObject(attribute.value.GetType(), targetProp.enumValueFlag));

        return Equals(attribute.value, targetProp.boxedValue);
    }
}
