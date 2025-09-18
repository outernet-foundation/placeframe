using System;
using System.Collections.Generic;
using System.Linq;

using UnityEngine;

using FofX;
using FofX.Stateful;

using Cysharp.Threading.Tasks;
using UnityEditor;
using PlerionClient.Model;

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

        private PersistedChangeTrackingHelper<Guid> _exhibitsPersistenceHelper =
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
            _exhibitsPersistenceHelper.hasPendingChanges ||
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
                _exhibitsPersistenceHelper.ClearChanges();
                _mapPersistenceHelper.ClearChanges();
                _layerPersistenceHelper.ClearChanges();
                _persistenceChangeTrackingBinding.Dispose();
                App.state.authoringTools.hasUnsavedChanges.ExecuteSetOrDelay(false);
                return;
            }

            _persistenceChangeTrackingBinding = Bindings.Compose(
                App.state.exhibits.Each(x => SetupPersistedObjectObserver(
                    _exhibitsPersistenceHelper,
                    x.key,
                    x.value
                )),
                App.state.authoringTools.maps.Each(x => SetupPersistedObjectObserver(
                    _mapPersistenceHelper,
                    x.key,
                    x.value
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
            if (!_exhibitsPersistenceHelper.hasPendingChanges &&
                !_mapPersistenceHelper.hasPendingChanges &&
                !_layerPersistenceHelper.hasPendingChanges)
            {
                return;
            }

            _pendingPersists.Enqueue(new PersistenceData()
            {
                upsertedNodes = _exhibitsPersistenceHelper.inserts.Concat(_exhibitsPersistenceHelper.updates)
                    .Select(Utility.ToExhibitModel)
                    .ToList(),

                upsertedMaps = _mapPersistenceHelper.inserts.Concat(_mapPersistenceHelper.updates)
                    .Select(Utility.ToMapRecord)
                    .ToList(),

                upsertedLayers = _layerPersistenceHelper.inserts.Concat(_layerPersistenceHelper.updates)
                    .Select(Utility.ToLayerModel)
                    .ToList(),

                deletedNodes = _exhibitsPersistenceHelper.deletes.ToList(),
                deletedMaps = _mapPersistenceHelper.deletes.ToList(),
                deletedLayers = _layerPersistenceHelper.deletes.ToList()
            });

            _exhibitsPersistenceHelper.ClearChanges();
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
                    PlerionAPI.api.DeleteLocalizationMapsAsync(toPersist.deletedMaps).AsUniTask(),
                    PlerionAPI.api.UpsertLocalizationMapsAsync(toPersist.upsertedMaps).AsUniTask(),
                    PlerionAPI.api.DeleteLayersAsync(toPersist.deletedLayers).AsUniTask(),
                    PlerionAPI.api.DeleteNodesAsync(toPersist.deletedNodes).AsUniTask(),
                    PlerionAPI.api.UpsertLayersAsync(toPersist.upsertedLayers).AsUniTask()
                        .ContinueWith(_ => PlerionAPI.api.UpsertNodesAsync(toPersist.upsertedNodes))
                );
            }

            _persistingChanges = false;

            await UniTask.SwitchToMainThread();
            UpdateHasUnsavedChangesIfNecessary();
        }

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
            public List<NodeModel> upsertedNodes;
            public List<LocalizationMapModel> upsertedMaps;
            public List<LayerModel> upsertedLayers;
            public List<Guid> deletedNodes;
            public List<Guid> deletedMaps;
            public List<Guid> deletedLayers;
        }
    }
}