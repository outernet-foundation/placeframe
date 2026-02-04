using System;
using System.Linq;
using FofX.Stateful;

using Unity.Mathematics;

using PlaceframeApiClient.Model;

using Quaternion = UnityEngine.Quaternion;

using SimpleJSON;

namespace Placeframe.MapRegistrationTool
{
    public class SetPrimitiveValueAction<T> : ObservableNodeAction<ObservablePrimitive<T>>
    {
        private T _value;

        public SetPrimitiveValueAction(T value)
        {
            _value = value;
        }

        public override void Execute(ObservablePrimitive<T> target)
        {
            target.value = _value;
        }
    }

    public class AddValueToSetAction<T> : ObservableNodeAction<ObservableSet<T>>
    {
        private T _value;

        public AddValueToSetAction(T value)
        {
            _value = value;
        }

        public override void Execute(ObservableSet<T> target)
        {
            target.Add(_value);
        }
    }

    public class RemoveValueFromSetAction<T> : ObservableNodeAction<ObservableSet<T>>
    {
        private T _value;

        public RemoveValueFromSetAction(T value)
        {
            _value = value;
        }

        public override void Execute(ObservableSet<T> target)
        {
            target.Remove(_value);
        }
    }

    public class SetValuesInSetAction<T> : ObservableNodeAction<ObservableSet<T>>
    {
        private T[] _values;

        public SetValuesInSetAction(T[] values)
        {
            _values = values;
        }

        public override void Execute(ObservableSet<T> target)
        {
            target.SetFrom(_values);
        }
    }

    public class AddKeyToDictionaryAction<TKey, TValue> : ObservableNodeAction<ObservableDictionary<TKey, TValue>>
        where TValue : IObservableNode, new()
    {
        private TKey _key;

        public AddKeyToDictionaryAction(TKey key)
        {
            _key = key;
        }

        public override void Execute(ObservableDictionary<TKey, TValue> target)
        {
            target.Add(_key);
        }
    }

    public class RemoveKeyFromDictionaryAction<TKey, TValue> : ObservableNodeAction<ObservableDictionary<TKey, TValue>>
        where TValue : IObservableNode, new()
    {
        private TKey _key;

        public RemoveKeyFromDictionaryAction(TKey key)
        {
            _key = key;
        }

        public override void Execute(ObservableDictionary<TKey, TValue> target)
        {
            target.Remove(_key);
        }
    }

    public class SetAuthStatusAction : ObservableNodeAction<AppState>
    {
        private AuthStatus _status;
        private string _error;

        public SetAuthStatusAction(AuthStatus status, string error = null)
        {
            _status = status;
            _error = error;
        }

        public override void Execute(AppState target)
        {
            target.authStatus.value = _status;
            target.authError.value = _status == AuthStatus.Error ? _error : null;
        }
    }

    public class SetMapsAction : ObservableNodeAction<AppState>
    {
        private LocalizationMapRead[] _maps;

        public SetMapsAction(LocalizationMapRead[] maps)
        {
            _maps = maps;
        }

        public override void Execute(AppState target)
        {
            var newMapsByID = _maps.ToDictionary(x => x.Id);
            var oldMapsByID = target.maps.ToDictionary(x => x.key, x => x.value);

            foreach (var toRemove in oldMapsByID.Where(x => !newMapsByID.ContainsKey(x.Key)))
                new DestroySceneObjectAction(toRemove.Key).Execute(target);

            foreach (var toUpdate in newMapsByID.Select(x => x.Value))
            {
                new AddOrUpdateMapAction(
                    uuid: toUpdate.Id,
                    name: toUpdate.Name,
                    position: new double3() { x = toUpdate.PositionX, y = toUpdate.PositionY, z = toUpdate.PositionZ },
                    rotation: new Quaternion((float)toUpdate.RotationX, (float)toUpdate.RotationY, (float)toUpdate.RotationZ, (float)toUpdate.RotationW),
                    lighting: (Lighting)(toUpdate.Lighting ?? 0),
                    reconstructionID: toUpdate.ReconstructionId
                ).Execute(target);
            }
        }
    }

    public class AddOrUpdateMapAction : ObservableNodeAction<AppState>
    {
        private Guid _uuid;
        private string _name;
        private double3 _position;
        private Quaternion _rotation;
        private Lighting _lighting;
        private Guid _reconstructionID;

        public AddOrUpdateMapAction(
            Guid uuid,
            string name = default,
            double3 position = default,
            Quaternion rotation = default,
            Lighting lighting = default,
            Guid reconstructionID = default)
        {
            _uuid = uuid;
            _name = name;
            _position = position;
            _rotation = rotation;
            _lighting = lighting;
            _reconstructionID = reconstructionID;
        }

        public override void Execute(AppState target)
        {
            var transform = target.transforms.GetOrAdd(_uuid);
            transform.position.value = _position;
            transform.rotation.value = _rotation;

            var map = target.maps.GetOrAdd(_uuid);
            map.name.value = _name;
            map.lighting.value = _lighting;
            map.reconstructionID.value = _reconstructionID;
        }
    }

    public class ClearSceneObjectsAction : ObservableNodeAction<AppState>
    {
        public override void Execute(AppState target)
        {
            foreach (var componentDict in target.componentDictionaries)
                componentDict.Clear();

            target.selectedObjects.Clear();
        }
    }

    public class DestroySceneObjectAction : ObservableNodeAction<AppState>
    {
        private Guid _sceneObjectID;

        public DestroySceneObjectAction(Guid sceneObjectID)
        {
            _sceneObjectID = sceneObjectID;
        }

        public override void Execute(AppState target)
        {
            target.selectedObjects.Remove(_sceneObjectID);

            foreach (var componentDict in target.componentDictionaries)
                componentDict.Remove(_sceneObjectID);
        }
    }

    public class SetSelectedObjectIDAction : ObservableNodeAction<AppState>
    {
        private Guid[] _selectedObjectID;

        public SetSelectedObjectIDAction(params Guid[] selectedObjectID)
        {
            _selectedObjectID = selectedObjectID;
        }

        public override void Execute(AppState target)
        {
            target.selectedObjects.SetFrom(_selectedObjectID);
        }
    }

    public class DuplicateSceneObjectAction : ObservableNodeAction<AppState>
    {
        private Guid _toDuplicate;
        private Guid _newSceneObjectID;

        public DuplicateSceneObjectAction(Guid toDuplicate, Guid newSceneObjectID = default)
        {
            _toDuplicate = toDuplicate;
            _newSceneObjectID = newSceneObjectID == default ? Guid.NewGuid() : newSceneObjectID;
        }

        public override void Execute(AppState target)
        {
            foreach (var componentDict in target.componentDictionaries)
            {
                if (componentDict.TryGetValue(_toDuplicate, out var sourceComponent))
                {
                    var destComponent = componentDict.Add(_newSceneObjectID);
                    sourceComponent.CopyTo(destComponent);
                }
            }
        }
    }

    public class SetLocationAction : ObservableNodeAction<AppState>
    {
        private double2? _location;

        public SetLocationAction(double2? location)
        {
            _location = location;
        }

        public override void Execute(AppState target)
        {
            target.location.value = _location;
        }
    }

    public class LoadSettingsAction : ObservableNodeAction<AppState>
    {
        private JSONNode _json;

        public LoadSettingsAction(JSONNode json)
        {
            _json = json;
        }

        public override void Execute(AppState target)
        {
            target.settings.FromJSON(_json);
            target.settings.loaded.value = true;
        }
    }

    public class SetLastLocationAction : ObservableNodeAction<AppState>
    {
        private double2? _lastLocation;
        public SetLastLocationAction(double2? lastLocation)
        {
            _lastLocation = lastLocation;
        }

        public override void Execute(AppState target)
        {
            target.settings.lastLocation.value = _lastLocation;
        }
    }

    public class SetupDefaultSettingsAction : ObservableNodeAction<AppState>
    {
        public override void Execute(AppState target)
        {
            target.settings.username.value = "user";
            target.settings.password.value = "password";
            target.settings.restoreLocationAutomatically.value = true;
            target.settings.nodeFetchRadius.value = 25f;
            target.settings.loaded.value = true;
        }
    }

    public class SetSceneObjectTransformAction : ObservableNodeAction<AppState>
    {
        private Guid _sceneObjectID;
        private double3 _position;
        private quaternion _rotation;

        public SetSceneObjectTransformAction(Guid sceneObjectID, double3 position, quaternion rotation)
        {
            _sceneObjectID = sceneObjectID;
            _position = position;
            _rotation = rotation;
        }

        public override void Execute(AppState target)
        {
            if (!target.transforms.TryGetValue(_sceneObjectID, out var transform))
                return;

            transform.position.value = _position;
            transform.rotation.value = _rotation;
        }
    }

    public class SetLocationContentLoadedAction : ObservableNodeAction<AppState>
    {
        private bool _locationContentLoaded;

        public SetLocationContentLoadedAction(bool locationContentLoaded)
        {
            _locationContentLoaded = locationContentLoaded;
        }

        public override void Execute(AppState target)
        {
            target.locationContentLoaded.value = _locationContentLoaded;
        }
    }

    public class UpdateMapLocationsAction : ObservableNodeAction<AppState>
    {
        private SceneMap.Props[] _toUpdate;

        public UpdateMapLocationsAction(SceneMap.Props[] toUpdate)
        {
            _toUpdate = toUpdate;
        }

        public override void Execute(AppState target)
        {
            foreach (var map in _toUpdate)
            {
                var transform = target.transforms[map.sceneObjectID.value];
                var localNodeTransform = MapRegistrationTool.Utility.EcefToLocal(
                    target.ecefToUnityWorldMatrix.value,
                    transform.position.value,
                    transform.rotation.value
                );

                map.position.value = localNodeTransform.position;
                map.rotation.value = localNodeTransform.rotation;
            }
        }
    }
}
