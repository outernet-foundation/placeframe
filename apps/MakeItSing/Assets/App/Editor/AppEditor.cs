using System.Collections.Generic;

using UnityEngine;
using UnityEditor;

using FofX.Stateful;
using System;

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
