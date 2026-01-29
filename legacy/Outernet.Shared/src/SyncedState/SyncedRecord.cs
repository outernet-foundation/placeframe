using System;
using System.Collections;
using MessagePack;
using R3;

namespace Outernet.Shared
{
    public abstract class SyncedRecord<TDerived, TDerivedInitializationData, FieldCount>
        : SyncedObject<TDerived, TDerivedInitializationData>,
          IDisposable
        where TDerived : SyncedRecord<TDerived, TDerivedInitializationData, FieldCount>
        where FieldCount : IIntLiteral, new()
    {
        private readonly BitArray dirtyFlags = new BitArray(new FieldCount().Literal);
        private readonly Subject<TDerived> subject = new Subject<TDerived>();
        private DisposableBag subscriptions;

        public SyncedRecord(SyncedStateSystem syncedStateSystem) : base(syncedStateSystem) { }

        //--------------------------//
        // Delta subscription logic //
        //--------------------------//

        public void SetupDeltaSubscription<T>(Observable<T> observable, int key)
        {
            observable
                .Subscribe(_ => UpdateDeltaForChange(key))
                .AddTo(ref subscriptions);
        }

        private void UpdateDeltaForChange(int key)
        {
            // Notify subscribers to this record that it has changed
            subject.OnNext((TDerived)this);

            // Deserialization should not update the local delta
            if (syncedStateSystem.Deserializing) return;

            dirtyFlags.Set(key, true);
        }

        //----------------------------//
        // IDisposable implementation //
        //----------------------------//

        public void Dispose()
        {
            DisposeGenerated();
            subscriptions.Dispose();
            subject.Dispose();
        }

        //---------------------------//
        // Observable implementation //
        //---------------------------//

        protected override IDisposable SubscribeCore(Observer<TDerived> observer)
        {
            observer.OnNext((TDerived)this);
            // https://github.com/Cysharp/R3/issues/247
            return ObservableSubscribeExtensions.Subscribe(subject, observer.OnNext);
        }

        //------------------------//
        // ISynced implementation //
        //------------------------//

        public override void SerializeDelta(ref MessagePackWriter writer)
        {
            int setBitsCount = dirtyFlags.NumSetBits();
            writer.WriteMapHeader(setBitsCount);

            for (int key = 0; key < dirtyFlags.Length; key++)
            {
                if (!dirtyFlags.Get(key)) continue;

                writer.Write(key);
                SerializeDeltaGenerated(ref writer, key);
            }
        }

        public override void DeserializeDelta(
            ref MessagePackReader reader)
        {
            int count = reader.ReadMapHeader();
            for (int i = 0; i < count; i++)
            {
                var key = reader.ReadInt32();
                DeserializeDeltaGenerated(ref reader, key);

                if (syncedStateSystem.ClientID == Guid.Empty)
                {
                    dirtyFlags.Set(key, true);
                }
            }
        }

        public override void ClearDelta()
        {
            dirtyFlags.SetAll(false);
            ClearDeltaGenerated();
        }

        //---------------------------------------------------//
        // Abstract functions implemented by code generation //
        //---------------------------------------------------//

        protected abstract void DisposeGenerated();
        protected abstract void SerializeDeltaGenerated(ref MessagePackWriter writer, int key);
        protected abstract void DeserializeDeltaGenerated(ref MessagePackReader reader, int key);
        protected abstract void ClearDeltaGenerated();
    }
}
