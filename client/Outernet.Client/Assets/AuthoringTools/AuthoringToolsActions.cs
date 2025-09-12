using System;
using System.Linq;

using FofX.Stateful;

using Unity.Mathematics;
using UnityEngine;

using SimpleJSON;
using PlerionClient.Model;

namespace Outernet.Client.AuthoringTools
{
    public class SetSelectedObjectIDAction : ObservableNodeAction<ClientState>
    {
        private Guid[] _selectedObjectID;

        public SetSelectedObjectIDAction(params Guid[] selectedObjectID)
        {
            _selectedObjectID = selectedObjectID;
        }

        public override void Execute(ClientState target)
        {
            target.authoringTools.selectedObjects.SetFrom(_selectedObjectID);
        }
    }

    public class DuplicateSceneObjectAction : ObservableNodeAction<ClientState>
    {
        private Guid _toDuplicate;
        private Guid _newSceneObjectID;

        public DuplicateSceneObjectAction(Guid toDuplicate, Guid newSceneObjectID = default)
        {
            _toDuplicate = toDuplicate;
            _newSceneObjectID = newSceneObjectID == default ? Guid.NewGuid() : newSceneObjectID;
        }

        public override void Execute(ClientState target)
        {
            foreach (var componentDict in target.authoringTools.componentDictionaries)
            {
                if (componentDict.TryGetValue(_toDuplicate, out var sourceComponent))
                {
                    var destComponent = componentDict.Add(_newSceneObjectID);
                    sourceComponent.CopyTo(destComponent);

                    if (componentDict == target.transforms)
                    {
                        var group = (TransformState)destComponent;

                        foreach (var childToDuplicate in ((TransformState)sourceComponent).childTransforms.ToArray())
                        {
                            var newChildID = Guid.NewGuid();
                            new DuplicateSceneObjectAction(childToDuplicate, newChildID).Execute(target);
                            new SetParentTransformAction(newChildID, _newSceneObjectID).Execute(target);
                        }
                    }
                }
            }
        }
    }

    public class SetLayersAction : ObservableNodeAction<ClientState>
    {
        private LayerModel[] _layers;

        public SetLayersAction(LayerModel[] layers)
        {
            _layers = layers;
        }

        public override void Execute(ClientState target)
        {
            var newLayersByID = _layers.ToDictionary(x => x.Id);
            var oldLayersByID = target.layers.ToDictionary(x => x.key, x => x.value);

            foreach (var toRemove in oldLayersByID.Where(x => !newLayersByID.ContainsKey(x.Key)))
                new DestroySceneObjectAction(toRemove.Key).Execute(target);

            foreach (var toUpdate in newLayersByID.Select(x => x.Value))
            {
                new AddOrUpdateLayerAction(
                    id: toUpdate.Id,
                    name: toUpdate.Name
                ).Execute(target);
            }
        }
    }

    public class AddOrUpdateLayerAction : ObservableNodeAction<ClientState>
    {
        private Guid _id;
        private string _name;

        public AddOrUpdateLayerAction(
            Guid id,
            string name = default
        )
        {
            _id = id;
            _name = name;
        }

        public override void Execute(ClientState target)
        {
            var layer = target.layers.GetOrAdd(_id);
            layer.layerName.value = _name;
        }
    }

    public class SetParentTransformAction : ObservableNodeAction<ClientState>
    {
        private Guid _id;
        private Guid? _parent;

        public SetParentTransformAction(Guid id, Guid? parent)
        {
            _id = id;
            _parent = parent;
        }

        public override void Execute(ClientState target)
        {
            target.transforms[_id].parentTransform.value = _parent;
        }
    }

    public class SetLocationAction : ObservableNodeAction<ClientState>
    {
        private double2? _location;

        public SetLocationAction(double2? location)
        {
            _location = location;
        }

        public override void Execute(ClientState target)
        {
            target.authoringTools.location.value = _location;
        }
    }

    public class LoadSettingsAction : ObservableNodeAction<ClientState>
    {
        private JSONNode _json;

        public LoadSettingsAction(JSONNode json)
        {
            _json = json;
        }

        public override void Execute(ClientState target)
        {
            target.authoringTools.settings.FromJSON(_json["authoringToolsSettings"]);
            target.settings.visibleLayers.FromJSON(_json["visibleLayers"]);
            target.authoringTools.settings.loaded.value = true;
        }
    }

    public class SetLastLocationAction : ObservableNodeAction<ClientState>
    {
        private double2? _lastLocation;
        public SetLastLocationAction(double2? lastLocation)
        {
            _lastLocation = lastLocation;
        }

        public override void Execute(ClientState target)
        {
            target.authoringTools.settings.lastLocation.value = _lastLocation;
        }
    }

    public class SetupDefaultSettingsAction : ObservableNodeAction<ClientState>
    {
        public override void Execute(ClientState target)
        {
            target.authoringTools.settings.restoreLocationAutomatically.value = true;
            target.authoringTools.settings.loaded.value = true;
            target.authoringTools.settings.nodeFetchRadius.value = 25f;
        }
    }

    public class SetTransformWorldValuesAction : ObservableNodeAction<ClientState>
    {
        private Guid _sceneObjectID;
        private Vector3 _localPosition;
        private Quaternion _localRotation;

        public SetTransformWorldValuesAction(Guid sceneObjectID, Vector3 position, Quaternion rotation)
        {
            _sceneObjectID = sceneObjectID;
            _localPosition = position;
            _localRotation = rotation;
        }

        public override void Execute(ClientState target)
        {
            var transform = target.transforms[_sceneObjectID];
            if (!transform.parentTransform.value.HasValue)
            {
                transform.localPosition.value = _localPosition;
                transform.localRotation.value = _localRotation;
                return;
            }

            var parentTransform = target.transforms[transform.parentTransform.value.Value];
            transform.localPosition.value = Matrix4x4.TRS(parentTransform.position.value, parentTransform.rotation.value, Vector3.one).inverse.MultiplyPoint3x4(_localPosition);
            transform.localRotation.value = Quaternion.Inverse(parentTransform.rotation.value) * _localRotation;
        }
    }

    public class SetLocationContentLoadedAction : ObservableNodeAction<ClientState>
    {
        private bool _locationContentLoaded;

        public SetLocationContentLoadedAction(bool locationContentLoaded)
        {
            _locationContentLoaded = locationContentLoaded;
        }

        public override void Execute(ClientState target)
        {
            target.authoringTools.locationContentLoaded.value = _locationContentLoaded;
        }
    }
}