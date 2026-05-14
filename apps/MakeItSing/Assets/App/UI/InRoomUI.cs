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
            public UnityAction onLeaveRoomSelected;
        }

        public static IControl InRoomUI(InRoomUIProps props)
        {
            return Control("InRoomMenu", new()
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
                        layout = FillParentProps(),
                        childControlWidth = Value(true),
                        childControlHeight = Value(true),
                        childForceExpandWidth = Value(true),
                        padding = Value(new RectOffset(10, 10, 10, 10)),
                        children = List(
                            Text(new()
                            {
                                value = Value("Settings"),
                                style =
                                {
                                    fontSize = Value(20f),
                                    horizontalAlignment = Value(TMPro.HorizontalAlignmentOptions.Center)
                                }
                            }),
                            Text(new()
                            {
                                value = Value("Add content here!"),
                                style = { horizontalAlignment = Value(TMPro.HorizontalAlignmentOptions.Center) }
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
            });
        }
    }
}