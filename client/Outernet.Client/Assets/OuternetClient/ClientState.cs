using System;
using System.Linq;

using Unity.Mathematics;
using UnityEngine;

using FofX.Stateful;

using Outernet.Client.AuthoringTools;

namespace Outernet.Client
{
    public class ClientState : ObservableObject
    {
        public ObservablePrimitive<Guid> clientID { get; private set; }
        public ObservableDictionary<Guid, TransformState> transforms { get; private set; }

        public ObservableDictionary<Guid, NodeState> nodes { get; private set; }
        public ObservableDictionary<Guid, ExhibitState> exhibits { get; private set; }
        public ObservableDictionary<Guid, MapState> maps { get; private set; }

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

        public bool TryGetName(Guid id, out ObservablePrimitive<string> name)
        {
            if (nodes.TryGetValue(id, out var node))
            {
                name = node.name;
                return true;
            }

            if (maps.TryGetValue(id, out var map))
            {
                name = map.name;
                return true;
            }

            name = default;
            return false;
        }
    }

    public class SettingsState : ObservableObject
    {
        public ObservablePrimitive<bool> animateNodeIndicators { get; private set; }
        public ObservablePrimitive<bool> showIndicators { get; private set; }
        public ObservableSet<Guid> visibleLayers { get; private set; }
    }

    public class TransformState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<Guid?> parentTransform { get; private set; }

        [HideInInspectorUI]
        public ObservableSet<Guid> childTransforms { get; private set; }

        public ObservablePrimitive<Vector3> localPosition { get; private set; }
        public ObservablePrimitive<Quaternion> localRotation { get; private set; }
        public ObservablePrimitive<Bounds> localBounds { get; private set; }

        public ObservablePrimitive<Vector3> position { get; private set; }
        public ObservablePrimitive<Quaternion> rotation { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;

        private ObservableDictionary<Guid, TransformState> _transforms => (root as ClientState).transforms;
        private TransformState _parentTransform;

        protected override void PostInitializeInternal()
        {
            ((IObservableNode)position).SetDerived(true);
            ((IObservableNode)rotation).SetDerived(true);
            ((IObservableNode)childTransforms).SetDerived(true);

            context.RegisterObserver(
                HandleParentTransformChanged,
                new ObserverParameters() { isDerived = true },
                parentTransform
            );
        }

        protected override void DisposeInternal()
        {
            context.DeregisterObserver(HandleLocalValuesChanged);
            context.DeregisterObserver(HandleParentExistsChanged);
            context.DeregisterObserver(HandleParentTransformValuesChanged);
        }

        private void HandleParentTransformChanged(NodeChangeEventArgs args)
        {
            if (args.initialize)
            {
                AddChildOrAwaitParent(parentTransform.value);
                return;
            }

            foreach (var change in args.changes)
            {
                if (change.changeType == ChangeType.Dispose)
                {
                    if (parentTransform.value.HasValue &&
                        _transforms.TryGetValue(parentTransform.value.Value, out var p))
                    {
                        p.childTransforms.Remove(id);
                    }

                    return;
                }

                var prevParentID = (Guid?)change.previousValue;
                if (prevParentID.HasValue &&
                    _transforms.TryGetValue(prevParentID.Value, out var prevParent))
                {
                    prevParent.childTransforms.Remove(id);
                }

                AddChildOrAwaitParent((Guid?)change.currentValue);
            }
        }

        private void AddChildOrAwaitParent(Guid? parentID)
        {
            context.DeregisterObserver(HandleLocalValuesChanged);
            context.DeregisterObserver(HandleParentExistsChanged);
            context.DeregisterObserver(HandleParentTransformValuesChanged);

            if (!parentID.HasValue)
            {
                context.RegisterObserver(
                    HandleLocalValuesChanged,
                    new ObserverParameters() { isDerived = true },
                    localPosition,
                    localRotation
                );

                return;
            }

            if (_transforms.TryGetValue(parentID.Value, out var currParent))
            {
                currParent.childTransforms.Add(id);
                return;
            }

            context.RegisterObserver(
                HandleParentExistsChanged,
                new ObserverParameters() { scope = ObservationScope.Self, isDerived = true },
                parentTransform,
                _transforms
            );
        }

        private void HandleLocalValuesChanged(NodeChangeEventArgs args)
        {
            position.value = localPosition.value;
            rotation.value = localRotation.value;
        }

        private void HandleParentExistsChanged(NodeChangeEventArgs args)
        {
            if (parentTransform.value.HasValue &&
                _transforms.TryGetValue(parentTransform.value.Value, out var currParent))
            {
                _parentTransform = currParent;
                _parentTransform.childTransforms.Add(id);
                context.DeregisterObserver(HandleParentExistsChanged);
                context.RegisterObserver(
                    HandleParentTransformValuesChanged,
                    new ObserverParameters() { isDerived = true },
                    _parentTransform.position,
                    _parentTransform.rotation,
                    localPosition,
                    localRotation
                );
            }
        }

        private void HandleParentTransformValuesChanged(NodeChangeEventArgs args)
        {
            position.value = Matrix4x4.TRS(_parentTransform.position.value, _parentTransform.rotation.value, Vector3.one).MultiplyPoint3x4(localPosition.value);
            rotation.value = Quaternion.Inverse(_parentTransform.rotation.value) * localRotation.value;
        }
    }

    public class NodeState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }

        public ObservablePrimitive<string> name { get; private set; }

        [InspectorType(typeof(LayerSelectInspector), LabelType.Adaptive)]
        public ObservablePrimitive<Guid> layer { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<bool> visible { get; private set; }

        [HideInInspectorUI]
        public ObservableSet<Guid> hoveringUsers { get; private set; }
        [HideInInspectorUI]
        public ObservablePrimitive<Guid> interactingUser { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;

        private ClientState _clientState => root as ClientState;

        protected override void PostInitializeInternal()
        {
            visible.RegisterDerived(
                _ => visible.value = _clientState.settings.visibleLayers.Contains(layer.value),
                ObservationScope.Self,
                layer,
                _clientState.settings.visibleLayers
            );
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

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;

        private ClientState _clientState => root as ClientState;

        protected override void PostInitializeInternal()
        {
            context.RegisterObserver(
                AwaitTransform,
                new ObserverParameters() { scope = ObservationScope.Self, isDerived = true },
                _clientState.transforms
            );
        }

        protected override void DisposeInternal()
        {
            context.DeregisterObserver(AwaitTransform);
        }

        private void AwaitTransform(NodeChangeEventArgs args)
        {
            if (!_clientState.transforms.TryGetValue(id, out var transform))
                return;

            context.DeregisterObserver(AwaitTransform);
            transform.localBounds.RegisterDerived(
                _ => transform.localBounds.value = new Bounds(
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

    public class MapState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }
        public ObservablePrimitive<string> name { get; private set; }
        public ObservablePrimitive<Shared.Lighting> lighting { get; private set; }
        public ObservablePrimitive<long> color { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitiveArray<double3> localInputImagePositions { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;

        private ClientState _clientState => root as ClientState;

        protected override void PostInitializeInternal()
        {
            context.RegisterObserver(
                AwaitTransform,
                new ObserverParameters() { scope = ObservationScope.Self, isDerived = true },
                _clientState.transforms
            );
        }

        protected override void DisposeInternal()
        {
            context.DeregisterObserver(AwaitTransform);
        }

        private void AwaitTransform(NodeChangeEventArgs args)
        {
            if (!_clientState.transforms.TryGetValue(id, out var transform))
                return;

            context.DeregisterObserver(AwaitTransform);
            transform.localBounds.RegisterDerived(
                _ =>
                {
                    if (localInputImagePositions.count == 0)
                    {
                        transform.localBounds.value = default;
                        return;
                    }

                    var min = new Vector3(
                        -(float)localInputImagePositions.Select(x => x.x).Min(),
                        -(float)localInputImagePositions.Select(x => x.y).Min(),
                        -(float)localInputImagePositions.Select(x => x.z).Min()
                    );

                    var max = new Vector3(
                        -(float)localInputImagePositions.Select(x => x.x).Max(),
                        -(float)localInputImagePositions.Select(x => x.y).Max(),
                        -(float)localInputImagePositions.Select(x => x.z).Max()
                    );

                    transform.localBounds.value = new Bounds(
                        (min + max) / 2f,
                        max - min
                    );
                },
                ObservationScope.Self,
                localInputImagePositions
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
