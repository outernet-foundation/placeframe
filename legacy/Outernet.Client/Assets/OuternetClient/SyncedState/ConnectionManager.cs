
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using Grpc.Core;
using Outernet.Shared;
using R3;

namespace Outernet.Client
{
    static public class ConnectionManager
    {
        public enum HubConnectionStatus
        {
            NotConnected,
            Connecting,
            Connected,
            Disconnecting,
            Disconnected,
            Errored
        }

        public enum RoomConnectionStatus
        {
            NotConnected,
            Connecting,
            Connected,
            Disconnecting
        }

        static private Dictionary<HubConnectionStatus, string> hubStatusStrings = new Dictionary<HubConnectionStatus, string>()
        {
            { HubConnectionStatus.Connecting, "Connecting to hub" },
            { HubConnectionStatus.Connected, "Connected to hub" },
            { HubConnectionStatus.Disconnecting, "Disconnecting from hub" },
            { HubConnectionStatus.Disconnected, "Disconnected from hub" },
            { HubConnectionStatus.NotConnected, "Not connected to hub" },
            { HubConnectionStatus.Errored, "Hub connection error" }
        };

        static private Dictionary<RoomConnectionStatus, string> roomStatusStrings = new Dictionary<RoomConnectionStatus, string>()
        {
            { RoomConnectionStatus.Connecting, "Joining room" },
            { RoomConnectionStatus.Connected, "Joined room" },
            { RoomConnectionStatus.Disconnecting, "Leaving room" },
            { RoomConnectionStatus.NotConnected, "Left room" },
        };

        static private SyncedStateClient client;
        static private IDisposable disposable;
        static private QueueSynchronizationContext context = new QueueSynchronizationContext();
        static private readonly ObservableProperty<HubConnectionStatus> hubConnectionStatus = new(context, HubConnectionStatus.NotConnected);
        static private readonly ObservableProperty<RoomConnectionStatus> roomConnectionStatus = new(context, RoomConnectionStatus.NotConnected);
        static private CancellationTokenSource hubConnectionCancellationTokenSource = null;
        static private CancellationTokenSource roomConnectionCancellationTokenSource = null;

        static public readonly ObservableProperty<bool> HubConnectionRequested = new(context, false);
        static public readonly ObservableProperty<string> RoomConnectionRequested = new(context, null);
        static public ReadOnlyReactiveProperty<HubConnectionStatus> HubConnectionStatusStream => hubConnectionStatus;
        static public ReadOnlyReactiveProperty<RoomConnectionStatus> RoomConnectionStatusStream => roomConnectionStatus;
        static public RoomRecord State => client.State;
        static public Guid? ClientID => client.ClientID;

        static public void Initialize()
        {
            client = new SyncedStateClient();
            var eventStreams = CreateEventStreams();

            disposable = Disposable.Combine(client, eventStreams);
        }

        static public async void Terminate()
        {
            HubConnectionRequested.EnqueueSet(false);

            await UniTask.WaitUntil(() => hubConnectionStatus.Value == HubConnectionStatus.NotConnected);

            disposable.Dispose();
        }

        static private IDisposable CreateEventStreams()
        {
            return Disposable.Combine
            (
                hubConnectionStatus
                    .Skip(1)
                    .Subscribe(status
                        => Log.Info(LogGroup.SyncedStateClient, hubStatusStrings[status])),

                roomConnectionStatus
                    .Skip(1)
                    .Subscribe(status
                        => Log.Info(LogGroup.SyncedStateClient, roomStatusStrings[status])),

                EventStream
                    .CombineLatest(
                        hubConnectionStatus,
                        HubConnectionRequested)
                    .Where(connectionEvent
                        => connectionEvent is (HubConnectionStatus.NotConnected, true))
                    .Subscribe(()
                        => hubConnectionStatus.EnqueueSet(HubConnectionStatus.Connecting)),

                EventStream
                    .CombineLatest(
                        hubConnectionStatus,
                        HubConnectionRequested)
                    .Where(connectionEvent
                        => connectionEvent is (HubConnectionStatus.Connecting, true))
                    .SubscribeCancellable(Connect, HandleConnectionException),

                EventStream
                    .CombineLatest(
                        hubConnectionStatus,
                        HubConnectionRequested)
                    .Where(connectionEvent
                        => connectionEvent is (HubConnectionStatus.Connecting, false))
                    .Subscribe(CancelConnect),

                hubConnectionStatus
                    .Where(status
                        => status is HubConnectionStatus.Connected)
                    .SubscribeAwait(WaitForDisconnect),

                EventStream
                    .CombineLatest(
                        hubConnectionStatus,
                        HubConnectionRequested)
                    .Where(connectionEvent
                        => connectionEvent is (HubConnectionStatus.Connected, false))
                    .Subscribe(()
                        => hubConnectionStatus.EnqueueSet(HubConnectionStatus.Disconnecting)),

                EventStream
                    .CombineLatest(
                        hubConnectionStatus,
                        roomConnectionStatus)
                    .Where(connectionEvent
                        => connectionEvent is (HubConnectionStatus.Disconnecting, RoomConnectionStatus.NotConnected))
                    .SubscribeAwait(Disconnect, HandleConnectionException),

                hubConnectionStatus
                    .Where(status
                        => status is HubConnectionStatus.Disconnected)
                    .Subscribe(() => client.ClearHubState()),

                hubConnectionStatus
                    .Pairwise()
                    .Where(previousAndCurrent
                        => previousAndCurrent is (HubConnectionStatus.Disconnecting, HubConnectionStatus.Disconnected))
                    .Subscribe(()
                        => hubConnectionStatus.EnqueueSet(HubConnectionStatus.NotConnected)),

                hubConnectionStatus
                    .Pairwise()
                    .Where(previousAndCurrent
                        => previousAndCurrent is (HubConnectionStatus.Connected, HubConnectionStatus.Disconnected))
                    .Subscribe(HandleConnectionLost),

                hubConnectionStatus
                    .Where(status
                        => status is HubConnectionStatus.Errored)
                    .SubscribeAwait(BackoffAndRetry),

                EventStream
                    .CombineLatest(
                        roomConnectionStatus,
                        hubConnectionStatus,
                        RoomConnectionRequested)
                    .Where(connectionEvent
                        => connectionEvent is (RoomConnectionStatus.NotConnected, HubConnectionStatus.Connected, not null))
                    .Subscribe(()
                        => roomConnectionStatus.EnqueueSet(RoomConnectionStatus.Connecting)),

                EventStream
                    .CombineLatest(
                        roomConnectionStatus,
                        hubConnectionStatus,
                        RoomConnectionRequested)
                    .Where(connectionEvent
                        => connectionEvent is (RoomConnectionStatus.Connecting, HubConnectionStatus.Connected, not null))
                    .SubscribeCancellable(JoinRoom, HandleConnectionException),

                EventStream
                    .CombineLatest(
                        roomConnectionStatus,
                        hubConnectionStatus,
                        RoomConnectionRequested)
                    .Where(connectionEvent
                        => connectionEvent is
                            (RoomConnectionStatus.Connecting, _, null) or
                            (RoomConnectionStatus.Connecting, HubConnectionStatus.Disconnecting or HubConnectionStatus.Errored, _))
                    .Subscribe(CancelRoomJoin),

                EventStream
                    .CombineLatest(
                        roomConnectionStatus,
                        hubConnectionStatus,
                        RoomConnectionRequested)
                    .Where(connectionEvent
                        => connectionEvent is
                            (RoomConnectionStatus.Connected, HubConnectionStatus.Disconnecting, _) or
                            (RoomConnectionStatus.Connected, _, null))
                    .Subscribe(()
                        => roomConnectionStatus.EnqueueSet(RoomConnectionStatus.Disconnecting)),

                EventStream
                    .CombineLatest(
                        roomConnectionStatus,
                        hubConnectionStatus)
                    .Where(connectionEvent
                        => connectionEvent is (RoomConnectionStatus.Connected, HubConnectionStatus.Errored))
                    .Subscribe(()
                        => roomConnectionStatus.EnqueueSet(RoomConnectionStatus.NotConnected)),

                roomConnectionStatus
                    .Where(status
                        => status is RoomConnectionStatus.Connected)
                    .Subscribe(()
                        => Toast.ShowToast($"Connected to room {RoomConnectionRequested.Value}")),

                roomConnectionStatus
                    .Where(status
                        => status is RoomConnectionStatus.Disconnecting)
                    .SubscribeAwait(LeaveRoom, HandleConnectionException),

                roomConnectionStatus
                    .Where(status
                        => status is RoomConnectionStatus.NotConnected)
                    .Subscribe(()
                        => client.ClearRoomState())
            );
        }

        static private async UniTask Connect(CancellationTokenSource cancellationTokenSource)
        {
            hubConnectionCancellationTokenSource = cancellationTokenSource;

            await client.ConnectToHubAsync(cancellationTokenSource.Token);

            hubConnectionStatus.EnqueueSet(HubConnectionStatus.Connected);
        }

        static private void CancelConnect()
        {
            hubConnectionCancellationTokenSource.Cancel();

            hubConnectionStatus.EnqueueSet(HubConnectionStatus.NotConnected);
        }

        static private async UniTask WaitForDisconnect(CancellationToken cancellationToken)
        {
            await client.WaitForDisconnect(cancellationToken);

            hubConnectionStatus.EnqueueSet(HubConnectionStatus.Disconnected);
        }

        static private void HandleConnectionLost()
        {
            Toast.ShowToast("Connection lost, did you lose internet?");

            hubConnectionStatus.EnqueueSet(HubConnectionStatus.Errored);
        }

        static private async UniTask BackoffAndRetry(CancellationToken cancellationToken)
        {
            await UniTask.Delay(1000, cancellationToken: cancellationToken);

            hubConnectionStatus.EnqueueSet(HubConnectionStatus.NotConnected);
        }

        static private async UniTask Disconnect(CancellationToken cancellationToken)
        {
            await client.DisconnectFromHubAsync();
        }

        static private async UniTask JoinRoom(CancellationTokenSource cancellationTokenSource)
        {
            roomConnectionCancellationTokenSource = cancellationTokenSource;

            await client.JoinRoomAsync(RoomConnectionRequested.Value, cancellationTokenSource.Token);

            roomConnectionStatus.EnqueueSet(RoomConnectionStatus.Connected);
        }

        static private void CancelRoomJoin()
        {
            roomConnectionCancellationTokenSource.Cancel();

            roomConnectionStatus.EnqueueSet(RoomConnectionStatus.NotConnected);
        }

        static private async UniTask LeaveRoom(CancellationToken cancellationToken)
        {
            await client.LeaveRoomAsync(cancellationToken);

            roomConnectionStatus.EnqueueSet(RoomConnectionStatus.NotConnected);
        }

        static private void HandleConnectionException(Exception exception)
        {
            var logLevel =
                exception is RpcException ||
                exception is TimeoutException ||
                exception is TaskCanceledException ?
                LogLevel.Warn : LogLevel.Error;

            Log.DoLog(logLevel, LogGroup.SyncedStateClient, exception);

            hubConnectionStatus.EnqueueSet(HubConnectionStatus.Errored);
        }


        static public void Update()
        {
            async UniTask clientUpdate()
            {
                try
                {
                    await client.UpdateAsync();
                }
                catch (Exception exception)
                {
                    HandleConnectionException(exception);
                }
            }

            clientUpdate().Forget();
        }
    }
}