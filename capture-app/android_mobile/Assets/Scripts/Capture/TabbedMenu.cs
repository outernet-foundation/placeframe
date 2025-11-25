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
        public class TabbedMenuProps : IDisposable
        {
            public ListObservable<string> tabs { get; } = new ListObservable<string>();
            public ImageProps background { get; } = new ImageProps();
            public ImageProps deselectedBackground { get; } = new ImageProps();
            public ImageProps selectedBackground { get; } = new ImageProps();
            public ValueObservable<float> tabHeight { get; } = new ValueObservable<float>(75);
            public ValueObservable<float> tabSpacing { get; } = new ValueObservable<float>();
            public ValueObservable<int> selectedTab { get; } = new ValueObservable<int>();

            public void Dispose()
            {
                tabs.Dispose();
                deselectedBackground.Dispose();
                selectedBackground.Dispose();
                tabHeight.Dispose();
                tabSpacing.Dispose();
                selectedTab.Dispose();
            }
        }

        public static IControl<TabbedMenuProps> TabbedMenu(string identifier = "tabbedMenu", TabbedMenuProps props = default)
        {
            return Control(identifier, props ?? new TabbedMenuProps()).Setup(control =>
            {
                control.AddBinding(
                    control.props.tabs.Subscribe(_ =>
                    {
                        if (control.props.tabs.count == 0)
                        {
                            control.props.selectedTab.From(-1);
                        }
                        else if (control.props.selectedTab.value == -1)
                        {
                            control.props.selectedTab.From(0);
                        }
                        else if (control.props.selectedTab.value >= control.props.tabs.count)
                        {
                            control.props.selectedTab.From(control.props.tabs.count - 1);
                        }
                    })
                );

                control.props.selectedBackground.color.From(elements.foregroundColor);
                control.props.selectedBackground.pixelsPerUnitMultiplier.From(1.3f);
                control.props.selectedBackground.imageType.From(UnityEngine.UI.Image.Type.Sliced);
                control.props.selectedBackground.sprite.From(elements.roundedRect);

                control.props.background.color.From(elements.backgroundColor);
                control.props.background.pixelsPerUnitMultiplier.From(1);
                control.props.background.imageType.From(UnityEngine.UI.Image.Type.Sliced);
                control.props.background.sprite.From(elements.roundedRect);

                control.Children(
                    Image(props: control.props.background).Setup(background => background.FillParent()),
                    Columns().Setup(columns =>
                    {
                        columns.FillParent();
                        columns.OffsetMin(new Vector2(10, 10));
                        columns.OffsetMax(new Vector2(-10, -10));
                        columns.props.spacing.From(control.props.tabSpacing);
                        columns.children.From(
                            control.props.tabs.CreateDynamic(tabLabel => Image("tab").Setup(tab =>
                            {
                                var tabIndex = columns.children.IndexOfDynamic(tab);
                                var isSelected = Observables.Combine(
                                    tabIndex,
                                    control.props.selectedTab,
                                    (index, selectedIndex) => index == selectedIndex
                                );

                                tab.props.From(isSelected.SelectDynamic(
                                    x => x ? control.props.selectedBackground : control.props.deselectedBackground
                                ));

                                var button = tab.gameObject.AddComponent<Button>();
                                button.onClick.AddListener(() => control.props.selectedTab.From(tabIndex));

                                tab.Children(Text().Setup(x =>
                                {
                                    x.FillParent();
                                    x.props.style.verticalAlignment.From(TMPro.VerticalAlignmentOptions.Capline);
                                    x.props.style.horizontalAlignment.From(TMPro.HorizontalAlignmentOptions.Center);
                                    x.props.text.From(tabLabel);
                                }));
                            }))
                        );
                    })
                );

                // control.Children(
                //     VerticalLayout().Setup(layout =>
                //     {
                //         layout.FillParent();
                //         layout.props.childControlWidth.From(true);
                //         layout.props.childControlHeight.From(true);
                //         layout.props.childForceExpandWidth.From(true);
                //         layout.Children(
                //             Control("topRegion").Setup(topRegion =>
                //             {
                //                 topRegion.MinHeight(control.props.tabHeight);
                //                 topRegion.Children(
                //                     Image().Setup(background =>
                //                     {
                //                         background.FillParent();
                //                         background.props.color.From(new Color(0.07843138f, 0.07843138f, 0.07843138f, 1f));
                //                     }),
                //                     Columns().Setup(columns =>
                //                     {
                //                         columns.FillParent();
                //                         columns.props.spacing.From(control.props.tabSpacing);
                //                         columns.children.From(
                //                             control.props.tabs.CreateDynamic(tabData => Image("tab").Setup(tab =>
                //                             {
                //                                 tab.props.From(control.props.selectedTab.SelectDynamic(
                //                                     x => x == tabData ? control.props.selectedBackground : control.props.deselectedBackground
                //                                 ));

                //                                 var button = tab.gameObject.AddComponent<Button>();
                //                                 button.onClick.AddListener(() => control.props.selectedTab.From(tabData));

                //                                 tab.Children(Text().Setup(x =>
                //                                 {
                //                                     x.FillParent();
                //                                     x.props.style.verticalAlignment.From(TMPro.VerticalAlignmentOptions.Capline);
                //                                     x.props.style.horizontalAlignment.From(TMPro.HorizontalAlignmentOptions.Center);
                //                                     x.props.text.From(tabData.tabLabel);
                //                                 }));
                //                             }))
                //                         );
                //                     })
                //                 );
                //             }),
                //             VerticalLayout("content").Setup(content =>
                //             {
                //                 content.FlexibleHeight(true);
                //                 content.props.childControlWidth.From(true);
                //                 content.props.childControlHeight.From(true);
                //                 content.props.childForceExpandWidth.From(true);
                //                 content.props.childForceExpandHeight.From(true);
                //                 content.SingleChild(control.props.selectedTab.SelectDynamic(x => x?.generateContent()));
                //             })
                //         );
                //     })
                // );
            });
        }
    }
}