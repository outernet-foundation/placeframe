using System.Collections.Generic;
using FofX.Stateful;
using UnityEditor;
using UnityEngine;

namespace Placeframe.Client
{
    [CustomEditor(typeof(App))]
    public class AppInspector : Editor
    {
        private static HashSet<string> _showStatuses = new HashSet<string>();

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
                App.DeregisterObserver(HandleAppStoreChanged);
                App.RegisterObserver(HandleAppStoreChanged, App.state);
            }
        }

        public void OnDisable()
        {
            if (Application.isPlaying)
                App.DeregisterObserver(HandleAppStoreChanged);
        }

        private void HandleAppStoreChanged(NodeChangeEventArgs args)
        {
            Repaint();
        }
    }
}
