using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;

using UnityEngine;
using UnityEditor;

using Unity.Mathematics;

namespace FofX.Stateful
{
    public static class NodeEditors
    {
        public static void DrawObservableNodeInspector(IObservableNode node, HashSet<string> showStatuses)
        {
            bool guiWasEnabled = GUI.enabled;
            GUI.enabled = !node.isDerived;

            if (node is IObservablePrimitiveArray array)
            {
                bool show = showStatuses.Contains(node.nodePath);
                bool newShow = EditorGUILayout.Foldout(show, node.nodeName, true);

                if (show != newShow)
                {
                    if (newShow)
                    {
                        showStatuses.Add(node.nodePath);
                    }
                    else
                    {
                        showStatuses.Remove(node.nodePath);
                    }

                    show = newShow;
                }

                if (show)
                {
                    EditorGUI.indentLevel++;
                    foreach (object value in array)
                        EditorGUILayout.LabelField(value.ToString());
                    EditorGUI.indentLevel--;
                }
            }
            else if (node is IObservablePrimitive primitive)
            {
                try
                {
                    object prevValue = primitive.GetValue();
                    object newValue = DrawPrimitiveField(node.nodeName, prevValue, primitive.primitiveType);
                    if (!object.Equals(prevValue, newValue))
                        primitive.context.ExecuteAction(primitive, new SetPrimitiveFromEditorAction(newValue));
                }
                catch
                {
                    Color currentColor = GUI.contentColor;
                    GUI.contentColor = Color.yellow;
                    EditorGUILayout.LabelField(node.nodeName, $"No drawer for type {primitive.primitiveType}");
                    GUI.contentColor = currentColor;
                }
            }
            else if (node is IObservableSet set)
            {
                if (HandleFoldout(node, showStatuses))
                {
                    EditorGUI.indentLevel++;
                    foreach (object value in set)
                        EditorGUILayout.LabelField(value.ToString());
                    EditorGUI.indentLevel--;
                }
            }
            else if (node is IObservableList list)
            {
                if (HandleFoldout(node, showStatuses))
                {
                    EditorGUI.indentLevel++;
                    for (int i = 0; i < list.count; i++)
                        DrawObservableNodeInspector(list[i], showStatuses);
                    EditorGUI.indentLevel--;
                }
            }
            else if (node is IObservableDictionary)
            {
                if (HandleFoldout(node, showStatuses))
                {
                    EditorGUI.indentLevel++;
                    foreach (IObservableNode child in node.children.OrderBy(x => x.nodeName))
                        DrawObservableNodeInspector(child, showStatuses);
                    EditorGUI.indentLevel--;
                }
            }
            else if (node is IObservablePrimitiveMap map)
            {
                if (HandleFoldout(node, showStatuses))
                {
                    EditorGUI.indentLevel++;
                    foreach (var pair in map.Cast<IPrimitiveMapPair>())
                        EditorGUILayout.LabelField(pair.ToString());
                    EditorGUI.indentLevel--;
                }
            }
            else if (node is ObservableObject)
            {
                if (HandleFoldout(node, showStatuses))
                {
                    EditorGUI.indentLevel++;
                    foreach (IObservableNode child in node.children)
                        DrawObservableNodeInspector(child, showStatuses);
                    EditorGUI.indentLevel--;
                }
            }
            else
            {
                Color currentColor = GUI.contentColor;
                GUI.contentColor = Color.yellow;
                EditorGUILayout.LabelField(node.nodeName, $"No drawer for type {node.GetType()}");
                GUI.contentColor = currentColor;
            }

            GUI.enabled = guiWasEnabled;
        }

        private static bool HandleFoldout(IObservableNode node, HashSet<string> showStatuses)
        {
            bool show = showStatuses.Contains(node.nodePath);
            bool newShow = EditorGUILayout.Foldout(show, node.nodeName, true);

            if (show != newShow)
            {
                if (newShow)
                {
                    showStatuses.Add(node.nodePath);
                }
                else
                {
                    showStatuses.Remove(node.nodePath);
                }
            }

            return newShow;
        }

        public static object DrawPrimitiveField(string label, object value, Type type)
        {
            if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(Nullable<>))
            {
                if (value == null)
                {
                    EditorGUILayout.LabelField(label, "NULL");
                    return null;
                }

                type = type.GetGenericArguments()[0];
            }

            if (type.IsArray)
            {
                EditorGUILayout.LabelField(label);
                if (value == null)
                    return null;

                EditorGUI.indentLevel++;
                foreach (var element in ((IEnumerable)value).Cast<object>())
                    EditorGUILayout.LabelField(element.ToString());
                EditorGUI.indentLevel--;
                return value;
            }
            else if (type == typeof(string))
            {
                return EditorGUILayout.DelayedTextField(label, (string)value);
            }
            else if (type == typeof(Guid))
            {
                return new Guid(EditorGUILayout.DelayedTextField(label, ((Guid)value).ToString()));
            }
            else if (type == typeof(DateTime))
            {
                EditorGUILayout.LabelField(label, ((DateTime)value).ToUniversalTime().ToString());
                return value;
            }
            else if (type == typeof(int))
            {
                return EditorGUILayout.DelayedIntField(label, (int)value);
            }
            else if (type == typeof(long))
            {
                return EditorGUILayout.LongField(label, (long)value);
            }
            else if (type == typeof(float))
            {
                return EditorGUILayout.DelayedFloatField(label, (float)value);
            }
            else if (type == typeof(byte))
            {
                EditorGUILayout.LabelField(label, ((byte)value).ToString());
                return value;
            }
            else if (type == typeof(bool))
            {
                return EditorGUILayout.Toggle(label, (bool)value);
            }
            else if (type == typeof(Vector2))
            {
                return EditorGUILayout.Vector2Field(label, (Vector2)value);
            }
            else if (type == typeof(Vector3))
            {
                return EditorGUILayout.Vector3Field(label, (Vector3)value);
            }
            else if (type == typeof(Vector4))
            {
                return EditorGUILayout.Vector4Field(label, (Vector4)value);
            }
            else if (type == typeof(Quaternion))
            {
                var quat = (Quaternion)value;
                var euler = quat.eulerAngles;
                var newEuler = EditorGUILayout.Vector3Field(label, euler);
                return newEuler == euler ? quat : Quaternion.Euler(newEuler);
            }
            else if (type == typeof(Vector2Int))
            {
                return EditorGUILayout.Vector2IntField(label, (Vector2Int)value);
            }
            else if (type == typeof(Vector3Int))
            {
                return EditorGUILayout.Vector3IntField(label, (Vector3Int)value);
            }
            else if (type == typeof(Color))
            {
                return EditorGUILayout.ColorField(label, (Color)value);
            }
            else if (type.IsEnum)
            {
                return EditorGUILayout.EnumPopup(label, (Enum)value);
            }
            else if (type == typeof(Uri))
            {
                return new Uri(EditorGUILayout.DelayedTextField(label, ((Uri)value).ToString()));
            }
            else if (type == typeof(double))
            {
                return EditorGUILayout.DoubleField(label, (double)value);
            }
            else if (type == typeof(double2))
            {
                var d2 = (double2)value;
                EditorGUILayout.LabelField(label);
                EditorGUI.indentLevel++;
                d2.x = EditorGUILayout.DoubleField("X", d2.x);
                d2.y = EditorGUILayout.DoubleField("Y", d2.y);
                EditorGUI.indentLevel--;

                return d2;
            }
            else if (type == typeof(double3))
            {
                var d3 = (double3)value;
                EditorGUILayout.LabelField(label);
                EditorGUI.indentLevel++;
                d3.x = EditorGUILayout.DoubleField("X", d3.x);
                d3.y = EditorGUILayout.DoubleField("Y", d3.y);
                d3.z = EditorGUILayout.DoubleField("Z", d3.z);
                EditorGUI.indentLevel--;

                return d3;
            }
            else if (type == typeof(Bounds))
            {
                return EditorGUILayout.BoundsField(label, (Bounds)value);
            }
            else if (type == typeof(object))
            {
                EditorGUILayout.LabelField(label, $"[Object: {value}]");
                return value;
            }
            else
            {
                throw new Exception($"Unhandled primitive type {type}");
            }
        }

        private class SetPrimitiveFromEditorAction : ObservableNodeAction<IObservablePrimitive>
        {
            private object _value;

            public SetPrimitiveFromEditorAction(object value)
            {
                _value = value;
            }

            public override void Execute(IObservablePrimitive target)
            {
                target.SetValue(_value);
            }
        }
    }
}