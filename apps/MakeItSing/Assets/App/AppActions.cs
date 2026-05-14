using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FofX.Stateful;
using SimpleJSON;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class RequestConnectionAction : StateTransaction<ConnectionState>
    {
        private string _connectionString;

        public RequestConnectionAction(string connectionString)
        {
            _connectionString = connectionString;
        }

        protected override void Execute(ConnectionState target)
        {
            target.connectionString.value = _connectionString;
            target.shouldBeConnected.value = true;
        }
    }

    public class SetConnectionStatusAction : StateTransaction<ConnectionState>
    {
        private ConnectionStatus _status;
        private string _error;

        public SetConnectionStatusAction(ConnectionStatus status, string error = default)
        {
            _status = status;
            _error = error;
        }

        protected override void Execute(ConnectionState target)
        {
            target.status.value = _status;
            target.error.value = _status == ConnectionStatus.Error ? _error : null;
        }
    }

    public class ConnectedToRoomAction : StateTransaction<AppState>
    {
        private int _playerID;
        private bool _isMasterClient;

        public ConnectedToRoomAction(int playerID, bool isMasterClient)
        {
            _playerID = playerID;
            _isMasterClient = isMasterClient;
        }

        protected override void Execute(AppState target)
        {
            target.playerID.value = _playerID;
            target.isMasterClient.value = _isMasterClient;
            target.roomConnection.status.value = ConnectionStatus.Connected;
        }
    }

    public class RemovePlayerAction : StateTransaction<AppState>
    {
        private int _playerID;

        public RemovePlayerAction(int playerID)
        {
            _playerID = playerID;
        }

        protected override void Execute(AppState target)
        {
            target.scene.players.Remove(_playerID);

            foreach (var pathToRemove in target.scene.highFrequencyPrimitives.Where(x => x.Value.owner.value == _playerID).ToArray())
                target.scene.highFrequencyPrimitives.Remove(pathToRemove.Key);

            foreach (var toRemove in target.scene.objects.Where(x => x.Value.destroyOnOwnerDisconnect.value && x.Value.ownerID.value == _playerID).ToArray())
                new DestroyObjectAction(toRemove.Key).ExecuteTransaction(target);
        }
    }

    public class ApplyIncrementalSyncAction : StateTransaction<AppState>
    {
        private PathIDCache<SceneState> _pathIDCache;
        private byte[] _data;

        public ApplyIncrementalSyncAction(PathIDCache<SceneState> pathIDCache, byte[] data)
        {
            _pathIDCache = pathIDCache;
            _data = data;
        }

        protected override void Execute(AppState state)
        {
            using (var stream = new MemoryStream(_data))
            using (var reader = new BinaryReader(stream))
            {
                while (stream.Position < stream.Length)
                {
                    var startPosition = stream.Position;
                    var length = reader.ReadInt64();

                    if (!_pathIDCache.TryReadPath(state.scene, reader, out var dest))
                    {
                        UnityEngine.Debug.LogError($"Target state not found!");
                        stream.Position = startPosition + length;
                        continue;
                    }

                    var isRemove = reader.ReadBoolean();

                    if (dest is IStateValue prim)
                    {
                        prim.value = PhotonSerialization.GetSerializer(prim.valueType).Deserialize(reader, false);
                    }
                    else if (dest is IStateValueArray array)
                    {
                        array.SetValue((IEnumerable)PhotonSerialization.GetSerializer(array.elementType).Deserialize(reader, true));
                    }
                    else if (dest is IStateDictionary dict)
                    {
                        var key = PhotonSerialization.GetSerializer(dict.keyType).Deserialize(reader, false);
                        if (isRemove)
                        {
                            dict.Remove(key);
                        }
                        else
                        {
                            dict.Add(key);
                        }
                    }
                    else if (dest is IStateList list)
                    {
                        var index = (int)PhotonSerialization.GetSerializer(typeof(int)).Deserialize(reader, false);
                        if (isRemove)
                        {
                            list.RemoveAt(index);
                        }
                        else
                        {
                            list.Insert(index);
                        }
                    }
                    else if (dest is IStateValueSet set)
                    {
                        var item = PhotonSerialization.GetSerializer(set.elementType).Deserialize(reader, false);
                        if (isRemove)
                        {
                            set.Remove(item);
                        }
                        else
                        {
                            set.Add(item);
                        }
                    }
                }
            }
        }
    }


    public class ApplyHighFrequencySyncAction : StateTransaction<AppState>
    {
        private byte[] _data;

        public ApplyHighFrequencySyncAction(byte[] data)
        {
            _data = data;
        }

        protected override void Execute(AppState target)
        {
            using (var stream = new MemoryStream(_data))
            using (var reader = new BinaryReader(stream))
            {
                while (stream.Position < stream.Length)
                {
                    var startPosition = stream.Position;
                    var length = reader.ReadInt64();
                    var id = reader.ReadInt32();

                    IStateNode valueObj;

                    if (!target.scene.highFrequencyPrimitivesById.TryGetValue(new HighFrequencyPrimitiveId(id), out var path) ||
                        !target.TryFindChild(path.value, out valueObj))
                    {
                        UnityEngine.Debug.LogError($"Target state not found: ID: {id} Path: {path?.value}");
                        stream.Position = startPosition + length;
                        continue;
                    }

                    var primitive = (IStateValue)valueObj;
                    primitive.value = PhotonSerialization.GetSerializer(primitive.valueType).Deserialize(reader, primitive is IStateValueArray);
                }
            }
        }
    }

    public class SetInitialRoomSettingsAction : StateTransaction<AppState>
    {
        private int _playerID;
        private int _masterClientID;
        private float _roomConnectionTime;

        public SetInitialRoomSettingsAction(int playerID, int masterClientID, float roomConnectionTime)
        {
            _playerID = playerID;
            _masterClientID = masterClientID;
            _roomConnectionTime = roomConnectionTime;
        }

        protected override void Execute(AppState target)
        {
            target.playerID.value = _playerID;
            (new SetMasterClientAction(_masterClientID)).ExecuteTransaction(target);
            target.roomConnectionTime.value = _roomConnectionTime;
        }
    }

    public class SetMasterClientAction : StateTransaction<AppState>
    {
        private int _masterClientID;

        public SetMasterClientAction(int masterClientID)
        {
            _masterClientID = masterClientID;
        }

        protected override void Execute(AppState target)
        {
            target.masterClientID.value = _masterClientID;
        }
    }

    public class ApplyInitialSceneStateAction : StateTransaction<AppState>
    {
        private JSONNode _json;
        private SceneState _scene;

        public ApplyInitialSceneStateAction(JSONNode json)
        {
            _json = json;
        }

        public ApplyInitialSceneStateAction(SceneState scene)
        {
            _scene = scene;
        }

        protected override void Execute(AppState target)
        {
            if (_scene != null)
            {
                _scene.CopyTo(target.scene);
            }
            else if (_json != null)
            {
                target.scene.FromJSON(_json);
            }

            target.roomStateInitialized.value = true;
        }
    }

    public class SetRoomSceneInitializedAction : StateTransaction<AppState>
    {
        private bool _roomSceneInitialized;

        public SetRoomSceneInitializedAction(bool roomSceneInitialized)
        {
            _roomSceneInitialized = roomSceneInitialized;
        }

        protected override void Execute(AppState target)
        {
            target.roomDemoSceneInitialized.value = _roomSceneInitialized;
        }
    }

    public class AddLocalPlayerDataAction : StateTransaction<AppState>
    {
        protected override void Execute(AppState target)
        {
            var avatarID = PlayerIdHelpers.SceneObjectIdHelper.AllocateID();

            var playerState = target.scene.players.Add(target.playerID.value);
            playerState.avatar.value = avatarID;

            var objState = target.scene.objects.Add(avatarID);
            objState.ownerID.value = target.playerID.value;
            objState.viewPrefab.value = "PlayerAvatar";
            objState.allowOwnershipTransfer.value = false;
            objState.destroyOnOwnerDisconnect.value = true;

            var transformState = target.scene.transforms.Add(avatarID);

            new AddHighFrequencyPrimitive(transformState.localPosition, PlayerIdHelpers.HighFrequencyPathIdHelper.AllocateID(), target.playerID.value, 16).ExecuteTransaction(target);
            new AddHighFrequencyPrimitive(transformState.localRotation, PlayerIdHelpers.HighFrequencyPathIdHelper.AllocateID(), target.playerID.value, 16).ExecuteTransaction(target);
        }
    }

    public class AddHighFrequencyPrimitive : StateTransaction<AppState>
    {
        private IStateValue _target;
        private HighFrequencyPrimitiveId _id;
        private int _owner;
        private byte _syncRate;

        public AddHighFrequencyPrimitive(IStateValue target, HighFrequencyPrimitiveId id, int owner, byte syncRate)
        {
            _target = target;
            _id = id;
            _owner = owner;
            _syncRate = syncRate;
        }

        protected override void Execute(AppState target)
        {
            var data = target.scene.highFrequencyPrimitives.Add(_target.nodePath);
            data.id.value = _id;
            data.owner.value = _owner;
            data.syncRate.value = _syncRate;
        }
    }

    public class RemoveHighFrequencyPrimitive : StateTransaction<AppState>
    {
        private string _path;

        public RemoveHighFrequencyPrimitive(IStateValue target)
        {
            _path = target.nodePath;
        }

        public RemoveHighFrequencyPrimitive(string path)
        {
            _path = path;
        }

        protected override void Execute(AppState target)
        {
            target.scene.highFrequencyPrimitives.Remove(_path);
        }
    }

    public class SetRoomsAction : StateTransaction<AppState>
    {
        private GetRoomResponse[] _rooms;
        private bool _removeLocalRooms;

        public SetRoomsAction(GetRoomResponse[] rooms, bool removeLocalRooms = false)
        {
            _rooms = rooms;
            _removeLocalRooms = removeLocalRooms;
        }

        protected override void Execute(AppState target)
        {
            if (_rooms == null)
            {
                if (_removeLocalRooms)
                {
                    target.rooms.Clear();
                    return;
                }

                var toRemove = target.rooms.Where(x => !x.Value.isLocal.value).Select(x => x.Key).ToArray();

                foreach (var room in toRemove)
                    target.rooms.Remove(room);

                return;
            }

            var removed = _removeLocalRooms ?
                target.rooms.keys.Except(_rooms.Select(x => x.id)).ToArray() :
                target.rooms.Where(x => !x.Value.isLocal.value).Select(x => x.Key).Except(_rooms.Select(x => x.id)).ToArray();

            foreach (var room in _rooms)
            {
                var copyTo = target.rooms.GetOrAdd(room.id);
                copyTo.name.value = room.name;
                copyTo.demoScene.value = room.demo_scene;
                copyTo.version.value = room.version;
            }

            foreach (var toRemove in removed)
                target.rooms.Remove(toRemove);
        }
    }

    public class SetDemoScenesAction : StateTransaction<AppState>
    {
        private string[] _demoScenes;

        public SetDemoScenesAction(string[] demoScenes)
        {
            _demoScenes = demoScenes;
        }

        protected override void Execute(AppState target)
        {
            if (_demoScenes == null)
            {
                target.remoteDemoScenes.Clear();
                return;
            }

            target.remoteDemoScenes.SetFrom(_demoScenes);
        }
    }

    public class LoadUserSettings : StateTransaction<AppState>
    {
        private string _json;

        public LoadUserSettings(string json)
        {
            _json = json;
        }

        protected override void Execute(AppState state)
        {
            state.userSettings.FromJSON(_json);
        }
    }

    public class LeaveRoomAction : StateTransaction<AppState>
    {
        protected override void Execute(AppState state)
        {
            state.roomID.value = Guid.Empty;
            state.roomStateInitialized.Reset();
            state.roomDemoSceneInitialized.Reset();
            state.roomConnectionTime.Reset();
            state.masterClientID.Reset();
            state.playerID.Reset();
            state.scene.Reset();
        }
    }

    public class DestroyObjectAction : StateTransaction<AppState>
    {
        private SceneObjectId _objectID;

        public DestroyObjectAction(SceneObjectId objectID)
        {
            _objectID = objectID;
        }

        protected override void Execute(AppState state)
        {
            HashSet<string> _removedPaths = new HashSet<string>();

            foreach (var componentDictionary in state.scene.componentDictionaries)
            {
                if (componentDictionary.TryGetValue(_objectID, out var toRemove))
                {
                    _removedPaths.Add(toRemove.nodePath);
                    componentDictionary.Remove(_objectID);
                }
            }

            var removedHighFrequencyPaths = state.scene.highFrequencyPrimitives.keys
                .Where(highFrequencyPath => _removedPaths.Any(removedPath => highFrequencyPath.StartsWith(removedPath)));

            foreach (var path in removedHighFrequencyPaths)
                new RemoveHighFrequencyPrimitive(path).ExecuteTransaction(state);
        }
    }
}