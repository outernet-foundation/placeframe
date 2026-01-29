using System.Buffers;
using MessagePack;
using Outernet.Shared;
using PlerionApiClient.Model;

namespace Outernet.Server
{
    class Room(SyncedStateSystem syncedStateSystem, string roomID, PlerionAPI plerionApi)
    {
        public string roomID = roomID;
        public Dictionary<Guid, Client> clients = [];
        public RoomRecord roomState = new(syncedStateSystem);
        public Queue<byte[]> pendingRemoteStateDeltas = new();
        public TaskCompletionSource<List<NodeRead>>? fetchNodesTaskCompletionSource = null;
        private SyncedStateSystem syncedStateSystem = syncedStateSystem;

        public void UpdateNodes(bool fetchNodes)
        {
            if (fetchNodesTaskCompletionSource != null)
            {
                if (!fetchNodesTaskCompletionSource.Task.IsCompleted)
                    return;

                var nodes = fetchNodesTaskCompletionSource.Task.Result;
                fetchNodesTaskCompletionSource = null;

                // Add new nodes
                foreach (var node in nodes.Where(node => !roomState.nodes.ContainsKey(node.Id)))
                {
                    roomState.nodes.EnqueueAdd(
                        node.Id,
                        new Shared.NodeRecord.InitializationData()
                        {
                            geoPose = new GeoPoseRecord.InitializationData()
                            {
                                ecefPosition = new Double3(node.PositionX, node.PositionY, node.PositionZ),
                                ecefRotation = new UnityEngine.Quaternion(
                                    (float)node.RotationX,
                                    (float)node.RotationY,
                                    (float)node.RotationZ,
                                    (float)node.RotationW
                                ),
                            },
                            link = node.Link,
                            linkType = Conversions.LinkType(node.LinkType),
                            label = node.Label,
                            labelType = Conversions.LabelType(node.LabelType),
                            labelScale = (float)node.LabelScale,
                            labelWidth = (float)node.LabelWidth,
                            labelHeight = (float)node.LabelHeight,
                            layer = node.LayerId ?? Guid.Empty,
                        }
                    );
                }

                // Remove nodes that are no longer present
                var nodeIDs = nodes.Select(node => node.Id).ToHashSet();
                foreach (var nodeID in roomState.nodes.Keys.Where(nodeID => !nodeIDs.Contains(nodeID)))
                {
                    roomState.nodes.EnqueueRemove(nodeID);
                }

                // // Update existing nodes
                foreach (var node in nodes.Where(node => roomState.nodes.ContainsKey(node.Id)))
                {
                    roomState
                        .nodes.Get(node.Id)
                        .geoPose.ecefPosition.EnqueueSet(new Double3(node.PositionX, node.PositionY, node.PositionZ));
                    roomState
                        .nodes.Get(node.Id)
                        .geoPose.ecefRotation.EnqueueSet(
                            new UnityEngine.Quaternion(
                                (float)node.RotationX,
                                (float)node.RotationY,
                                (float)node.RotationZ,
                                (float)node.RotationW
                            )
                        );
                    roomState.nodes.Get(node.Id).link.EnqueueSet(node.Link);
                    roomState.nodes.Get(node.Id).linkType.EnqueueSet(Conversions.LinkType(node.LinkType));
                    roomState.nodes.Get(node.Id).label.EnqueueSet(node.Label);
                    roomState.nodes.Get(node.Id).labelType.EnqueueSet(Conversions.LabelType(node.LabelType));
                    roomState.nodes.Get(node.Id).labelScale.EnqueueSet((float)node.LabelScale);
                    roomState.nodes.Get(node.Id).labelWidth.EnqueueSet((float)node.LabelWidth);
                    roomState.nodes.Get(node.Id).labelHeight.EnqueueSet((float)node.LabelHeight);
                    roomState.nodes.Get(node.Id).layer.EnqueueSet(node.LayerId ?? Guid.Empty);
                }
            }

            if (fetchNodes)
            {
                fetchNodesTaskCompletionSource = new TaskCompletionSource<List<NodeRead>>();

                plerionApi
                    .GetNodes(
                        roomState
                            .users.Values.Select(user => user.geoPose.ecefPosition.Value)
                            .Where(ecefPosition => ecefPosition.x != 0 || ecefPosition.y != 0 || ecefPosition.z != 0),
                        roomState.settingsNodeFetchRadius.Value,
                        roomState.settingsNodeFetchLimit.Value
                    )
                    .ContinueWith(task => {
                        fetchNodesTaskCompletionSource.SetResult(task.Result);
                    });
            }
        }

        public void ApplyClientDeltas()
        {
            while (pendingRemoteStateDeltas.Count > 0)
            {
                var reader = new MessagePackReader(pendingRemoteStateDeltas.Dequeue());
                roomState.DeserializeDelta(ref reader);
            }
        }

        public void UpdateClients()
        {
            // Perform a full serialization of the room state to be sent to any client
            // requiring it
            var serializedRoomState = Serialize(roomState);

            foreach (var client in clients)
            {
                if (client.Value.fullSerializationTaskCompletionSource != null)
                {
                    client.Value.fullSerializationTaskCompletionSource.SetResult(serializedRoomState);
                    client.Value.fullSerializationTaskCompletionSource = null;
                    continue;
                }

                // Serialize the per-client delta and send it to that client
                client
                    .Value.group.Single(client.Value.connectionID)
                    .OnReceiveRoomStateDelta(SerializeDelta(roomState));
            }

            // Clear the entire delta
            roomState.ClearDelta();
        }

        private static byte[] Serialize(RoomRecord roomState)
        {
            var sequenceWriter = new ArrayBufferWriter<byte>();
            var writer = new MessagePackWriter(sequenceWriter);
            roomState.Serialize(ref writer);
            writer.Flush();
            return sequenceWriter.WrittenSpan.ToArray();
        }

        private static byte[] SerializeDelta(RoomRecord roomState)
        {
            var sequenceWriter = new ArrayBufferWriter<byte>();
            var writer = new MessagePackWriter(sequenceWriter);
            roomState.SerializeDelta(ref writer);
            writer.Flush();
            return sequenceWriter.WrittenSpan.ToArray();
        }
    }
}
