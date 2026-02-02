using System;
using System.Collections.Generic;
using System.Linq;

using UnityEngine;

using FofX;
using FofX.Stateful;

using Cysharp.Threading.Tasks;
using UnityEditor;
using PlaceframeApiClient.Model;

namespace Outernet.Client.AuthoringTools
{
    public class DontPersistAttribute : Attribute { }

    public class PersistenceManager : MonoBehaviour
    {
        private class PersistedChangeTrackingHelper<T>
        {
            public HashSet<T> inserts { get; private set; } = new HashSet<T>();
            public HashSet<T> updates { get; private set; } = new HashSet<T>();
            public HashSet<T> deletes { get; private set; } = new HashSet<T>();

            public bool hasPendingChanges => inserts.Count > 0 || updates.Count > 0 || deletes.Count > 0;

            public void RegisterInsert(T entry)
            {
                if (deletes.Remove(entry))
                {
                    updates.Add(entry);
                    return;
                }

                inserts.Add(entry);
            }

            public void RegisterUpdate(T entry)
            {
                if (inserts.Contains(entry))
                    return;

                if (deletes.Contains(entry))
                    throw new Exception($"Cannot update a deleted entry. Entry: {entry}");

                updates.Add(entry);
            }

            public void RegisterDelete(T entry)
            {
                updates.Remove(entry);

                if (inserts.Remove(entry))
                    return;

                deletes.Add(entry);
            }

            public void ClearChanges()
            {
                inserts.Clear();
                updates.Clear();
                deletes.Clear();
            }
        }

        private PersistedChangeTrackingHelper<Guid> _nodePersistenceHelper =
            new PersistedChangeTrackingHelper<Guid>();

        private PersistedChangeTrackingHelper<Guid> _nodeGroupPersistenceHelper =
            new PersistedChangeTrackingHelper<Guid>();

        private PersistedChangeTrackingHelper<Guid> _mapPersistenceHelper =
            new PersistedChangeTrackingHelper<Guid>();

        private PersistedChangeTrackingHelper<Guid> _layerPersistenceHelper =
            new PersistedChangeTrackingHelper<Guid>();

        private IDisposable _persistenceChangeTrackingBinding = Bindings.Empty();
        private bool _bindingsInitialized = false;

        private Queue<PersistenceData> _pendingPersists = new Queue<PersistenceData>();
        private TaskHandle _persistenceTask = TaskHandle.Complete;
        private bool _persistingChanges = false;
        private bool _settingHasPendingChanges = false;

        private bool _hasPendingChanges =>
            _nodePersistenceHelper.hasPendingChanges ||
            _nodeGroupPersistenceHelper.hasPendingChanges ||
            _mapPersistenceHelper.hasPendingChanges ||
            _layerPersistenceHelper.hasPendingChanges ||
            _persistingChanges;

        private void Awake()
        {
            App.RegisterObserver(
                HandleLocationContentLoadedChanged,
                App.state.authoringTools.locationContentLoaded
            );

            SystemMenu.AddMenuItem(
                "File/Save",
                () => App.state.authoringTools.saveRequested.ExecuteSet(true),
                validate: () => App.state.authoringTools.hasUnsavedChanges.value,
                commandKeys: new UnityEngine.InputSystem.Key[]
                {
                    Utility.GetPlatformCommandKey(),
                    UnityEngine.InputSystem.Key.S
                }
            );

            App.RegisterObserver(
                HandleSaveRequestedChanged,
                App.state.authoringTools.saveRequested
            );
        }

        private void OnDestroy()
        {
            _bindingsInitialized = false;
            _persistenceChangeTrackingBinding.Dispose();
        }

        private void HandleLocationContentLoadedChanged(NodeChangeEventArgs args)
        {
            if (!App.state.authoringTools.locationContentLoaded.value)
            {
                _bindingsInitialized = false;
                _nodePersistenceHelper.ClearChanges();
                _nodeGroupPersistenceHelper.ClearChanges();
                _mapPersistenceHelper.ClearChanges();
                _layerPersistenceHelper.ClearChanges();
                _persistenceChangeTrackingBinding.Dispose();
                App.state.authoringTools.hasUnsavedChanges.ExecuteSetOrDelay(false);
                return;
            }

            _persistenceChangeTrackingBinding = Bindings.Compose(
                App.state.nodes.Each(x => SetupPersistedObjectObserver(
                    _nodePersistenceHelper,
                    x.key,
                    x.value,
                    App.state.transforms[x.key]
                )),
                App.state.authoringTools.nodeGroups.Each(x => SetupPersistedObjectObserver(
                    _nodeGroupPersistenceHelper,
                    x.key,
                    x.value,
                    App.state.authoringTools.nodeGroups[x.key]
                )),
                App.state.authoringTools.maps.Each(x => SetupPersistedObjectObserver(
                    _mapPersistenceHelper,
                    x.key,
                    x.value,
                    App.state.transforms[x.key]
                )),
                App.state.layers.Each(x => SetupPersistedObjectObserver(
                    _layerPersistenceHelper,
                    x.key,
                    x.value
                ))
            );

            _bindingsInitialized = true;
        }

        private void HandleSaveRequestedChanged(NodeChangeEventArgs args)
        {
            if (args.initialize || !App.state.authoringTools.saveRequested.value)
                return;

            App.state.authoringTools.saveRequested.ExecuteSetOrDelay(false);
            PersistChanges();
        }

        private IDisposable SetupPersistedObjectObserver<T>(PersistedChangeTrackingHelper<T> trackingHelper, T entryData, params IObservableNode[] componentState)
        {
            if (_bindingsInitialized)
            {
                trackingHelper.RegisterInsert(entryData);
                UpdateHasUnsavedChangesIfNecessary();
            }

            return Bindings.Compose(
                Bindings.Observer(
                    args =>
                    {
                        if (args.initialize || !_bindingsInitialized)
                            return;

                        if (args.changes.All(x => x.source.isDerived || x.source.HasAttribute<DontPersistAttribute>()))
                            return;

                        trackingHelper.RegisterUpdate(entryData);
                        UpdateHasUnsavedChangesIfNecessary();
                    },
                    ObservationScope.All,
                    componentState
                ),
                Bindings.OnRelease(() =>
                {
                    if (_bindingsInitialized)
                    {
                        trackingHelper.RegisterDelete(entryData);
                        UpdateHasUnsavedChangesIfNecessary();
                    }
                })
            );
        }

        private void PersistChanges()
        {
            if (!_nodePersistenceHelper.hasPendingChanges &&
                !_nodeGroupPersistenceHelper.hasPendingChanges &&
                !_mapPersistenceHelper.hasPendingChanges &&
                !_layerPersistenceHelper.hasPendingChanges)
            {
                return;
            }

            _pendingPersists.Enqueue(new PersistenceData()
            {
                insertedNodes = _nodePersistenceHelper.inserts.Select(Utility.ToNodeBatchCreate).ToList(),
                insertedGroups = _nodeGroupPersistenceHelper.inserts.Select(Utility.ToGroupBatchCreate).ToList(),
                insertedMaps = _mapPersistenceHelper.inserts.Select(Utility.ToMapCreate).ToList(),
                insertedLayers = _layerPersistenceHelper.inserts.Select(Utility.ToLayerCreate).ToList(),

                updatedNodes = _nodePersistenceHelper.updates.Select(Utility.ToNodeUpdate).ToList(),
                updatedGroups = _nodeGroupPersistenceHelper.updates.Select(Utility.ToGroupUpdate).ToList(),
                updatedMaps = _mapPersistenceHelper.updates.Select(Utility.ToMapUpdate).ToList(),
                updatedLayers = _layerPersistenceHelper.updates.Select(Utility.ToLayerUpdate).ToList(),

                deletedNodes = _nodePersistenceHelper.deletes.ToList(),
                deletedGroups = _nodeGroupPersistenceHelper.deletes.ToList(),
                deletedMaps = _mapPersistenceHelper.deletes.ToList(),
                deletedLayers = _layerPersistenceHelper.deletes.ToList()
            });

            _nodePersistenceHelper.ClearChanges();
            _nodeGroupPersistenceHelper.ClearChanges();
            _mapPersistenceHelper.ClearChanges();
            _layerPersistenceHelper.ClearChanges();

            if (!_persistenceTask.pending)
                _persistenceTask = TaskHandle.Execute(_ => PersistAllPendingChanges());
        }

        private async UniTask PersistAllPendingChanges()
        {
            _persistingChanges = true;

            while (_pendingPersists.TryDequeue(out var toPersist))
            {
                await UniTask.WhenAll(
                    toPersist.insertedMaps.Count != 0 ? CreateLocalizationMapsAsync(toPersist.insertedMaps) : UniTask.CompletedTask,
                    toPersist.updatedMaps.Count != 0 ? App.API.UpdateLocalizationMapsAsync(toPersist.updatedMaps).AsUniTask() : UniTask.CompletedTask,
                    toPersist.deletedMaps.Count != 0 ? App.API.DeleteLocalizationMapsAsync(toPersist.deletedMaps).AsUniTask() : UniTask.CompletedTask,
                    toPersist.deletedGroups.Count != 0 ? App.API.DeleteGroupsAsync(toPersist.deletedGroups, cascade: true).AsUniTask() : UniTask.CompletedTask,
                    toPersist.deletedLayers.Count != 0 ? App.API.DeleteLayersAsync(toPersist.deletedLayers).AsUniTask() : UniTask.CompletedTask,
                    toPersist.deletedNodes.Count != 0 ? App.API.DeleteNodesAsync(toPersist.deletedNodes).AsUniTask() : UniTask.CompletedTask,
                    (toPersist.insertedLayers.Count != 0 ? CreateLayersAsync(toPersist.insertedLayers) : UniTask.CompletedTask)
                        .ContinueWith(() => toPersist.insertedGroups.Count != 0 || toPersist.insertedNodes.Count != 0 ?
                            App.API.CreateGraphAsync(new CreateGraphRequest() { Groups = toPersist.insertedGroups, Nodes = toPersist.insertedNodes }).AsUniTask() : UniTask.CompletedTask
                        )
                        .ContinueWith(() => UniTask.WhenAll(
                            toPersist.updatedLayers.Count != 0 ? App.API.UpdateLayersAsync(toPersist.updatedLayers).AsUniTask() : UniTask.CompletedTask,
                            toPersist.updatedGroups.Count != 0 ? App.API.UpdateGroupsAsync(toPersist.updatedGroups).AsUniTask() : UniTask.CompletedTask,
                            toPersist.updatedNodes.Count != 0 ? App.API.UpdateNodesAsync(toPersist.updatedNodes).AsUniTask() : UniTask.CompletedTask
                        ))
                );
            }

            _persistingChanges = false;

            await UniTask.SwitchToMainThread();
            UpdateHasUnsavedChangesIfNecessary();
        }

        private UniTask CreateNodesAsync(List<NodeCreate> nodes)
            => UniTask.WhenAll(nodes.Select(x => App.API.CreateNodeAsync(x).AsUniTask()));

        private async UniTask CreateGroupsAsync(List<GroupCreate> groups)
        {
            foreach (var group in groups)
                await App.API.CreateGroupAsync(group).AsUniTask();
        }

        private UniTask CreateLocalizationMapsAsync(List<LocalizationMapCreate> localizationMaps)
            => UniTask.WhenAll(localizationMaps.Select(x => App.API.CreateLocalizationMapAsync(x).AsUniTask()));

        private UniTask CreateLayersAsync(List<LayerCreate> layers)
            => UniTask.WhenAll(layers.Select(x => App.API.CreateLayerAsync(x).AsUniTask()));

        private void UpdateHasUnsavedChangesIfNecessary()
        {
            bool hasPendingChanges = _hasPendingChanges;
            if (App.state.authoringTools.hasUnsavedChanges.value != _hasPendingChanges &&
                !_settingHasPendingChanges)
            {
                _settingHasPendingChanges = true;
                App.state.authoringTools.hasUnsavedChanges.ExecuteSetOrDelay(
                    hasPendingChanges,
                    postObserverCallback: () => _settingHasPendingChanges = false
                );
            }
        }

        private class PersistenceData
        {
            public List<NodeBatchCreate> insertedNodes;
            public List<GroupBatchCreate> insertedGroups;
            public List<LocalizationMapCreate> insertedMaps;
            public List<LayerCreate> insertedLayers;

            public List<NodeBatchUpdate> updatedNodes;
            public List<GroupBatchUpdate> updatedGroups;
            public List<LocalizationMapBatchUpdate> updatedMaps;
            public List<LayerBatchUpdate> updatedLayers;

            public List<Guid> deletedNodes;
            public List<Guid> deletedGroups;
            public List<Guid> deletedMaps;
            public List<Guid> deletedLayers;
        }
    }
}