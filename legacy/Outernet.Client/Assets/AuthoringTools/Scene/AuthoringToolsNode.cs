using System;

using UnityEngine;
using UnityEngine.EventSystems;

namespace Outernet.Client.AuthoringTools
{
    public class AuthoringToolsNode : NodeBase, IPointerClickHandler
    {
        private void Update()
        {
            if (transform.position != props.position.value)
                props.position.ExecuteSet(transform.position);

            if (transform.rotation != props.rotation.value)
                props.rotation.ExecuteSet(transform.rotation);

            var prevMatrix = RuntimeGizmos.matrix;
            RuntimeGizmos.matrix = _currentView.transform.localToWorldMatrix;
            RuntimeGizmos.DrawCube(
                Vector3.zero,
                new Vector3(
                    props.labelDimensions.value.x * 0.5f,
                    props.labelDimensions.value.y * 0.5f,
                    0
                ),
                0.005f / props.labelScale.value,
                Color.yellow.WithAlpha(0.5f)
            );
            RuntimeGizmos.matrix = prevMatrix;
        }

        void IPointerClickHandler.OnPointerClick(PointerEventData eventData)
        {
            AuthoringToolsApp.SetSelectedObjects(props.uuid.value);
        }

        public static AuthoringToolsNode Create(
            int nodeID = default,
            Guid uuid = default,
            string link = default,
            Shared.LinkType linkType = default,
            string label = default,
            Shared.LabelType labelType = default,
            float labelScale = default,
            Vector2 labelDimensions = default,
            Vector3 position = default,
            Quaternion? rotation = default,
            bool visible = default,
            bool exhibitOpen = default,
            Vector3 exhibitPosition = default,
            Quaternion? exhibitRotation = default,
            Vector2 exhibitPanelDimensions = default,
            float exhibitPanelScrollPosition = default,
            Transform parent = default,
            Func<NodeProps, IDisposable> bind = default)
        {
            AuthoringToolsNode instance = Instantiate(AuthoringToolsPrefabs.AuthoringToolsNode, parent);
            instance.InitializeAndBind(new NodeProps(
                nodeID,
                uuid,
                link,
                linkType,
                label,
                labelType,
                labelScale,
                labelDimensions,
                position,
                rotation,
                visible,
                exhibitOpen,
                exhibitPosition,
                exhibitRotation,
                exhibitPanelDimensions,
                exhibitPanelScrollPosition
            ));

            instance.AddBinding(Bindings.OnRelease(() => PrefabSystem.Destroy(instance)));

            if (bind != null)
                instance.AddBinding(bind(instance.props));

            return instance;
        }
    }
}