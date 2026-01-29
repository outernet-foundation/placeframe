using System.Collections.Generic;
using Outernet.Shared;

namespace Outernet.Client
{
    class OuternetHubReceiver : ISyncedStateHubReceiver
    {
        private readonly Queue<byte[]> pendingRemoteStateDeltas;

        public OuternetHubReceiver(Queue<byte[]> pendingRemoteStateDeltas)
        {
            this.pendingRemoteStateDeltas = pendingRemoteStateDeltas;
        }

        public void OnReceiveRoomStateDelta(byte[] deltaStateData)
        {
            pendingRemoteStateDeltas.Enqueue(deltaStateData);
        }
    }
}