using Cysharp.Threading;
using MagicOnion;
using MagicOnion.Server.Hubs;
using Microsoft.Extensions.Hosting;
using Outernet.Shared;

namespace Outernet.Server
{
    class SyncedStateService : SyncedStateSystem, IHostedService
    {
        private static SyncedStateService? singleton;

        private readonly PlerionAPI _plerionApi;

        public const int targetFps = 60;
        private const int shutdownDelay = 0;
        private const float fetchNodesFrequency = 2.0f; // seconds

        private readonly LogicLooper logicLooper;
        private Dictionary<string, Room> rooms = [];
        private long lastFetchNodesFrame = 0;

        protected override void HandleException(Exception exception) =>
            Log.Error(exception, "Exception throw while executing enqueued actions");

        public override Guid? ClientID { get; set; } = Guid.Empty;
        public override bool Deserializing { get; protected set; } = false;
        public override uint Tick { get; protected set; }

        public static Dictionary<string, RoomRecord.InitializationData> roomSettings { get; } = new();

        public SyncedStateService(PlerionAPI plerionApi)
        {
            singleton = this;

            _plerionApi = plerionApi;

            logicLooper = new LogicLooper(targetFps);
        }

        public Task StartAsync(CancellationToken cancellationToken)
        {
            logicLooper.RegisterActionAsync(Update);

            return Task.CompletedTask;
        }

        public async Task StopAsync(CancellationToken cancellationToken)
        {
            await logicLooper.ShutdownAsync(TimeSpan.FromSeconds(shutdownDelay));
        }

        private bool Update(in LogicLooperActionContext context)
        {
            var fetchNodes = context.CurrentFrame - lastFetchNodesFrame > targetFps * fetchNodesFrequency;
            if (fetchNodes)
            {
                lastFetchNodesFrame = context.CurrentFrame;
            }

            try
            {
                lock (rooms)
                {
                    foreach (var room in rooms.Values)
                    {
                        room.UpdateNodes(fetchNodes);
                    }

                    DrainActionQueue();

                    foreach (var room in rooms.Values)
                    {
                        Deserializing = true;
                        room.ApplyClientDeltas();
                        Deserializing = false;

                        room.UpdateClients();
                    }
                }
            }
            catch (Exception exception)
            {
                Log.Error(exception, "Update failed");
            }

            ++Tick;

            return true;
        }

        public static async ValueTask<byte[]> JoinRoom(
            string roomID,
            string userName,
            Guid clientID,
            IGroup<ISyncedStateHubReceiver> group
        )
        {
            if (singleton == null)
                throw new InvalidOperationException("StateSyncService singleton not initialized");

            try
            {
                var fullSerializationTaskCompletionSource = new TaskCompletionSource<byte[]>();

                lock (singleton.rooms)
                {
                    // Create the room if it does not exist
                    if (!singleton.rooms.ContainsKey(roomID))
                    {
                        singleton.rooms.Add(roomID, new Room(singleton, roomID, singleton._plerionApi));
                        roomSettings.TryGetValue(roomID, out RoomRecord.InitializationData? value);
                        Log.Info("dafuq");
                        if (value != null)
                        {
                            Log.Info($"Room \"{roomID}\" initialized with existing settings");
                        }
                        else
                        {
                            Log.Info($"Room \"{roomID}\" created with default settings");
                        }
                        singleton.rooms[roomID].roomState.Initialize(value ?? new RoomRecord.InitializationData());
                        Log.Info($"Room \"{roomID}\" created");
                    }

                    singleton
                        .rooms[roomID]
                        .roomState.users.EnqueueAdd(
                            clientID,
                            new UserRecord.InitializationData() { userName = userName }
                        );

                    singleton
                        .rooms[roomID]
                        .clients.Add(
                            clientID,
                            new Client(clientID, group, fullSerializationTaskCompletionSource, singleton.Tick)
                        );
                }

                // The delta must be empty when the new client joins the room, so use a task
                // completion source to wait until the current tick ends, finishes adding the
                // client, fully serializes the room state, and returns it
                var roomStateData = await fullSerializationTaskCompletionSource.Task;

                Log.Info($"User \"{userName}\" joined room \"{roomID}\" as client {clientID}");

                // Send the fully serialized room state to the new client
                return roomStateData;
            }
            catch (Exception exception)
            {
                Log.Error(exception, "JoinRoom failed");
                throw;
            }
        }

        public static void LeaveRoom(string roomID, Guid clientID)
        {
            try
            {
                lock (singleton.rooms[roomID])
                {
                    // If the client is not in the room, they timed out and were removed before the
                    // actual OnDisconnected function was called
                    if (!singleton.rooms[roomID].clients.ContainsKey(clientID))
                        return;

                    singleton.rooms[roomID].roomState.users.EnqueueRemove(clientID);
                    singleton.rooms[roomID].clients.Remove(clientID);

                    Log.Info($"Client {clientID} left room \"{roomID}\"");

                    if (singleton.rooms[roomID].clients.Count == 0)
                    {
                        lock (singleton.rooms)
                        {
                            roomSettings[roomID] = singleton.rooms[roomID].roomState.GetInitializationData();

                            Log.Info($"Room \"{roomID}\" empty, removing");
                            singleton.rooms.Remove(roomID);
                        }
                    }
                }
            }
            catch (Exception exception)
            {
                Log.Error(exception, "LeaveRoom failed");
                throw;
            }
        }

        public static void ReceiveRoomStateDelta(Guid clientID, byte[] roomStateDeltaData, string roomID)
        {
            if (singleton == null)
                throw new InvalidOperationException("StateSyncService singleton not initialized");

            lock (singleton.rooms)
            {
                if (!singleton.rooms[roomID].clients.ContainsKey(clientID))
                {
                    // Client timed out and was removed from the room, throw an exception
                    throw new ReturnStatusException(
                        Grpc.Core.StatusCode.NotFound,
                        $"Client {clientID} timed out and was removed from room \"{roomID}\""
                    );
                }

                singleton.rooms[roomID].clients[clientID].heartbeat = singleton.Tick;
                singleton.rooms[roomID].pendingRemoteStateDeltas.Enqueue(roomStateDeltaData);
            }
        }
    }
}
