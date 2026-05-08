using Nessle;

using UnityEngine.Events;

using static Nessle.UIBuilder;
using static Nessle.Props;
using UnityEngine;
using ObserveThing;

namespace Plerion.MakeItSing
{
    public static partial class UIElements
    {
        public struct InRoomUIProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<bool> showMenuButton;
            public UnityAction onLeaveRoomSelected;
        }

        public static IControl InRoomUI(InRoomUIProps props)
        {
            ObservableValue<bool> open = new ObservableValue<bool>();

            return Control("InRoomUI", new()
            {
                element = props.element,
                layout = props.layout,
                children = List(
                    Control("Menu", new()
                    {
                        element = { active = open },
                        layout = FillParentProps(),
                        children = List(
                            Image(new()
                            {
                                style = { color = Value(elements.backgroundColor) },
                                layout = FillParentProps()
                            }),
                            VerticalLayout(new()
                            {
                                layout = FillParentProps(),
                                childControlWidth = Value(true),
                                childControlHeight = Value(true),
                                childForceExpandWidth = Value(true),
                                children = List(
                                    Text(new()
                                    {
                                        value = Value("Settings"),
                                        style =
                                        {
                                            fontSize = Value(40f),
                                            horizontalAlignment = Value(TMPro.HorizontalAlignmentOptions.Center)
                                        }
                                    }),
                                    Button(new()
                                    {
                                        background = { style = { color = Value(new Color(0.33f, 0, 0, 1f)) } },
                                        content = List(
                                            Text(new()
                                            {
                                                value = Value("Leave Room"),
                                                style =
                                                {
                                                    color = Value(Color.red),
                                                    horizontalAlignment = Value(TMPro.HorizontalAlignmentOptions.Center)
                                                }
                                            })
                                        ),
                                        onClick = props.onLeaveRoomSelected
                                    })
                                )
                            })
                        )
                    }),
                    RoundButton(new()
                    {
                        element = { active = props.showMenuButton },
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
                        onClick = () => open.value = !open.value
                    })
                )
            });
        }
    }
}