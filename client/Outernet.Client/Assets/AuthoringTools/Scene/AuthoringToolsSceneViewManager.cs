using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

using FofX.Stateful;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;

namespace Outernet.Client.AuthoringTools
{
    public class AuthoringToolsSceneViewManager : MonoBehaviour
    {
        public static Transform sceneRoot => _instance.transform;
        private static AuthoringToolsSceneViewManager _instance;
        private static Dictionary<Guid, TaskCompletionSource<GameObject>> _completionSources = new Dictionary<Guid, TaskCompletionSource<GameObject>>();

        private void Awake()
        {
            if (_instance != null)
            {
                Destroy(this);
                throw new Exception($"Only one instance of {nameof(AuthoringToolsSceneViewManager)} allowed in the scene at a time!");
            }

            _instance = this;

            App.state.exhibits.Each(kvp => SetupExhibit(kvp.value));
            App.state.authoringTools.maps.Each(kvp => SetupMap(kvp.value));
        }

        private IDisposable SetupMap(MapState map)
        {
            var node = App.state.nodes[map.id];
            var instance = Instantiate(AuthoringToolsPrefabs.SceneMap, sceneRoot);
            instance.Setup(sceneObjectID: map.id, mapID: map.id);
            instance.AddBinding(
                instance.props.name.From(node.name),
                instance.props.localPosition.BindTo(node.localPosition),
                instance.props.localRotation.BindTo(node.localRotation),
                instance.props.localBounds.From(node.localBounds),
                instance.props.color.From(map.color),
                instance.props.localInputImagePositions.Derive(
                    _ => instance.props.localInputImagePositions.SetValue(
                        map.localInputImagePositions
                            .Where((x, i) => i % 3 == 0)
                            .Select(x => new Vector3(-(float)x.x, -(float)x.y, -(float)x.z))
                            .ToArray()
                    ),
                    ObservationScope.All,
                    map.localInputImagePositions
                )
            );

            CompleteGetViewTask(map.id, instance.gameObject);

            return instance;
        }

        private IDisposable SetupExhibit(ExhibitState exhibit)
        {
            var node = App.state.nodes[exhibit.id];
            var instance = AuthoringToolsNode.Create(
                uuid: node.id,
                parentID: node.parentID.value,
                localPosition: node.localPosition.value,
                localRotation: node.localRotation.value,
                bind: props => Bindings.Compose(
                    props.parentID.BindTo(node.parentID),
                    props.localPosition.BindTo(node.localPosition),
                    props.localRotation.BindTo(node.localRotation),
                    props.localBounds.BindTo(node.localBounds),
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
                    Bindings.OnRelease(() => _completionSources.Remove(exhibit.id))
                )
            );

            CompleteGetViewTask(node.id, instance.gameObject);

            return instance;
        }

        private void CompleteGetViewTask(Guid id, GameObject view)
        {
            if (!_completionSources.TryGetValue(id, out var completionSource))
            {
                completionSource = new TaskCompletionSource<GameObject>();
                _completionSources.Add(id, completionSource);
            }

            completionSource.SetResult(view);
        }

        public static UniTask<GameObject> GetView(Guid id)
        {
            if (!_completionSources.TryGetValue(id, out var completionSource))
            {
                completionSource = new TaskCompletionSource<GameObject>();
                _completionSources.Add(id, completionSource);
            }

            return completionSource.Task.AsUniTask();
        }
    }
}