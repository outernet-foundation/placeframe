using System;
using Cysharp.Threading.Tasks;
using MessagePack.Resolvers;
using MessagePack;
using MessagePack.Unity;
using Outernet.Shared;
using System.Buffers;
using System.Collections.Generic;
using static Outernet.Shared.Assert;
using MagicOnion.Unity;
using Cysharp.Net.Http;
using Grpc.Net.Client;
using MagicOnion;
using System.Threading;
using MagicOnion.Client;
using UnityEngine;

namespace Outernet.Client
{
    public class SyncedStateClient : SyncedStateSystem, IDisposable
    {
        private OuternetHubReceiver stateSyncReceiver;
        private ISyncedStateHub client;
        private Queue<byte[]> pendingRemoteStateDeltas = new Queue<byte[]>();

        public override Guid? ClientID { get; set; } = null;
        public override uint Tick { get; protected set; } = 0;
        public override bool Deserializing { get; protected set; } = false;
        public RoomRecord State { get; private set; } = null;

        protected override void HandleException(Exception exception)
            => Log.Error(
                LogGroup.SyncedStateClient,
                "Exception thrown while executing enqueued action",
                exception);

        public SyncedStateClient()
        {
            StaticCompositeResolver.Instance.Register(
                GeneratedResolver.Instance,
                UnityResolver.Instance,
                StandardResolver.Instance
            );

            MessagePackSerializer.DefaultOptions = MessagePackSerializer.DefaultOptions
                .WithResolver(StaticCompositeResolver.Instance);

            GrpcChannelProviderHost.Initialize(new DefaultGrpcChannelProvider(() => new GrpcChannelOptions()
            {
                HttpHandler = new YetAnotherHttpHandler() { Http2Only = true },
                DisposeHttpClient = true,
                LoggerFactory = new Log.LoggerFactory(LogGroup.Grpc)
            }));

            stateSyncReceiver = new OuternetHubReceiver(pendingRemoteStateDeltas);

            State = new RoomRecord(this);
        }

        public void Dispose() => State.Dispose();

        public async UniTask ConnectToHubAsync(CancellationToken cancellationToken)
        {
            var channelOptions = new GrpcChannelOptions()
            {
                HttpHandler = new YetAnotherHttpHandler() 
                { 
                    Http2Only = true
                },
                DisposeHttpClient = true
            };

            client = await StreamingHubClient.ConnectAsync<ISyncedStateHub, ISyncedStateHubReceiver>(
                GrpcChannel.ForAddress(App.apiUrl, channelOptions),
                stateSyncReceiver,
                StreamingHubClientOptions.CreateWithDefault()
                    .WithClientHeartbeatInterval(TimeSpan.FromSeconds(10))
                    .WithClientHeartbeatTimeout(TimeSpan.FromSeconds(5)),
                cancellationToken: cancellationToken);

            ClientID = await client
                .GetClientIDAsync(SystemInfo.deviceName)
                .AsUniTask()
                .AttachExternalCancellation(cancellationToken);
        }

        public async UniTask DisconnectFromHubAsync()
            => await client.DisposeAsync();

        public async UniTask WaitForDisconnect(CancellationToken cancellationToken)
            => await client
                .WaitForDisconnect()
                .AsUniTask()
                .AttachExternalCancellation(cancellationToken);

        public void ClearHubState()
        {
            ClientID = null;
            client = null;
        }

        public async UniTask JoinRoomAsync(string roomID, CancellationToken cancellationToken)
        {
            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);

            var initialState = await client
                .JoinRoomAsync(roomID)
                .AsUniTask()
                .AttachExternalCancellation(cancellationToken);

            void DeserializeState(byte[] stateData)
            {
                Deserializing = true;
                var reader = new MessagePackReader(stateData);
                State.Deserialize(ref reader);
                Deserializing = false;
            }

            DeserializeState(initialState);
        }

        public async UniTask LeaveRoomAsync(CancellationToken cancellationToken)
            => await client
                .LeaveRoomAsync()
                .AsUniTask()
                .AttachExternalCancellation(cancellationToken);

        public void ClearRoomState()
        {
            pendingRemoteStateDeltas.Clear();
            State.users.EnqueueClear();
            State.nodes.EnqueueClear();
            DrainActionQueue();
            State.ClearDelta();

            ASSERT(State.users.Count == 0 && State.nodes.Count == 0, "state was not empty after clearing");
        }

        public async UniTask UpdateAsync()
        {
            // Always drain the action queue
            DrainActionQueue();

            // Can't synchronize if we're not connected
            if (ConnectionManager.RoomConnectionStatusStream.CurrentValue != ConnectionManager.RoomConnectionStatus.Connected)
            {
                return;
            }

            await client.SendRoomStateDeltaAsync(Update());
        }

        public byte[] Update()
        {
            // Serialize the local state delta
            var sequenceWriter = new ArrayBufferWriter<byte>();
            var writer = new MessagePackWriter(sequenceWriter);
            State.SerializeDelta(ref writer);
            writer.Flush();
            var localStateDelta = sequenceWriter.WrittenSpan.ToArray();

            // Clear the local state delta so that we are in a clean state before applying remote
            // deltas
            State.ClearDelta();

            // Apply any pending remote state deltas
            Deserializing = true;
            while (pendingRemoteStateDeltas.Count > 0)
            {
                var reader = new MessagePackReader(pendingRemoteStateDeltas.Dequeue());
                State.DeserializeDelta(ref reader);
            }
            Deserializing = false;

            ++Tick;

            return localStateDelta;
        }
    }
}