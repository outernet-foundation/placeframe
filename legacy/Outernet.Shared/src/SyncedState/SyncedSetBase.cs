// https://github.com/dotnet/project-system/issues/5551
#nullable enable

using System;
using System.Collections.Generic;
using System.Linq;
using MessagePack;
using static Outernet.Shared.Assert;

namespace Outernet.Shared
{
    public abstract class SyncedSetBase<T, TDerived, TDerivedInitializationData>
        : SyncedObject<TDerived, TDerivedInitializationData>
        where TDerived : SyncedSetBase<T, TDerived, TDerivedInitializationData>
    {
        protected struct Tag
        {
            public Guid addingClientID;
            public uint addTick;

            public Tag(Guid addingClientID, uint addTick)
            {
                this.addingClientID = addingClientID;
                this.addTick = addTick;
            }
        }


        private class RemoveOperation
        {
            public T key;
            public Tag tag;
            public Guid removingClientID;

            public RemoveOperation(T key, Tag tag, Guid removingClientID)
            {
                this.key = key;
                this.tag = tag;
                this.removingClientID = removingClientID;
            }
        }

        private readonly Dictionary<T, Tag> tags = new Dictionary<T, Tag>();
        private readonly HashSet<T> addOperations = new HashSet<T>();
        private readonly HashSet<RemoveOperation> removeOperations = new HashSet<RemoveOperation>();

        public SyncedSetBase(SyncedStateSystem syncedStateSystem) : base(syncedStateSystem) { }

        protected Tag GetTag(T key) => tags[key];
        protected bool AddedThisTick(T key) => addOperations.Contains(key);

        protected void UpdateDeltaForAddBase(T key)
        {
            // TODO: Upadte this comment, we also already modified tags if we are deserializing
            // Deserialization should not update the local delta
            if (syncedStateSystem.Deserializing) return;

            ASSERT(
                !tags.ContainsKey(key),
                "Tag already existed for key when SyncedDictionary.UpdateDeltaForAdd() was called"
            );

            // Add a tag for this key
            tags.Add(key, new Tag(syncedStateSystem.ClientID!.Value, syncedStateSystem.Tick));

            // Update the delta
            addOperations.Add(key);
        }

        protected void UpdateDeltaForRemoveBase(T key)
        {
            // TODO: Upadte this comment, we also already modified tags if we are deserializing
            // Deserialization should not update the delta
            if (syncedStateSystem.Deserializing) return;

            ASSERT(
                tags.ContainsKey(key),
                "Tag did not exist for key when SyncedDictionary.UpdateDeltaForRemove() was called"
            );

            var tag = tags[key];

            // Remove the tag for this key
            tags.Remove(key);

            // If the entry was added this tick, remove the add operation
            addOperations.Remove(key);

            // Update the delta
            removeOperations.Add(new RemoveOperation(key, tag, syncedStateSystem.ClientID!.Value));
        }

        // Full serialization happens on the client only during delta serialization when this
        // dictionary was added to it's parent during the current tick
        public override void Serialize(ref MessagePackWriter writer)
        {
            writer.WriteArrayHeader(Count);
            foreach (var tag in tags)
            {
                MessagePackSerializer.Serialize(ref writer, tag.Key);
                MessagePackSerializer.Serialize(ref writer, tag.Value.addingClientID);
                MessagePackSerializer.Serialize(ref writer, tag.Value.addTick);
                SerializeValue(ref writer, tag.Key);
            }
        }

        public override void Deserialize(ref MessagePackReader reader)
        {
            // Deserialize assumes that the set is empty and has no delta
            ASSERT(
                Count == 0,
                "SyncedDictionary.Deserialize() was called on a non-empty dictionary"
            );
            ASSERT(
                addOperations.Count == 0,
                "SyncedDictionary.Deserialize() was called on a dictionary with add operations"
            );
            ASSERT(
                removeOperations.Count == 0,
                "SyncedDictionary.Deserialize() was called on a dictionary with remove operations"
            );
            ASSERT(
                tags.Count == 0,
                "SyncedDictionary.Deserialize() was called on a dictionary with keys"
            );

            var count = reader.ReadArrayHeader();
            for (var i = 0; i < count; i++)
            {
                var key = MessagePackSerializer.Deserialize<T>(ref reader);
                var addingClientID = MessagePackSerializer.Deserialize<Guid>(ref reader);
                var addTick = MessagePackSerializer.Deserialize<uint>(ref reader);
                tags.Add(key, new Tag(addingClientID, addTick));
                AddEntry(ref reader, key);
            }
        }

        protected void SerializeDeltaBase(ref MessagePackWriter writer)
        {
            // During deserialization, remove operations must be performed before add operations, so
            // serialize them first
            writer.WriteArrayHeader(removeOperations.Count());
            foreach (var removeOperation in removeOperations)
            {
                MessagePackSerializer.Serialize(ref writer, removeOperation.key);
                MessagePackSerializer.Serialize(ref writer, removeOperation.tag.addingClientID);
                MessagePackSerializer.Serialize(ref writer, removeOperation.tag.addTick);
                MessagePackSerializer.Serialize(ref writer, removeOperation.removingClientID);
            }

            writer.WriteArrayHeader(addOperations.Count());
            foreach (var key in addOperations)
            {
                MessagePackSerializer.Serialize(ref writer, key);
                MessagePackSerializer.Serialize(ref writer, tags[key].addingClientID);
                MessagePackSerializer.Serialize(ref writer, tags[key].addTick);
                SerializeValue(ref writer, key);
            }
        }

        protected void DeserializeDeltaBase(ref MessagePackReader reader)
        {
            // Apply remove operations
            var count = reader.ReadArrayHeader();
            for (var i = 0; i < count; i++)
            {
                var key = MessagePackSerializer.Deserialize<T>(ref reader);
                var addingClientID = MessagePackSerializer.Deserialize<Guid>(ref reader);
                var addTick = MessagePackSerializer.Deserialize<uint>(ref reader);
                var removingClientID = MessagePackSerializer.Deserialize<Guid>(ref reader);

                // If we are the removing client, we don't need to remove the entry
                if (removingClientID == syncedStateSystem.ClientID)
                {
                    continue;
                }

                // Can't remove something that's already been removed
                if (!ContainsKey(key) || tags[key].addingClientID != addingClientID || tags[key].addTick != addTick)
                {
                    continue;
                }

                RemoveEntry(key);
                tags.Remove(key);

                if (syncedStateSystem.ClientID == Guid.Empty)
                {
                    addOperations.Remove(key);
                    removeOperations.Add(new RemoveOperation(key, new Tag(addingClientID, addTick), removingClientID));
                }
            }

            // Apply add operations
            count = reader.ReadArrayHeader();
            for (var i = 0; i < count; i++)
            {
                var key = MessagePackSerializer.Deserialize<T>(ref reader);
                var addingClientID = MessagePackSerializer.Deserialize<Guid>(ref reader);
                var addTick = MessagePackSerializer.Deserialize<uint>(ref reader);

                // If we are the adding client, we don't need to add the entry
                if (addingClientID == syncedStateSystem.ClientID)
                {
                    DeserializeAndDiscardValue(ref reader);
                    continue;
                }

                if (ContainsKey(key))
                {
                    // We have conflicting add operations; resolve with the server's entry, which is
                    // always the earlier one

                    if (syncedStateSystem.ClientID == Guid.Empty)
                    {
                        // If we are the server, just deserialize and discard the conflicting add
                        // operation, and continue to the next add operation
                        DeserializeAndDiscardValue(ref reader);
                        continue;
                    }

                    // If we are a non-server client, remove our entry so we can replace it with the
                    // server's earlier entry
                    RemoveEntry(key);
                    tags.Remove(key);
                }

                AddEntry(ref reader, key);
                tags.Add(key, new Tag(addingClientID, addTick));

                if (syncedStateSystem.ClientID == Guid.Empty)
                {
                    addOperations.Add(key);
                }
            }
        }

        protected void ClearDeltaBase()
        {
            addOperations.Clear();
            removeOperations.Clear();
        }

        public abstract int Count { get; }
        public abstract bool ContainsKey(T key);
        protected abstract IEnumerable<T> GetKeys();
        protected abstract void AddEntry(ref MessagePackReader reader, T key);
        protected abstract void RemoveEntry(T key);
        protected abstract void SerializeValue(ref MessagePackWriter writer, T key);
        protected abstract void DeserializeAndDiscardValue(ref MessagePackReader reader);
    }
}
