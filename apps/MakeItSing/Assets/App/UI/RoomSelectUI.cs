using System;

using UnityEngine;
using UnityEngine.Events;

using FofX.Stateful;

using Nessle;

using ObserveThing;

using static Nessle.UIBuilder;
using static Nessle.Props;

namespace Plerion.MakeItSing
{
    public static partial class UIElements
    {
        public struct RoomProps
        {
            public IValueObservable<string> name;
            public IValueObservable<string> version;
            public IValueObservable<string> demoScene;
            public IValueObservable<bool> recent;
            public UnityAction onSelected;
        }

        public struct DemoSceneProps
        {
            public string id;
            public IValueObservable<string> displayName;
        }

        public struct RoomSelectUIProps
        {
            public ElementProps element;
            public LayoutProps layout;

            public IValueObservable<string> roomName;
            public IValueObservable<string> demoScene;
            public IListObservable<RoomProps> rooms;
            public IListObservable<DemoSceneProps> demoScenes;
            public Action<string, string> onCreateRoomSelected;
        }

        public static IControl RoomSelectUI(RoomSelectUIProps props)
        {
            ObservableValue<string> internalRoomName = new ObservableValue<string>();
            string demoSceneId = default;

            props.element.bindings = props.element.bindings.With(
                props.roomName?.Subscribe(x => internalRoomName.value = x)
            );

            var recentRooms = props.rooms?.ObservableWhere(x => x.recent ?? Value(false));
            var unaccessedRooms = props.rooms?.ObservableExcept(recentRooms);

            return Control(
                "RoomSelectUI",
                new()
                {
                    element = props.element,
                    layout = props.layout,
                    children = List(
                        Image(new()
                        {
                            style = { color = Value(elements.backgroundColor) },
                            layout = FillParentProps()
                        }),
                        VerticalLayout(new()
                        {
                            childControlHeight = Value(true),
                            childControlWidth = Value(true),
                            childAlignment = Value(TextAnchor.MiddleCenter),
                            layout = FillParentProps(),
                            padding = Value(new RectOffset(20, 20, 0, 0)),
                            children = List(
                                Control(
                                    "SafeArea",
                                    new()
                                    {
                                        layout =
                                        {
                                            preferredWidth = Value(600f),
                                            flexibleWidth = Value(0f),
                                            flexibleHeight = Value(1f)
                                        },
                                        children = List(
                                            VerticalLayout(new()
                                            {
                                                childControlHeight = Value(true),
                                                childControlWidth = Value(true),
                                                spacing = Value(10f),
                                                childAlignment = Value(TextAnchor.LowerLeft),
                                                padding = Value(new RectOffset(0, 0, 0, 10)),
                                                layout =
                                                {
                                                    anchorMin = Value(new Vector2(0f, 0.5f)),
                                                    anchorMax = Value(new Vector2(1f, 1f)),
                                                    offsetMin = Value(new Vector2(0f, 0f)),
                                                    offsetMax = Value(new Vector2(0f, 0f)),
                                                    pivot = Value(new Vector2(0.5f, 0f))
                                                },
                                                children = List(
                                                    Text(new()
                                                    {
                                                        value = Value("Join Room"),
                                                        style = { fontSize = Value(20f) }
                                                    }),
                                                    LabeledProperty(new()
                                                    {
                                                        label = Value("Room Name"),
                                                        labelWidth = Value(100f),
                                                        content = Value(
                                                            HorizontalLayout(new()
                                                            {
                                                                layout = { flexibleWidth = Value(1f) },
                                                                spacing = Value(10f),
                                                                childAlignment = Value(TextAnchor.MiddleLeft),
                                                                childControlHeight = Value(true),
                                                                childControlWidth = Value(true),
                                                                children = List(
                                                                    PlatformInputField(new()
                                                                    {
                                                                        inputField =
                                                                        {
                                                                            value = internalRoomName,
                                                                            layout = { flexibleWidth = Value(1f) },
                                                                            onValueChanged = x => internalRoomName.value = x
                                                                        }
                                                                    }),
                                                                    TypedDropdown<string>(new()
                                                                    {
                                                                        displayNameSelector = x => props.demoScenes?.ObservableFirstOrDefault(y => y.id == x).ObservableSelect(x => x.displayName),
                                                                        options = props.demoScenes?.ObservableSelect(x => x.id),
                                                                        value = props.demoScene,
                                                                        onValueChanged = x => demoSceneId = x
                                                                    }),
                                                                    Button(new()
                                                                    {
                                                                        onClick = () => props.onCreateRoomSelected?.Invoke(internalRoomName.value, demoSceneId),
                                                                        content = List(
                                                                            Text(new() { value = Value("Create") })
                                                                        )
                                                                    })
                                                                )
                                                            })
                                                        )
                                                    })
                                                )
                                            }),
                                            VerticalScrollRect(new()
                                            {
                                                layout =
                                                {
                                                    anchorMin = Value(new Vector2(0, 0f)),
                                                    anchorMax = Value(new Vector2(1, 0.5f)),
                                                    offsetMin = Value(new Vector2(0, 0)),
                                                    offsetMax = Value(new Vector2(0, 0))
                                                },
                                                childForceExpandWidth = Value(true),
                                                children = List(
                                                    VerticalLayout(new()
                                                    {
                                                        element = { active = recentRooms?.ObservableCount().ObservableSelect(x => x > 0) ?? Value(false) },
                                                        childControlHeight = Value(true),
                                                        childControlWidth = Value(true),
                                                        spacing = Value(10f),
                                                        children = List(
                                                            Text(new() { value = Value("Recent") }),
                                                            VerticalLayout(new()
                                                            {
                                                                childControlHeight = Value(true),
                                                                childControlWidth = Value(true),
                                                                childForceExpandWidth = Value(true),
                                                                spacing = Value(10f),
                                                                children = recentRooms?.ObservableCreate(RoomListElement)
                                                            })
                                                        )
                                                    }),
                                                    VerticalLayout(new()
                                                    {
                                                        element = { active = unaccessedRooms?.ObservableCount().ObservableSelect(x => x > 0) ?? Value(false) },
                                                        childControlHeight = Value(true),
                                                        childControlWidth = Value(true),
                                                        spacing = Value(10f),
                                                        children = List(
                                                            Text(new() { value = Value("Rooms") }),
                                                            VerticalLayout(new()
                                                            {
                                                                childControlHeight = Value(true),
                                                                childControlWidth = Value(true),
                                                                childForceExpandWidth = Value(true),
                                                                spacing = Value(10f),
                                                                children = unaccessedRooms?.ObservableCreate(RoomListElement)
                                                            })
                                                        )
                                                    })
                                                )
                                            })
                                        )
                                    }
                                )
                            )
                        })
                    )
                }
            );
        }

        private static IControl RoomListElement(RoomProps props)
        {
            return Button(new()
            {
                content = List(Text(new() { value = props.name, })),
                onClick = props.onSelected
            });
        }
    }
}