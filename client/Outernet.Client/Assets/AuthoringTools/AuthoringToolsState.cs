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

        public ObservableSet<Guid> selectedObjects { get; private set; }

        public ObservablePrimitive<bool> saveRequested { get; private set; }
        public ObservablePrimitive<bool> hasUnsavedChanges { get; private set; }

        public IEnumerable<IObservableDictionary<Guid>> componentDictionaries
        {
            get
            {
                var clientState = root as ClientState;

                yield return clientState.nodes;
                yield return clientState.maps;
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
}