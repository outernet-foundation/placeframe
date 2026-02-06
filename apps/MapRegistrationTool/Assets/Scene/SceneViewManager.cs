using System;
using System.Collections.Generic;
using System.Linq;
using Placeframe.Core;
using UnityEngine;

namespace Placeframe.MapRegistrationTool
{
    public class SceneViewManager : MonoBehaviour
    {
        public static Transform sceneRoot => _instance.transform;
        private static SceneViewManager _instance;

        private Dictionary<Guid, SceneMap> _maps = new Dictionary<Guid, SceneMap>();

        private void Awake()
        {
            if (_instance != null)
            {
                Destroy(this);
                throw new Exception($"Only one instance of {nameof(SceneViewManager)} allowed in the scene at a time!");
            }

            _instance = this;

            VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated += HandleEcefToUnityWorldChanged;
            App.state.maps.Each(kvp => SetupMap(kvp.value));
        }

        private void HandleEcefToUnityWorldChanged()
        {
            App.ExecuteActionOrDelay(
                // Use one action to update all loaded maps when our reference frame changes.
                // This is more efficient and removes the need for a duplicate ecefToUnityWorldTransform
                // value in App.state.
                new UpdateMapLocationsAction(
                    VisualPositioningSystem.EcefToUnityWorldTransform,
                    _maps.Values.Select(x => x.props).ToArray()
                )
            );
        }

        private IDisposable SetupMap(MapState map)
        {
            var transform = App.state.transforms[map.uuid];
            var instance = SceneMap.Create(
                sceneObjectID: map.uuid,
                mapId: map.uuid,
                bind: props =>
                    Bindings.Compose(
                        Bindings.BindECEFTransform(
                            transform.position,
                            transform.rotation,
                            props.position,
                            props.rotation
                        ),
                        props.name.From(map.name),
                        Bindings.OnRelease(() => _maps.Remove(map.uuid))
                    )
            );

            _maps.Add(map.uuid, instance);
            return instance;
        }
    }
}
