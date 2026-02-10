using UnityEngine;
using Nessle;

using static Nessle.UIBuilder;
using static Nessle.Props;
using ObserveThing;
using ObserveThing.StatefulExtensions;
using System;
using UnityEngine.Events;
using FofX.Stateful;

namespace Plerion.MakeItSing
{
    public class AppUI : MonoBehaviour
    {
        private IControl _ui;

        private void Awake()
        {
            _ui = Canvas(new()
            {
                children = List(
                    Observables.Combine(
                        App.state.loggedIn.AsObservable(),
                        App.state.roomConnection.shouldBeConnected.AsObservable(),
                        App.state.roomConnection.status.AsObservable(),
                        (loggedIn, shouldConnectToRoom, connectionStatus) =>
                        {
                            if (!loggedIn)
                            {
                                return LoginUI(new()
                                {
                                    layout = GetPlatformLayoutProps(),
                                    domain = App.state.userSettings.domain.AsObservable(),
                                    username = App.state.userSettings.username.AsObservable(),
                                    password = App.state.userSettings.password.AsObservable(),
                                    onDomainChanged = x => App.state.userSettings.domain.ExecuteSetOrDelay(x),
                                    onUsernameChanged = x => App.state.userSettings.username.ExecuteSetOrDelay(x),
                                    onPasswordChanged = x => App.state.userSettings.password.ExecuteSetOrDelay(x),
                                    onLoginSelected = () =>
                                    {
                                        // do here
                                    }
                                });
                            }
                            else if (!shouldConnectToRoom)
                            {
                                return RoomSelectUI(new()
                                {
                                    layout = GetPlatformLayoutProps(),

                                });
                            }
                            else if (connectionStatus != ConnectionStatus.Connected)
                            {
                                return ConnectingToRoomUI();
                            }
                            else
                            {
                                return null;
                            }
                        }
                    )
                )
            });
        }

        private LayoutProps GetPlatformLayoutProps()
        {
            if (Application.isMobilePlatform)
            {
                return FillParentProps();
            }
            else
            {
                return new LayoutProps()
                {
                    anchorMin = Value(new Vector2(0.33f, 0)),
                    anchorMax = Value(new Vector2(0.66f, 1)),
                    offsetMin = Value(new Vector2(0, 0)),
                    offsetMax = Value(new Vector2(0, 0))
                };
            }
        }

        public struct LoginUIProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<string> domain;
            public IValueObservable<string> username;
            public IValueObservable<string> password;
            public UnityAction<string> onDomainChanged;
            public UnityAction<string> onUsernameChanged;
            public UnityAction<string> onPasswordChanged;
            public UnityAction onLoginSelected;
        }

        private IControl LoginUI(LoginUIProps props)
        {
            return Control(
                "LoginUI",
                new()
                {
                    element = props.element,
                    layout = props.layout,
                    children = List(
                        VerticalLayout(new()
                        {
                            layout =
                            {
                                anchorMin = Value(new Vector2(0.5f, 0.5f)),
                                anchorMax = Value(new Vector2(0.5f, 0.5f)),
                                sizeDelta = Value(new Vector2(400, 0)),
                                fitContentVertical = Value(UnityEngine.UI.ContentSizeFitter.FitMode.PreferredSize)
                            },
                            childAlignment = Value(TextAnchor.MiddleCenter),
                            spacing = Value(10f),
                            childControlWidth = Value(true),
                            childControlHeight = Value(true),
                            children = List(
                                LabeledProperty(new()
                                {
                                    label = Value("Domain"),
                                    labelWidth = Value(100f),
                                    content = Value(InputField(new()
                                    {
                                        value = props.domain,
                                        layout = { flexibleWidth = Value(true) },
                                        onValueChanged = props.onDomainChanged
                                    }))
                                }),
                                LabeledProperty(new()
                                {
                                    label = Value("Username"),
                                    labelWidth = Value(100f),
                                    content = Value(InputField(new()
                                    {
                                        value = props.domain,
                                        layout = { flexibleWidth = Value(true) },
                                        onValueChanged = props.onUsernameChanged
                                    }))
                                }),
                                LabeledProperty(new()
                                {
                                    label = Value("Password"),
                                    labelWidth = Value(100f),
                                    content = Value(InputField(new()
                                    {
                                        value = props.domain,
                                        layout = { flexibleWidth = Value(true) },
                                        contentType = Value(TMPro.TMP_InputField.ContentType.Password),
                                        onValueChanged = props.onPasswordChanged
                                    }))
                                }),
                                HorizontalLayout(new()
                                {
                                    childControlHeight = Value(true),
                                    childControlWidth = Value(true),
                                    childAlignment = Value(TextAnchor.MiddleCenter),
                                    children = List(
                                        Button(new()
                                        {
                                            onClick = props.onLoginSelected,
                                            content = List(Text(new() { value = Value("Login") }))
                                        })
                                    )
                                })
                            )
                        })
                    )
                }
            );
        }

        public static LayoutProps FillParentProps(LayoutProps from = default)
        {
            from.anchorMin = from.anchorMin ?? Value(new Vector2(0, 0));
            from.anchorMax = from.anchorMax ?? Value(new Vector2(1, 1));
            from.offsetMin = from.offsetMin ?? Value(new Vector2(0, 0));
            from.offsetMax = from.offsetMax ?? Value(new Vector2(0, 0));

            return from;
        }

        public struct LabeledPropertyProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<string> label;
            public IValueObservable<float> labelWidth;
            public IValueObservable<IControl> content;
        }

        private static IControl LabeledProperty(LabeledPropertyProps props)
        {
            return HorizontalLayout(new()
            {
                element = props.element,
                layout = props.layout,
                childAlignment = Value(TextAnchor.MiddleLeft),
                spacing = Value(10f),
                childControlWidth = Value(true),
                childControlHeight = Value(true),
                children = List(
                    Value(Text(new()
                    {
                        value = props.label,
                        layout =
                        {
                            preferredWidth = props.labelWidth,
                            minWidth = props.labelWidth
                        }
                    })),
                    props.content
                )
            });
        }

        public struct RoomSelectUIProps
        {
            public ElementProps element;
            public LayoutProps layout;

            public IValueObservable<string> roomName;

            public IListObservable<string> activeRooms;
            public IListObservable<string> recentRooms;

            public Action<string> onRoomSelected;
        }

        private IControl RoomSelectUI(RoomSelectUIProps props)
        {
            ValueObservable<string> internalRoomName = new ValueObservable<string>();

            return Control(
                "RoomSelectUI",
                new()
                {
                    element = props.element,
                    layout = props.layout,
                    children = List(
                        VerticalLayout(new()
                        {
                            childControlHeight = Value(true),
                            childControlWidth = Value(true),
                            spacing = Value(10f),
                            layout =
                            {
                                anchorMin = Value(new Vector2(0, 0f)),
                                anchorMax = Value(new Vector2(1, 0.5f)),
                                offsetMin = Value(new Vector2(0, 0)),
                                offsetMax = Value(new Vector2(0, 45f)) // center the input field in the middle of the screen
                            },
                            children = List(
                                Text(new()
                                {
                                    value = Value("Join Room"),
                                    style =
                                    {
                                        verticalAlignment = Value(TMPro.VerticalAlignmentOptions.Baseline),
                                        horizontalAlignment = Value(TMPro.HorizontalAlignmentOptions.Center)
                                    }
                                }),
                                LabeledProperty(new()
                                {
                                    label = Value("Room Name"),
                                    labelWidth = Value(100f),
                                    content = Value(
                                        HorizontalLayout(new()
                                        {
                                            layout = { flexibleWidth = Value(true) },
                                            spacing = Value(10f),
                                            childAlignment = Value(TextAnchor.MiddleLeft),
                                            childControlHeight = Value(true),
                                            childControlWidth = Value(true),
                                            children = List(
                                                InputField(new()
                                                {
                                                    value = props.roomName,
                                                    layout = { flexibleWidth = Value(true) },
                                                    onValueChanged = x => internalRoomName.value = x
                                                }),
                                                Button(new()
                                                {
                                                    content = List(
                                                        Text(new()
                                                        {
                                                            value = props.activeRooms
                                                                .ContainsDynamic(internalRoomName)
                                                                .SelectDynamic(x => x ? "Join" : "Create"),
                                                            layout = { minWidth = Value(100f) }
                                                        })
                                                    )
                                                })
                                            )
                                        })
                                    )
                                }),
                                VerticalLayout(new()
                                {
                                    element = { active = props.activeRooms.CountDynamic().SelectDynamic(x => x > 0) },
                                    childControlHeight = Value(true),
                                    childControlWidth = Value(true),
                                    spacing = Value(10f),
                                    children = List(
                                        Text(new() { value = Value("Active") }),
                                        VerticalLayout(new()
                                        {
                                            childControlHeight = Value(true),
                                            childControlWidth = Value(true),
                                            spacing = Value(10f),
                                            children = props.activeRooms.CreateDynamic(x => Button(new()
                                            {
                                                background = { sprite = Value(default(Sprite)) },
                                                content = List(Text(new() { value = Value(x), })),
                                                onClick = () => props.onRoomSelected?.Invoke(x)
                                            }))
                                        })
                                    )
                                }),
                                VerticalLayout(new()
                                {
                                    element = { active = props.activeRooms.CountDynamic().SelectDynamic(x => x > 0) },
                                    childControlHeight = Value(true),
                                    childControlWidth = Value(true),
                                    spacing = Value(10f),
                                    children = List(
                                        Text(new() { value = Value("Active") }),
                                        VerticalLayout(new()
                                        {
                                            childControlHeight = Value(true),
                                            childControlWidth = Value(true),
                                            spacing = Value(10f),
                                            children = props.activeRooms.CreateDynamic(x => Button(new()
                                            {
                                                background = { sprite = Value(default(Sprite)) },
                                                content = List(Text(new() { value = Value(x), })),
                                                onClick = () => props.onRoomSelected?.Invoke(x)
                                            }))
                                        })
                                    )
                                })
                            )
                        })
                    )
                }
            );
        }

        private IControl ConnectingToRoomUI()
        {

        }
    }
}