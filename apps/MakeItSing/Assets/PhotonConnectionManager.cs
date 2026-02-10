using UnityEngine;

using System;
using System.Threading;

using Cysharp.Threading.Tasks;

using FofX;
using FofX.Stateful;

using Photon.Realtime;
using Photon.Client;

namespace Plerion.MakeItSing
{
    public class ConnectionManager : IDisposable
    {
        private ConnectionState _connectionState;
        private Func<string, CancellationToken, UniTask> _connectMethod;
        private Func<CancellationToken, UniTask> _disconnectMethod;
        private TaskHandle _connectionTask = TaskHandle.Complete;

        public ConnectionManager(ConnectionState connectionState, Func<string, CancellationToken, UniTask> connectMethod, Func<CancellationToken, UniTask> disconnectMethod)
        {
            _connectionState = connectionState;
            _connectMethod = connectMethod;
            _disconnectMethod = disconnectMethod;

            connectionState.context.RegisterObserver(
                HandleShouldBeConnectedChanged,
                _connectionState.shouldBeConnected,
                _connectionState.connected
            );
        }

        private void HandleShouldBeConnectedChanged(NodeChangeEventArgs args)
        {
            _connectionTask.Cancel();

            if (_connectionState.shouldBeConnected.value)
            {
                _connectionTask = TaskHandle.Execute(Connect);
            }
            else
            {
                _connectionTask = TaskHandle.Execute(Disconnect);
            }
        }

        private async UniTask Connect(CancellationToken cancellationToken = default)
        {
            if (_connectionState.status.value == ConnectionStatus.Connected)
                return;

            _connectionState.ExecuteActionOrDelay(new SetConnectionStatusAction(ConnectionStatus.Connecting));

            try
            {
                await _connectMethod(_connectionState.connectionString.value, cancellationToken);
            }
            catch (Exception exc)
            {
                await UniTask.SwitchToMainThread();
                _connectionState.ExecuteAction(new SetConnectionStatusAction(ConnectionStatus.Error, exc.Message));

                throw;
            }

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);
            _connectionState.ExecuteAction(new SetConnectionStatusAction(ConnectionStatus.Connected));
        }

        private async UniTask Disconnect(CancellationToken cancellationToken = default)
        {
            if (_connectionState.status.value == ConnectionStatus.Disconnected ||
                _connectionState.status.value == ConnectionStatus.Error)
            {
                return;
            }

            _connectionState.ExecuteActionOrDelay(new SetConnectionStatusAction(ConnectionStatus.Disconnecting));

            try
            {
                await _disconnectMethod(cancellationToken);
            }
            catch (Exception exc)
            {
                await UniTask.SwitchToMainThread();
                _connectionState.ExecuteAction(new SetConnectionStatusAction(ConnectionStatus.Error, exc.Message));

                throw;
            }

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);
            _connectionState.ExecuteAction(new SetConnectionStatusAction(ConnectionStatus.Disconnected));
        }

        public void Dispose()
        {
            _connectionTask.Cancel();
            _connectionState.context.DeregisterObserver(HandleShouldBeConnectedChanged);
        }
    }

    public class PhotonConnectionManager : MonoBehaviour, IInRoomCallbacks, IOnEventCallback
    {
        private RealtimeClient _client;
        private ConnectionManager _nameserverConnection;
        private ConnectionManager _roomConnection;

        private void Awake()
        {
            AsyncSetup.Startup();

            _client = new RealtimeClient(ConnectionProtocol.Tcp);
            _client.AddCallbackTarget(this);

            _nameserverConnection = new ConnectionManager(
                App.state.nameServerConnection,
                (appID, _) => _client.ConnectUsingSettingsAsync(new AppSettings() { AppIdRealtime = appID }).AsUniTask(),
                _ => _client.DisconnectAsync().AsUniTask()
            );

            _roomConnection = new ConnectionManager(
                App.state.roomConnection,
                (roomID, _) => _client.ConnectToRoomAsync(new MatchmakingArguments() { RoomName = roomID, PhotonSettings = _client.AppSettings }).AsUniTask(),
                _ => _client.LeaveRoomAsync().AsUniTask()
            );
        }

        private void Update()
        {
            while (true)
            {
                if (!_client.DispatchIncomingCommands())
                    break;
            }
        }

        private void LateUpdate()
        {
            while (true)
            {
                if (!_client.SendOutgoingCommands())
                    break;
            }
        }

        private void OnDestroy()
        {
            _nameserverConnection.Dispose();
            _roomConnection.Dispose();
        }

        // IInRoomCallbacks
        public void OnPlayerEnteredRoom(Player newPlayer)
        {

        }

        public void OnPlayerLeftRoom(Player otherPlayer)
        {
        }

        public void OnPlayerPropertiesUpdate(Player targetPlayer, PhotonHashtable changedProps)
        {

        }

        public void OnMasterClientSwitched(Player newMasterClient)
        {
            App.state.isMasterClient.ExecuteSet(newMasterClient.ActorNumber == _client.LocalPlayer.ActorNumber);
        }

        public void OnRoomPropertiesUpdate(PhotonHashtable propertiesThatChanged) { }

        // IOnEventCallback
        public void OnEvent(EventData photonEvent)
        {
        }
    }
}