using UnityEngine;
using Unity.Mathematics;
using FofX.Stateful;
using System;
using ObserveThing;
using UnityEngine.Splines;
using FofX;
using System.Collections;
using System.Collections.Generic;

namespace Plerion.MakeItSing
{
    public enum Platform
    {
        Windows,
        OSX,
        Linux,
        MagicLeap,
        AndroidMobile
    }

    public enum LoginStatus
    {
        NotLoggedIn,
        LoginRequested,
        LoggingIn,
        LoggedIn,
        Error
    }

    public class AppConfigState : StateObject
    {
        public StateValue<LogGroup> logGroups { get; private set; }
        public StateValue<Outernet.Logging.LogLevel> logLevel { get; private set; }
        public StateValue<Outernet.Logging.LogLevel> stackTraceLevel { get; private set; }
        public StateValue<Outernet.Logging.LogLevel> notificationLevel { get; private set; }
        public StateValue<bool> disableSystemUI { get; private set; }
    }

    public class AppState : StateObject
    {
        public StateValue<Platform> platform { get; private set; }
        public StateValue<string> version { get; private set; }
        public UserSettings userSettings { get; private set; }
        public AppConfigState config { get; private set; }
        public StateValue<bool> offlineMode { get; private set; }
        public StateValue<bool> systemUIOpen { get; private set; }

#if UNITY_EDITOR
        public EditorOnlyState editorOnly { get; private set; }
#endif

        public StateValue<LoginStatus> loginStatus { get; private set; }
        public StateValue<bool> loggedIn { get; private set; }
        public StateValue<string> loginError { get; private set; }

        public ConnectionState nameServerConnection { get; private set; }
        public ConnectionState roomConnection { get; private set; }

        public StateValue<double2> roughGrainedLocation { get; private set; }
        public StateValue<double3> sceneOriginEcefPosition { get; private set; }
        public StateValue<quaternion> sceneOriginEcefRotation { get; private set; }

        public StateDictionary<Guid, RoomData> rooms { get; private set; }
        public StateValueSet<string> remoteDemoScenes { get; private set; }
        public StateDictionary<string, StateValue<string>> loadedDemoScenes { get; private set; }

        public StateValue<Guid> roomID { get; private set; }

        public StateValue<int> playerID { get; private set; }
        public StateValue<int> masterClientID { get; private set; }
        public StateValue<bool> isMasterClient { get; private set; }

        public StateValue<bool> joiningRoom { get; private set; }
        public StateValue<bool> inRoom { get; private set; }
        public StateValue<bool> roomDemoSceneInitialized { get; private set; }
        public StateValue<bool> roomStateInitialized { get; private set; }
        public StateValue<bool> inRoomAndSynchronized { get; private set; }
        public StateValue<float> roomConnectionTime { get; private set; }

        public SceneState scene { get; private set; }

        public StateList<NotificationState> notifications { get; private set; }

        protected override void PostInitializeInternal()
        {
            loggedIn.Derive(loginStatus.ObservableSelect(x => x == LoginStatus.LoggedIn));

            nameServerConnection.shouldBeConnected.Derive(
                Observables.ObservableCombineValues(
                    offlineMode,
                    loggedIn,
                    nameServerConnection.connectionString,
                    (offlineMode, loggedIn, connectionString) => !offlineMode && loggedIn && !string.IsNullOrEmpty(connectionString)
                )
            );

            roomConnection.connectionString.Derive(roomID.ObservableSelect(x => x == Guid.Empty ? null : x.ToString()));

            roomConnection.shouldBeConnected.Derive(
                Observables.ObservableCombineValues(
                    offlineMode,
                    nameServerConnection.status,
                    roomConnection.connectionString,
                    (offlineMode, status, connectionString) =>
                        !offlineMode &&
                        status == ConnectionStatus.Connected &&
                        !string.IsNullOrEmpty(connectionString)
                )
            );

            inRoom.Derive(
                Observables.ObservableCombineValues(
                    offlineMode,
                    roomID,
                    roomConnection.connected,
                    (offlineMode, roomID, connectedToRoom) => (offlineMode && roomID != Guid.Empty) || connectedToRoom
                )
            );

            joiningRoom.Derive(
                Observables.ObservableCombineValues(
                    roomID,
                    inRoom,
                    (roomID, inRoom) => roomID != Guid.Empty && !inRoom
                )
            );

            inRoomAndSynchronized.Derive(
                Observables.ObservableCombineValues(
                    inRoom,
                    roomStateInitialized,
                    roomDemoSceneInitialized,
                    (inRoom, stateInit, sceneInit) => inRoom && stateInit && sceneInit
                )
            );

            isMasterClient.Derive(
                Observables.ObservableCombineValues(
                    playerID,
                    masterClientID,
                    inRoom,
                    (player, masterClient, inRoom) => player == masterClient && inRoom
                )
            );
        }
    }

#if UNITY_EDITOR
    public class EditorOnlyState : StateObject
    {

    }
#endif

    public class NotificationState : StateObject
    {
        public StateValue<string> message { get; private set; }
        public StateValue<float> generatedTime { get; private set; }
        public StateValue<float> displayDuration { get; private set; }
        public StateValue<Outernet.Logging.LogLevel> logLevel { get; private set; }
    }

    public class RoomData : StateObject, IKeyedStateNode<Guid>
    {
        public Guid id { get; private set; }
        public StateValue<string> name { get; private set; }
        public StateValue<string> demoScene { get; private set; }
        public StateValue<string> version { get; private set; }
        public StateValue<bool> isLocal { get; private set; }

        void IKeyedStateNode<Guid>.AssignKey(Guid key)
            => id = key;
    }


    public enum ConnectionStatus
    {
        Disconnected,
        Connecting,
        Connected,
        Disconnecting,
        Error
    }

    public class ConnectionState : StateObject
    {
        public StateValue<string> connectionString { get; private set; }
        public StateValue<bool> shouldBeConnected { get; private set; }
        public StateValue<ConnectionStatus> status { get; private set; }
        public StateValue<bool> connected { get; private set; }
        public StateValue<string> error { get; private set; }

        protected override void PostInitializeInternal()
        {
            connected.Derive(
                status.ObservableSelect(x => x == ConnectionStatus.Connected)
            );
        }
    }

    public class UserSettings : StateObject
    {
        public StateValue<string> domain { get; private set; }
        public StateValue<string> username { get; private set; }
        public StateValue<string> password { get; private set; }
        public StateDictionary<Guid, StateValue<DateTime>> recentRooms { get; private set; }
    }

    public class SceneState : StateObject
    {
        public StateValue<float> startTime { get; private set; }
        public StateDictionary<int, PlayerData> players { get; private set; }
        public StateDictionary<SceneObjectId, StateValue<int>> avatarToPlayer { get; private set; }
        public StateDictionary<SceneObjectId, SceneObjectState> objects { get; private set; }
        public StateDictionary<SceneObjectId, SceneTransformState> transforms { get; private set; }
        public StateDictionary<SceneObjectId, SplineState> splines { get; private set; }

        public StateDictionary<string, HighFrequencyPrimitiveData> highFrequencyPrimitives { get; private set; }
        public StateDictionary<HighFrequencyPrimitiveId, StateValue<string>> highFrequencyPrimitivesById { get; private set; }

        public IEnumerable<IStateDictionary> componentDictionaries
        {
            get
            {
                yield return objects;
                yield return transforms;
                yield return splines;
            }
        }

        protected override void PostInitializeInternal()
        {
            avatarToPlayer.Derive(
                players.ObservableToDictionary(
                    x => x.Value.avatar.AsObservable(),
                    x =>
                    {
                        var prim = new StateValue<int>();
                        prim.Initialize(avatarToPlayer, x.Key.ToString());
                        prim.Derive(new ObservableValue<int>(x.Value.playerID));
                        return prim;
                    }
                )
            );

            highFrequencyPrimitivesById.Derive(
                highFrequencyPrimitives.ObservableToDictionary(
                    x => x.Value.id.AsObservable(),
                    x =>
                    {
                        var prim = new StateValue<string>();
                        prim.Initialize(highFrequencyPrimitivesById, x.Key);
                        prim.Derive(new ObservableValue<string>(x.Value.path));
                        return prim;
                    }
                )
            );
        }
    }

    public class SceneObjectComponentState : StateObject, IKeyedStateNode<SceneObjectId>
    {
        public SceneObjectId id { get; private set; }

        void IKeyedStateNode<SceneObjectId>.AssignKey(SceneObjectId key)
            => id = key;
    }

    public class SceneObjectState : SceneObjectComponentState
    {
        public StateValue<int> ownerID { get; private set; }
        public StateValue<bool> isMine { get; private set; }
        public StateValue<bool> allowOwnershipTransfer { get; private set; } = new StateValue<bool>(true);
        public StateValue<string> viewPrefab { get; private set; }
        public StateValue<bool> destroyOnOwnerDisconnect { get; private set; }

        protected override void PostInitializeInternal()
        {
            if (root is AppState) // sometimes scene state is generated standalone- in those cases we don't need to derive this state
            {
                isMine.Derive(Observables.ObservableCombineValues(
                    ((AppState)root).playerID,
                    ownerID,
                    (playerID, ownerID) => playerID == ownerID
                ));
            }
            else
            {
                isMine.Derive(new ObservableValue<bool>(false));
            }
        }
    }

    public class SceneTransformState : SceneObjectComponentState
    {
        public StateValue<Vector3> localPosition { get; private set; }
        public StateValue<Quaternion> localRotation { get; private set; } = new StateValue<Quaternion>(Quaternion.identity);
        public StateValue<Vector3> localScale { get; private set; } = new StateValue<Vector3>(Vector3.one);
    }

    public class SplineState : SceneObjectComponentState
    {
        public StateList<StateValueArray<BezierKnot>> splines { get; private set; }
    }

    public class HighFrequencyPrimitiveData : StateObject, IKeyedStateNode<string>
    {
        public string path { get; private set; }
        public StateValue<HighFrequencyPrimitiveId> id { get; private set; }
        public StateValue<int> owner { get; private set; }
        public StateValue<byte> syncRate { get; private set; }

        void IKeyedStateNode<string>.AssignKey(string key)
            => path = key;
    }


    public class PlayerData : StateObject, IKeyedStateNode<int>
    {
        public int playerID { get; private set; }
        public StateValue<SceneObjectId> avatar { get; private set; }

        public void AssignKey(int key)
            => playerID = key;
    }

    [System.Serializable]
    public struct SceneObjectId
    {
        public static SceneObjectId Empty => new SceneObjectId(0);

        public int value => _value;
        public bool IsEmpty => _value == 0;

        [HideInInspector, SerializeField]
        private int _value;

        public SceneObjectId(int value)
        {
            _value = value;
        }

        public override string ToString()
        {
            return $"{nameof(SceneObjectId)}[{value}]";
        }
    }

    public struct HighFrequencyPrimitiveId
    {
        public static HighFrequencyPrimitiveId Empty => new HighFrequencyPrimitiveId(0);

        public int value { get; }
        public bool IsEmpty => value == 0;

        public HighFrequencyPrimitiveId(int value)
        {
            this.value = value;
        }

        public override string ToString()
        {
            return $"{nameof(HighFrequencyPrimitiveId)}[{value}]";
        }
    }
}