using System.Collections.Generic;

using UnityEngine;
using UnityEditor;

using FofX.Stateful;
using System;
using Unity.Mathematics;

namespace Plerion.MakeItSing
{
    [CustomEditor(typeof(App))]
    public class AppInspector : Editor
    {
        private static HashSet<string> _openFoldouts = new HashSet<string>();
        private Dictionary<Type, Func<string, object, object>> _additionalDrawers = new Dictionary<Type, Func<string, object, object>>()
        {
            {
                typeof(SceneObjectId),
                (label, id) =>
                {
                    EditorGUILayout.LabelField(label, ((SceneObjectId)id).ToString());
                    return id;
                }
            },
            {
                typeof(HighFrequencyPrimitiveId),
                (label, id) =>
                {
                    EditorGUILayout.LabelField(label, ((HighFrequencyPrimitiveId)id).ToString());
                    return id;
                }
            },
            {
                typeof(double2),
                (label, value) =>
                {
                    var val = (double2)value;
                    EditorGUILayout.LabelField(label);
                    EditorGUI.indentLevel++;
                    val.x = EditorGUILayout.DoubleField("X", val.x);
                    val.y = EditorGUILayout.DoubleField("Y", val.y);
                    EditorGUI.indentLevel--;
                    return val;
                }
            },
            {
                typeof(double3),
                (label, value) =>
                {
                    var val = (double3)value;
                    EditorGUILayout.LabelField(label);
                    EditorGUI.indentLevel++;
                    val.x = EditorGUILayout.DoubleField("X", val.x);
                    val.y = EditorGUILayout.DoubleField("Y", val.y);
                    val.z = EditorGUILayout.DoubleField("Z", val.z);
                    EditorGUI.indentLevel--;
                    return val;
                }
            },
            {
                typeof(quaternion),
                (label, value) =>
                {
                    var val = ((Quaternion)(quaternion)value).eulerAngles;
                    EditorGUILayout.LabelField(label);
                    EditorGUI.indentLevel++;
                    val.x = EditorGUILayout.FloatField("X", val.x);
                    val.y = EditorGUILayout.FloatField("Y", val.y);
                    val.z = EditorGUILayout.FloatField("Z", val.z);
                    EditorGUI.indentLevel--;
                    return (quaternion)Quaternion.Euler(val);
                }
            }
        };

        private IDisposable _subscription;

        public override void OnInspectorGUI()
        {
            if (!Application.isPlaying)
            {
                DrawDefaultInspector();
                return;
            }

            if (App.state == null)
                return;

            NodeEditors.DrawObservableNodeInspector(App.state, _openFoldouts, _additionalDrawers);
        }

        public void OnEnable()
        {
            if (Application.isPlaying)
            {
                _subscription?.Dispose();
                _subscription = App.state.SubscribeOperationsRecursive(_ => Repaint());
            }
        }

        public void OnDisable()
        {
            if (Application.isPlaying)
            {
                _subscription?.Dispose();
                _subscription = null;
            }
        }
    }
}
