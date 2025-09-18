using System;
using System.Linq;

using Unity.Mathematics;
using UnityEngine;

using FofX.Stateful;

using Outernet.Client.AuthoringTools;
using UnityEditor;

namespace Outernet.Client
{
    public class ClientState : ObservableObject
    {
        public ObservablePrimitive<Guid> clientID { get; private set; }

        public ObservableDictionary<Guid, NodeState> nodes { get; private set; }
        public ObservableDictionary<Guid, ExhibitState> exhibits { get; private set; }

        public ObservableDictionary<Guid, LayerState> layers { get; private set; }

        public ObservablePrimitive<double4x4> ecefToLocalMatrix { get; private set; } = new ObservablePrimitive<double4x4>(double4x4.identity);
        public ObservablePrimitive<double4x4> localToEcefMatrix { get; private set; }

        public AuthoringToolsState authoringTools { get; private set; }

        public SettingsState settings { get; private set; }

        protected override void PostInitializeInternal()
        {
            localToEcefMatrix.RegisterDerived(
                _ => localToEcefMatrix.value = math.inverse(ecefToLocalMatrix.value),
                ObservationScope.Self,
                ecefToLocalMatrix
            );
        }
    }

    public class SettingsState : ObservableObject
    {
        public ObservablePrimitive<bool> animateNodeIndicators { get; private set; }
        public ObservablePrimitive<bool> showIndicators { get; private set; }
        public ObservableSet<Guid> visibleLayers { get; private set; }
    }

    public class NodeState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }

        public ObservablePrimitive<string> name { get; private set; }
        public ObservablePrimitive<bool> active { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<Guid?> parentID { get; private set; }
        public ObservableSet<Guid> childNodes { get; private set; }

        public ObservablePrimitive<Vector3> localPosition { get; private set; }
        public ObservablePrimitive<Quaternion> localRotation { get; private set; }
        public ObservablePrimitive<Bounds> localBounds { get; private set; }

        public ObservablePrimitive<Vector3> position { get; private set; }
        public ObservablePrimitive<Quaternion> rotation { get; private set; }

        [InspectorType(typeof(LayerSelectInspector), LabelType.Adaptive)]
        public ObservablePrimitive<Guid> layer { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<bool> visible { get; private set; }

        [HideInInspectorUI]
        public ObservableSet<Guid> hoveringUsers { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<Guid> interactingUser { get; private set; }

        private ClientState _clientState => root as ClientState;
        private ObservableDictionary<Guid, NodeState> _nodes => (root as ClientState).nodes;

        private NodeState _parentNode;

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;

        protected override void PostInitializeInternal()
        {
            ((IObservableNode)childNodes).SetDerived(true);
            ((IObservableNode)position).SetDerived(true);
            ((IObservableNode)rotation).SetDerived(true);

            visible.RegisterDerived(
                _ => visible.value = _clientState.settings.visibleLayers.Contains(layer.value),
                ObservationScope.Self,
                layer,
                _clientState.settings.visibleLayers
            );

            context.RegisterObserver(
                HandleParentNodeChanged,
                new ObserverParameters() { isDerived = true },
                parentID
            );
        }

        protected override void DisposeInternal()
        {
            context.DeregisterObserver(HandleParentNodeChanged);
            context.DeregisterObserver(HandleParentExistsChanged);
            context.DeregisterObserver(HandleWorldTransformSourcesChanged);
        }

        private void HandleParentNodeChanged(NodeChangeEventArgs args)
        {
            if (args.initialize)
            {
                RegisterParentObservers(parentID.value);
                return;
            }

            foreach (var change in args.changes)
            {
                if (change.changeType == ChangeType.Dispose)
                {
                    if (parentID.value.HasValue &&
                        _nodes.TryGetValue(parentID.value.Value, out var parent))
                    {
                        parent.childNodes.Remove(id);
                    }

                    return;
                }

                var prevParentID = (Guid?)change.previousValue;
                if (prevParentID.HasValue &&
                    _nodes.TryGetValue(prevParentID.Value, out var prevParent))
                {
                    prevParent.childNodes.Remove(id);
                }

                RegisterParentObservers((Guid?)change.currentValue);
            }
        }

        private void RegisterParentObservers(Guid? parentID)
        {
            context.DeregisterObserver(HandleParentExistsChanged);
            context.DeregisterObserver(HandleWorldTransformSourcesChanged);

            if (!parentID.HasValue)
            {
                context.RegisterObserver(
                    HandleWorldTransformSourcesChanged,
                    new ObserverParameters() { isDerived = true },
                    localPosition,
                    localRotation
                );

                return;
            }

            if (_nodes.TryGetValue(parentID.Value, out _parentNode))
            {
                _parentNode.childNodes.Add(id);

                context.RegisterObserver(
                    HandleWorldTransformSourcesChanged,
                    new ObserverParameters() { isDerived = true },
                    _parentNode.position,
                    _parentNode.rotation,
                    localPosition,
                    localRotation
                );

                return;
            }

            context.RegisterObserver(
                HandleParentExistsChanged,
                new ObserverParameters() { scope = ObservationScope.Self, isDerived = true },
                _nodes
            );
        }

        private void HandleParentExistsChanged(NodeChangeEventArgs args)
        {
            if (_nodes.TryGetValue(parentID.value.Value, out _parentNode))
            {
                _parentNode.childNodes.Add(id);
                context.DeregisterObserver(HandleParentExistsChanged);
                context.RegisterObserver(
                    HandleWorldTransformSourcesChanged,
                    new ObserverParameters() { isDerived = true },
                    _parentNode.position,
                    _parentNode.rotation,
                    localPosition,
                    localRotation
                );
            }
        }

        private void HandleWorldTransformSourcesChanged(NodeChangeEventArgs args)
        {
            if (_parentNode == null)
            {
                position.value = localPosition.value;
                rotation.value = localRotation.value;
                return;
            }

            var matrix = Matrix4x4.TRS(_parentNode.position.value, _parentNode.rotation.value, Vector3.one);
            position.value = matrix.MultiplyPoint3x4(localPosition.value);
            rotation.value = _parentNode.rotation.value * localRotation.value;
        }
    }

    public class ExhibitState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }

        public ObservablePrimitive<string> label { get; private set; }
        public ObservablePrimitive<Shared.LabelType> labelType { get; private set; }
        public ObservablePrimitive<string> link { get; private set; }
        public ObservablePrimitive<Shared.LinkType> linkType { get; private set; }
        public ObservablePrimitive<float> labelScale { get; private set; }
        public ObservablePrimitive<float> labelWidth { get; private set; }
        public ObservablePrimitive<float> labelHeight { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<bool> exhibitOpen { get; private set; }
        [HideInInspectorUI]
        public ObservablePrimitive<Vector3> exhibitLocalPosition { get; private set; }
        [HideInInspectorUI]
        public ObservablePrimitive<Quaternion> exhibitLocalRotation { get; private set; }
        [HideInInspectorUI]
        public ObservablePrimitive<Vector2> exhibitPanelDimensions { get; private set; }
        [HideInInspectorUI]
        public ObservablePrimitive<float> exhibitPanelScrollPosition { get; private set; }

        private ClientState _clientState => root as ClientState;

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;

        protected override void PostInitializeInternal()
        {
            context.RegisterObserver(
                AwaitNode,
                new ObserverParameters() { scope = ObservationScope.Self, isDerived = true },
                _clientState.nodes
            );
        }

        protected override void DisposeInternal()
        {
            context.DeregisterObserver(AwaitNode);
        }

        private void AwaitNode(NodeChangeEventArgs args)
        {
            if (!_clientState.nodes.TryGetValue(id, out var node))
                return;

            context.DeregisterObserver(AwaitNode);
            node.localBounds.RegisterDerived(
                _ => node.localBounds.value = new Bounds(
                    new Vector3(0, 0, -0.5f) * labelScale.value,
                    new Vector3(
                        labelWidth.value,
                        labelHeight.value,
                        1f
                    ) * labelScale.value
                ),
                ObservationScope.Self,
                labelWidth,
                labelHeight,
                labelScale
            );
        }
    }

    public class LayerState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }
        public ObservablePrimitive<string> layerName { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;
    }
}
