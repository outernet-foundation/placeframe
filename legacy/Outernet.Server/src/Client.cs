using MagicOnion.Server.Hubs;
using Outernet.Shared;

namespace Outernet.Server
{
    class Client(Guid connectionID, IGroup<ISyncedStateHubReceiver> group, TaskCompletionSource<byte[]> fullSerializationTaskCompletionSource, uint heartbeat)
    {
        public Guid connectionID = connectionID;
        public IGroup<ISyncedStateHubReceiver> group = group;
        public TaskCompletionSource<byte[]>? fullSerializationTaskCompletionSource = fullSerializationTaskCompletionSource;
        public uint heartbeat = heartbeat;
    }
}