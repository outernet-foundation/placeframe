using MagicOnion.Server.Hubs;
using Outernet.Shared;

namespace Outernet.Server
{
    [Heartbeat(Interval = 10 * 1000, Timeout = 5 * 1000)]
    public class SyncedStateHub
        : StreamingHubBase<ISyncedStateHub, ISyncedStateHubReceiver>,
            ISyncedStateHub
    {
        string? userName = null;
        string? roomID = null;
        IGroup<ISyncedStateHubReceiver>? group = null;

        public ValueTask<Guid> GetClientIDAsync(string userName)
        {
            Assert.ASSERT(this.userName == null, "ClientID already set");

            this.userName = userName;

            return new ValueTask<Guid>(ConnectionId);
        }

        protected override ValueTask OnConnected()
        {
            Log.Info($"Connection {ConnectionId} established");
            base.OnConnected();
            return new ValueTask();
        }

        protected override ValueTask OnDisconnected()
        {
            try
            {
                // clientID should never be null here
                // if (clientID == null) throw new InvalidOperationException("clientID is null");

                // If this this disconnection was not expected, the client might still be in a room,
                // so remove them from it
                if (roomID != null)
                {
                    SyncedStateService.LeaveRoom(roomID, ConnectionId);

                    // We don't need to remove the client from the group here, because that happens
                    // automatically on disconnection
                    // await group.RemoveAsync(Context);
                }

                Log.Info($"Connection {ConnectionId} terminated");

                roomID = null;
                group = null;

                base.OnDisconnected();
            }
            catch (Exception exception)
            {
                Log.Error(exception, "OnDisconnected failed");
                throw;
            }

            return new ValueTask();
        }

        async ValueTask<byte[]> ISyncedStateHub.JoinRoomAsync(string roomID)
        {
            try
            {
                if (this.userName == null) throw new InvalidOperationException("userName is null");
                if (this.roomID != null) throw new InvalidOperationException($"Client {ConnectionId} attempted to join room {roomID} while already in room {this.roomID}");

                this.roomID = roomID;
                group = await Group.AddAsync(roomID);

                if (group == null) throw new InvalidOperationException($"ConnectionId {ConnectionId} disconnected while waiting to be added to group {roomID}");

                return await SyncedStateService.JoinRoom(roomID, userName, ConnectionId, group);
            }
            catch (Exception exception)
            {
                Log.Error(exception, "JoinRoomAsync failed");
                throw;
            }
        }

        async ValueTask ISyncedStateHub.LeaveRoomAsync()
        {
            try
            {
                // If this client is not in a room, throw an exception
                if (roomID == null) throw new InvalidOperationException("roomID is null");
                if (group == null) throw new InvalidOperationException("group is null");

                await group.RemoveAsync(Context);
                SyncedStateService.LeaveRoom(roomID, ConnectionId);

                group = null;
                roomID = null;
            }
            catch (Exception exception)
            {
                Log.Error(exception, "LeaveRoomAsync failed");
                throw;
            }
        }

        public ValueTask SendRoomStateDeltaAsync(byte[] deltaStateData)
        {
            try
            {
                // This function should never be called if the client is not in a room
                if (roomID == null) throw new AssertionFailedException("roomID is null");
                if (group == null) throw new AssertionFailedException("group is null");

                SyncedStateService.ReceiveRoomStateDelta(ConnectionId, deltaStateData, roomID);
            }
            catch (Exception exception)
            {
                Log.Error(exception, "SendRoomStateDeltaAsync failed");
                throw;
            }

            return new ValueTask();
        }
    }
}
