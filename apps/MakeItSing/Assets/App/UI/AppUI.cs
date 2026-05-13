using UnityEngine;
using Nessle;

using static Nessle.UIBuilder;
using static Nessle.Props;

using ObserveThing;

using Cysharp.Threading.Tasks;

using static Plerion.MakeItSing.UIElements;
using UnityEngine.SceneManagement;
using System.Collections.Generic;
using System;
using UnityEngine.XR.Interaction.Toolkit.UI;

namespace Plerion.MakeItSing
{
    public class AppUI : MonoBehaviour
    {
        private IControl _ui;
        private IControl _overlayUI;
        private IDisposable _subscription;

        private void Awake()
        {
            _ui = SystemUICanvas(new()
            {
                element = { active = App.state.config.disableSystemUI.ObservableSelect(x => !x) },
                children = List(
                    Control("SystemUI", new()
                    {
                        layout = FillParentProps(),
                        children = List(
                            Observables.ObservableCombineValues(
                                App.state.config.disableSystemUI,
                                App.state.offlineMode,
                                App.state.loggedIn,
                                App.state.joiningRoom,
                                App.state.inRoom,
                                (disabled, offlineMode, loggedIn, joiningRoom, inRoom) =>
                                {
                                    if (disabled)
                                        return default;

                                    if (!loggedIn && !offlineMode)
                                        return GenerateLoginUI;

                                    if (!inRoom && !joiningRoom)
                                        return GenerateRoomSelectUI;

                                    if (inRoom)
                                        return GenerateInRoomUI;

                                    return default(Func<IControl>);
                                }
                            ).ObservableCreate(generator => generator?.Invoke())
                        )
                    })
                )
            });

            _overlayUI = OverlayUICanvas(new()
            {
                children = List(
                    NotificationList(new()
                    {
                        notifications = App.state.notifications,
                        layout = FillParentProps()
                    })
                )
            });
        }

        private void OnDestroy()
        {
            _ui?.Dispose();
            _overlayUI?.Dispose();
            _subscription?.Dispose();
        }

        private IControl GenerateLoginUI()
        {
            return LoginUI(new()
            {
                layout = FillParentProps(),
                domain = App.state.userSettings.domain,
                username = App.state.userSettings.username,
                password = App.state.userSettings.password,
                onDomainChanged = x => App.state.userSettings.domain.value = x,
                onUsernameChanged = x => App.state.userSettings.username.value = x,
                onPasswordChanged = x => App.state.userSettings.password.value = x,
                loginErrorMessage = App.state.loginError,
                onLoginSelected = () => Tasks.Login().Forget()
            });
        }

        private IControl GenerateRoomSelectUI()
        {
            return RoomSelectUI(new()
            {
                layout = FillParentProps(),
                demoScenes = App.state.remoteDemoScenes
                    .ObservableSelect(x => new DemoSceneProps()
                    {
                        id = x,
                        displayName = Value(x)
                    })
                    .ObservableConcat(List(EnumerateEmbeddedScenes()))
                    .ObservableOrderBy(x => x.displayName),
                rooms = App.state.rooms
                    .ObservableWhere(x => Observables.ObservableCombineValues(
                        x.Value.demoScene.ObservableSelect(x =>
                        {
                            if (x.StartsWith("EDITOR://"))
                                return Value(true);

                            if (x.StartsWith("EMBEDDED://"))
                                return Value(true);

                            if (x.StartsWith("FILE://"))
                                return Value(System.IO.File.Exists(x.Substring(7)));

                            return App.state.remoteDemoScenes.ObservableContains(x);
                        }),
                        App.state.loadedDemoScenes.ObservableSelect(x => x.Key).ObservableContains(x.Value.demoScene),
                        (sceneCanBeLoaded, sceneLoaded) => sceneCanBeLoaded || sceneLoaded
                    ))
                    .ObservableOrderByDescending(x => App.state.userSettings.recentRooms.ObservableTrack(x.Key).ObservableSelect(x => x.keyPresent ? x.value.AsObservable() : default))
                    .ObservableSelect(x => new RoomProps()
                    {
                        name = x.Value.name,
                        demoScene = x.Value.demoScene,
                        version = x.Value.version,
                        onSelected = () => App.state.roomID.value = x.Key,
                        recent = App.state.userSettings.recentRooms
                            .ObservableSelect(x => x.Key)
                            .ObservableContains(x.Key)
                    }),
                onCreateRoomSelected = (roomName, roomDemoScene) => CreateAndJoinRoom(roomName, roomDemoScene, App.state.version.value).Forget()
            });
        }

        private IControl GenerateInRoomUI()
        {
            return InRoomUI(new()
            {
                layout = FillParentProps(),
                onLeaveRoomSelected = () => App.ExecuteTransaction(new LeaveRoomAction()),
                showMenuButton = App.state.platform.ObservableSelect(x => x != Platform.MagicLeap)
            });

            // _screen = AppStateLog(new() { layout = FillParentProps() });
        }

        private IEnumerable<DemoSceneProps> EnumerateEmbeddedScenes()
        {
            for (int i = 0; i < SceneManager.sceneCountInBuildSettings; i++)
            {
                var path = SceneUtility.GetScenePathByBuildIndex(i);
                var name = System.IO.Path.GetFileNameWithoutExtension(path);

                if (name == "Main")
                    continue;

                yield return new DemoSceneProps()
                {
                    id = $"EMBEDDED://{i}",
                    displayName = Value(name)
                };
            }
        }

        private async UniTask CreateAndJoinRoom(string roomName, string roomDemoScene, string version)
        {
            if (App.state.offlineMode.value)
            {
                App.ExecuteTransaction(x =>
                {
                    var roomData = x.rooms.Add(Guid.NewGuid());
                    roomData.name.value = roomName;
                    roomData.demoScene.value = roomDemoScene;
                    roomData.version.value = version;
                    x.roomID.value = roomData.id;
                });

                return;
            }

            if (!SupabaseAPI.IsConfigured)
            {
                Debug.LogWarning("[AppUI] Cannot create room: Supabase is not configured. Use offline mode or provide UnityEnv.asset.");
                return;
            }

            var room = await SupabaseAPI.CreateRoom(roomName, roomDemoScene, version);
            App.ExecuteTransaction(x =>
            {
                var roomData = x.rooms.Add(room.id);
                roomData.name.value = room.name;
                roomData.demoScene.value = room.demo_scene;
                roomData.version.value = room.version;
                x.roomID.value = room.id;
            });
        }

        private IControl SystemUICanvas(CanvasProps props)
        {
            if (App.state.platform.value == Platform.MagicLeap)
            {
                props.worldCamera = Value(Camera.main);

                var camera = Camera.main.transform;
                var position = camera.forward;

                position.y = 0;
                position = position.normalized;
                position.y = camera.position.y - .33f;

                props.layout.localPosition = props.layout.localPosition ?? Value(position);
                props.layout.localRotation = props.layout.localRotation ?? Value(Quaternion.LookRotation(position - camera.position, Vector3.up));

                return WorldspaceCanvas(props);
            }
            else
            {
                return Canvas(props);
            }
        }

        private IControl WorldspaceCanvas(CanvasProps props)
        {
            props.worldCamera = props.worldCamera ?? Value(Camera.main);
            props.renderMode = props.renderMode ?? Value(RenderMode.WorldSpace);
            props.layout.localScale = props.layout.localScale ?? Value(new Vector3(0.001f, 0.001f, 0.001f));
            props.layout.sizeDelta = props.layout.sizeDelta ?? Value(new Vector2(960, 540));

            var control = Canvas(props);

            control.gameObject.AddComponent<TrackedDeviceGraphicRaycaster>();

            return control;
        }

        private IControl OverlayUICanvas(CanvasProps props)
        {
            if (App.state.platform.value == Platform.MagicLeap)
            {
                props.layout.localPosition = props.layout.localPosition ?? Value(Vector3.zero);
                props.layout.localRotation = props.layout.localRotation ?? Value(Quaternion.AngleAxis(180f, Vector3.up));

                return Tagalong(new()
                {
                    targetCamera = Value(Camera.main),
                    targetRegionMin = Value(new Vector3(0.4f, 0.3f, 0.66f)),
                    targetRegionMax = Value(new Vector3(0.6f, 0.7f, 1f)),
                    children = List(WorldspaceCanvas(props))
                });
            }
            else
            {
                props.sortingOrder = props.sortingOrder ?? Value(1);
                return Canvas(props);
            }
        }

        public struct NotificationListProps
        {
            public LayoutProps layout;
            public ElementProps element;
            public IListObservable<NotificationState> notifications;
        }

        private IControl NotificationList(NotificationListProps props)
        {
            return AnimatedList(new()
            {
                element = props.element,
                layout = props.layout,
                childControlWidth = Value(true),
                childControlHeight = Value(true),
                spacing = Value(5f),
                padding = Value(new RectOffset(0, 0, 0, 15)),
                childAlignment = Value(TextAnchor.LowerCenter),
                children = props.notifications?
                    .ObservableWhere(x => Observables.ObservableCombineValues(x.logLevel, App.state.config.notificationLogLevel, (level, minLevel) => level >= minLevel))
                    .ObservableSelect(x =>
                    {
                        bool isError = x.logLevel.value == Outernet.Logging.LogLevel.Error || x.logLevel.value == Outernet.Logging.LogLevel.Fatal;
                        return Notification(new()
                        {
                            message = x.message,
                            messageStyle = { color = isError ? Value(Color.red) : default },
                            backgroundStyle = { color = isError ? Value(new Color(0.33f, 0, 0)) : default }
                        });
                    })
            });
        }
    }
}