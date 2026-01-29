using System;
using System.Runtime.CompilerServices;
using MessagePack;
using R3;
using static Outernet.Shared.Assert;

namespace Outernet.Shared
{
    public class SyncedProperty<T>
        : SyncedObject<SyncedProperty<T>, T>,
            IDisposable
    {
        private ReactiveProperty<T> property = new ReactiveProperty<T>();
        private readonly Subject<SyncedProperty<T>> subject = new Subject<SyncedProperty<T>>();
        private DisposableBag subscriptions;
        private Guid lastModifyingClientID;
        private uint lastModifyingClientTick;
        private bool awaitingAck = false;

        protected override IDisposable SubscribeCore(Observer<SyncedProperty<T>> observer)
        {
            observer.OnNext(this);
            // https://github.com/Cysharp/R3/issues/247
            return ObservableSubscribeExtensions.Subscribe(subject, observer.OnNext);
        }

        public SyncedProperty(SyncedStateSystem syncedStateSystem) : base(syncedStateSystem)
        {
            property
                .Subscribe(_ =>
                {
                    lastModifyingClientID = syncedStateSystem.ClientID.HasValue ? syncedStateSystem.ClientID.Value : Guid.Empty;
                    lastModifyingClientTick = syncedStateSystem.Tick;
                    subject.OnNext(this);
                })
                .AddTo(ref subscriptions);
        }

        public override void Initialize(T initializationData)
        {
            property.Value = initializationData;
        }

        public void Dispose()
        {
            // I have no idea how dispose is supposed to work with R3, fml
            subscriptions.Dispose();
            subject.Dispose();
            property.Dispose();
        }

        public T Value => property.Value;
        public void EnqueueSet(
            T value,
            [CallerMemberName] string caller = "unknown",
            [CallerFilePath] string filePath = "unknown",
            [CallerLineNumber] int lineNumber = 0)
        {
            if (value.Equals(property.Value)) return;
            syncedStateSystem.EnqueueAction(() => property.Value = value, caller, filePath, lineNumber);
        }

        public override void Serialize(ref MessagePackWriter writer)
        {
            MessagePackSerializer.Serialize(ref writer, Value);
        }

        public override void Deserialize(ref MessagePackReader reader)
        {
            property.Value = MessagePackSerializer.Deserialize<T>(ref reader);
        }

        public override void SerializeDelta(ref MessagePackWriter writer)
        {
            if (syncedStateSystem.ClientID != Guid.Empty)
            {
                ASSERT(lastModifyingClientID == syncedStateSystem.ClientID, "Serializing delta on client but lastModifyClientID is not self");

                awaitingAck = true;
            }

            MessagePackSerializer.Serialize(ref writer, Value);
            MessagePackSerializer.Serialize(ref writer, lastModifyingClientID);
            MessagePackSerializer.Serialize(ref writer, lastModifyingClientTick);
        }

        public override void DeserializeDelta(ref MessagePackReader reader)
        {
            var value = MessagePackSerializer.Deserialize<T>(ref reader);
            var modifyingClientID = MessagePackSerializer.Deserialize<Guid>(ref reader);
            var modifyingClientTick = MessagePackSerializer.Deserialize<uint>(ref reader);

            if (syncedStateSystem.ClientID == Guid.Empty ||
                !awaitingAck)
            {
                property.Value = value;
                lastModifyingClientID = modifyingClientID;
                lastModifyingClientTick = modifyingClientTick;
                return;
            }

            ASSERT(lastModifyingClientID == syncedStateSystem.ClientID, "awaiting ack but last modifying client is not self");

            if (modifyingClientID == lastModifyingClientID && modifyingClientTick == lastModifyingClientTick)
            {
                awaitingAck = false;
            }
        }

        public override void ClearDelta() { }
    }
}