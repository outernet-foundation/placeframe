using Nessle;
using UnityEngine;

using ObserveThing;

using static Nessle.UIBuilder;
using static Nessle.Props;

using System;
using ObserveThing.StatefulExtensions;
using UnityEngine.InputSystem;

namespace Outernet.MapRegistrationTool
{
    public class UIElementSet : ScriptableObject
    {
        public Color backgroundColor;
        public Color midgroundColor;
        public Color foregroundColor;
        public Sprite panelSprite;
        public Sprite addButtonSprite;
        public Nessle.Control<DropZoneProps> dropZone;
    }

    public static partial class UIElements
    {
        public static UIElementSet elements;

        public static IControl UI()
        {
            return Canvas(new()
            {
                children = List(
                    ResizablePanel(new()
                    {
                        rightEnabled = Value(true),
                        backgroundColor = Value(elements.backgroundColor),
                        layout =
                        {
                            pivot = Value(new Vector2(0, 0.5f)),
                            anchorMin = Value(new Vector2(0, 0)),
                            anchorMax = Value(new Vector2(0, 1)),
                            offsetMin = Value(new Vector2(0, 0)),
                            offsetMax = Value(new Vector2(Screen.width * 0.25f, 0)),
                        },
                        children = List(
                            TightRowsWideColumns(new()
                            {
                                layout = FillParentProps(),
                                children = List(
                                    VerticalPanelWithHeader(new()
                                    {
                                        layout = { flexibleHeight = Value(true) },
                                        header =
                                        {
                                            label = Value("Nodes"),
                                            showAddButton = Value(true),
                                            onAddButtonClicked = () =>
                                            {
                                                // add node here
                                            }
                                        },
                                        // children = App.state.nodes.CreateDynamic() // TODO: create/show node children here
                                    }),
                                    VerticalPanelWithHeader(new()
                                    {
                                        header =
                                        {
                                            label = Value("Scans"),
                                            showAddButton = Value(true),
                                            onAddButtonClicked = () =>
                                            {
                                                // add scan here
                                            }
                                        },
                                        children = App.state.maps.AsObservable().OrderByDynamic(x => x.Key).CreateDynamic(x =>
                                            SelectableMenuItem(new()
                                            {
                                                label = x.Value.name.AsObservable(),
                                                selected = App.state.selectedObjects.AsObservable().ContainsDynamic(x.Key),
                                                onPressed = () =>
                                                {
                                                    if (Keyboard.current.shiftKey.isPressed)
                                                    {
                                                        App.state.selectedObjects.ExecuteAddOrDelay(x.Key);
                                                    }
                                                    else
                                                    {
                                                        App.state.selectedObjects.ExecuteSetOrDelay(new[] { x.Key });
                                                    }
                                                }
                                            })
                                        )
                                    }),
                                    VerticalPanelWithHeader(new()
                                    {
                                        header =
                                        {
                                            label = Value("Tilesets"),
                                            showAddButton = Value(false)
                                        }
                                    })
                                )
                            })
                        )
                    }),
                    ResizablePanel(new()
                    {
                        leftEnabled = Value(true),
                        backgroundColor = Value(elements.backgroundColor),
                        layout =
                        {
                            pivot = Value(new Vector2(1, 0.5f)),
                            anchorMin = Value(new Vector2(0, 0)),
                            anchorMax = Value(new Vector2(0, 1)),
                            offsetMin = Value(new Vector2(Screen.width * 0.25f, 0)),
                            offsetMax = Value(new Vector2(0, 0)),
                        },
                        children = List(
                            VerticalPanelWithHeader(new()
                            {
                                layout = FillParentProps(),
                                header =
                                {
                                    label = Value("Inspector"),
                                    showAddButton = Value(false)
                                },
                                // children = List(
                                // TODO: Populate inspector here 
                                // )
                            })
                        )
                    })
                )
            });
        }

        public struct LabeledPropertyProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<string> label;
            public TextStyleProps labelStyle;
            public IValueObservable<float> labelWidth;
            public IValueObservable<IControl> property;
        }

        public static IControl LabeledProperty(LabeledPropertyProps props)
        {
            return HorizontalLayout(new()
            {
                element = props.element,
                layout = props.layout,
                childControlWidth = Value(true),
                childControlHeight = Value(true),
                childAlignment = Value(TextAnchor.MiddleLeft),
                children = List(
                    Text(new()
                    {
                        value = props.label,
                        style = props.labelStyle,
                        layout = { minWidth = props.labelWidth, preferredWidth = props.labelWidth }
                    }),
                    HorizontalLayout(new()
                    {
                        childControlWidth = Value(true),
                        childControlHeight = Value(true),
                        childAlignment = Value(TextAnchor.MiddleLeft),
                        layout = { flexibleWidth = Value(true) },
                        children = List(props.property)
                    })
                )
            });
        }

        public struct VerticalPanelWithHeaderProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public HeaderProps header;
            public IListObservable<IControl> children;
        }

        public static IControl VerticalPanelWithHeader(VerticalPanelWithHeaderProps props)
        {
            return Panel(new()
            {
                element = props.element,
                layout = props.layout,
                background = Value(elements.panelSprite),
                backgroundStyle = { color = Value(elements.midgroundColor) },
                children = List(
                    TightRowsWideColumns(new()
                    {
                        children = List(
                            Header(props.header),
                            TightRowsWideColumns(new() { children = props.children })
                        )
                    })
                )
            });
        }

        public static IControl TightRowsWideColumns(LayoutGroupProps props)
        {
            props.childControlWidth = props.childControlWidth ?? Value(true);
            props.childControlHeight = props.childControlHeight ?? Value(true);
            props.childForceExpandWidth = props.childForceExpandWidth ?? Value(true);
            return VerticalLayout(props);
        }

        public struct SelectableMenuItemProps
        {
            public IValueObservable<string> label;
            public IValueObservable<bool> selected;
            public IValueObservable<bool> foldoutIsOpen;
            public IValueEventArgs<int> indentLevel;
            public Action onPressed;
            public IListEventArgs<IControl> children;
        }



        private static IControl SelectableMenuItem(SelectableMenuItemProps props)
        {
            return default;
        }

        public struct HeaderProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<string> label;
            public TextStyleProps labelStyle;
            public IValueObservable<bool> showAddButton;
            public Action onAddButtonClicked;
        }

        public static IControl Header(HeaderProps props)
        {
            return Control("Header", new()
            {
                element = props.element,
                layout = props.layout,
                children = List(
                    Title(new()
                    {
                        layout = FillParentProps(),
                        value = props.label,
                        style = props.labelStyle
                    }),
                    IconButton(new()
                    {
                        element = { active = props.showAddButton },
                        layout =
                        {
                            anchorMin = Value(new Vector2(1, 0.5f)),
                            anchorMax = Value(new Vector2(1, 0.5f)),
                            sizeDelta = Value(new Vector2(30, 30)),
                            anchoredPosition = Value(new Vector2(30, 0))
                        },
                        icon = Value(elements.addButtonSprite),
                        backgroundStyle = { color = Value(Color.clear) },
                        onClick = props.onAddButtonClicked
                    }),
                    Image(new()
                    {
                        layout =
                        {
                            anchorMin = Value(new Vector2(0, 0)),
                            anchorMax = Value(new Vector2(1, 0)),
                            pivot = Value(new Vector2(0.5f, 0)),
                            anchoredPosition = Value(new Vector2(0, 0)),
                            sizeDelta = Value(new Vector2(0, 2f))
                        },
                        style = { color = Value(Color.white) }
                    })
                )
            });
        }

        public struct IconButtonProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<Sprite> icon;
            public ImageStyleProps iconStyle;
            public IValueObservable<Sprite> background;
            public ImageStyleProps backgroundStyle;
            public Action onClick;
        }

        public static IControl IconButton(IconButtonProps props)
        {
            return default;
        }

        public static IControl Title(TextProps props)
        {
            props.style.fontSize = props.style.fontSize ?? Value(65f);
            props.style.verticalAlignment = props.style.verticalAlignment ?? Value(TMPro.VerticalAlignmentOptions.Baseline);
            props.style.horizontalAlignment = props.style.horizontalAlignment ?? Value(TMPro.HorizontalAlignmentOptions.Center);
            props.style.textWrappingMode = props.style.textWrappingMode ?? Value(TMPro.TextWrappingModes.NoWrap);
            props.style.overflowMode = props.style.overflowMode ?? Value(TMPro.TextOverflowModes.Ellipsis);
            return Text(props);
        }

        public static LayoutProps FillParentProps()
        {
            return new()
            {
                anchorMin = Value(new Vector2(0, 0)),
                anchorMax = Value(new Vector2(1, 1)),
                offsetMin = Value(new Vector2(0, 0)),
                offsetMax = Value(new Vector2(0, 0))
            };
        }

        public struct PanelProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<Sprite> background;
            public ImageStyleProps backgroundStyle;
            public IListObservable<IControl> children;
        }

        public static IControl Panel(PanelProps props)
        {
            return Control("Panel", new()
            {
                element = props.element,
                layout = props.layout,
                children = List(
                    Image(new()
                    {
                        layout = FillParentProps(),
                        sprite = props.background,
                        style = props.backgroundStyle
                    }),
                    Control("Content", new()
                    {
                        layout = FillParentProps(),
                        children = props.children
                    })
               )
            });
        }

        public struct ResizablePanelProps
        {
            public LayoutProps layout;
            public IValueObservable<bool> leftEnabled;
            public IValueObservable<bool> rightEnabled;
            public IValueObservable<bool> topEnabled;
            public IValueObservable<bool> bottomEnabled;
            public IListObservable<IControl> children;
            public IValueObservable<Color> backgroundColor;
        }

        public static IControl ResizablePanel(ResizablePanelProps props)
        {
            return default;
        }

        public static IControl DropZone(DropZoneProps props)
            => Control(elements.dropZone, props);
    }
}