using System;
using System.Linq;
using System.Reflection;

using UnityEngine;
using UnityEngine.UI;

using FofX.Stateful;

using Nessle;

using ObserveThing;
using ObserveThing.StatefulExtensions;

using static Nessle.UIBuilder;
using DeviceType = PlerionApiClient.Model.DeviceType;
using PlerionApiClient.Model;
using Cysharp.Threading.Tasks;
using Plerion.Core;

namespace PlerionClient.Client
{
    public static partial class UIElements
    {
        public struct MainAppUIProps
        {
            public IValueObservable<AppMode> mode;
            public Action<AppMode> onModeChanged;
        }

        public static IControl MainAppUI(MainAppUIProps props = default)
        {
            return Control(new GameObject("Main UI")).Children(
                TabbedMenu(new TabbedMenuProps()
                {
                    value = props.mode.SelectDynamic(x => (int)x),
                    tabs = Props.From("Capture", "Validate"),
                    onValueChanged = x => props.onModeChanged?.Invoke((AppMode)x)
                }).AnchorToBottom()
                    .FillParentWidth()
                    .SetPivot(new Vector2(0.5f, 0))
                    .AnchoredPosition(new Vector2(0, 95))
                    .SizeDelta(new Vector2(-190, 95)),
                Control(new GameObject("Content"))
                    .FillParent()
                    .SingleChild(
                        props.mode.SelectDynamic(x =>
                        {
                            if (x == AppMode.Capture)
                                return CaptureUI();
                            else if (x == AppMode.Validation)
                                return ValidationUI();
                            else
                                throw new Exception($"Unhandled App Mode {x}");
                        })
                    )
            );
        }

        public static IControl CaptureUI()
        {
            var captureUI = Control(new GameObject("Capture UI"));
            return captureUI
                .FillParent()
                .Children(
                    Control(new GameObject("Bottom Bar"))
                        .SetPivot(new Vector2(0.5f, 0))
                        .AnchorToBottom()
                        .AnchoredPosition(new Vector2(0, 250))
                        .SizeDelta(new Vector2(785, 170))
                        .Children(
                            LabeledButton(new LabeledButtonProps()
                            {
                                label = Props.From("Captures"),
                                onClick = () => captureUI.children.Add(
                                    CapturesListUI().Style(x => x.FillParent())
                                )
                            }).SizeDelta(new Vector2(255, 75))
                                .SetPivot(new Vector2(1, 0.5f))
                                .AnchorToRight()
                                .AnchoredPosition(new Vector2(0, 0)),
                            LabeledButton(new LabeledButtonProps()
                            {
                                label = App.state.captureMode.AsObservable().SelectDynamic(x => x == DeviceType.ARFoundation ? "Local" : "Zed"),
                                onClick = () => App.state.captureMode.ExecuteSetOrDelay(App.state.captureMode.value == DeviceType.ARFoundation ? DeviceType.Zed : DeviceType.ARFoundation)
                            }).SizeDelta(new Vector2(255, 75))
                                .SetPivot(new Vector2(0, 0.5f))
                                .AnchorToLeft()
                                .AnchoredPosition(new Vector2(0, 0)),
                            Toggle(prefab: elements.recordButton, props: new ToggleProps()
                            {
                                value = App.state.captureStatus
                                    .AsObservable()
                                    .SelectDynamic(x => x == CaptureStatus.Capturing || x == CaptureStatus.Starting),
                                interactable = App.state.captureStatus
                                    .AsObservable()
                                    .SelectDynamic(x => x == CaptureStatus.Idle || x == CaptureStatus.Capturing),
                                onValueChanged = isOn =>
                                {
                                    if (isOn)
                                    {
                                        if (App.state.captureStatus.value == CaptureStatus.Idle)
                                            App.state.captureStatus.ExecuteSetOrDelay(CaptureStatus.Starting);
                                    }
                                    else
                                    {
                                        if (App.state.captureStatus.value == CaptureStatus.Capturing)
                                            App.state.captureStatus.ExecuteSetOrDelay(CaptureStatus.Stopping);
                                    }
                                }
                            }).Anchor(new Vector2(0.5f, 0.5f))
                                .AnchoredPosition(new Vector2(0, 0))
                        )
                );
        }

        public static IControl CapturesListUI()
        {
            var capturesListUI = Image(new ImageProps() { color = Props.From(elements.backgroundColor) });
            return capturesListUI
                .FillParent()
                .Children(SafeArea().Children(
                    TightRowsWideColumns(new LayoutProps() { padding = Props.From(new RectOffset(30, 30, 30, 30)) })
                        .FillParent()
                        .Children(
                            Image(new ImageProps() { color = Props.From(elements.backgroundColor) })
                                .IgnoreLayout(true)
                                .FillParent(),
                            Title(new TextProps() { value = Props.From("Captures") }),
                            ScrollRect(new ScrollRectProps()
                            {
                                value = Props.From(new Vector2(0, 1)),
                                vertical = Props.From(true),
                                content = Props.From(
                                    TightRowsWideColumns()
                                        .FillParentWidth()
                                        .FitContentVertical(ContentSizeFitter.FitMode.PreferredSize)
                                        .Children(
                                            App.state.captures
                                                .AsObservable()
                                                .OrderByDynamic(x => x.Value.name.AsObservable())
                                                .CreateDynamic(x => CaptureRow(x.Value))
                                        )
                                )
                            }).FlexibleHeight(true),
                            Row(new LayoutProps() { childAlignment = Props.From(TextAnchor.MiddleRight) })
                                .Children(
                                    LabeledButton(new LabeledButtonProps()
                                    {
                                        label = Props.From("Done"),
                                        onClick = () => capturesListUI.Dispose()
                                    })
                                )
                        )
                ));
        }

        public static IControl LocalizationMetricsDialog()
        {
            var metrics = new ValueObservable<LocalizationMetrics>(VisualPositioningSystem.MostRecentMetrics);
            Action handleMetricsChanged = () => metrics.From(VisualPositioningSystem.MostRecentMetrics);
            VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated += handleMetricsChanged;

            var control = VerticalLayout(new LayoutProps()
            {
                childControlWidth = Props.From(true),
                childControlHeight = Props.From(true),
                padding = Props.From(new RectOffset(30, 30, 30, 30)),
                spacing = Props.From(10f)
            }).Children(
                Title(new TextProps()
                {
                    value = Props.From("Metrics"),
                    style = new TextStyleProps() { outlineWidth = Props.From(.15f) }
                }),
                ReadonlyInspector(metrics)
            );

            control.AddBinding(new Disposable(() => VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated -= handleMetricsChanged));

            return control;
        }

        public static IControl ReadonlyInspector<T>(IValueObservable<T> target)
        {
            return VerticalLayout(new LayoutProps()
            {
                childControlWidth = Props.From(true),
                childControlHeight = Props.From(true),
                spacing = Props.From(10f)
            }).Children(typeof(T)
                .GetMembers(BindingFlags.DeclaredOnly | BindingFlags.Instance | BindingFlags.Public)
                .Where(x => x is FieldInfo || x is PropertyInfo)
                .Select(memberInfo =>
                {
                    string name = default;
                    Func<object, object> getValue = default;

                    if (memberInfo is FieldInfo fieldInfo)
                    {
                        name = fieldInfo.Name;
                        getValue = fieldInfo.GetValue;
                    }
                    else
                    {
                        var propertyInfo = memberInfo as PropertyInfo;

                        name = propertyInfo.Name;
                        getValue = propertyInfo.GetValue;
                    }

                    return HorizontalLayout(new LayoutProps()
                    {
                        childControlWidth = Props.From(true),
                        childControlHeight = Props.From(true),
                        spacing = Props.From(10f),
                    }).Children(
                        Text(new TextProps()
                        {
                            value = Props.From(name),
                            style = new TextStyleProps() { outlineWidth = Props.From(.15f) }
                        }).MinWidth(470),
                        Text(new TextProps()
                        {
                            value = target.SelectDynamic(x => x == null ? "--" : getValue(x).ToString()),
                            style = new TextStyleProps()
                            {
                                outlineWidth = Props.From(.15f),
                                horizontalAlignment = Props.From(TMPro.HorizontalAlignmentOptions.Right),
                                overflowMode = Props.From(TMPro.TextOverflowModes.Ellipsis),
                                textWrappingMode = Props.From(TMPro.TextWrappingModes.NoWrap)
                            }
                        }).FlexibleWidth(true)
                    );
                })
            );
        }

        public static IControl ValidationUI()
        {
            var validationUI = Control(new GameObject("Validation UI"));
            var metricsDialogOpen = new ValueObservable<bool>(false);

            return validationUI
                .FillParent()
                .Children(
                    LocalizationMetricsDialog()
                        .FillParent()
                        .OffsetMin(new Vector2(95, 480))
                        .OffsetMax(new Vector2(-95, -95))
                        .Active(metricsDialogOpen),
                    Control(new GameObject("Bottom Bar"))
                        .SetPivot(new Vector2(0.5f, 0))
                        .AnchorToBottom()
                        .AnchoredPosition(new Vector2(0, 250))
                        .SizeDelta(new Vector2(785, 170))
                        .Children(
                            LabeledButton(new LabeledButtonProps()
                            {
                                label = Props.From("Metrics"),
                                onClick = () => metricsDialogOpen.From(!metricsDialogOpen.value)
                            }).SizeDelta(new Vector2(255, 75))
                                .SetPivot(new Vector2(1, 0.5f))
                                .AnchorToRight()
                                .AnchoredPosition(new Vector2(0, 0)),
                            LabeledButton(new LabeledButtonProps()
                            {
                                label = App.state.captures.AsObservable()
                                    .WhereDynamic(x => x.Value.localizationMapId.AsObservable().SelectDynamic(x => x != Guid.Empty))
                                    .ToDictionaryDynamic(
                                        x => x.Value.localizationMapId.AsObservable(),
                                        x => x.Value
                                    )
                                    .TrackDynamic(App.state.mapForLocalization.AsObservable())
                                    .SelectDynamic(x => x.keyPresent ? x.value.name.value : "Maps"),
                                labelStyle = new TextStyleProps()
                                {
                                    textWrappingMode = Props.From(TMPro.TextWrappingModes.NoWrap),
                                    overflowMode = Props.From(TMPro.TextOverflowModes.Ellipsis)
                                },
                                onClick = () => validationUI.children.Add(SelectValidationTargetDialog())
                            }).SizeDelta(new Vector2(255, 75))
                                .SetPivot(new Vector2(0, 0.5f))
                                .AnchorToLeft()
                                .AnchoredPosition(new Vector2(0, 0)),
                            Toggle(prefab: elements.playButton, props: new ToggleProps()
                            {
                                value = App.state.localizing.AsObservable(),
                                interactable = App.state.mapForLocalization.AsObservable().SelectDynamic(x => x != Guid.Empty),
                                onValueChanged = x => App.state.localizing.ExecuteSetOrDelay(x)
                            }).Anchor(new Vector2(0.5f, 0.5f))
                                .AnchoredPosition(new Vector2(0, 0))
                        )
                );
        }

        public static IControl SelectValidationTargetDialog()
        {
            var selectValidationTargetDialog = Image(new ImageProps() { color = Props.From(elements.backgroundColor) });
            return selectValidationTargetDialog
                .FillParent()
                .Children(SafeArea().Children(
                    TightRowsWideColumns(new LayoutProps() { padding = Props.From(new RectOffset(30, 30, 30, 30)) })
                        .FillParent()
                        .Children(
                            Image(new ImageProps() { color = Props.From(elements.backgroundColor) })
                                .IgnoreLayout(true)
                                .FillParent(),
                            Title(new TextProps() { value = Props.From("Localization Maps") }),
                            ScrollRect(new ScrollRectProps()
                            {
                                value = Props.From(new Vector2(0, 1)),
                                horizontal = Props.From(false),
                                content = Props.From(
                                    TightRowsWideColumns(new LayoutProps() { padding = Props.From(new RectOffset(30, 30, 30, 30)) })
                                        .FillParentWidth()
                                        .FitContentVertical(ContentSizeFitter.FitMode.PreferredSize)
                                        .Children(App.state.captures
                                            .AsObservable()
                                            .WhereDynamic(x => x.Value.localizationMapId.AsObservable().SelectDynamic(x => x != Guid.Empty))
                                            .OrderByDynamic(x => x.Value.name.AsObservable())
                                            .SelectDynamic(x => LabeledButton(new LabeledButtonProps()
                                            {
                                                label = x.Value.name.AsObservable(),
                                                onClick = () =>
                                                {
                                                    App.state.mapForLocalization.ExecuteSetOrDelay(x.Value.localizationMapId.value);
                                                    App.state.localizing.ExecuteSetOrDelay(true);
                                                    selectValidationTargetDialog.Dispose();
                                                }
                                            }))
                                        )
                                    )
                            }).FlexibleHeight(true),
                            Row(new LayoutProps() { childAlignment = Props.From(TextAnchor.MiddleRight) })
                                .Children(
                                    LabeledButton(new LabeledButtonProps()
                                    {
                                        label = Props.From("Done"),
                                        onClick = () => selectValidationTargetDialog.Dispose()
                                    })
                                )
                        )
                ));
        }

        public struct ReconstructionOptionsDialogProps
        {
            public CaptureState capture;
            public ReconstructionOptions options;
            public Action<ReconstructionOptions> onDialogComplete;
            public Action onDialogCancelled;
        }

        public static IControl ReconstructionOptionsDialog(ReconstructionOptionsDialogProps props)
        {
            props.options = props.options ?? new ReconstructionOptions();
            var optionsDialog = Control(new GameObject("Reconstruction Options Dialog"));
            return optionsDialog
                .FillParent()
                .Children(SafeArea().Children(
                    Image(new ImageProps() { color = Props.From(elements.backgroundColor) }).FillParent(),
                    TightRowsWideColumns(new LayoutProps() { padding = Props.From(new RectOffset(30, 30, 30, 30)) })
                        .FillParent()
                        .Children(
                            Title(new TextProps() { value = Props.From("Reconstruction Options") }),
                            ScrollRect(new ScrollRectProps()
                            {
                                vertical = Props.From(true),
                                value = Props.From(new Vector2(0, 1)),
                                content = Props.From(
                                    VerticalLayout(new LayoutProps()
                                    {
                                        childControlHeight = Props.From(true),
                                        childControlWidth = Props.From(true),
                                        spacing = Props.From(10f),
                                        padding = Props.From(new RectOffset(30, 30, 30, 30))
                                    }).FillParentWidth()
                                        .FitContentVertical(ContentSizeFitter.FitMode.PreferredSize)
                                        .Children(ObjectFieldInspectors(props.options))
                                )
                            }).FlexibleHeight(true),
                            HorizontalLayout(new LayoutProps()
                            {
                                childControlWidth = Props.From(true),
                                childControlHeight = Props.From(true),
                                spacing = Props.From(10f),
                                childAlignment = Props.From(TextAnchor.MiddleRight)
                            }).FlexibleWidth(true)
                                .Children(
                                    LabeledButton(new LabeledButtonProps()
                                    {
                                        label = Props.From("Cancel"),
                                        onClick = () =>
                                        {
                                            optionsDialog.Dispose();
                                            props.onDialogCancelled?.Invoke();
                                        }
                                    }),
                                    LabeledButton(new LabeledButtonProps()
                                    {
                                        label = Props.From("Done"),
                                        onClick = () =>
                                        {
                                            optionsDialog.Dispose();
                                            props.onDialogComplete?.Invoke(props.options);
                                        }
                                    })
                                )
                        )
                ));
        }

        public static IControl CaptureDataDialog(CaptureState capture)
        {
            var control = Image(new ImageProps() { color = Props.From(elements.backgroundColor) });

            return control.Children(
                SafeArea().Children(
                    VerticalLayout(new LayoutProps()
                    {
                        childControlWidth = Props.From(true),
                        childControlHeight = Props.From(true),
                        childForceExpandWidth = Props.From(true),
                        spacing = Props.From(30f),
                        padding = Props.From(new RectOffset(30, 30, 30, 30))
                    }).FillParent()
                    .Children(
                        Title(new TextProps() { value = Props.From("Capture Data") }),
                        ScrollRect(new ScrollRectProps()
                        {
                            vertical = Props.From(true),
                            content = Props.From(
                                VerticalLayout(new LayoutProps()
                                {
                                    childControlWidth = Props.From(true),
                                    childControlHeight = Props.From(true),
                                    spacing = Props.From(10f),
                                    padding = Props.From(new RectOffset(30, 30, 30, 30))
                                }).FillParentWidth()
                                    .FitContentVertical(ContentSizeFitter.FitMode.PreferredSize)
                                    .Children(
                                        LabeledControl(new LabeledControlProps()
                                        {
                                            label = new TextProps() { value = Props.From("Name") },
                                            control = InputField(new InputFieldProps()
                                            {
                                                value = capture.name.AsObservable(),
                                                placeholderValue = Props.From(capture.id.ToString()),
                                                onEndEdit = x => capture.name.ExecuteSetOrDelay(x)
                                            })
                                        }),
                                        LabeledControl(new LabeledControlProps()
                                        {
                                            label = new TextProps() { value = Props.From("Source") },
                                            labelWidth = Props.From(240f),
                                            control = Text(new TextProps()
                                            {
                                                value = capture.type.AsObservable().SelectDynamic(x => x == DeviceType.ARFoundation ? "Mobile" : "Zed"),
                                                style = new TextStyleProps()
                                                {
                                                    verticalAlignment = Props.From(TMPro.VerticalAlignmentOptions.Capline),
                                                    horizontalAlignment = Props.From(TMPro.HorizontalAlignmentOptions.Right)
                                                }
                                            })
                                        }),
                                        LabeledControl(new LabeledControlProps()
                                        {
                                            label = new TextProps() { value = Props.From("Created At") },
                                            labelWidth = Props.From(240f),
                                            control = Text(new TextProps()
                                            {
                                                value = capture.createdAt.AsObservable().SelectDynamic(x => x.ToString()),
                                                style = new TextStyleProps()
                                                {
                                                    verticalAlignment = Props.From(TMPro.VerticalAlignmentOptions.Capline),
                                                    horizontalAlignment = Props.From(TMPro.HorizontalAlignmentOptions.Right)
                                                }
                                            })
                                        }),
                                        Columns(Props.From(30f)).FlexibleWidth(true).MinHeight(75).Children(
                                            LabeledButton(new LabeledButtonProps()
                                            {
                                                label = Props.From("Clear Local Files "),
                                                interactable = Observables.Combine(
                                                    capture.status.AsObservable(),
                                                    capture.hasLocalFiles.AsObservable(),
                                                    (status, hasLocalFiles) =>
                                                        hasLocalFiles && (
                                                            status == CaptureUploadStatus.NotUploaded ||
                                                            status == CaptureUploadStatus.ReconstructionNotStarted ||
                                                            status == CaptureUploadStatus.Uploaded ||
                                                            status == CaptureUploadStatus.MapCreated ||
                                                            status == CaptureUploadStatus.Failed
                                                        )
                                                ),
                                                onClick = () =>
                                                {
                                                    if (capture.type.value == DeviceType.ARFoundation)
                                                    {
                                                        LocalCaptureController.DeleteCapture(capture.id);
                                                    }
                                                    else
                                                    {
                                                        ZedCaptureController.DeleteCapture(capture.id).Forget();
                                                    }

                                                    if (capture.status.value == CaptureUploadStatus.NotUploaded)
                                                    {
                                                        App.state.captures.ExecuteRemoveOrDelay(capture.id);
                                                    }
                                                    else
                                                    {
                                                        capture.hasLocalFiles.ExecuteSetOrDelay(false);
                                                    }
                                                }
                                            }),
                                            LabeledButton(new LabeledButtonProps()
                                            {
                                                label = capture.status.AsObservable().SelectDynamic(x =>
                                                    x switch
                                                    {
                                                        CaptureUploadStatus.NotUploaded => "Upload",
                                                        CaptureUploadStatus.UploadRequested => "Initializing",
                                                        CaptureUploadStatus.Initializing => "Initializing",
                                                        CaptureUploadStatus.Uploading => "Uploading",
                                                        CaptureUploadStatus.ReconstructionNotStarted => "Reconstruct",
                                                        CaptureUploadStatus.ReconstructRequested => "Constructing",
                                                        CaptureUploadStatus.Reconstructing => "Constructing",
                                                        CaptureUploadStatus.Uploaded => "Create Map",
                                                        CaptureUploadStatus.CreateMapRequested => "Create Map",
                                                        CaptureUploadStatus.MapCreated => "Map Created",
                                                        CaptureUploadStatus.Failed => "Failed",
                                                        _ => throw new ArgumentOutOfRangeException(nameof(x), x, null)
                                                    }
                                                ),
                                                interactable = capture.status.AsObservable().SelectDynamic(x =>
                                                    x == CaptureUploadStatus.NotUploaded ||
                                                    x == CaptureUploadStatus.ReconstructionNotStarted ||
                                                    x == CaptureUploadStatus.Uploaded
                                                ),
                                                onClick = () =>
                                                {
                                                    if (capture.status.value == CaptureUploadStatus.NotUploaded)
                                                    {
                                                        capture.status.ExecuteSetOrDelay(CaptureUploadStatus.UploadRequested);
                                                    }
                                                    else if (capture.status.value == CaptureUploadStatus.ReconstructionNotStarted)
                                                    {
                                                        capture.status.ExecuteSetOrDelay(CaptureUploadStatus.ReconstructRequested);
                                                    }
                                                    else if (capture.status.value == CaptureUploadStatus.Uploaded)
                                                    {
                                                        capture.status.ExecuteSetOrDelay(CaptureUploadStatus.CreateMapRequested);
                                                    }
                                                }
                                            })
                                        ),
                                        ObjectInspector(new ObjectInspectorProps()
                                        {
                                            target = capture.manifest.value?.Options ?? new ReconstructionOptions(),
                                            foldout = new FoldoutProps()
                                            {
                                                label = new TextProps() { value = Props.From("Reconstruction Options") },
                                                isOpen = Props.From(false),
                                                interactable = capture.manifest.AsObservable().SelectDynamic(x => x != null)
                                            },
                                            isReadonly = Props.From(true)
                                        }),
                                        ObjectInspector(new ObjectInspectorProps()
                                        {
                                            target = capture.manifest.value?.Metrics ?? new ReconstructionMetrics(),
                                            foldout = new FoldoutProps()
                                            {
                                                label = new TextProps() { value = Props.From("Reconstruction Metrics") },
                                                isOpen = Props.From(false),
                                                interactable = capture.manifest.AsObservable().SelectDynamic(x => x != null)
                                            },
                                            isReadonly = Props.From(true)
                                        })
                                    )
                            )
                        }).FlexibleHeight(true),
                        HorizontalLayout(new LayoutProps()
                        {
                            childControlWidth = Props.From(true),
                            childControlHeight = Props.From(true),
                            spacing = Props.From(10f),
                            childAlignment = Props.From(TextAnchor.MiddleRight)
                        }).Children(
                            LabeledButton(new LabeledButtonProps()
                            {
                                label = Props.From("Done"),
                                onClick = () => control.Dispose()
                            })
                        )
                    )
                )
            );
        }
    }
}
