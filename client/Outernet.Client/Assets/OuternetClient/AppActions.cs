using System;
using System.Linq;

using UnityEngine;
using FofX.Stateful;

using Unity.Mathematics;
using PlerionClient.Model;
using System.Collections;
using System.Collections.Generic;

namespace Outernet.Client
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

    public class SetMapsAction : ObservableNodeAction<ClientState>
    {
        private LocalizationMapModel[] _maps;

        public SetMapsAction(LocalizationMapModel[] maps)
        {
            _maps = maps;
        }

        public override void Execute(ClientState target)
        {
            var newMapsByID = _maps.ToDictionary(x => x.Id);
            var oldMapsByID = target.maps.ToDictionary(x => x.key, x => x.value);

            foreach (var toRemove in oldMapsByID.Where(x => !newMapsByID.ContainsKey(x.Key)))
                new DestroySceneObjectAction(toRemove.Key).Execute(target);

            foreach (var map in newMapsByID.Select(x => x.Value))
            {
                var mapWorldTransform = Utility.EcefToLocal(
                    target.ecefToLocalMatrix.value,
                    new double3(map.PositionX, map.PositionY, map.PositionZ),
                    new quaternion((float)map.RotationX, (float)map.RotationY, (float)map.RotationZ, (float)map.RotationW)
                );

                /* TODO: Parent support??
                Vector3 localPosition;
                Quaternion localRotation;

                var mapWorldTransform = Utility.EcefToLocal(
                    target.ecefToLocalMatrix.value,
                    new double3(map.PositionX, map.PositionY, map.PositionZ),
                    new quaternion((float)map.RotationX, (float)map.RotationY, (float)map.RotationZ, (float)map.RotationW)
                );

                if (!map.Parent.HasValue)
                {
                    localPosition = mapWorldTransform.position;
                    localRotation = mapWorldTransform.rotation;
                }
                else
                {
                    var parent = newMapsByID[map.Parent.Value];
                    var parentWorldTransform = Utility.EcefToLocal(
                        target.ecefToLocalMatrix.value,
                        new double3(parent.PositionX, parent.PositionY, parent.PositionZ),
                        new quaternion((float)parent.RotationX, (float)parent.RotationY, (float)parent.RotationZ, (float)parent.RotationW)
                    );

                    var parentWorldToLocalMatrix = Matrix4x4.TRS(
                        parentWorldTransform.position,
                        parentWorldTransform.rotation,
                        Vector3.one
                    );

                    localPosition = parentWorldToLocalMatrix.inverse.MultiplyPoint3x4(mapWorldTransform.position);
                    localRotation = Quaternion.Inverse(parentWorldTransform.rotation) * mapWorldTransform.rotation;
                }
                */

                new AddOrUpdateMapAction(
                    id: map.Id,
                    name: map.Name,
                    localPosition: mapWorldTransform.position,
                    localRotation: mapWorldTransform.rotation,
                    lighting: (Shared.Lighting)map.Lighting,
                    color: map.Color,
                    localInputImagePositions: ParsePoints(map.Points)
                ).Execute(target);
            }
        }

        private double3[] ParsePoints(List<double> flatPoints)
        {
            var result = new double3[flatPoints.Count / 3];
            for (int i = 0; i < flatPoints.Count; i += 3)
                result[i / 3] = new double3(flatPoints[i], flatPoints[i + 1], flatPoints[i + 2]);

            return result;
        }
    }

    public class AddOrUpdateMapAction : ObservableNodeAction<ClientState>
    {
        private Guid _id;
        private string _name;
        private Vector3 _localPosition;
        private Quaternion _localRotation;
        private Shared.Lighting _lighting;
        private long _color;
        private double3[] _localInputImagePositions;

        public AddOrUpdateMapAction(
            Guid id,
            string name = default,
            Vector3 localPosition = default,
            Quaternion localRotation = default,
            Shared.Lighting lighting = default,
            long color = default,
            double3[] localInputImagePositions = default)
        {
            _id = id;
            _name = name;
            _localPosition = localPosition;
            _localRotation = localRotation;
            _lighting = lighting;
            _color = color;
            _localInputImagePositions = localInputImagePositions;
        }

        public override void Execute(ClientState target)
        {
            var map = target.maps.GetOrAdd(_id);
            var transform = target.transforms.GetOrAdd(_id);

            map.name.value = _name;
            map.lighting.value = _lighting;
            map.color.value = _color;
            map.localInputImagePositions.SetValue(_localInputImagePositions);

            transform.localPosition.value = _localPosition;
            transform.localRotation.value = _localRotation;
        }
    }

    public class SetNodesAction : ObservableNodeAction<ClientState>
    {
        private NodeModel[] _nodes;

        public SetNodesAction(NodeModel[] nodes)
        {
            _nodes = nodes;
        }

        public override void Execute(ClientState target)
        {
            var newNodesByID = _nodes.ToDictionary(x => x.Id);
            var oldNodesByID = target.nodes.ToDictionary(x => x.key, x => x.value);

            foreach (var toRemove in oldNodesByID.Where(x => !newNodesByID.ContainsKey(x.Key)))
                new DestroySceneObjectAction(toRemove.Key).Execute(target);

            foreach (var node in newNodesByID.Select(x => x.Value))
            {
                Vector3 localPosition;
                Quaternion localRotation;

                var nodeWorldTransform = Utility.EcefToLocal(
                    target.ecefToLocalMatrix.value,
                    new double3(node.PositionX, node.PositionY, node.PositionZ),
                    new quaternion((float)node.RotationX, (float)node.RotationY, (float)node.RotationZ, (float)node.RotationW)
                );

                if (!node.Parent.HasValue)
                {
                    localPosition = nodeWorldTransform.position;
                    localRotation = nodeWorldTransform.rotation;
                }
                else
                {
                    var parent = newNodesByID[node.Parent.Value];
                    var parentWorldTransform = Utility.EcefToLocal(
                        target.ecefToLocalMatrix.value,
                        new double3(parent.PositionX, parent.PositionY, parent.PositionZ),
                        new quaternion((float)parent.RotationX, (float)parent.RotationY, (float)parent.RotationZ, (float)parent.RotationW)
                    );

                    var parentWorldToLocalMatrix = Matrix4x4.TRS(
                        parentWorldTransform.position,
                        parentWorldTransform.rotation,
                        Vector3.one
                    );

                    localPosition = parentWorldToLocalMatrix.inverse.MultiplyPoint3x4(nodeWorldTransform.position);
                    localRotation = Quaternion.Inverse(parentWorldTransform.rotation) * nodeWorldTransform.rotation;
                }

                new AddOrUpdateNodeAction(
                    id: node.Id,
                    name: node.Name,
                    label: node.Label,
                    labelType: (Shared.LabelType)(node.LabelType.HasValue ? node.LabelType.Value : default),
                    link: node.Link,
                    linkType: (Shared.LinkType)(node.LinkType.HasValue ? node.LinkType.Value : default),
                    labelScale: (float)(node.LabelScale.HasValue ? node.LabelScale.Value : default),
                    labelWidth: (float)(node.LabelWidth.HasValue ? node.LabelWidth.Value : default),
                    labelHeight: (float)(node.LabelHeight.HasValue ? node.LabelHeight.Value : default),
                    layer: node.Layer.HasValue ? node.Layer.Value : Guid.Empty,
                    parentID: node.Parent,
                    localPosition: localPosition,
                    localRotation: localRotation
                ).Execute(target);
            }
        }
    }

    public class AddOrUpdateNodeAction : ObservableNodeAction<ClientState>
    {
        private Guid _id;
        private string _name;
        private Guid? _parentID;
        private string _label;
        private Shared.LabelType _labelType;
        private string _link;
        private Shared.LinkType _linkType;
        private float _labelScale;
        private float _labelWidth;
        private float _labelHeight;
        private Guid _layer;
        private Guid[] _hoveringUsers;
        private Guid _interactingUser;
        private bool _exhibitOpen;
        private Vector3 _exhibitLocalPosition;
        private Quaternion _exhibitLocalRotation;
        private Vector2 _exhibitPanelDimensions;
        private float _exhibitPanelScrollPosition;

        private Vector3 _localPosition;
        private Quaternion _localRotation;

        public AddOrUpdateNodeAction(
            Guid id,
            string name = default,
            string label = default,
            Shared.LabelType labelType = default,
            string link = default,
            Shared.LinkType linkType = default,
            float labelScale = default,
            float labelWidth = default,
            float labelHeight = default,
            Guid layer = default,
            Guid? parentID = default,
            Guid[] hoveringUsers = default,
            Guid interactingUser = default,
            bool exhibitOpen = default,
            Vector3 exhibitLocalPosition = default,
            Quaternion exhibitLocalRotation = default,
            Vector2 exhibitPanelDimensions = default,
            float exhibitPanelScrollPosition = default,
            Vector3 localPosition = default,
            Quaternion localRotation = default
        )
        {
            _id = id;
            _name = name;
            _label = label;
            _labelType = labelType;
            _link = link;
            _linkType = linkType;
            _labelScale = labelScale;
            _labelWidth = labelWidth;
            _labelHeight = labelHeight;
            _layer = layer;
            _parentID = parentID;
            _hoveringUsers = hoveringUsers;
            _interactingUser = interactingUser;
            _exhibitOpen = exhibitOpen;
            _exhibitLocalPosition = exhibitLocalPosition;
            _exhibitLocalRotation = exhibitLocalRotation;
            _exhibitPanelDimensions = exhibitPanelDimensions;
            _exhibitPanelScrollPosition = exhibitPanelScrollPosition;
            _localPosition = localPosition;
            _localRotation = localRotation;
        }

        public override void Execute(ClientState target)
        {
            var node = target.nodes.GetOrAdd(_id);
            var transform = target.transforms.GetOrAdd(_id);
            var exhibit = target.exhibits.GetOrAdd(_id);

            node.name.value = _name;
            node.layer.value = _layer;
            node.hoveringUsers.SetFrom(_hoveringUsers);
            node.interactingUser.value = _interactingUser;

            transform.parentTransform.value = _parentID;
            transform.localPosition.value = _localPosition;
            transform.localRotation.value = _localRotation;

            exhibit.label.value = _label;
            exhibit.labelType.value = _labelType;
            exhibit.link.value = _link;
            exhibit.linkType.value = _linkType;
            exhibit.labelScale.value = _labelScale;
            exhibit.labelWidth.value = _labelWidth;
            exhibit.labelHeight.value = _labelHeight;
            exhibit.exhibitOpen.value = _exhibitOpen;
            exhibit.exhibitLocalPosition.value = _exhibitLocalPosition;
            exhibit.exhibitLocalRotation.value = _exhibitLocalRotation;
            exhibit.exhibitPanelDimensions.value = _exhibitPanelDimensions;
            exhibit.exhibitPanelScrollPosition.value = _exhibitPanelScrollPosition;
        }
    }

    public class ClearSceneObjectsAction : ObservableNodeAction<ClientState>
    {
        public override void Execute(ClientState target)
        {
            foreach (var componentDict in target.authoringTools.componentDictionaries)
                componentDict.Clear();

            target.authoringTools.selectedObjects.Clear();
        }
    }

    public class DestroySceneObjectAction : ObservableNodeAction<ClientState>
    {
        private Guid _sceneObjectID;

        public DestroySceneObjectAction(Guid sceneObjectID)
        {
            _sceneObjectID = sceneObjectID;
        }

        public override void Execute(ClientState target)
        {
            if (target.transforms.TryGetValue(_sceneObjectID, out var transform))
            {
                foreach (var child in transform.childTransforms.ToArray())
                    new DestroySceneObjectAction(child).Execute(target);
            }

            target.authoringTools.selectedObjects.Remove(_sceneObjectID);

            foreach (var componentDict in target.authoringTools.componentDictionaries)
                componentDict.Remove(_sceneObjectID);
        }
    }

    public class SetEcefToLocalMatrixAction : ObservableNodeAction<ClientState>
    {
        private double4x4 _matrix;
        private bool _updateTransforms;

        public SetEcefToLocalMatrixAction(double4x4 matrix, bool updateTransforms = true)
        {
            _matrix = matrix;
            _updateTransforms = updateTransforms;
        }

        public override void Execute(ClientState target)
        {
            var prevLocalToEcefMatrix = target.localToEcefMatrix.value;
            target.ecefToLocalMatrix.value = _matrix; // this updates target.localToEcefMatrix automatically

            if (!_updateTransforms)
                return;

            foreach (var transform in target.transforms.values)
            {
                // we only need to update roots
                if (!transform.parentTransform.value.HasValue)
                {
                    var ecefCoords = Utility.LocalToEcef(
                        prevLocalToEcefMatrix,
                        transform.localPosition.value,
                        transform.localRotation.value
                    );

                    var newLocalCoords = Utility.EcefToLocal(
                        _matrix,
                        ecefCoords.position,
                        ecefCoords.rotation
                    );

                    transform.localPosition.value = newLocalCoords.position;
                    transform.localRotation.value = newLocalCoords.rotation;
                }

                if (target.exhibits.TryGetValue(transform.id, out var exhibit) && exhibit.exhibitOpen.value)
                {
                    var nodeState = target.nodes[exhibit.id];

                    if (nodeState.interactingUser.value != Guid.Empty &&
                        nodeState.interactingUser.value == target.clientID.value)
                    {
                        // TODO: 
                        // Update exhibits that are in the middle of interactions 
                        // so they don't move when the origin does
                    }
                }
            }
        }
    }

    public class RemoveLayerAction : ObservableNodeAction<ClientState>
    {
        private Guid _layer;

        public RemoveLayerAction(Guid layer)
        {
            _layer = layer;
        }

        public override void Execute(ClientState target)
        {
            target.layers.Remove(_layer);
            foreach (var node in target.nodes)
            {
                if (node.value.layer.value == _layer)
                    node.value.layer.value = Guid.Empty;
            }
        }
    }
}
