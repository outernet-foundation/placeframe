using System;
using System.Linq;

using Unity.Mathematics;
using UnityEngine;

using FofX.Stateful;

using Outernet.Client.AuthoringTools;
using Plerion.VPS;

namespace Outernet.Client
{
    public class ClientState : ObservableObject
    {
        public ObservablePrimitive<bool> loggedIn { get; private set; }
        public ObservablePrimitive<double2> roughGrainedLocation { get; private set; }
        public ObservableDictionary<Guid, NodeState> nodes { get; private set; }
        public ObservableDictionary<Guid, MapState> maps { get; private set; }
        public ObservableDictionary<Guid, TransformState> transforms { get; private set; }
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

#if AUTHORING_TOOLS_ENABLED && !MAP_REGISTRATION_TOOLS_ENABLED
            if (authoringTools.nodeGroups.TryGetValue(id, out var group))
            {
                name = group.name;
                return true;
            }
#endif

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

    public class NodeState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }

        public ObservablePrimitive<string> name { get; private set; }
        public ObservablePrimitive<string> label { get; private set; }
        public ObservablePrimitive<Shared.LabelType> labelType { get; private set; }
        public ObservablePrimitive<string> link { get; private set; }
        public ObservablePrimitive<Shared.LinkType> linkType { get; private set; }
        public ObservablePrimitive<float> labelScale { get; private set; }
        public ObservablePrimitive<float> labelWidth { get; private set; }
        public ObservablePrimitive<float> labelHeight { get; private set; }

        [InspectorType(typeof(LayerSelectInspector), LabelType.Adaptive)]
        public ObservablePrimitive<Guid> layer { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<Guid?> parentID { get; private set; }

        // This is "instance" stuff? maybe it should be somewhere else?
        [HideInInspectorUI]
        public ObservableSet<Guid> hoveringUsers { get; private set; }
        [HideInInspectorUI]
        public ObservablePrimitive<Guid> interactingUser { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<bool> exhibitOpen { get; private set; }
        [HideInInspectorUI]
        public ObservablePrimitive<double3> exhibitPosition { get; private set; }
        [HideInInspectorUI]
        public ObservablePrimitive<Quaternion> exhibitRotation { get; private set; }
        [HideInInspectorUI]
        public ObservablePrimitive<Vector2> exhibitPanelDimensions { get; private set; }
        [HideInInspectorUI]
        public ObservablePrimitive<float> exhibitPanelScrollPosition { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<bool> visible { get; private set; }

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

            visible.RegisterDerived(
                _ => visible.value = _clientState.settings.visibleLayers.Contains(layer.value),
                ObservationScope.Self,
                layer,
                _clientState.settings.visibleLayers
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
            transform.bounds.RegisterDerived(
                _ => transform.bounds.value = new Bounds(
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
        public Guid uuid { get; private set; }
        public ObservablePrimitive<int> id { get; private set; }
        public ObservablePrimitive<string> name { get; private set; }
        public ObservablePrimitive<Lighting> lighting { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitiveArray<Vector3> localInputImagePositions { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => uuid = key;

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
            if (!_clientState.transforms.TryGetValue(uuid, out var transform))
                return;

            context.DeregisterObserver(AwaitTransform);
            transform.bounds.RegisterDerived(
                _ =>
                {
                    if (localInputImagePositions.count == 0)
                    {
                        transform.bounds.value = default;
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

                    transform.bounds.value = new Bounds(
                        (min + max) / 2f,
                        max - min
                    );
                },
                ObservationScope.Self,
                localInputImagePositions
            );
        }
    }

    public class TransformState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }

        [InspectorType(typeof(ECEFPositionInspector), LabelType.Adaptive)]
        public ObservablePrimitive<double3> position { get; private set; }

        [InspectorType(typeof(ECEFRotationInspector), LabelType.Adaptive)]
        public ObservablePrimitive<Quaternion> rotation { get; private set; }

        public ObservablePrimitive<Bounds> bounds { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;
    }

    public class LayerState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }
        public ObservablePrimitive<string> layerName { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;
    }
}
