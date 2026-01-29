using System;
using System.Collections.Generic;
using System.Linq;
using FofX.Stateful;
using Unity.Mathematics;

namespace Outernet.Client.AuthoringTools
{
    public class AuthoringToolsState : ObservableObject
    {
        public UserSettings settings { get; private set; }
        public ObservablePrimitive<double2?> location { get; private set; }
        public ObservablePrimitive<bool> locationContentLoaded { get; private set; }

        public ObservableDictionary<Guid, MapState> maps { get; private set; }
        public ObservableDictionary<Guid, NodeGroupState> nodeGroups { get; private set; }

        public ObservableDictionary<Guid, ObservableSet<Guid>> childByGroup { get; private set; }
        public ObservableSet<Guid> selectedObjects { get; private set; }

        public ObservablePrimitive<bool> saveRequested { get; private set; }
        public ObservablePrimitive<bool> hasUnsavedChanges { get; private set; }

        public IEnumerable<IObservableDictionary<Guid>> componentDictionaries
        {
            get
            {
                var clientState = root as ClientState;

                yield return clientState.nodes;
                yield return maps;
                yield return nodeGroups;
                yield return clientState.transforms;
            }
        }

        private ClientState clientState => root as ClientState;

        protected override void PostInitializeInternal()
        {
            ((IObservableNode)childByGroup).SetDerived(true);

            nodeGroups.Each(isDerived: true, bind: x => BindGroupedObject(x.key, x.value.parentID));
            clientState.nodes.Each(isDerived: true, bind: x => BindGroupedObject(x.key, x.value.parentID));
        }

        private IDisposable BindGroupedObject(Guid sceneObjectID, ObservablePrimitive<Guid?> parentID)
        {
            ObserverDelegate observer = args =>
            {
                if (args.initialize)
                {
                    if (parentID.value.HasValue)
                        childByGroup.GetOrAdd(parentID.value.Value).Add(sceneObjectID);

                    return;
                }

                foreach (var change in args.changes)
                {
                    var prevGroup = (Guid?)change.previousValue;
                    var currGroup = (Guid?)change.currentValue;

                    if (prevGroup.HasValue &&
                        childByGroup.TryGetValue(prevGroup.Value, out var children))
                    {
                        children.Remove(sceneObjectID);
                    }

                    if (currGroup.HasValue)
                        childByGroup.GetOrAdd(currGroup.Value).Add(sceneObjectID);
                }
            };

            context.RegisterObserver(observer, new ObserverParameters() { isDerived = true }, parentID);

            return Bindings.OnRelease(() => context.DeregisterObserver(observer));
        }

        public bool TryGetName(Guid id, out ObservablePrimitive<string> name)
        {
            if (clientState.nodes.TryGetValue(id, out var node))
            {
                name = node.name;
                return true;
            }

            if (maps.TryGetValue(id, out var map))
            {
                name = map.name;
                return true;
            }

            if (nodeGroups.TryGetValue(id, out var group))
            {
                name = group.name;
                return true;
            }

            name = default;
            return false;
        }

        public IEnumerable<TransformState> SelectedTransforms()
            => SelectedTransforms(selectedObjects).Distinct();

        public bool HasSelectedTransforms()
            => SelectedTransforms(selectedObjects).FirstOrDefault() != default;

        private IEnumerable<TransformState> SelectedTransforms(IEnumerable<Guid> sceneObjects)
        {
            foreach (var id in sceneObjects)
            {
                if (clientState.transforms.TryGetValue(id, out var transform))
                    yield return transform;

                if (nodeGroups.TryGetValue(id, out var group))
                {
                    foreach (var child in SelectedTransforms(group.childObjects))
                        yield return child;
                }
            }
        }

        public bool TryGetParent(Guid child, out Guid parentID)
        {
            if (clientState.nodes.TryGetValue(child, out var node))
            {
                if (!node.parentID.value.HasValue)
                {
                    parentID = default;
                    return false;
                }

                parentID = node.parentID.value.Value;
                return true;
            }

            if (nodeGroups.TryGetValue(child, out var group))
            {
                if (!group.parentID.value.HasValue)
                {
                    parentID = default;
                    return false;
                }

                parentID = group.parentID.value.Value;
                return true;
            }

            parentID = default;
            return false;
        }
    }

    public class UserSettings : ObservableObject
    {
        public ObservablePrimitive<bool> loaded { get; private set; }
        public ObservablePrimitive<double2?> lastLocation { get; private set; }
        public ObservablePrimitive<bool> restoreLocationAutomatically { get; private set; }
        public ObservableList<LocationHistoryData> locationHistory { get; private set; }
        public ObservablePrimitive<bool> autosaveEnabled { get; private set; }
        public ObservablePrimitive<float> nodeFetchRadius { get; private set; }
    }

    public class LocationHistoryData : ObservableObject
    {
        public ObservablePrimitive<string> name { get; private set; }
        public ObservablePrimitive<double2> location { get; private set; }
    }

    public class NodeGroupState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }

        public ObservablePrimitive<string> name { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<Guid?> parentID { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<bool> visible { get; private set; }

        public IEnumerable<Guid> childObjects
        {
            get
            {
                if ((root as ClientState).authoringTools.childByGroup.TryGetValue(id, out var children))
                {
                    foreach (var child in children)
                        yield return child;
                }
                else
                {
                    yield break;
                }
            }
        }

        private ClientState _clientState;
        private IDisposable _visibleObserver;

        protected override void PostInitializeInternal()
        {
            _clientState = root as ClientState;

            ((IObservableNode)visible).SetDerived(true);
            _visibleObserver = _clientState.authoringTools.childByGroup.Track(
                key: id,
                isDerived: true,
                bind: children => children.value.Each(
                    isDerived: true,
                    bind: child =>
                    {
                        ObservablePrimitive<bool> childVisible = default;

                        if (_clientState.authoringTools.nodeGroups.TryGetValue(child, out var childGroup))
                        {
                            childVisible = childGroup.visible;
                        }
                        else if (_clientState.nodes.TryGetValue(child, out var childNode))
                        {
                            childVisible = childNode.visible;
                        }

                        if (childVisible == null)
                            throw new Exception($"{child} is not present in the group or node collections.");

                        return Bindings.Observe(
                            childVisible,
                            new ObserverParameters() { isDerived = true },
                            args =>
                            {
                                if (childVisible.disposed)
                                {
                                    visible.value = IsVisible();
                                    return;
                                }

                                visible.value = childVisible.value ? true : IsVisible();
                            }
                        );
                    }
                )
            );
        }

        protected override void DisposeInternal()
        {
            _visibleObserver.Dispose();
        }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;

        private bool IsVisible()
        {
            if (!_clientState.authoringTools.childByGroup.TryGetValue(id, out var children))
                return false;

            foreach (var child in children)
            {
                if (_clientState.nodes.TryGetValue(child, out var node))
                {
                    if (node.visible.value)
                        return true;

                    continue;
                }

                if (_clientState.authoringTools.nodeGroups.TryGetValue(child, out var nodeGroup))
                {
                    if (nodeGroup.visible.value)
                        return true;

                    continue;
                }
            }

            return false;
        }
    }
}