using UnityEngine;

using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;

using Cysharp.Threading.Tasks;

using FofX;
using FofX.Stateful;

using Photon.Realtime;
using Photon.Client;

using SimpleJSON;
using System.Collections.Generic;
using ObserveThing;
using System.Threading.Tasks;
using Outernet.Logging;

namespace Plerion.MakeItSing
{
    public class ConnectionManager : IDisposable
    {
        private ConnectionState _connectionState;
        private Func<string, CancellationToken, UniTask> _connectMethod;
        private Func<CancellationToken, UniTask> _disconnectMethod;

        private IDisposable _subscription;
        private TaskHandle _connectionTask = TaskHandle.Complete;
        private bool _reconnecting;

        public ConnectionManager(ConnectionState connectionState, Func<string, CancellationToken, UniTask> connectMethod, Func<CancellationToken, UniTask> disconnectMethod)
        {
            _connectionState = connectionState;
            _connectMethod = connectMethod;
            _disconnectMethod = disconnectMethod;

            _subscription = StateObservables.SubscribeOperations(HandleConnectionStatusChanged, connectionState.status, connectionState.shouldBeConnected);
        }

        private void HandleConnectionStatusChanged(IReadOnlyList<IStateOperation> ops)
        {
            if (_connectionState.shouldBeConnected.value)
            {
                if (_reconnecting)
                    return;

                if (_connectionState.status.value == ConnectionStatus.Disconnected)
                    _connectionTask = TaskHandle.Execute(Connect);

                if (_connectionState.status.value == ConnectionStatus.Error)
                    _connectionTask = TaskHandle.Execute(Reconnect);
            }
            else if (_connectionState.status.value == ConnectionStatus.Connected)
            {
                _connectionTask = TaskHandle.Execute(Disconnect);
            }
        }

        private async UniTask Reconnect(CancellationToken cancellationToken = default)
        {
            _reconnecting = true;

            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    await Connect(cancellationToken);
                    break;
                }
                catch (Exception exc)
                {
                    if (exc is TaskCanceledException)
                        break;

                    Log<LogGroup>.Error(LogGroup.PhotonConnection, exc);
                }

                try
                {
                    await UniTask.WaitForSeconds(3f, cancellationToken: cancellationToken);
                }
                catch (Exception exc)
                {
                    if (exc is TaskCanceledException)
                        break;

                    Log<LogGroup>.Error(LogGroup.PhotonConnection, exc);
                }
            }

            _reconnecting = false;
        }

        private async UniTask Connect(CancellationToken cancellationToken = default)
        {
            if (_connectionState.status.value == ConnectionStatus.Connected)
                return;

            _connectionState.status.value = ConnectionStatus.Connecting;

            try
            {
                await _connectMethod(_connectionState.connectionString.value, cancellationToken);
            }
            catch (Exception exc)
            {
                await _disconnectMethod(cancellationToken);

                await UniTask.SwitchToMainThread();

                App.ExecuteTransaction(_ =>
                {
                    _connectionState.status.value = ConnectionStatus.Error;
                    _connectionState.error.value = exc.Message;
                });

                throw;
            }

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);
            _connectionState.status.value = ConnectionStatus.Connected;
        }

        private async UniTask Disconnect(CancellationToken cancellationToken = default)
        {
            if (_connectionState.status.value == ConnectionStatus.Disconnected ||
                _connectionState.status.value == ConnectionStatus.Error)
            {
                return;
            }

            _connectionState.status.value = ConnectionStatus.Disconnecting;

            try
            {
                await _disconnectMethod(cancellationToken);
            }
            catch (Exception exc)
            {
                await UniTask.SwitchToMainThread();

                App.ExecuteTransaction(_ =>
                {
                    _connectionState.status.value = ConnectionStatus.Error;
                    _connectionState.error.value = exc.Message;
                });

                throw;
            }

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);
            _connectionState.status.value = ConnectionStatus.Disconnected;
        }

        public void Dispose()
        {
            _connectionTask.Cancel();
            _subscription.Dispose();
        }
    }

    public class PhotonConnectionManager : MonoBehaviour, IInRoomCallbacks, IOnEventCallback, IConnectionCallbacks
    {
        private const byte INITIAL_SYNC_EVENT = 1;
        private const byte INCREMENTAL_SYNC_EVENT = 2;
        private const byte HIGH_FREQUENCY_SYNC_EVENT = 3;

        private RealtimeClient _client;
        private ConnectionManager _nameserverConnection;
        private ConnectionManager _roomConnection;

        private MemoryStream _incrementalSyncStream = new MemoryStream();
        private MemoryStream _highFrequencySyncStream = new MemoryStream();
        private PathIDCache<SceneState> _pathIDCache = new PathIDCache<SceneState>();

        private bool _inRoomAndSynchronized = false;
        private bool _applyingIncrementalSync = false;

        private List<HighFrequencySyncData> _highFrequencySyncData = new List<HighFrequencySyncData>();

        private class HighFrequencySyncData
        {
            public HighFrequencyPrimitiveData state;
            public IStateValue target;
            public float lastSyncTime;
            public bool isDirty;
            private IDisposable _subscription;

            public HighFrequencySyncData(HighFrequencyPrimitiveData state)
            {
                this.state = state;
                IStateNode objTarget = default;

                if (!state.root.TryFindChild(state.path, out objTarget))
                    throw new Exception($"Unable to find target state for {state.id}. Path: {state.path}");

                if (!(objTarget is IStateValue))
                    throw new Exception($"High frequency sync for non-primitives is not supported!");

                target = (IStateValue)objTarget;
                lastSyncTime = Time.time - (1f / state.syncRate.value);

                _subscription = target.Subscribe(_ => isDirty = true);
            }

            public void Dispose()
            {
                _subscription?.Dispose();
            }
        }

        private IDisposable _subscriptions;

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
                (roomID, _) => ConnectToRoom(roomID),
                _ => _client.LeaveRoomAsync().AsUniTask()
            );

            _subscriptions = new ComposedDisposable(
                StateObservables.SubscribeOperations(HandleShouldInitializeUnsyncedPlayersChanged, App.state.inRoomAndSynchronized, App.state.isMasterClient),
                StateObservables.SubscribeOperationsRecursive(HandleSceneChanged, App.state.inRoomAndSynchronized, App.state.scene),
                App.state.scene.highFrequencyPrimitives
                    .ObservableWhere(x => Observables.ObservableCombineValues(
                        x.Value.owner,
                        App.state.playerID,
                        (owner, player) => owner == player // is this path mine?
                    ))
                    .ObservableSelect(x => new HighFrequencySyncData(x.Value))
                    .Subscribe(
                        onAdd: x => _highFrequencySyncData.Add(x),
                        onRemove: x =>
                        {
                            _highFrequencySyncData.Remove(x);
                            x.Dispose();
                        }
                    )
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
            using (var writer = new BinaryWriter(_highFrequencySyncStream, Encoding.UTF8, true))
            {
                foreach (var data in _highFrequencySyncData)
                {
                    float timeBetweenSyncs = 1f / data.state.syncRate.value;
                    if (data.isDirty && Time.time - data.lastSyncTime >= timeBetweenSyncs)
                    {
                        data.lastSyncTime = Time.time;
                        data.isDirty = false;

                        var startPosition = writer.BaseStream.Position;

                        writer.Write(default(long)); // this will be the length of the message, after we know what it is
                        writer.Write(data.state.id.value.value);
                        PhotonSerialization.GetSerializer(data.target.valueType).Serialize(
                            writer,
                            data.target.value,
                            data.target is IStateValueArray
                        );

                        var endPosition = writer.BaseStream.Position;
                        writer.BaseStream.Position = startPosition;
                        writer.Write(endPosition - startPosition);
                        writer.BaseStream.Position = endPosition;
                    }
                }

                writer.Flush();
            }

            if (_highFrequencySyncStream.Length > 0)
            {
                _client.OpRaiseEvent(
                    HIGH_FREQUENCY_SYNC_EVENT,
                    _highFrequencySyncStream.ToArray(),
                    new RaiseEventArgs() { CachingOption = EventCaching.DoNotCache, Receivers = ReceiverGroup.Others },
                    new SendOptions() { DeliveryMode = DeliveryMode.Unreliable }
                );

                _highFrequencySyncStream.SetLength(0);
            }

            if (_incrementalSyncStream.Length > 0)
            {
                _client.OpRaiseEvent(
                    INCREMENTAL_SYNC_EVENT,
                    _incrementalSyncStream.ToArray(),
                    new RaiseEventArgs() { CachingOption = EventCaching.DoNotCache, Receivers = ReceiverGroup.Others },
                    new SendOptions() { DeliveryMode = DeliveryMode.Reliable }
                );

                _incrementalSyncStream.SetLength(0);
            }

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
            _subscriptions.Dispose();
        }

        private async UniTask ConnectToRoom(string roomID)
        {
            await _client.ConnectToRoomAsync(new MatchmakingArguments()
            {
                RoomName = roomID,
                PhotonSettings = _client.AppSettings
            });

            await UniTask.SwitchToMainThread();

            App.ExecuteTransaction(new SetInitialRoomSettingsAction(
                _client.LocalPlayer.ActorNumber,
                _client.CurrentRoom.MasterClientId,
                _client.RealtimePeer.ServerTimeInMilliseconds / 1000f
            ));
        }

        private void HandleShouldInitializeUnsyncedPlayersChanged(IReadOnlyList<IStateOperation> ops)
        {
            if (!App.state.isMasterClient.value || !App.state.inRoomAndSynchronized.value)
                return;

            var unsyncedPlayers = _client.CurrentRoom.Players.Keys
                .Except(App.state.scene.players.keys)
                .Where(x => x != _client.LocalPlayer.ActorNumber)
                .ToArray();

            if (unsyncedPlayers.Length > 0)
                SendInitialSync(unsyncedPlayers);
        }

        private void HandleSceneChanged(IReadOnlyList<IStateOperation> ops)
        {
            if (_applyingIncrementalSync)
                return;

            foreach (var op in ops)
            {
                if (op.source == App.state.inRoomAndSynchronized)
                    _inRoomAndSynchronized = (bool)op.param;

                if (!_inRoomAndSynchronized ||
                    op.opType == OpType.Dispose ||
                    op.opType == OpType.None ||
                    op.source == App.state.inRoomAndSynchronized ||
                    App.state.scene.highFrequencyPrimitives.ContainsKey(op.source.nodePath) ||
                    op.source.derived)
                {
                    continue;
                }

                WriteChange(_incrementalSyncStream, op);
            }
        }

        private void WriteChange(MemoryStream stream, IStateOperation change)
        {
            using (var writer = new BinaryWriter(stream, Encoding.UTF8, true))
            {
                long startPosition = writer.BaseStream.Position;
                writer.Write(default(long)); // this will be the length of the message, after we know what it is
                _pathIDCache.WritePath(change.source, App.state.scene, writer);
                writer.Write(change.opType == OpType.Remove);

                if (change.source is IStateValue prim)
                {
                    PhotonSerialization.GetSerializer(prim.valueType).Serialize(writer, change.param, false);
                }
                else if (change.source is IStateValueArray array)
                {
                    PhotonSerialization.GetSerializer(array.elementType).Serialize(writer, change.param, true);
                }
                else if (change.source is IStateDictionary dict)
                {
                    PhotonSerialization.GetSerializer(dict.keyType).Serialize(writer, change.param, false);
                }
                else if (change.source is IStateList list)
                {
                    PhotonSerialization.GetSerializer(typeof(int)).Serialize(writer, change.param, false);
                }
                else if (change.source is IStateValueSet set)
                {
                    PhotonSerialization.GetSerializer(set.elementType).Serialize(writer, change.param, false);
                }

                var length = writer.BaseStream.Position - startPosition;
                var endPosition = writer.BaseStream.Position;
                writer.BaseStream.Position = startPosition;
                writer.Write(length);
                writer.BaseStream.Position = endPosition;
                writer.Flush();
            }
        }

        private void SendInitialSync(params int[] targets)
        {
            var json = App.state.scene.ToJSON(x => !x.derived);
            _client.OpRaiseEvent(
                INITIAL_SYNC_EVENT,
                json.ToString(),
                new RaiseEventArgs() { TargetActors = targets },
                new SendOptions() { DeliveryMode = DeliveryMode.Reliable }
            );
        }

        // IInRoomCallbacks
        public void OnPlayerEnteredRoom(Player newPlayer)
        {
            if (App.state.isMasterClient.value && App.state.inRoomAndSynchronized.value)
                SendInitialSync(newPlayer.ActorNumber);
        }

        public void OnPlayerLeftRoom(Player otherPlayer)
        {
            _applyingIncrementalSync = true; // disconnected players are removed on all clients simultaneously- no need to sync the operations
            App.ExecuteTransaction(new RemovePlayerAction(otherPlayer.ActorNumber));
            _applyingIncrementalSync = false;
        }

        public void OnPlayerPropertiesUpdate(Player targetPlayer, PhotonHashtable changedProps)
        {

        }

        public void OnMasterClientSwitched(Player newMasterClient)
        {
            App.ExecuteTransaction(new SetMasterClientAction(newMasterClient.ActorNumber));
        }

        public void OnRoomPropertiesUpdate(PhotonHashtable propertiesThatChanged) { }

        // IOnEventCallback
        public void OnEvent(EventData photonEvent)
        {
            if (photonEvent.Code == HIGH_FREQUENCY_SYNC_EVENT)
            {
                App.ExecuteTransaction(new ApplyHighFrequencySyncAction((byte[])photonEvent.CustomData));
            }
            else if (photonEvent.Code == INCREMENTAL_SYNC_EVENT)
            {
                _applyingIncrementalSync = true;
                App.ExecuteTransaction(new ApplyIncrementalSyncAction(_pathIDCache, (byte[])photonEvent.CustomData));
                _applyingIncrementalSync = false;
            }
            else if (photonEvent.Code == INITIAL_SYNC_EVENT)
            {
                App.ExecuteTransaction(new ApplyInitialSceneStateAction(JSONNode.Parse((string)photonEvent.CustomData)));
            }
        }

        // IConnectionCallbacks
        public void OnConnected() { }

        public void OnConnectedToMaster() { }

        public void OnDisconnected(DisconnectCause cause)
        {
            _client.Disconnect();

            App.ExecuteTransaction(state =>
            {
                if (state.nameServerConnection.status.value != ConnectionStatus.Disconnected)
                {
                    state.nameServerConnection.status.value = ConnectionStatus.Error;
                    state.nameServerConnection.error.value = cause.ToString();
                }

                if (state.roomConnection.status.value != ConnectionStatus.Disconnected)
                {
                    state.roomConnection.status.value = ConnectionStatus.Error;
                    state.roomConnection.error.value = cause.ToString();
                }

                var roomID = state.roomID.value;
                new LeaveRoomAction().ExecuteTransaction(state);
                state.roomID.value = roomID;
            });
        }

        public void OnRegionListReceived(RegionHandler regionHandler)
        {

        }

        public void OnCustomAuthenticationResponse(Dictionary<string, object> data)
        {

        }

        public void OnCustomAuthenticationFailed(string debugMessage)
        {

        }
    }
}