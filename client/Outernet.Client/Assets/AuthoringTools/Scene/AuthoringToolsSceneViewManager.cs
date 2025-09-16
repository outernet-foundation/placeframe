using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

using FofX.Stateful;

using Outernet.Client.Location;

namespace Outernet.Client.AuthoringTools
{
    public class AuthoringToolsSceneViewManager : MonoBehaviour
    {
        public static Transform sceneRoot => _instance.transform;

        private static AuthoringToolsSceneViewManager _instance;

        private Dictionary<Guid, AuthoringToolsNode> _nodes = new Dictionary<Guid, AuthoringToolsNode>();
        private Dictionary<Guid, SceneMap> _maps = new Dictionary<Guid, SceneMap>();

        private void Awake()
        {
            if (_instance != null)
            {
                Destroy(this);
                throw new Exception($"Only one instance of {nameof(AuthoringToolsSceneViewManager)} allowed in the scene at a time!");
            }

            _instance = this;

            App.state.maps.Each(kvp => SetupMap(kvp.value));
            App.state.exhibits.Each(kvp => SetupExhibit(kvp.value));
        }

        private IDisposable SetupMap(MapState map)
        {
            var node = App.state.nodes[map.id];

            var view = Instantiate(AuthoringToolsPrefabs.SceneMap, sceneRoot);
            view.Setup(sceneObjectID: map.id, mapID: map.id);
            view.AddBinding(
                view.props.localPosition.From(node.localPosition),
                view.props.localRotation.From(node.localRotation),
                view.props.name.From(map.name),
                view.props.bounds.From(node.localBounds),
                view.props.color.From(map.color),
                view.props.localInputImagePositions.Derive(
                    _ => view.props.localInputImagePositions.SetValue(
                        map.localInputImagePositions
                            .Where((x, i) => i % 3 == 0)
                            .Select(x => new Vector3(-(float)x.x, -(float)x.y, -(float)x.z))
                            .ToArray()
                    ),
                    ObservationScope.All,
                    map.localInputImagePositions
                ),
                Bindings.OnRelease(() => _maps.Remove(map.id))
            );

            _maps.Add(map.id, view);
            return view;
        }

        private IDisposable SetupExhibit(ExhibitState exhibit)
        {
            var node = App.state.nodes[exhibit.id];
            var instance = AuthoringToolsNode.Create(
                uuid: node.id,
                parent: sceneRoot,
                bind: props => Bindings.Compose(
                    props.localPosition.BindTo(node.localPosition),
                    props.localRotation.BindTo(node.localRotation),
                    props.bounds.BindTo(node.localBounds),
                    props.visible.From(node.visible),
                    props.link.From(exhibit.link),
                    props.linkType.From(exhibit.linkType),
                    props.label.From(exhibit.label),
                    props.labelType.From(exhibit.labelType),
                    props.labelScale.From(exhibit.labelScale),
                    props.labelDimensions.Derive(
                        _ => props.labelDimensions.value = new Vector2(
                            exhibit.labelWidth.value,
                            exhibit.labelHeight.value
                        ),
                        ObservationScope.Self,
                        exhibit.labelWidth,
                        exhibit.labelHeight
                    ),
                    Bindings.OnRelease(() => _nodes.Remove(node.id))
                )
            );

            _nodes.Add(node.id, instance);
            return instance;
        }
    }
}