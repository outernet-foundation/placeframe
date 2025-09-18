using System;
using System.Collections.Generic;
using System.Linq;
using FofX.Stateful;
using Unity.Mathematics;
using UnityEngine;

namespace Outernet.Client.AuthoringTools
{
    public class AuthoringToolsState : ObservableObject
    {
        public UserSettings settings { get; private set; }
        public ObservablePrimitive<double2?> location { get; private set; }
        public ObservablePrimitive<bool> locationContentLoaded { get; private set; }

        public ObservableDictionary<Guid, MapState> maps { get; private set; }
        public ObservableSet<Guid> selectedObjects { get; private set; }

        public ObservablePrimitive<bool> saveRequested { get; private set; }
        public ObservablePrimitive<bool> hasUnsavedChanges { get; private set; }

        public IEnumerable<IObservableDictionary<Guid>> componentDictionaries
        {
            get
            {
                var clientState = root as ClientState;

                yield return clientState.nodes;
                yield return clientState.exhibits;
            }
        }

        private ClientState _clientState => root as ClientState;

        public IEnumerable<NodeState> SelectedNodes()
            => SelectedNodes(selectedObjects).Distinct();

        public bool HasSelectedNodes()
            => SelectedNodes(selectedObjects).FirstOrDefault() != default;

        private IEnumerable<NodeState> SelectedNodes(IEnumerable<Guid> sceneElements)
        {
            foreach (var id in sceneElements)
            {
                if (_clientState.nodes.TryGetValue(id, out var node))
                    yield return node;

                foreach (var child in SelectedNodes(node.childNodes))
                    yield return child;
            }
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

    public class MapState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }
        public ObservablePrimitive<string> name { get; private set; }
        public ObservablePrimitive<Vector3> position { get; private set; }
        public ObservablePrimitive<Quaternion> rotation { get; private set; }
        public ObservablePrimitive<Bounds> bounds { get; private set; }
        public ObservablePrimitive<Shared.Lighting> lighting { get; private set; }
        public ObservablePrimitive<long> color { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitiveArray<double3> localInputImagePositions { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;

        protected override void PostInitializeInternal()
        {
            bounds.RegisterDerived(
                _ =>
                {
                    if (localInputImagePositions.count == 0)
                    {
                        bounds.value = default;
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

                    bounds.value = new Bounds(
                        (min + max) / 2f,
                        max - min
                    );
                },
                ObservationScope.Self,
                localInputImagePositions
            );
        }
    }
}