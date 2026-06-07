using System;
using Nessle;
using ObserveThing;
using UnityEngine;
using UnityEngine.UI;
using static Nessle.UIBuilder;

namespace Placeframe.Client
{
    public static partial class UIElements
    {
        public class TabbedMenuProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IListObservable<string> tabs;
            public IValueObservable<Sprite> background;
            public ImageStyleProps backgroundStyle;
            public IValueObservable<Sprite> deselectedBackground;
            public ImageStyleProps deselectedBackgroundStyle;
            public IValueObservable<Sprite> selectedBackground;
            public ImageStyleProps selectedBackgroundStyle;
            public IValueObservable<float> tabSpacing;
            public IValueObservable<int> value;
            public Action<int> onValueChanged;
        }

        public static IControl TabbedMenu(TabbedMenuProps props = default)
        {
            props.selectedBackground = props.selectedBackground ?? Props.Value(elements.roundedRect);
            props.selectedBackgroundStyle.color = props.selectedBackgroundStyle.color ?? Props.Value(elements.foregroundColor);
            props.selectedBackgroundStyle.pixelsPerUnitMultiplier = props.selectedBackgroundStyle.pixelsPerUnitMultiplier ?? Props.Value(1.3f);
            props.selectedBackgroundStyle.imageType = props.selectedBackgroundStyle.imageType ?? Props.Value(UnityEngine.UI.Image.Type.Sliced);
            props.selectedBackgroundStyle.fillCenter = props.selectedBackgroundStyle.fillCenter ?? Props.Value(true);
            props.selectedBackgroundStyle.raycastTarget = props.selectedBackgroundStyle.raycastTarget ?? Props.Value(true);

            props.deselectedBackgroundStyle.color = props.deselectedBackgroundStyle.color ?? Props.Value(Color.clear);
            props.deselectedBackgroundStyle.raycastTarget = props.deselectedBackgroundStyle.raycastTarget ?? Props.Value(true);

            props.background = props.background ?? Props.Value(elements.roundedRect);
            props.backgroundStyle.color = props.backgroundStyle.color ?? Props.Value(elements.backgroundColor);
            props.backgroundStyle.pixelsPerUnitMultiplier = props.backgroundStyle.pixelsPerUnitMultiplier ?? Props.Value(1f);
            props.backgroundStyle.imageType = props.backgroundStyle.imageType ?? Props.Value(UnityEngine.UI.Image.Type.Sliced);
            props.backgroundStyle.fillCenter = props.backgroundStyle.fillCenter ?? Props.Value(true);

            ObservableValue<int> selectedTabIndex = new ObservableValue<int>(-1);

            var control = Control(new GameObject("Tabbed Menu"), new()
            {
                element = props.element,
                layout = props.layout,
                children = Props.List(
                    Image(new() { sprite = props.background, style = props.backgroundStyle, layout = Utility.FillParentProps() }),
                    Columns(new()
                    {
                        layout = Utility.FillParentProps(new()
                        {
                            offsetMin = Props.Value(new Vector2(10, 10)),
                            offsetMax = Props.Value(new Vector2(-10, -10))
                        }),
                        spacing = props.tabSpacing,
                        columns = props.tabs.ObservableCreate(tabLabel =>
                        {
                            var tabIndex = props.tabs.ObservableIndexOf(tabLabel);
                            var currentTabIndex = -1;
                            var currentBackgroundStyle = Observables.ObservableCombineValues(
                                tabIndex,
                                selectedTabIndex,
                                (index, selectedIndex) => index == selectedIndex ? props.selectedBackgroundStyle : props.deselectedBackgroundStyle
                            );

                            return Button(new()
                            {
                                element = new()
                                {
                                    bindings = Props.List(tabIndex.Subscribe(x => currentTabIndex = x))
                                },
                                onClick = () => selectedTabIndex.value = currentTabIndex,
                                background =
                                {
                                    sprite = Observables.ObservableCombineValues(
                                        tabIndex,
                                        selectedTabIndex,
                                        (index, selectedIndex) => index == selectedIndex ? props.selectedBackground : props.deselectedBackground
                                    ),
                                    style =
                                    {
                                        color = currentBackgroundStyle.ObservableSelect(x => x.color),
                                        imageType = currentBackgroundStyle.ObservableSelect(x => x.imageType),
                                        fillCenter = currentBackgroundStyle.ObservableSelect(x => x.fillCenter),
                                        pixelsPerUnitMultiplier = currentBackgroundStyle.ObservableSelect(x => x.pixelsPerUnitMultiplier),
                                        raycastTarget = currentBackgroundStyle.ObservableSelect(x => x.raycastTarget),
                                        raycastPadding = currentBackgroundStyle.ObservableSelect(x => x.raycastPadding),
                                        useSpriteMesh = currentBackgroundStyle.ObservableSelect(x => x.useSpriteMesh),
                                        preserveAspect = currentBackgroundStyle.ObservableSelect(x => x.preserveAspect),
                                        fillOrigin = currentBackgroundStyle.ObservableSelect(x => x.fillOrigin),
                                        fillMethod = currentBackgroundStyle.ObservableSelect(x => x.fillMethod),
                                        fillAmount = currentBackgroundStyle.ObservableSelect(x => x.fillAmount)
                                    }
                                },
                                content = Props.List(
                                    Text(new TextProps()
                                    {
                                        value = Props.Value(tabLabel),
                                        layout = Utility.FillParentProps(),
                                        style = new TextStyleProps()
                                        {
                                            verticalAlignment = Props.Value(TMPro.VerticalAlignmentOptions.Capline),
                                            horizontalAlignment = Props.Value(TMPro.HorizontalAlignmentOptions.Center)
                                        }
                                    })
                                )
                            });
                        })
                    })
                )
            });

            control.AddBinding(
                props.tabs.Subscribe(_ => selectedTabIndex.value = 0),
                props.value.Subscribe(x => selectedTabIndex.value = x),
                selectedTabIndex.Subscribe(x => props.onValueChanged?.Invoke(x))
            );

            return control;
        }
    }
}