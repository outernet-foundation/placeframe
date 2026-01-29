// https://github.com/dotnet/project-system/issues/5551
#nullable enable

// This check can't seem to see through the indirection to SetupDeltaSubscriptions
#pragma warning disable CS8618

using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using MessagePack;
using ObservableCollections;
using R3;

namespace Outernet.Shared
{
    public class SyncedSet<T>
        : SyncedSetBase<T, SyncedSet<T>, HashSet<T>>,
            IEnumerable<T>,
            IEnumerable,
            IReadOnlyCollection<T>,
            IObservableCollection<T>,
            IDisposable
        where T : notnull
    {
        private readonly ObservableHashSet<T> set = new ObservableHashSet<T>();

        //-------------------------------//
        // Delta subscription management //
        //-------------------------------//

        private readonly Subject<SyncedSet<T>> subject = new Subject<SyncedSet<T>>();
        private IDisposable observeAddSubscription;
        private IDisposable observeRemoveSubscription;

        public SyncedSet(SyncedStateSystem syncedStateSystem) : base(syncedStateSystem)
        {
            observeAddSubscription = this.ObserveAdd().Subscribe(addEvent => UpdateDeltaForAdd(addEvent.Value));
            observeRemoveSubscription = this.ObserveRemove().Subscribe(removeEvent => UpdateDeltaForRemove(removeEvent.Value));
        }

        public override void Initialize(HashSet<T> initializationData)
        {
            foreach (var item in initializationData)
            {
                set.Add(item);
            }
        }

        public HashSet<T> GetItems()
        {
            return new HashSet<T>(set);
        }

        private void UpdateDeltaForAdd(T item)
        {
            UpdateDeltaForAddBase(item);

            // Notify subscribers that the set has changed
            subject.OnNext(this);
        }

        private void UpdateDeltaForRemove(T item)
        {
            UpdateDeltaForRemoveBase(item);

            // Notify subscribers that the set has changed
            subject.OnNext(this);
        }

        //----------------------------//
        // IDisposable implementation //
        //----------------------------//

        public void Dispose()
        {
            observeAddSubscription.Dispose();
            observeRemoveSubscription.Dispose();
            subject.Dispose();
        }

        //---------------------------//
        // Observable implementation //
        //---------------------------//

        protected override IDisposable SubscribeCore(Observer<SyncedSet<T>> observer)
        {
            observer.OnNext(this);
            // https://github.com/Cysharp/R3/issues/247
            return ObservableSubscribeExtensions.Subscribe(subject, observer.OnNext);
        }

        //------------------------//
        // ISynced implementation //
        //------------------------//

        public override void SerializeDelta(ref MessagePackWriter writer) => SerializeDeltaBase(ref writer);
        public override void DeserializeDelta(ref MessagePackReader reader) => DeserializeDeltaBase(ref reader);
        public override void ClearDelta() => ClearDeltaBase();

        // -----------------------------//
        // SyncedSetBase implementation //
        //------------------------------//

        public override int Count => set.Count;
        public override bool ContainsKey(T key) => set.Contains(key);
        protected override IEnumerable<T> GetKeys() => set;
        protected override void AddEntry(ref MessagePackReader reader, T key) => set.Add(key);
        protected override void RemoveEntry(T key) => set.Remove(key);
        protected override void SerializeValue(ref MessagePackWriter writer, T key) { /* No value to serialize */ }
        protected override void DeserializeAndDiscardValue(ref MessagePackReader reader) { /* No value to deserialize */ }

        //---------------------------------------------------------------//
        // Thin wrappers around ObservableHashSet methods and properties //
        //---------------------------------------------------------------//

        public event NotifyCollectionChangedEventHandler<T>? CollectionChanged
        {
            add => set.CollectionChanged += value;
            remove => set.CollectionChanged -= value;
        }

        public bool Contains(T item) => set.Contains(item);

        public void EnqueueAdd(
            T item,
            [CallerMemberName] string caller = "unknown",
            [CallerFilePath] string filePath = "unknown",
            [CallerLineNumber] int lineNumber = 0)
        {
            if (set.Contains(item)) throw new InvalidOperationException($"Item {item} already exists in set");

            syncedStateSystem.EnqueueAction(() => set.Add(item), caller, filePath, lineNumber);
        }

        public void EnqueueRemove(
            T item,
            [CallerMemberName] string caller = "unknown",
            [CallerFilePath] string filePath = "unknown",
            [CallerLineNumber] int lineNumber = 0)
        {
            if (!set.Contains(item)) throw new InvalidOperationException($"Item {item} does not exist in set");

            syncedStateSystem.EnqueueAction(() => set.Remove(item), caller, filePath, lineNumber);
        }

        public void EnqueueClear(
            [CallerMemberName] string caller = "unknown",
            [CallerFilePath] string filePath = "unknown",
            [CallerLineNumber] int lineNumber = 0)
        {
            // Enqueue individual remove actions (instead of a single clear action) to simplify
            // delta subscriptions
            foreach (var item in set)
            {
                EnqueueRemove(item, caller, filePath, lineNumber);
            }
        }

        //----------------------------------------//
        // IObserverableCollection implementation //
        //----------------------------------------//

        public object SyncRoot => set.SyncRoot;
        public ISynchronizedView<T, TView> CreateView<TView>(Func<T, TView> transform, bool _ = false) => set.CreateView(transform, _);

        //-------------------------------//
        // IEnumerable<T> implementation //
        //-------------------------------//

        public IEnumerator<T> GetEnumerator() => set.GetEnumerator();

        //----------------------------//
        // IEnumerable implementation //
        //----------------------------//

        IEnumerator IEnumerable.GetEnumerator() => set.GetEnumerator();
    }
}