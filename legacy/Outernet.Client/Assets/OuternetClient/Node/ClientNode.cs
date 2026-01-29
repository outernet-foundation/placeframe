using System;
using Placeframe.Core;
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.Interactables;

namespace Outernet.Client
{
    public class ClientNode : NodeBase
    {
        private const float exhibitSpawnDistanceFromCamera = 1.5f;
        private const float exhibitOffsetDown = 0.5f;
        private const float exhibitSpawnTilt = 20f;

        public XRBaseInteractable interactable;

        protected override void Bind()
        {
            base.Bind();

            AddBinding(
                interactable.firstHoverEntered.OnRaised(_ => props.hoveredLocally.ExecuteSetOrDelay(true)),
                interactable.lastHoverExited.OnRaised(_ => props.hoveredLocally.ExecuteSetOrDelay(false)),
                interactable.selectExited.OnRaised(_ =>
                {
                    var cameraToPOI = (transform.position - Camera.main.transform.position).normalized;
                    var position =
                        Camera.main.transform.position
                        + (cameraToPOI * exhibitSpawnDistanceFromCamera)
                        + (Vector3.down * exhibitOffsetDown);
                    var rotation = Quaternion.LookRotation(cameraToPOI) * Quaternion.Euler(exhibitSpawnTilt, 0, 0);
                    props.ExecuteAction(
                        (position, rotation),
                        (data, props) =>
                        {
                            props.exhibitPosition.value = data.position;
                            props.exhibitRotation.value = data.rotation;
                            props.exhibitPanelDimensions.value = new Vector2(1, 0.7f);
                            props.exhibitPanelScrollPosition.value = 1f;
                            props.exhibitOpen.value = true;
                        }
                    );
                }),
                props.hovered.OnChange(hovered =>
                {
                    if (_currentView.TryGetComponent(out Sample_TMP3D_Animation animator))
                        animator.animate = hovered;
                })
            // App.state.settings.showNodeIndicators.DynamicBind(show => show ? SetupIndicator() : null)
            );
        }

        // private IDisposable SetupIndicator()
        // {
        //     return ClientIndicator.Create(
        //         color: Color.green,
        //         inViewPosition: GetIndicatorTargetPosition(),
        //         inViewRotation: props.rotation * Quaternion.Euler(90f, 0f, 180f),
        //         inViewScale: 1f,
        //         bind: indicatorProps => Bindings.Compose(
        //             indicatorProps.animate.From(App.state.settings.animateNodeIndicators),
        //             indicatorProps.inViewRotation.From(props.rotation, x => x * Quaternion.Euler(90f, 0f, 180f)),
        //             indicatorProps.inViewPosition.From(
        //                 _ => GetIndicatorTargetPosition(),
        //                 ObservationScope.Self,
        //                 props.position,
        //                 props.rotation,
        //                 props.bounds
        //             )
        //         )
        //     );
        // }

        // private Vector3 GetIndicatorTargetPosition()
        // {
        //     var matrix = Matrix4x4.TRS(props.position.value, props.rotation.value, Vector3.one);
        //     return matrix.MultiplyPoint3x4(new Vector3(0, props.bounds.value.center.y + (props.bounds.value.size.y * 0.5f), 0));
        // }

        public static ClientNode Create(
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
            Bounds bounds = default,
            bool visible = default,
            bool exhibitOpen = default,
            Vector3 exhibitPosition = default,
            Quaternion? exhibitRotation = default,
            Vector2 exhibitPanelDimensions = default,
            float exhibitPanelScrollPosition = default,
            Transform parent = default,
            Func<NodeProps, IDisposable> bind = default
        )
        {
            ClientNode instance = PrefabSystem.Create(PrefabSystem.clientNode, parent);
            instance.InitializeAndBind(
                new NodeProps(
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
                )
            );

            instance.AddBinding(Bindings.OnRelease(() => PrefabSystem.Destroy(instance)));

            if (bind != null)
                instance.AddBinding(bind(instance.props));

            return instance;
        }
    }
}
