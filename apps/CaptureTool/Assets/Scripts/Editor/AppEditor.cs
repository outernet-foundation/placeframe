using System.Collections.Generic;

using UnityEngine;
using UnityEditor;

using FofX.Stateful;
using System;

namespace Placeframe.Client
{
    [CustomEditor(typeof(App))]
    public class AppInspector : Editor
    {
        private static HashSet<string> _showStatuses = new HashSet<string>();
        private static IDisposable _subscription;

        public override void OnInspectorGUI()
        {
            if (!Application.isPlaying)
            {
                DrawDefaultInspector();
                return;
            }

            if (App.state == null)
                return;

            NodeEditors.DrawObservableNodeInspector(App.state, _showStatuses);
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
                _subscription?.Dispose();
        }
    }
}
