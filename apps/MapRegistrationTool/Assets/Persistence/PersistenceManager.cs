using System;
using System.Collections.Generic;
using System.Linq;

using UnityEngine;

using FofX;
using FofX.Stateful;

using Cysharp.Threading.Tasks;
using UnityEditor;
using PlaceframeApiClient.Model;

namespace Placeframe.MapRegistrationTool
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
                App.state.locationContentLoaded
            );

            SystemMenu.AddMenuItem(
                "File/Save",
                () => App.state.saveRequested.ExecuteSet(true),
                validate: () => App.state.hasUnsavedChanges.value,
                commandKeys: new UnityEngine.InputSystem.Key[]
                {
                    Utility.GetPlatformCommandKey(),
                    UnityEngine.InputSystem.Key.S
                }
            );

            App.RegisterObserver(
                HandleSaveRequestedChanged,
                App.state.saveRequested
            );
        }

        private void OnDestroy()
        {
            _bindingsInitialized = false;
            _persistenceChangeTrackingBinding.Dispose();
        }

        private void HandleLocationContentLoadedChanged(NodeChangeEventArgs args)
        {
            if (!App.state.locationContentLoaded.value)
            {
                _bindingsInitialized = false;
                _nodePersistenceHelper.ClearChanges();
                _nodeGroupPersistenceHelper.ClearChanges();
                _mapPersistenceHelper.ClearChanges();
                _layerPersistenceHelper.ClearChanges();
                _persistenceChangeTrackingBinding.Dispose();
                App.state.hasUnsavedChanges.ExecuteSetOrDelay(false);
                return;
            }

            _persistenceChangeTrackingBinding = App.state.maps.Each(x => SetupPersistedObjectObserver(
                _mapPersistenceHelper,
                x.key,
                x.value,
                App.state.transforms[x.key]
            ));

            _bindingsInitialized = true;
        }

        private void HandleSaveRequestedChanged(NodeChangeEventArgs args)
        {
            if (args.initialize || !App.state.saveRequested.value)
                return;

            App.state.saveRequested.ExecuteSetOrDelay(false);
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
                insertedMaps = _mapPersistenceHelper.inserts.Select(Utility.ToMapCreate).ToList(),
                updatedMaps = _mapPersistenceHelper.updates.Select(Utility.ToMapUpdate).ToList(),
                deletedMaps = _mapPersistenceHelper.deletes.ToList()
            });

            _mapPersistenceHelper.ClearChanges();

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
                    toPersist.deletedMaps.Count != 0 ? App.API.DeleteLocalizationMapsAsync(toPersist.deletedMaps).AsUniTask() : UniTask.CompletedTask
                );
            }

            _persistingChanges = false;

            await UniTask.SwitchToMainThread();
            UpdateHasUnsavedChangesIfNecessary();
        }

        private UniTask CreateLocalizationMapsAsync(List<LocalizationMapCreate> localizationMaps)
            => UniTask.WhenAll(localizationMaps.Select(x => App.API.CreateLocalizationMapAsync(x).AsUniTask()));

        private void UpdateHasUnsavedChangesIfNecessary()
        {
            bool hasPendingChanges = _hasPendingChanges;
            if (App.state.hasUnsavedChanges.value != _hasPendingChanges &&
                !_settingHasPendingChanges)
            {
                _settingHasPendingChanges = true;
                App.state.hasUnsavedChanges.ExecuteSetOrDelay(
                    hasPendingChanges,
                    postObserverCallback: () => _settingHasPendingChanges = false
                );
            }
        }

        private class PersistenceData
        {
            public List<LocalizationMapCreate> insertedMaps;
            public List<LocalizationMapBatchUpdate> updatedMaps;
            public List<Guid> deletedMaps;
        }
    }
}