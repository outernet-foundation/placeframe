using System;
using System.Linq;

using FofX.Stateful;
using Placeframe.Core;
using PlaceframeApiClient.Model;
using SimpleJSON;
using Unity.Mathematics;

using SimpleJSON;
using PlaceframeApiClient.Model;

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

                    if (componentDict == target.authoringTools.nodeGroups)
                    {
                        var group = (NodeGroupState)destComponent;

                        foreach (var childToDuplicate in ((NodeGroupState)sourceComponent).childObjects.ToArray())
                        {
                            var newChildID = Guid.NewGuid();
                            new DuplicateSceneObjectAction(childToDuplicate, newChildID).Execute(target);
                            new SetParentGroupAction(newChildID, _newSceneObjectID).Execute(target);
                        }
                    }
                }
            }
        }
    }

    public class SetNodeGroupsAction : ObservableNodeAction<ClientState>
    {
        private GroupRead[] _groups;

        public SetNodeGroupsAction(GroupRead[] groups)
        {
            _groups = groups;
        }

        public override void Execute(ClientState target)
        {
            var newMapsByID = _groups.ToDictionary(x => x.Id);
            var oldMapsByID = target.authoringTools.nodeGroups.ToDictionary(x => x.key, x => x.value);

            foreach (var toRemove in oldMapsByID.Where(x => !newMapsByID.ContainsKey(x.Key)))
                new DestroySceneObjectAction(toRemove.Key).Execute(target);

            foreach (var toUpdate in newMapsByID.Select(x => x.Value))
            {
                new AddOrUpdateNodeGroupAction(
                    id: toUpdate.Id,
                    name: toUpdate.Name,
                    parent: toUpdate.ParentId
                ).Execute(target);
            }
        }
    }

    public class AddOrUpdateNodeGroupAction : ObservableNodeAction<ClientState>
    {
        private Guid _id;
        private string _name;
        private Guid? _parent;
        private Guid[] _children;

        public AddOrUpdateNodeGroupAction(
            Guid id,
            string name = default,
            Guid? parent = default,
            params Guid[] children
        )
        {
            _id = id;
            _name = name;
            _parent = parent;
            _children = children;
        }

        public override void Execute(ClientState target)
        {
            var nodeGroup = target.authoringTools.nodeGroups.GetOrAdd(_id);

            nodeGroup.name.value = _name;
            nodeGroup.parentID.value = _parent;

            foreach (var child in _children)
            {
                if (target.nodes.TryGetValue(child, out var node))
                {
                    node.parentID.value = _id;
                    continue;
                }

                if (target.authoringTools.nodeGroups.TryGetValue(child, out var group))
                {
                    group.parentID.value = _id;
                    continue;
                }
            }
        }
    }

    public class SetParentGroupAction : ObservableNodeAction<ClientState>
    {
        private Guid _id;
        private Guid? _group;

        public SetParentGroupAction(Guid id, Guid? group)
        {
            _id = id;
            _group = group;
        }

        public override void Execute(ClientState target)
        {
            if (target.nodes.TryGetValue(_id, out var node))
            {
                node.parentID.value = _group;
                return;
            }

            if (target.authoringTools.nodeGroups.TryGetValue(_id, out var group))
            {
                group.parentID.value = _group;
                return;
            }
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

    public class SetSceneObjectTransformAction : ObservableNodeAction<ClientState>
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

        public override void Execute(ClientState target)
        {
            if (!target.transforms.TryGetValue(_sceneObjectID, out var transform))
                return;

            transform.position.value = _position;
            transform.rotation.value = _rotation;
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

    public class UpdateMapLocationsAction : ObservableNodeAction<ClientState>
    {
        private double4x4 _ecefToLocalMatrix;
        private AuthoringToolsMap.Props[] _toUpdate;

        public UpdateMapLocationsAction(double4x4 ecefToLocalMatrix, AuthoringToolsMap.Props[] toUpdate)
        {
            _ecefToLocalMatrix = ecefToLocalMatrix;
            _toUpdate = toUpdate;
        }

        public override void Execute(ClientState target)
        {
            foreach (var map in _toUpdate)
            {
                var transform = target.transforms[map.sceneObjectID.value];
                var localNodeTransform = LocationUtilities.UnityFromEcef(
                    _ecefToLocalMatrix,
                    transform.position.value,
                    transform.rotation.value
                );

                map.position.value = new UnityEngine.Vector3((float)localNodeTransform.position.x, (float)localNodeTransform.position.y, (float)localNodeTransform.position.z);
                map.rotation.value = localNodeTransform.rotation;
            }
        }
    }
}