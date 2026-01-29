using System.Collections.Generic;

using UnityEngine;
using UnityEditor;

using FofX.Stateful;

namespace Outernet.Client
{
    [CustomEditor(typeof(Control), true)]
    public class ControlBaseInspector : Editor
    {
        private HashSet<string> _showStatuses = new HashSet<string>();
        private Control targetControl => (Control)target;

        public override void OnInspectorGUI()
        {
            DrawDefaultInspector();

            if (!Application.isPlaying || targetControl.propsAsNode == null)
                return;

            NodeEditors.DrawObservableNodeInspector(targetControl.propsAsNode, _showStatuses);
        }

        public void OnEnable()
        {
            if (Application.isPlaying && targetControl.propsAsNode != null)
            {
                targetControl.propsAsNode.context.DeregisterObserver(HandleAppStoreChanged);
                targetControl.propsAsNode.context.RegisterObserver(HandleAppStoreChanged, targetControl.propsAsNode);
            }
        }

        public void OnDisable()
        {
            if (Application.isPlaying && targetControl.propsAsNode != null)
                targetControl.propsAsNode.context.DeregisterObserver(HandleAppStoreChanged);
        }

        private void HandleAppStoreChanged(NodeChangeEventArgs args)
        {
            Repaint();
        }
    }
}
