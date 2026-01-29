using MessagePack;
using R3;

namespace Outernet.Shared
{
    public abstract class SyncedObject<T, TInitializationData>
        : Observable<T>
        where T : SyncedObject<T, TInitializationData>
    {
        protected SyncedStateSystem syncedStateSystem;
        public SyncedObject(SyncedStateSystem syncedStateSystem) => this.syncedStateSystem = syncedStateSystem;
        public abstract void Initialize(TInitializationData initializationData);
        public abstract void Serialize(ref MessagePackWriter writer);
        public abstract void Deserialize(ref MessagePackReader reader);
        public abstract void SerializeDelta(ref MessagePackWriter writer);
        public abstract void DeserializeDelta(ref MessagePackReader reader);
        public abstract void ClearDelta();
    }
}
