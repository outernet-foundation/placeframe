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
using UnityEngine.Events;

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
            IControl currentScreen = null;

            return Control("Main UI", new()
            {
                layout = Utility.FillParentProps(),
                children = Props.List(
                    TabbedMenu(new()
                    {
                        value = props.mode.SelectDynamic(x => (int)x),
                        tabs = Props.List("Capture", "Validate"),
                        onValueChanged = x => props.onModeChanged?.Invoke((AppMode)x),
                        layout = new()
                        {
                            anchorMin = Props.Value(new Vector2(0, 0)),
                            anchorMax = Props.Value(new Vector2(1, 0)),
                            anchoredPosition = Props.Value(new Vector2(0, 95f)),
                            sizeDelta = Props.Value(new Vector2(-190, 95)),
                            pivot = Props.Value(new Vector2(0.5f, 0))
                        }
                    }),
                    Control("Content", new()
                    {
                        layout = Utility.FillParentProps(),
                        children = Props.List(props.mode.SelectDynamic(x =>
                        {
                            currentScreen?.Dispose();

                            if (x == AppMode.Capture)
                                currentScreen = CaptureUI();
                            else if (x == AppMode.Validation)
                                currentScreen = ValidationUI();
                            else
                                throw new Exception($"Unhandled App Mode {x}");

                            return currentScreen;
                        }))
                    })
                )
            });
        }

        public static IControl CaptureUI()
        {
            return Control("Capture UI", new()
            {
                layout = Utility.FillParentProps(),
                children = Props.List(
                    Control("Bottom Bar", new()
                    {
                        layout = new()
                        {
                            pivot = Props.Value(new Vector2(0.5f, 0)),
                            anchorMin = Props.Value(new Vector2(0.5f, 0)),
                            anchorMax = Props.Value(new Vector2(0.5f, 0)),
                            anchoredPosition = Props.Value(new Vector2(0, 250)),
                            sizeDelta = Props.Value(new Vector2(785, 170))
                        },
                        children = Props.List(
                            LabeledButton(new LabeledButtonProps()
                            {
                                label = Props.Value("Captures"),
                                onClick = () => CapturesListUI(),
                                layout = new()
                                {
                                    sizeDelta = Props.Value(new Vector2(255, 75)),
                                    anchorMin = Props.Value(new Vector2(1, 0.5f)),
                                    anchorMax = Props.Value(new Vector2(1, 0.5f)),
                                    pivot = Props.Value(new Vector2(1, 0.5f)),
                                    anchoredPosition = Props.Value(new Vector2(0, 0))
                                }
                            }),
                            LabeledButton(new LabeledButtonProps()
                            {
                                label = App.state.captureMode.AsObservable().SelectDynamic(x => x == DeviceType.ARFoundation ? "Local" : "Zed"),
                                onClick = () => App.state.captureMode.ExecuteSetOrDelay(App.state.captureMode.value == DeviceType.ARFoundation ? DeviceType.Zed : DeviceType.ARFoundation),
                                layout = new()
                                {
                                    sizeDelta = Props.Value(new Vector2(255, 75)),
                                    anchorMin = Props.Value(new Vector2(0, 0.5f)),
                                    anchorMax = Props.Value(new Vector2(0, 0.5f)),
                                    pivot = Props.Value(new Vector2(0, 0.5f)),
                                    anchoredPosition = Props.Value(new Vector2(0, 0))
                                }
                            }),
                            Toggle(prefab: elements.recordButton, props: new ToggleProps()
                            {
                                value = App.state.captureStatus
                                    .AsObservable()
                                    .SelectDynamic(x => x == CaptureStatus.Capturing || x == CaptureStatus.Starting),
                                interactable = App.state.captureStatus
                                    .AsObservable()
                                    .SelectDynamic(x => x == CaptureStatus.Idle || x == CaptureStatus.Capturing),
                                layout = new()
                                {
                                    anchorMin = Props.Value(new Vector2(0.5f, 0.5f)),
                                    anchorMax = Props.Value(new Vector2(0.5f, 0.5f)),
                                    anchoredPosition = Props.Value(new Vector2(0, 0))
                                },
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
                            })
                        )
                    })
                )
            });
        }

        public static IControl CapturesListUI()
        {
            return Dialog(new()
            {
                useBackground = Props.Value(true),
                backgroundColor = Props.Value(elements.backgroundColor),
                contentConstructor = dialog => Props.Value(SafeArea(new()
                {
                    children = Props.List(
                        TightRowsWideColumns(new()
                        {
                            padding = Props.Value(new RectOffset(30, 30, 30, 30)),
                            layout = Utility.FillParentProps(),
                            children = Props.List(
                                Image(new()
                                {
                                    color = Props.Value(elements.backgroundColor),
                                    layout = Utility.FillParentProps(new() { ignoreLayout = Props.Value(true) })
                                }),
                                Title(new() { value = Props.Value("Captures") }),
                                ScrollRect(new()
                                {
                                    value = Props.Value(new Vector2(0, 1)),
                                    vertical = Props.Value(true),
                                    layout = new() { flexibleHeight = Props.Value(true) },
                                    content = Props.Value(
                                        TightRowsWideColumns(new()
                                        {
                                            layout = Utility.FillParentProps(new()
                                            {
                                                fitContentVertical = Props.Value(ContentSizeFitter.FitMode.PreferredSize),
                                                pivot = Props.Value(new Vector2(0, 1))
                                            }),
                                            children = App.state.captures
                                                .AsObservable()
                                                .OrderByDynamic(x => x.Value.name.AsObservable())
                                                .CreateDynamic(x => CaptureRow(x.Value))
                                        })
                                    )
                                }),
                                Row(new()
                                {
                                    childAlignment = Props.Value(TextAnchor.MiddleRight),
                                    children = Props.List(
                                        LabeledButton(new()
                                        {
                                            label = Props.Value("Done"),
                                            onClick = dialog.Dispose
                                        })
                                    )
                                })
                            )
                        })
                    )
                }))
            });
        }

        public struct LocalizationMetricsDialogProps
        {
            public ElementProps element;
            public LayoutProps layout;
        }

        public static IControl LocalizationMetricsDialog(LocalizationMetricsDialogProps props)
        {
            var metrics = new ValueObservable<LocalizationMetrics>(VisualPositioningSystem.MostRecentMetrics);
            Action handleMetricsChanged = () => metrics.value = VisualPositioningSystem.MostRecentMetrics;
            VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated += handleMetricsChanged;

            var control = VerticalLayout(new()
            {
                childControlWidth = Props.Value(true),
                childControlHeight = Props.Value(true),
                padding = Props.Value(new RectOffset(30, 30, 30, 30)),
                spacing = Props.Value(10f),
                element = props.element,
                layout = props.layout,
                children = Props.List(
                    Title(new()
                    {
                        value = Props.Value("Metrics"),
                        style = new() { outlineWidth = Props.Value(.15f) }
                    }),
                    ReadonlyInspector(metrics)
                )
            });

            control.AddBinding(
                new Disposable(() => VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated -= handleMetricsChanged)
            );

            return control;
        }

        public static IControl ReadonlyInspector<T>(IValueObservable<T> target)
        {
            return VerticalLayout(new()
            {
                childControlWidth = Props.Value(true),
                childControlHeight = Props.Value(true),
                spacing = Props.Value(10f),
                children = Props.List(typeof(T)
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

                        return HorizontalLayout(new()
                        {
                            childControlWidth = Props.Value(true),
                            childControlHeight = Props.Value(true),
                            spacing = Props.Value(10f),
                            children = Props.List(
                                Text(new()
                                {
                                    value = Props.Value(name),
                                    style = new() { outlineWidth = Props.Value(.15f) },
                                    layout = new() { minWidth = Props.Value(470f) }
                                }),
                                Text(new()
                                {
                                    value = target.SelectDynamic(x => x == null ? "--" : getValue(x).ToString()),
                                    layout = new() { flexibleWidth = Props.Value(true) },
                                    style = new()
                                    {
                                        outlineWidth = Props.Value(.15f),
                                        horizontalAlignment = Props.Value(TMPro.HorizontalAlignmentOptions.Right),
                                        overflowMode = Props.Value(TMPro.TextOverflowModes.Ellipsis),
                                        textWrappingMode = Props.Value(TMPro.TextWrappingModes.NoWrap)
                                    }
                                })
                            )
                        });
                    })
                )
            });
        }

        public static IControl ValidationUI()
        {
            var metricsDialogOpen = new ValueObservable<bool>(false);
            IControl selectValidationTargetDialog = default;

            return Control("Validation UI", new()
            {
                layout = Utility.FillParentProps(),
                children = Props.List(
                    LocalizationMetricsDialog(new()
                    {
                        element = new() { active = metricsDialogOpen },
                        layout = Utility.FillParentProps(new()
                        {
                            offsetMin = Props.Value(new Vector2(95, 480)),
                            offsetMax = Props.Value(new Vector2(-95, -95))
                        })
                    }),
                    Control("Bottom Bar", new()
                    {
                        layout = new()
                        {
                            pivot = Props.Value(new Vector2(0.5f, 0)),
                            anchorMin = Props.Value(new Vector2(0.5f, 0)),
                            anchorMax = Props.Value(new Vector2(0.5f, 0)),
                            anchoredPosition = Props.Value(new Vector2(0, 250)),
                            sizeDelta = Props.Value(new Vector2(785, 170))
                        },
                        children = Props.List(
                            LabeledButton(new LabeledButtonProps()
                            {
                                label = Props.Value("Metrics"),
                                onClick = () => metricsDialogOpen.value = !metricsDialogOpen.value,
                                layout = new()
                                {
                                    sizeDelta = Props.Value(new Vector2(255, 75)),
                                    pivot = Props.Value(new Vector2(1, 0.5f)),
                                    anchorMin = Props.Value(new Vector2(1, 0.5f)),
                                    anchorMax = Props.Value(new Vector2(1, 0.5f)),
                                    anchoredPosition = Props.Value(new Vector2(0, 0))
                                }
                            }),
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
                                    textWrappingMode = Props.Value(TMPro.TextWrappingModes.NoWrap),
                                    overflowMode = Props.Value(TMPro.TextOverflowModes.Ellipsis)
                                },
                                onClick = () => SelectValidationTargetDialog(new()
                                {
                                    onValidationTargetSelected = x =>
                                    {
                                        App.state.mapForLocalization.ExecuteSetOrDelay(x);
                                        selectValidationTargetDialog.Dispose();
                                    }
                                }),
                                layout = new()
                                {
                                    sizeDelta = Props.Value(new Vector2(255, 75)),
                                    pivot = Props.Value(new Vector2(0, 0.5f)),
                                    anchorMin = Props.Value(new Vector2(0, 0.5f)),
                                    anchorMax = Props.Value(new Vector2(0, 0.5f)),
                                    anchoredPosition = Props.Value(new Vector2(0, 0))
                                }
                            }),
                            Toggle(prefab: elements.playButton, props: new ToggleProps()
                            {
                                value = App.state.localizing.AsObservable(),
                                interactable = App.state.mapForLocalization.AsObservable().SelectDynamic(x => x != Guid.Empty),
                                onValueChanged = x => App.state.localizing.ExecuteSetOrDelay(x),
                                layout = new()
                                {
                                    anchorMin = Props.Value(new Vector2(0.5f, 0.5f)),
                                    anchorMax = Props.Value(new Vector2(0.5f, 0.5f)),
                                    anchoredPosition = Props.Value(new Vector2(0, 0))
                                }
                            })
                        )
                    })
                )
            });
        }

        public struct SelectValidationTargetProps
        {
            public UnityAction<Guid> onValidationTargetSelected;
        }

        public static IControl SelectValidationTargetDialog(SelectValidationTargetProps props = default)
        {
            return Dialog(new()
            {
                useBackground = Props.Value(true),
                backgroundColor = Props.Value(elements.backgroundColor),
                contentConstructor = dialog => Props.Value(SafeArea(new()
                {
                    children = Props.List(
                        TightRowsWideColumns(new()
                        {
                            padding = Props.Value(new RectOffset(30, 30, 30, 30)),
                            layout = Utility.FillParentProps(),
                            children = Props.List(
                                Title(new() { value = Props.Value("Localization Maps") }),
                                ScrollRect(new()
                                {
                                    value = Props.Value(new Vector2(0, 1)),
                                    horizontal = Props.Value(false),
                                    layout = new() { flexibleHeight = Props.Value(true) },
                                    content = Props.Value(
                                        TightRowsWideColumns(new()
                                        {
                                            padding = Props.Value(new RectOffset(30, 30, 30, 30)),
                                            layout = Utility.FillParentProps(new()
                                            {
                                                pivot = Props.Value(new Vector2(0, 1)),
                                                anchorMin = Props.Value(new Vector2(0, 1)),
                                                anchorMax = Props.Value(new Vector2(1, 1)),
                                                offsetMin = Props.Value(new Vector2(0, 0)),
                                                offsetMax = Props.Value(new Vector2(0, 0)),
                                                fitContentVertical = Props.Value(ContentSizeFitter.FitMode.PreferredSize)
                                            }),
                                            children = App.state.captures
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
                                                        props.onValidationTargetSelected?.Invoke(x.Key);
                                                    }
                                                }))
                                        })
                                    )
                                }),
                                Row(new()
                                {
                                    childAlignment = Props.Value(TextAnchor.MiddleRight),
                                    children = Props.List(
                                        LabeledButton(new LabeledButtonProps()
                                        {
                                            label = Props.Value("Done"),
                                            onClick = dialog.Dispose
                                        })
                                    )
                                })
                            )
                        })
                    )
                }))
            });
        }

        public struct ReconstructionOptionsDialogProps
        {
            public CaptureState capture;
            public ReconstructionOptions options;
            public UnityAction<ReconstructionOptions> onDialogComplete;
            public UnityAction onDialogCancelled;
        }

        public static IControl ReconstructionOptionsDialog(ReconstructionOptionsDialogProps props)
        {
            props.options = props.options ?? new ReconstructionOptions();

            return Dialog(new()
            {
                useBackground = Props.Value(true),
                backgroundColor = Props.Value(elements.backgroundColor),
                contentConstructor = dialog => Props.Value(SafeArea(new()
                {
                    children = Props.List(
                        TightRowsWideColumns(new()
                        {
                            padding = Props.Value(new RectOffset(30, 30, 30, 30)),
                            layout = Utility.FillParentProps(),
                            children = Props.List(
                                Title(new TextProps() { value = Props.Value("Reconstruction Options") }),
                                ScrollRect(new ScrollRectProps()
                                {
                                    vertical = Props.Value(true),
                                    value = Props.Value(new Vector2(0, 1)),
                                    layout = new() { flexibleHeight = Props.Value(true) },
                                    content = Props.Value(
                                        VerticalLayout(new()
                                        {
                                            childControlHeight = Props.Value(true),
                                            childControlWidth = Props.Value(true),
                                            spacing = Props.Value(10f),
                                            padding = Props.Value(new RectOffset(30, 30, 30, 30)),
                                            layout = new()
                                            {
                                                anchorMin = Props.Value(new Vector2(0, 1)),
                                                anchorMax = Props.Value(new Vector2(1, 1)),
                                                offsetMin = Props.Value(new Vector2(0, 0)),
                                                offsetMax = Props.Value(new Vector2(0, 0)),
                                                fitContentVertical = Props.Value(ContentSizeFitter.FitMode.PreferredSize),
                                            },
                                            children = Props.List(ObjectFieldInspectors(props.options))
                                        })
                                    )
                                }),
                                HorizontalLayout(new()
                                {
                                    childControlWidth = Props.Value(true),
                                    childControlHeight = Props.Value(true),
                                    spacing = Props.Value(10f),
                                    childAlignment = Props.Value(TextAnchor.MiddleRight),
                                    layout = new() { flexibleWidth = Props.Value(true) },
                                    children = Props.List(
                                        LabeledButton(new LabeledButtonProps()
                                        {
                                            label = Props.Value("Cancel"),
                                            onClick = () =>
                                            {
                                                dialog.Dispose();
                                                props.onDialogCancelled?.Invoke();
                                            }
                                        }),
                                        LabeledButton(new LabeledButtonProps()
                                        {
                                            label = Props.Value("Done"),
                                            onClick = () =>
                                            {
                                                dialog.Dispose();
                                                props.onDialogComplete?.Invoke(props.options);
                                            }
                                        })
                                    )
                                })
                            )
                        })
                    )
                }))
            });
        }

        public static IControl CaptureDataDialog(CaptureState capture)
        {
            return Dialog(new()
            {
                useBackground = Props.Value(true),
                backgroundColor = Props.Value(elements.backgroundColor),
                contentConstructor = dialog => Props.Value(SafeArea(new()
                {
                    children = Props.List(
                        VerticalLayout(new()
                        {
                            childControlWidth = Props.Value(true),
                            childControlHeight = Props.Value(true),
                            childForceExpandWidth = Props.Value(true),
                            spacing = Props.Value(30f),
                            padding = Props.Value(new RectOffset(30, 30, 30, 30)),
                            layout = Utility.FillParentProps(),
                            children = Props.List(
                                Title(new TextProps() { value = Props.Value("Capture Data") }),
                                ScrollRect(new ScrollRectProps()
                                {
                                    vertical = Props.Value(true),
                                    layout = new() { flexibleHeight = Props.Value(true) },
                                    content = Props.Value(
                                        VerticalLayout(new()
                                        {
                                            childControlWidth = Props.Value(true),
                                            childControlHeight = Props.Value(true),
                                            spacing = Props.Value(10f),
                                            padding = Props.Value(new RectOffset(30, 30, 30, 30)),
                                            layout = new()
                                            {
                                                pivot = Props.Value(new Vector2(0, 1)),
                                                anchorMin = Props.Value(new Vector2(0, 1)),
                                                anchorMax = Props.Value(new Vector2(1, 1)),
                                                offsetMin = Props.Value(new Vector2(0, 0)),
                                                offsetMax = Props.Value(new Vector2(0, 0)),
                                                fitContentVertical = Props.Value(ContentSizeFitter.FitMode.PreferredSize)
                                            },
                                            children = Props.List(
                                                LabeledControl(new LabeledControlProps()
                                                {
                                                    label = Props.Value("Name"),
                                                    control = InputField(new InputFieldProps()
                                                    {
                                                        layout = new() { flexibleWidth = Props.Value(true) },
                                                        value = capture.name.AsObservable(),
                                                        placeholderValue = Props.Value(capture.id.ToString()),
                                                        onEndEdit = x => capture.name.ExecuteSetOrDelay(x)
                                                    })
                                                }),
                                                LabeledControl(new LabeledControlProps()
                                                {
                                                    label = Props.Value("Source"),
                                                    labelWidth = Props.Value(240f),
                                                    control = Text(new TextProps()
                                                    {
                                                        layout = new() { flexibleWidth = Props.Value(true) },
                                                        value = capture.type.AsObservable().SelectDynamic(x => x == DeviceType.ARFoundation ? "Mobile" : "Zed"),
                                                        style = new TextStyleProps()
                                                        {
                                                            verticalAlignment = Props.Value(TMPro.VerticalAlignmentOptions.Capline),
                                                            horizontalAlignment = Props.Value(TMPro.HorizontalAlignmentOptions.Right)
                                                        }
                                                    })
                                                }),
                                                LabeledControl(new LabeledControlProps()
                                                {
                                                    label = Props.Value("Created At"),
                                                    labelWidth = Props.Value(240f),
                                                    control = Text(new TextProps()
                                                    {
                                                        layout = new() { flexibleWidth = Props.Value(true) },
                                                        value = capture.createdAt.AsObservable().SelectDynamic(x => x.ToString()),
                                                        style = new TextStyleProps()
                                                        {
                                                            verticalAlignment = Props.Value(TMPro.VerticalAlignmentOptions.Capline),
                                                            horizontalAlignment = Props.Value(TMPro.HorizontalAlignmentOptions.Right)
                                                        }
                                                    })
                                                }),
                                                Columns(new()
                                                {
                                                    spacing = Props.Value(30f),
                                                    layout = new()
                                                    {
                                                        flexibleWidth = Props.Value(true),
                                                        minHeight = Props.Value(75f),
                                                    },
                                                    columns = Props.List(
                                                        LabeledButton(new LabeledButtonProps()
                                                        {
                                                            label = Props.Value("Clear Local Files "),
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
                                                    )
                                                }),
                                                ObjectInspector(new ObjectInspectorProps()
                                                {
                                                    target = capture.manifest.value?.Options ?? new ReconstructionOptions(),
                                                    foldout = new FoldoutProps()
                                                    {
                                                        label = new TextProps() { value = Props.Value("Reconstruction Options") },
                                                        isOpen = Props.Value(false),
                                                        interactable = capture.manifest.AsObservable().SelectDynamic(x => x != null)
                                                    },
                                                    isReadonly = Props.Value(true)
                                                }),
                                                ObjectInspector(new ObjectInspectorProps()
                                                {
                                                    target = capture.manifest.value?.Metrics ?? new ReconstructionMetrics(),
                                                    foldout = new FoldoutProps()
                                                    {
                                                        label = new TextProps() { value = Props.Value("Reconstruction Metrics") },
                                                        isOpen = Props.Value(false),
                                                        interactable = capture.manifest.AsObservable().SelectDynamic(x => x != null)
                                                    },
                                                    isReadonly = Props.Value(true)
                                                })
                                            )
                                        })
                                    )
                                }),
                                HorizontalLayout(new()
                                {
                                    childControlWidth = Props.Value(true),
                                    childControlHeight = Props.Value(true),
                                    spacing = Props.Value(10f),
                                    childAlignment = Props.Value(TextAnchor.MiddleRight),
                                    children = Props.List(
                                        LabeledButton(new LabeledButtonProps()
                                        {
                                            label = Props.Value("Done"),
                                            onClick = dialog.Dispose
                                        })
                                    )
                                })
                            )
                        })
                    )
                }))
            });
        }
    }
}
