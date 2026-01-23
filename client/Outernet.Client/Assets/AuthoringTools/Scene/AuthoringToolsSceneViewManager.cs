using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

using FofX.Stateful;

using Outernet.Client.Location;
using Plerion.Core;
using UnityEngine.UIElements;

namespace Outernet.Client.AuthoringTools
{
    public class AuthoringToolsSceneViewManager : MonoBehaviour
    {
        public static Transform sceneRoot => _instance.transform;

        private static AuthoringToolsSceneViewManager _instance;

        private Dictionary<Guid, AuthoringToolsNode> _nodes = new Dictionary<Guid, AuthoringToolsNode>();
        private Dictionary<Guid, AuthoringToolsMap> _maps = new Dictionary<Guid, AuthoringToolsMap>();

        private void Awake()
        {
            VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated += () => App.ExecuteActionOrDelay(
                new UpdateNodeLocationsAction(VisualPositioningSystem.EcefToUnityWorldTransform, _nodes.Values.Select(x => x.props).ToArray()),
                new UpdateMapLocationsAction(VisualPositioningSystem.EcefToUnityWorldTransform, _maps.Values.Select(x => x.props).ToArray())
            );

            if (_instance != null)
            {
                Destroy(this);
                throw new Exception($"Only one instance of {nameof(AuthoringToolsSceneViewManager)} allowed in the scene at a time!");
            }

            _instance = this;

            App.state.authoringTools.maps.Each(kvp => SetupMap(kvp.value));
            App.state.nodes.Each(kvp => SetupNode(kvp.value));
        }

        private IDisposable SetupMap(MapState map)
        {
            var transform = App.state.transforms[map.uuid];
            var instance = AuthoringToolsMap.Create(
                sceneObjectID: map.uuid,
                bind: props => Bindings.Compose(
                    Bindings.BindECEFTransform(transform.position, transform.rotation, props.position, props.rotation),
                    props.name.From(map.name),
                    props.reconstructionID.From(map.reconstructionID),
                    Bindings.OnRelease(() => _maps.Remove(map.uuid))
                )
            );

            _maps.Add(map.uuid, instance);
            return instance;
        }

        private IDisposable SetupNode(NodeState node)
        {
            var transform = App.state.transforms[node.id];
            var instance = AuthoringToolsNode.Create(
                uuid: node.id,
                parent: sceneRoot,
                bind: props => Bindings.Compose(
                    Bindings.BindECEFTransform(transform.position, transform.rotation, props.position, props.rotation),
                    props.visible.From(node.visible),
                    props.link.From(node.link),
                    props.linkType.From(node.linkType),
                    props.label.From(node.label),
                    props.labelType.From(node.labelType),
                    props.labelScale.From(node.labelScale),
                    props.labelDimensions.Derive(
                        _ => props.labelDimensions.value = new Vector2(
                            node.labelWidth.value,
                            node.labelHeight.value
                        ),
                        ObservationScope.Self,
                        node.labelWidth,
                        node.labelHeight
                    ),
                    Bindings.OnRelease(() => _nodes.Remove(node.id))
                )
            );

            _nodes.Add(node.id, instance);
            return instance;
        }
    }
}