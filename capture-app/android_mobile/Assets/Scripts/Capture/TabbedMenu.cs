using System;
using Nessle;
using ObserveThing;
using UnityEngine;
using UnityEngine.UI;
using static Nessle.UIBuilder;

namespace PlerionClient.Client
{
    public static partial class UIElements
    {
        public class TabbedMenuProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IListObservable<string> tabs;
            public ImageProps background;
            public ImageProps deselectedBackground;
            public ImageProps selectedBackground;
            public IValueObservable<float> tabSpacing;
            public IValueObservable<int> value;
            public Action<int> onValueChanged;
        }

        public static IControl TabbedMenu(TabbedMenuProps props = default)
        {
            props.selectedBackground.color = props.selectedBackground.color ?? Props.Value(elements.foregroundColor);
            props.selectedBackground.pixelsPerUnitMultiplier = props.selectedBackground.pixelsPerUnitMultiplier ?? Props.Value(1.3f);
            props.selectedBackground.imageType = props.selectedBackground.imageType ?? Props.Value(UnityEngine.UI.Image.Type.Sliced);
            props.selectedBackground.sprite = props.selectedBackground.sprite ?? Props.Value(elements.roundedRect);
            props.selectedBackground.fillCenter = props.selectedBackground.fillCenter ?? Props.Value(true);
            props.selectedBackground.raycastTarget = props.selectedBackground.raycastTarget ?? Props.Value(true);

            props.deselectedBackground.raycastTarget = props.deselectedBackground.raycastTarget ?? Props.Value(true);

            props.background.color = props.background.color ?? Props.Value(elements.backgroundColor);
            props.background.pixelsPerUnitMultiplier = props.background.pixelsPerUnitMultiplier ?? Props.Value(1f);
            props.background.imageType = props.background.imageType ?? Props.Value(UnityEngine.UI.Image.Type.Sliced);
            props.background.sprite = props.background.sprite ?? Props.Value(elements.roundedRect);
            props.background.fillCenter = props.background.fillCenter ?? Props.Value(true);
            props.background.layout = Utility.FillParentProps(props.background.layout);

            ValueObservable<int> selectedTabIndex = new ValueObservable<int>(-1);

            var control = Control(new GameObject("Tabbed Menu"), new()
            {
                element = props.element,
                layout = props.layout,
                children = Props.List(
                    Image(props.background),
                    Columns(new()
                    {
                        layout = Utility.FillParentProps(new()
                        {
                            offsetMin = Props.Value(new Vector2(10, 10)),
                            offsetMax = Props.Value(new Vector2(-10, -10))
                        }),
                        spacing = props.tabSpacing,
                        columns = props.tabs.CreateDynamic(tabLabel =>
                        {
                            var tabIndex = props.tabs.IndexOfDynamic(tabLabel);
                            var currentTabIndex = -1;
                            var currentBackground = Observables.Combine(
                                tabIndex,
                                selectedTabIndex,
                                (index, selectedIndex) => index == selectedIndex ? props.selectedBackground : props.deselectedBackground
                            );

                            return Button(new()
                            {
                                element = new()
                                {
                                    bindings = Props.List(tabIndex.Subscribe(x => currentTabIndex = x.currentValue))
                                },
                                onClick = () => selectedTabIndex.value = currentTabIndex,
                                background =
                                {
                                    sprite = currentBackground.SelectDynamic(x => x.sprite),
                                    color = currentBackground.SelectDynamic(x => x.color),
                                    imageType = currentBackground.SelectDynamic(x => x.imageType),
                                    fillCenter = currentBackground.SelectDynamic(x => x.fillCenter),
                                    pixelsPerUnitMultiplier = currentBackground.SelectDynamic(x => x.pixelsPerUnitMultiplier),
                                    raycastTarget = currentBackground.SelectDynamic(x => x.raycastTarget),
                                    raycastPadding = currentBackground.SelectDynamic(x => x.raycastPadding),
                                    useSpriteMesh = currentBackground.SelectDynamic(x => x.useSpriteMesh),
                                    preserveAspect = currentBackground.SelectDynamic(x => x.preserveAspect),
                                    fillOrigin = currentBackground.SelectDynamic(x => x.fillOrigin),
                                    fillMethod = currentBackground.SelectDynamic(x => x.fillMethod),
                                    fillAmount = currentBackground.SelectDynamic(x => x.fillAmount)
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
                props.value.Subscribe(x => selectedTabIndex.value = x.currentValue),
                selectedTabIndex.Subscribe(x => props.onValueChanged?.Invoke(x.currentValue))
            );

            return control;
        }
    }
}