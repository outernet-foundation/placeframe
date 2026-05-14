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
using UnityEngine.InputSystem;

namespace Plerion.MakeItSing
{
    public class AppUI : MonoBehaviour
    {
        private IControl _ui;
        private IControl _notificationUI;
        private IDisposable _subscriptions;

        private InputAction _spaceAction = new InputAction(type: InputActionType.Button, binding: "<Keyboard>/space");
        private InputAction _magicLeapMenuButtonAction = new InputAction(type: InputActionType.Button, binding: "<MagicLeapController>/menu");

        private void Awake()
        {
            _spaceAction.Enable();
            _magicLeapMenuButtonAction.Enable();

            _subscriptions = App.state.inRoom.Subscribe(inRoom => App.state.systemUIOpen.value = !inRoom);

            var systemUILayoutProps = default(LayoutProps);

            if (App.state.platform.value == Platform.MagicLeap)
            {
                var transform = App.state.systemUIOpen.ObservableSelect(
                    open =>
                    {
                        var camera = Camera.main;
                        var forward = camera.transform.forward;

                        forward.y = 0;
                        forward = forward.normalized;
                        forward.y = -0.33f;

                        var position = camera.transform.position + forward;
                        var rotation = Quaternion.LookRotation(position - camera.transform.position, Vector3.up);

                        return (position, rotation);
                    }
                );

                systemUILayoutProps.localPosition = transform.ObservableSelect(x => x.position);
                systemUILayoutProps.localRotation = transform.ObservableSelect(x => x.rotation);
            }
            else
            {
                systemUILayoutProps = FillParentProps();
            }

            _ui = SystemUICanvas(new()
            {
                element = { active = App.state.config.disableSystemUI.ObservableSelect(x => !x) },
                layout = systemUILayoutProps,
                worldCamera = Value(Camera.main),
                children = List(
                    Control("Menu", new()
                    {
                        element = { active = App.state.systemUIOpen },
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
                    }),
                    RoundButton(new()
                    {
                        element =
                        {
                            active = Observables.ObservableCombineValues(
                                App.state.inRoom,
                                App.state.joiningRoom,
                                App.state.platform.ObservableSelect(x => x != Platform.MagicLeap),
                                (inRoom, joiningRoom, platformValid) => inRoom && !joiningRoom && platformValid
                            )
                        },
                        layout =
                        {
                            sizeDelta = Value(new Vector2(35, 35)),
                            anchorMin = Value(new Vector2(1, 1)),
                            anchorMax = Value(new Vector2(1, 1)),
                            localPosition = Value(new Vector3(-10, -10, 0)),
                            pivot = Value(new Vector2(1, 1))
                        },
                        content = List(Image(new() { sprite = Value(elements.hamburgerMenu) })),
                        padding = Value(new RectOffset(9, 9, 9, 9)),
                        onClick = () => App.state.systemUIOpen.value = !App.state.systemUIOpen.value
                    })
                )
            });

            if (App.state.platform.value == Platform.MagicLeap)
            {
                _notificationUI = Tagalong(new()
                {
                    targetCamera = Value(Camera.main),
                    targetRegionMin = Value(new Vector3(0.45f, 0.45f, 1f)),
                    targetRegionMax = Value(new Vector3(0.55f, 0.4f, 1.25f)),
                    paddingLeft = Value(0.03f),
                    paddingRight = Value(0.03f),
                    paddingTop = Value(0.25f),
                    children = List(WorldspaceCanvas(new()
                    {
                        layout =
                        {
                            localPosition = Value(Vector3.zero),
                            localRotation = Value(Quaternion.AngleAxis(180f, Vector3.up)),
                            pivot = Value(new Vector2(0.5f, 0))
                        },
                        children = List(NotificationList(new()
                        {
                            layout = FillParentProps(),
                            notifications = App.state.notifications
                        }))
                    }))
                });
            }
            else
            {
                _notificationUI = Canvas(new()
                {
                    sortingOrder = Value(1),
                    children = List(NotificationList(new()
                    {
                        layout = FillParentProps(),
                        notifications = App.state.notifications
                    }))
                });
            }
        }

        private void Update()
        {
            if (_magicLeapMenuButtonAction.WasPerformedThisFrame() || _spaceAction.WasPerformedThisFrame())
                App.state.systemUIOpen.value = !App.state.systemUIOpen.value;
        }

        private void OnDestroy()
        {
            _ui?.Dispose();
            _notificationUI?.Dispose();
            _subscriptions?.Dispose();
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
                onLeaveRoomSelected = () => App.ExecuteTransaction(new LeaveRoomAction())
            });
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
                props.layout.sizeDelta = props.layout.sizeDelta ?? Value(new Vector2(800, 540));

                return Tagalong(new()
                {
                    targetCamera = Value(Camera.main),
                    targetRegionMin = Value(new Vector3(0.45f, 0.45f, 1f)),
                    targetRegionMax = Value(new Vector3(0.55f, 0.4f, 1.25f)),
                    paddingLeft = Value(0.03f),
                    paddingRight = Value(0.03f),
                    paddingTop = Value(0.25f),
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
                    .ObservableWhere(x => Observables.ObservableCombineValues(x.logLevel, App.state.config.notificationLevel, (level, minLevel) => level >= minLevel))
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