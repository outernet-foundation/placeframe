// https://github.com/dotnet/project-system/issues/5551
#nullable enable

// This check can't seem to see through the indirection to SetupDeltaSubscriptions
#pragma warning disable CS8618

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using MessagePack;
using ObservableCollections;
using R3;

namespace Outernet.Shared
{
    public partial class SyncedDictionary<TKey, TValue, TValueInitializationData>
        : SyncedSetBase<TKey, SyncedDictionary<TKey, TValue, TValueInitializationData>, Dictionary<TKey, TValueInitializationData>>,
            IEnumerable<KeyValuePair<TKey, TValue>>,
            IEnumerable,
            IObservableCollection<KeyValuePair<TKey, TValue>>
        where TKey : notnull
        where TValue : SyncedObject<TValue, TValueInitializationData>, IDisposable
        where TValueInitializationData : new()
    {
        private readonly ObservableDictionary<TKey, TValue> dictionary = new ObservableDictionary<TKey, TValue>();
        private readonly Func<SyncedStateSystem, TValue> valueFactory;
        private readonly HashSet<TKey> changeOperations = new HashSet<TKey>();

        //-------------------------------//
        // Delta subscription management //
        //-------------------------------//

        private readonly Subject<SyncedDictionary<TKey, TValue, TValueInitializationData>> subject = new Subject<SyncedDictionary<TKey, TValue, TValueInitializationData>>();
        private IDisposable observeAddSubscription;
        private IDisposable observeRemoveSubscription;
        private readonly Dictionary<TKey, IDisposable> observeChangeSubscriptions = new Dictionary<TKey, IDisposable>();

        public SyncedDictionary(SyncedStateSystem syncedStateSystem, Func<SyncedStateSystem, TValue> valueFactory)
            : base(syncedStateSystem)
        {
            this.valueFactory = valueFactory;
            observeAddSubscription = this.ObserveAdd().Subscribe(addEvent => UpdateDeltaForAdd(addEvent.Value));
            observeRemoveSubscription = this.ObserveRemove().Subscribe(removeEvent => UpdateDeltaForRemove(removeEvent.Value));
        }

        public override void Initialize(Dictionary<TKey, TValueInitializationData> initializationData)
        {
            foreach (var kvp in initializationData)
            {
                var value = valueFactory(syncedStateSystem);
                value.Initialize(kvp.Value);
                dictionary.Add(kvp.Key, value);
            }
        }

        private void UpdateDeltaForAdd(KeyValuePair<TKey, TValue> kvp)
        {
            UpdateDeltaForAddBase(kvp.Key);

            // Subscribe to changes to this value, so we can track it in the set of change
            // operations, and update subscribers to this dictionary when the value changes
            var subscription = kvp.Value.Subscribe(_ => UpdateDeltaForChange(kvp.Key));
            observeChangeSubscriptions.Add(kvp.Key, subscription);

            // Notify subscribers to this dictionary that it has changed
            subject.OnNext(this);
        }

        private void UpdateDeltaForRemove(KeyValuePair<TKey, TValue> kvp)
        {
            UpdateDeltaForRemoveBase(kvp.Key);

            // Dispose the change subscription
            observeChangeSubscriptions[kvp.Key].Dispose();
            observeChangeSubscriptions.Remove(kvp.Key);

            // Dispose the value
            kvp.Value.Dispose();

            // Notify subscribers to this dictionary that it has changed
            subject.OnNext(this);

            // Deserialization should not update the local delta
            if (syncedStateSystem.Deserializing) return;

            // If the entry wad changed this tick, remove the change operation
            changeOperations.Remove(kvp.Key);
        }

        private void UpdateDeltaForChange(TKey key)
        {
            // Notify subscribers to this dictionary that it has changed
            subject.OnNext(this);

            // Deserialization should not update the local delta, and if this key was added this
            // tick, we are already tracking it with an add operation
            if (syncedStateSystem.Deserializing || AddedThisTick(key)) return;

            // Update the delta
            changeOperations.Add(key);
        }

        //----------------------------//
        // IDisposable implementation //
        //----------------------------//

        public void Dispose()
        {
            observeAddSubscription.Dispose();
            observeRemoveSubscription.Dispose();
            foreach (var subscription in observeChangeSubscriptions.Values)
            {
                subscription.Dispose();
            }
            subject.Dispose();
        }

        //---------------------------//
        // Observable implementation //
        //---------------------------//

        protected override IDisposable SubscribeCore(Observer<SyncedDictionary<TKey, TValue, TValueInitializationData>> observer)
        {
            observer.OnNext(this);
            // https://github.com/Cysharp/R3/issues/247
            return ObservableSubscribeExtensions.Subscribe(subject, observer.OnNext);
        }

        //------------------------//
        // ISynced implementation //
        //------------------------//

        public override void SerializeDelta(ref MessagePackWriter writer)
        {
            SerializeDeltaBase(ref writer);

            writer.WriteArrayHeader(changeOperations.Count());
            foreach (var key in changeOperations)
            {
                MessagePackSerializer.Serialize(ref writer, key);
                MessagePackSerializer.Serialize(ref writer, GetTag(key).addingClientID);
                MessagePackSerializer.Serialize(ref writer, GetTag(key).addTick);
                dictionary[key].SerializeDelta(ref writer);
            }
        }

        public override void DeserializeDelta(ref MessagePackReader reader)
        {
            DeserializeDeltaBase(ref reader);

            // Apply change operations
            var count = reader.ReadArrayHeader();
            for (var i = 0; i < count; i++)
            {
                var key = MessagePackSerializer.Deserialize<TKey>(ref reader);
                var addingClientID = MessagePackSerializer.Deserialize<Guid>(ref reader);
                var addTick = MessagePackSerializer.Deserialize<uint>(ref reader);

                if (!ContainsKey(key) || GetTag(key).addingClientID != addingClientID || GetTag(key).addTick != addTick)
                {
                    // If this tag was removed, just deserialize and discard the delta
                    //
                    // TODO: This is presumably an inefficient way to do this; should probably just
                    // intelligently skip the serialized delta instead
                    valueFactory(syncedStateSystem).DeserializeDelta(ref reader);

                    continue;
                }

                dictionary[key].DeserializeDelta(ref reader);

                if (syncedStateSystem.ClientID == Guid.Empty)
                {
                    changeOperations.Add(key);
                }
            }
        }
        public override void ClearDelta()
        {
            ClearDeltaBase();
            changeOperations.Clear();
            foreach (var value in Values)
            {
                value.ClearDelta();
            }
        }

        // -----------------------------//
        // SyncedSetBase implementation //
        //------------------------------//

        public override int Count => dictionary.Count;
        public override bool ContainsKey(TKey key) => dictionary.ContainsKey(key);
        protected override IEnumerable<TKey> GetKeys() => Keys;

        protected override void AddEntry(ref MessagePackReader reader, TKey key)
        {
            var value = valueFactory(syncedStateSystem);
            value.Deserialize(ref reader);
            dictionary.Add(key, value);
        }

        protected override void RemoveEntry(TKey key)
        {
            dictionary.Remove(key);
            changeOperations.Remove(key);
        }

        protected override void SerializeValue(ref MessagePackWriter writer, TKey key) =>
            dictionary[key].Serialize(ref writer);

        protected override void DeserializeAndDiscardValue(ref MessagePackReader reader) =>
            valueFactory(syncedStateSystem).Deserialize(ref reader);

        //------------------------------------------------------------------//
        // Thin wrappers around ObservableDictionary methods and properties //
        //------------------------------------------------------------------//

        public event NotifyCollectionChangedEventHandler<KeyValuePair<TKey, TValue>>? CollectionChanged
        {
            add => dictionary.CollectionChanged += value;
            remove => dictionary.CollectionChanged -= value;
        }

        public ICollection<TKey> Keys => ((IDictionary<TKey, TValue>)dictionary).Keys;
        public ICollection<TValue> Values => ((IDictionary<TKey, TValue>)dictionary).Values;
        public TValue Get(TKey key) => dictionary[key];
        public bool TryGetValue(TKey key, out TValue value) => dictionary.TryGetValue(key, out value!);
        public bool Contains(KeyValuePair<TKey, TValue> item) => dictionary.Contains(item);

        // TODO BUG: Need to keep track of enqueued operations to prevent duplicate operations
        // TODO: make enqueuadd awaitable with and return value

        public void EnqueueAdd(
            TKey key,
            TValueInitializationData initializationData,
            [CallerMemberName] string caller = "unknown",
            [CallerFilePath] string filePath = "unknown",
            [CallerLineNumber] int lineNumber = 0)
        {
            if (dictionary.ContainsKey(key)) throw new ArgumentException($"Key {key} already exists in dictionary");

            var value = valueFactory(syncedStateSystem);
            value.Initialize(initializationData);
            syncedStateSystem.EnqueueAction(() => dictionary.Add(key, value), caller, filePath, lineNumber);
        }

        public void EnqueueAdd(
            TKey key,
            [CallerMemberName] string caller = "unknown",
            [CallerFilePath] string filePath = "unknown",
            [CallerLineNumber] int lineNumber = 0)
        {
            if (dictionary.ContainsKey(key)) throw new ArgumentException($"Key {key} already exists in dictionary");

            var value = valueFactory(syncedStateSystem);
            syncedStateSystem.EnqueueAction(() => dictionary.Add(key, value), caller, filePath, lineNumber);
        }

        public void EnqueueRemove(
            TKey key,
            [CallerMemberName] string caller = "unknown",
            [CallerFilePath] string filePath = "unknown",
            [CallerLineNumber] int lineNumber = 0)
        {
            if (!dictionary.ContainsKey(key)) throw new KeyNotFoundException($"Key {key} not found in dictionary");

            syncedStateSystem.EnqueueAction(() => dictionary.Remove(key), caller, filePath, lineNumber);
        }

        public void EnqueueClear(
            [CallerMemberName] string caller = "unknown",
            [CallerFilePath] string filePath = "unknown",
            [CallerLineNumber] int lineNumber = 0)
        {
            // Enqueue individual remove actions (instead of a single clear action) to simplify
            // delta subscriptions
            foreach (var key in Keys)
            {
                EnqueueRemove(key, caller, filePath, lineNumber);
            }
        }

        //----------------------------------------//
        // IObserverableCollection implementation //
        //----------------------------------------//

        public object SyncRoot => dictionary.SyncRoot;
        public ISynchronizedView<KeyValuePair<TKey, TValue>, TView> CreateView<TView>(Func<KeyValuePair<TKey, TValue>, TView> transform, bool _ = false) => dictionary.CreateView(transform, _);

        //--------------------------------------------------------//
        // IEnumerable<KeyValuePair<TKey, TValue>> implementation //
        //--------------------------------------------------------//
        public IEnumerator<KeyValuePair<TKey, TValue>> GetEnumerator() => dictionary.GetEnumerator();

        //----------------------------//
        // IEnumerable implementation //
        //----------------------------//

        IEnumerator IEnumerable.GetEnumerator() => ((IEnumerable)dictionary).GetEnumerator();
    }
}
