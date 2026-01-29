using System;
using System.Threading.Tasks;
using MagicOnion;

namespace Outernet.Shared
{
    public interface ISyncedStateHub : IStreamingHub<ISyncedStateHub, ISyncedStateHubReceiver>
    {
        ValueTask<Guid> GetClientIDAsync(string userName);
        ValueTask<byte[]> JoinRoomAsync(string roomName);
        ValueTask LeaveRoomAsync();
        ValueTask SendRoomStateDeltaAsync(byte[] deltaStateData);
    }

    public interface ISyncedStateHubReceiver
    {
        void OnReceiveRoomStateDelta(byte[] deltaStateData);
    }
}
