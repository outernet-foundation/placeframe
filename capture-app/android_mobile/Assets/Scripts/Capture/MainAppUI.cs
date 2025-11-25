using System;

using UnityEngine;
using UnityEngine.UI;

using FofX.Stateful;

using Nessle;
using Nessle.StatefulExtensions;

using ObserveThing;
using ObserveThing.StatefulExtensions;

using static Nessle.UIBuilder;

namespace PlerionClient.Client
{
    public static partial class UIElements
    {
        public class MainAppUIProps
        {
            public ValueObservable<AppMode> mode { get; } = new ValueObservable<AppMode>();
        }

        public static IControl<MainAppUIProps> MainAppUI()
        {
            return Control("mainUI", new MainAppUIProps()).Setup(mainUI => mainUI.Children(
                TabbedMenu("tabs").Setup(tabs =>
                {
                    tabs.AnchorToBottom();
                    tabs.FillParentWidth();
                    tabs.SetPivot(new Vector2(0.5f, 0));
                    tabs.AnchoredPosition(new Vector2(0, 95));
                    tabs.SizeDelta(new Vector2(-190, 95));
                    tabs.props.tabs.From("Capture", "Validate");
                    tabs.BindValue(props => props.selectedTab, mainUI.props.mode, x => (AppMode)x, x => (int)x);
                }),
                Control("content").Setup(content =>
                {
                    content.FillParent();
                    content.SingleChild(
                        mainUI.props.mode.SelectDynamic(x =>
                        {
                            if (x == AppMode.Capture)
                                return CaptureUI();
                            else if (x == AppMode.Validation)
                                return ValidationUI();
                            else
                                throw new Exception($"Unhandled App Mode {x}");
                        })
                    );
                })
            ));
        }

        public static IControl CaptureUI()
        {
            return Control("captureUI").Setup(captureUI =>
            {
                captureUI.FillParent();
                captureUI.Children(
                    Button().Setup(capturesButton =>
                    {
                        capturesButton.FitContentHorizontal(ContentSizeFitter.FitMode.PreferredSize);
                        capturesButton.SetPivot(new Vector2(0.5f, 0));
                        capturesButton.AnchorToBottom();
                        capturesButton.AnchoredPosition(new Vector2(0, 230));
                        capturesButton.LabelFrom("Captures");
                        capturesButton.props.onClick.From(() =>
                        {
                            captureUI.children.Add(
                                CapturesListUI().Setup(x =>
                                {
                                    x.FillParent();
                                })
                            );
                        });
                    }),
                    Toggle(prefab: elements.recordButton).Setup(recordButton =>
                    {
                        recordButton.SetPivot(new Vector2(0.5f, 0));
                        recordButton.AnchorToBottom();
                        recordButton.AnchoredPosition(new Vector2(0, 350));

                        recordButton.props.interactable.From(App.state.captureStatus
                            .AsObservable()
                            .SelectDynamic(x => x == CaptureStatus.Idle || x == CaptureStatus.Capturing)
                        );

                        recordButton.props.isOn.From(App.state.captureStatus
                            .AsObservable()
                            .SelectDynamic(x => x == CaptureStatus.Capturing || x == CaptureStatus.Starting)
                        );

                        recordButton.AddBinding(
                            recordButton.props.isOn.Subscribe(x =>
                            {
                                if (x.currentValue)
                                {
                                    if (App.state.captureStatus.value == CaptureStatus.Idle)
                                        App.state.captureStatus.ExecuteSetOrDelay(CaptureStatus.Starting);
                                }
                                else
                                {
                                    if (App.state.captureStatus.value == CaptureStatus.Capturing)
                                        App.state.captureStatus.ExecuteSetOrDelay(CaptureStatus.Stopping);
                                }
                            })
                        );
                    })
                );
            });
        }

        public static IControl CapturesListUI()
        {
            return Image("capturesListUI").Setup(capturesListUI =>
            {
                capturesListUI.FillParent();
                capturesListUI.props.color.From(elements.backgroundColor);
                capturesListUI.Children(SafeArea().Setup(x => x.Children(
                    TightRowsWideColumns("capturesListUI").Setup(safeLayout =>
                    {
                        safeLayout.props.padding.From(new RectOffset(30, 30, 30, 30));
                        safeLayout.FillParent();
                        safeLayout.Children(
                            Image().Setup(x =>
                            {
                                x.IgnoreLayout(true);
                                x.FillParent();
                                x.props.color.From(elements.backgroundColor);
                            }),
                            Title().Setup(x => x.props.text.From("Captures")),
                            ScrollRect("captureList").Setup(captureList =>
                            {
                                captureList.FlexibleHeight(true);
                                captureList.props.horizontal.From(false);
                                captureList.props.content.From(TightRowsWideColumns("content").Setup(content =>
                                {
                                    content.FillParentWidth();
                                    content.FitContentVertical(ContentSizeFitter.FitMode.PreferredSize);
                                    content.Children(
                                        TightRowsWideColumns("captures").Setup(captures => captures.Children(
                                            App.state.captures
                                                .AsObservable()
                                                .OrderByDynamic(x => x.Value.name.AsObservable())
                                                .CreateDynamic(x => CaptureRow(x.Value))
                                        ))
                                    );
                                }));
                            }),
                            Row("bottomBar").Setup(row =>
                            {
                                row.props.childAlignment.From(TextAnchor.MiddleRight);
                                row.Children(
                                    Button().Setup(doneButton =>
                                    {
                                        doneButton.LabelFrom("Done");
                                        doneButton.props.onClick.From(() => capturesListUI.Dispose());
                                    })
                                );
                            })
                        );
                    })))
                );
            });
        }

        public static IControl ValidationUI()
        {
            return Control("validationUI").Setup(validationUI =>
            {
                validationUI.FillParent();
                validationUI.Children(
                    Button().Setup(selectMapButton =>
                    {
                        selectMapButton.FitContentHorizontal(ContentSizeFitter.FitMode.PreferredSize);
                        selectMapButton.SetPivot(new Vector2(0.5f, 0));
                        selectMapButton.AnchorToBottom();
                        selectMapButton.AnchoredPosition(new Vector2(0, 230));
                        selectMapButton.LabelFrom(
                            App.state.captures.AsObservable()
                                .WhereDynamic(x => x.Value.localizationMapId.AsObservable().SelectDynamic(x => x != Guid.Empty))
                                .ToDictionaryDynamic(
                                    x => x.Value.localizationMapId.AsObservable(),
                                    x => x.Value
                                )
                                .TrackDynamic(App.state.mapForLocalization.AsObservable())
                                .SelectDynamic(x => x.keyPresent ? x.value.name.value : "Select Map")
                        );
                        selectMapButton.props.onClick.From(() =>
                        {
                            validationUI.children.Add(SelectValidationTargetDialog());
                        });
                    }),
                    Toggle(prefab: elements.playButton).Setup(playButton =>
                    {
                        playButton.props.interactable.From(App.state.mapForLocalization.AsObservable().SelectDynamic(x => x != Guid.Empty));
                        playButton.SetPivot(new Vector2(0.5f, 0));
                        playButton.AnchorToBottom();
                        playButton.AnchoredPosition(new Vector2(0, 350));
                        playButton.BindValue(App.state.localizing);
                    })
                );
            });
        }

        public static IControl SelectValidationTargetDialog()
        {
            return Image("selectValidationTargetDialog").Setup(selectValidationTargetDialog =>
            {
                selectValidationTargetDialog.FillParent();
                selectValidationTargetDialog.props.color.From(elements.backgroundColor);
                selectValidationTargetDialog.Children(SafeArea().Setup(x => x.Children(
                    TightRowsWideColumns().Setup(safeLayout =>
                    {
                        safeLayout.props.padding.From(new RectOffset(30, 30, 30, 30));
                        safeLayout.FillParent();
                        safeLayout.Children(
                            Image().Setup(x =>
                            {
                                x.IgnoreLayout(true);
                                x.FillParent();
                                x.props.color.From(elements.backgroundColor);
                            }),
                            Title().Setup(x => x.props.text.From("Localization Maps")),
                            ScrollRect("localizationMapList").Setup(localizationMapList =>
                            {
                                localizationMapList.FlexibleHeight(true);
                                localizationMapList.props.horizontal.From(false);
                                localizationMapList.props.content.From(TightRowsWideColumns("content").Setup(content =>
                                {
                                    content.FillParentWidth();
                                    content.FitContentVertical(ContentSizeFitter.FitMode.PreferredSize);
                                    content.props.padding.From(new RectOffset(30, 30, 30, 30));
                                    content.Children(App.state.captures
                                        .AsObservable()
                                        .WhereDynamic(x => x.Value.localizationMapId.AsObservable().SelectDynamic(x => x != Guid.Empty))
                                        .OrderByDynamic(x => x.Value.name.AsObservable())
                                        .SelectDynamic(x => Button().Setup(button =>
                                        {
                                            button.LabelFrom(x.Value.name.AsObservable());
                                            button.props.onClick.From(() =>
                                            {
                                                App.state.mapForLocalization.ExecuteSetOrDelay(x.Value.localizationMapId.value);
                                                App.state.localizing.ExecuteSetOrDelay(true);
                                                selectValidationTargetDialog.Dispose();
                                            });
                                        }))
                                    );
                                }));
                            }),
                            Row("bottomBar").Setup(row =>
                            {
                                row.props.childAlignment.From(TextAnchor.MiddleRight);
                                row.Children(
                                    Button().Setup(doneButton =>
                                    {
                                        doneButton.LabelFrom("Done");
                                        doneButton.props.onClick.From(() => selectValidationTargetDialog.Dispose());
                                    })
                                );
                            })
                        );
                    })
                )));
            });
        }

        public static IControl SelectValidationTargetDialog2()
        {
            return Image("selectValidationTargetDialog").Setup(selectPanel =>
            {
                selectPanel.props.color.From(elements.midgroundColor);
                selectPanel.FillParent();
                selectPanel.OffsetMin(new Vector2(20, 20));
                selectPanel.OffsetMax(new Vector2(-20, -20));
                selectPanel.Children(VerticalLayout("layout").Setup(layout =>
                {
                    layout.FillParent();
                    layout.props.spacing.From(10);
                    layout.props.padding.From(new RectOffset(10, 10, 10, 10));
                    layout.props.childForceExpandWidth.From(true);
                    layout.props.childControlWidth.From(true);
                    layout.props.childControlHeight.From(true);

                    layout.Children(
                        Text().Setup(label =>
                        {
                            label.props.text.From("Select Localization Map");
                            label.FlexibleWidth(true);
                            label.props.style.verticalAlignment.From(TMPro.VerticalAlignmentOptions.Capline);
                            label.props.style.horizontalAlignment.From(TMPro.HorizontalAlignmentOptions.Center);
                        }),
                        ScrollRect().Setup(scrollRect =>
                        {
                            scrollRect.FlexibleHeight(true);
                            scrollRect.props.horizontal.From(false);
                            scrollRect.props.content.From(
                                VerticalLayout("list").Setup(list =>
                                {
                                    list.AnchorToTop();
                                    list.FillParentWidth();
                                    list.props.childControlWidth.From(true);
                                    list.props.childControlHeight.From(true);
                                    list.props.childForceExpandWidth.From(true);
                                    list.props.spacing.From(10);
                                    list.FitContentVertical(ContentSizeFitter.FitMode.PreferredSize);
                                    list.Children(App.state.captures
                                        .AsObservable()
                                        .WhereDynamic(x => x.Value.localizationMapId.AsObservable().SelectDynamic(x => x != Guid.Empty))
                                        .OrderByDynamic(x => x.Value.name)
                                        .SelectDynamic(x => Button().Setup(button =>
                                        {
                                            button.LabelFrom(x.Value.name.AsObservable());
                                            button.props.onClick.From(() =>
                                            {
                                                App.state.mapForLocalization.ExecuteSetOrDelay(x.Value.localizationMapId.value);
                                                selectPanel.Dispose();
                                            });
                                        }))
                                    );
                                })
                            );
                        })
                    );
                }));
            });
        }
    }
}