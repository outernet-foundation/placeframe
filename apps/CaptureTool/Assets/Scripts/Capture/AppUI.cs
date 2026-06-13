using System;
using System.Linq;

using UnityEngine;
using UnityEngine.UI;

using FofX.Stateful;

using Nessle;

using ObserveThing;

using static Nessle.UIBuilder;
using DeviceType = PlaceframeApiClient.Model.DeviceType;
using PlaceframeApiClient.Model;
using Cysharp.Threading.Tasks;
using Placeframe.Core;
using R3;
using UnityEngine.Events;
using Placeframe.Core.ARFoundation;

namespace Placeframe.Client
{
    public static partial class UIElements
    {
        public static IControl AppUI() =>
            OrderedCanvas(new()
            {
                children = Props.List(
                    App.state.screen
                        .ObservableCreate(screen => screen switch
                        {
                            AppScreen.Main => MainAppUI(new MainAppUIProps()
                            {
                                mode = App.state.mode,
                                onModeChanged = x => App.state.mode.value = x,
                            }),
                            AppScreen.Login => LoginUI(),
                            _ => ConnectUI(),
                        })
                ),
            });

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
                        value = props.mode.ObservableSelect(x => (int)x),
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
                        children = Props.List(props.mode.ObservableSelect(x =>
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

        private static bool IsBannerState(ZedStatusKind kind) => kind switch
        {
            ZedStatusKind.Stabilizing => true,
            ZedStatusKind.Unreachable => true,
            ZedStatusKind.LostMidCapture => true,
            ZedStatusKind.DegradedDiskLow => true,
            ZedStatusKind.DegradedError => true,
            _ => false,
        };

        private static Color ColorForBanner(ZedStatusKind kind) => kind switch
        {
            ZedStatusKind.Stabilizing => new Color(0.20f, 0.55f, 0.90f, 1f),
            ZedStatusKind.DegradedDiskLow => new Color(1.00f, 0.70f, 0.00f, 1f),
            ZedStatusKind.DegradedError => new Color(1.00f, 0.70f, 0.00f, 1f),
            _ => new Color(0.90f, 0.25f, 0.25f, 1f),
        };

        private static string LabelForBanner(ZedStatusKind kind) => kind switch
        {
            ZedStatusKind.Stabilizing => "Hold the Zed still and level — stabilizing…",
            ZedStatusKind.Unreachable => "Zed box not reachable",
            ZedStatusKind.LostMidCapture => "Connection lost to Zed box",
            ZedStatusKind.DegradedDiskLow => "Zed box disk low",
            ZedStatusKind.DegradedError => "Zed box camera error",
            _ => "",
        };

        public static IControl CaptureUI()
        {
            var zedStatusObservable = App.state.zedStatus;
            IControl namePromptDialog = default;

            return Control("Capture UI", new()
            {
                layout = Utility.FillParentProps(),
                children = Props.List(
                    Control("Zed Status Banner", new()
                    {
                        layout = new()
                        {
                            pivot = Props.Value(new Vector2(0.5f, 0)),
                            anchorMin = Props.Value(new Vector2(0.5f, 0)),
                            anchorMax = Props.Value(new Vector2(0.5f, 0)),
                            anchoredPosition = Props.Value(new Vector2(0, 430)),
                            sizeDelta = Props.Value(new Vector2(785, 60))
                        },
                        element = new()
                        {
                            active = Observables.ObservableCombineValues(
                                App.state.captureMode,
                                zedStatusObservable,
                                (mode, status) => mode == DeviceType.Zed && IsBannerState(status))
                        },
                        children = Props.List(
                            Image(new()
                            {
                                sprite = Props.Value(elements.roundedRect),
                                style = { color = zedStatusObservable.ObservableSelect(ColorForBanner) },
                                layout = Utility.FillParentProps()
                            }),
                            Text(new()
                            {
                                value = zedStatusObservable.ObservableSelect(LabelForBanner),
                                style =
                                {
                                    horizontalAlignment = Props.Value(TMPro.HorizontalAlignmentOptions.Center),
                                    verticalAlignment = Props.Value(TMPro.VerticalAlignmentOptions.Capline)
                                },
                                layout = Utility.FillParentProps()
                            })
                        )
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
                                label = App.state.captureMode.ObservableSelect(x => x == DeviceType.ARFoundation ? "Local" : "Zed"),
                                onClick = () => App.state.captureMode.value = App.state.captureMode.value == DeviceType.ARFoundation ? DeviceType.Zed : DeviceType.ARFoundation,
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
                                    .ObservableSelect(x => x == CaptureStatus.Capturing || x == CaptureStatus.Starting),
                                interactable = Observables.ObservableCombineValues(
                                    App.state.captureStatus,
                                    App.state.captureMode,
                                    zedStatusObservable,
                                    (status, mode, zed) =>
                                    {
                                        var statusOk = status == CaptureStatus.Idle || status == CaptureStatus.Capturing;
                                        if (!statusOk)
                                            return false;
                                        if (mode != DeviceType.Zed)
                                            return true;
                                        return zed == ZedStatusKind.Ready || zed == ZedStatusKind.Recording;
                                    }),
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
                                            App.state.captureStatus.value = CaptureStatus.Starting;
                                    }
                                    else
                                    {
                                        if (App.state.captureStatus.value == CaptureStatus.Capturing)
                                        {
                                            namePromptDialog = NamePromptDialog(new()
                                            {
                                                onSubmit = name =>
                                                {
                                                    App.state.pendingCaptureName.value = name;
                                                    App.state.captureStatus.value = CaptureStatus.Stopping;
                                                    namePromptDialog.Dispose();
                                                }
                                            });
                                        }
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
                                    style = { color = Props.Value(elements.backgroundColor) },
                                    layout = Utility.FillParentProps(new() { ignoreLayout = Props.Value(true) })
                                }),
                                Title(new() { value = Props.Value("Captures") }),
                                ScrollRect(new()
                                {
                                    value = Props.Value(new Vector2(0, 1)),
                                    vertical = Props.Value(true),
                                    layout = new() { flexibleHeight = Props.Value(1f) },
                                    content = Props.Value(
                                        TightRowsWideColumns(new()
                                        {
                                            layout = Utility.FillParentProps(new()
                                            {
                                                fitContentVertical = Props.Value(ContentSizeFitter.FitMode.PreferredSize),
                                                pivot = Props.Value(new Vector2(0, 1))
                                            }),
                                            children = App.state.captures
                                                .ObservableOrderBy(x => x.Value.recordedAt.ObservableSelect(t => -t.Ticks))
                                                .ObservableCreate(x => CaptureRow(x.Value))
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
            var filterHealth = new ObservableValue<FilterHealth>(FilterHealth.Snapshot());

            var tickSubscription = Observable
                .EveryUpdate(UnityFrameProvider.Update)
                .Subscribe(_ => filterHealth.value = FilterHealth.Snapshot());

            var lostObservable = filterHealth.ObservableSelect(h => h.LocalizationLost);
            var lastAcceptObservable = filterHealth.ObservableSelect(h =>
                float.IsPositiveInfinity(h.SecondsSinceLastAccept)
                    ? "Last accept: never"
                    : $"Last accept: {h.SecondsSinceLastAccept:F1}s ago"
            );

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
                    Text(new()
                    {
                        value = Props.Value("LOCALIZATION LOST — Stop and Start to recover."),
                        element = new() { active = lostObservable },
                        style = new()
                        {
                            color = Props.Value(Color.red),
                            outlineWidth = Props.Value(.15f),
                            horizontalAlignment = Props.Value(TMPro.HorizontalAlignmentOptions.Center)
                        }
                    }),
                    Text(new() { value = lastAcceptObservable })
                )
            });

            control.AddBinding(tickSubscription);

            return control;
        }

        public static IControl ValidationUI()
        {
            var metricsDialogOpen = new ObservableValue<bool>(false);
            var lockupHealth = new ObservableValue<FilterHealth>(FilterHealth.Snapshot());
            var lockupTick = Observable
                .EveryUpdate(UnityFrameProvider.Update)
                .Subscribe(_ => lockupHealth.value = FilterHealth.Snapshot());
            IControl selectValidationTargetDialog = default;

            var control = Control("Validation UI", new()
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
                                labelStyle = new TextStyleProps()
                                {
                                    color = lockupHealth.ObservableSelect(h => h.LocalizationLost ? Color.red : Color.white)
                                },
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
                                label = App.state.mapForLocalization.ObservableSelect(x =>
                                {
                                    if (x == Guid.Empty)
                                        return Props.Value("Maps");

                                    return App.state.captures
                                        .ObservableSelect(x => x.Value)
                                        .ObservableFirstOrDefault(x => Observables.ObservableCombineValues(
                                            App.state.mapForLocalization,
                                            x.localizationMapId,
                                            (targetCapture, capture) => targetCapture == capture
                                        ))
                                        .ObservableSelect(x => x?.name.ObservableSelect(n => n ?? $"Unnamed [{x.id}]") ?? Props.Value("Maps"));
                                }),
                                labelStyle = new TextStyleProps()
                                {
                                    textWrappingMode = Props.Value(TMPro.TextWrappingModes.NoWrap),
                                    overflowMode = Props.Value(TMPro.TextOverflowModes.Ellipsis)
                                },
                                onClick = () => selectValidationTargetDialog = SelectValidationTargetDialog(new()
                                {
                                    onValidationTargetSelected = x =>
                                    {
                                        App.state.mapForLocalization.value = x;
                                        App.state.localizing.value = true;
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
                                value = App.state.localizing,
                                interactable = App.state.mapForLocalization.ObservableSelect(x => x != Guid.Empty),
                                onValueChanged = x => App.state.localizing.value = x,
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

            control.AddBinding(lockupTick);
            return control;
        }

        public struct SelectValidationTargetProps
        {
            public UnityAction<Guid> onValidationTargetSelected;
        }

        public struct NamePromptDialogProps
        {
            public Action<string> onSubmit;
        }

        public static IControl NamePromptDialog(NamePromptDialogProps props)
        {
            var input = new ObservableValue<string>("");
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
                                Title(new() { value = Props.Value("Name this capture") }),
                                InputField(new InputFieldProps()
                                {
                                    layout = new() { flexibleWidth = Props.Value(1f) },
                                    value = input,
                                    placeholderValue = Props.Value("e.g. west stairwell"),
                                    onValueChanged = x => input.value = x
                                }),
                                Row(new()
                                {
                                    childAlignment = Props.Value(TextAnchor.MiddleRight),
                                    children = Props.List(
                                        LabeledButton(new LabeledButtonProps()
                                        {
                                            label = Props.Value("OK"),
                                            interactable = input.ObservableSelect(n => !string.IsNullOrWhiteSpace(n)),
                                            onClick = () => props.onSubmit?.Invoke(input.value.Trim())
                                        })
                                    )
                                })
                            )
                        })
                    )
                }))
            });
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
                                    layout = new() { flexibleHeight = Props.Value(1f) },
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
                                                .ObservableWhere(x => x.Value.localizationMapId.ObservableSelect(x => x != Guid.Empty))
                                                .ObservableOrderBy(x => x.Value.recordedAt.ObservableSelect(t => -t.Ticks))
                                                .ObservableSelect(x => LabeledButton(new LabeledButtonProps()
                                                {
                                                    label = x.Value.name.ObservableSelect(n => n ?? $"Unnamed [{x.Value.id}]"),
                                                    onClick = () => props.onValidationTargetSelected?.Invoke(x.Value.localizationMapId.value)
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
                                    layout = new() { flexibleHeight = Props.Value(1f) },
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
                                                        layout = new() { flexibleWidth = Props.Value(1f) },
                                                        value = capture.name,
                                                        placeholderValue = Props.Value(capture.id.ToString()),
                                                        onEndEdit = x => capture.name.value = x
                                                    })
                                                }),
                                                LabeledControl(new LabeledControlProps()
                                                {
                                                    label = Props.Value("Source"),
                                                    labelWidth = Props.Value(240f),
                                                    control = Text(new TextProps()
                                                    {
                                                        layout = new() { flexibleWidth = Props.Value(1f) },
                                                        value = capture.type.ObservableSelect(x => x == DeviceType.ARFoundation ? "Mobile" : "Zed"),
                                                        style = new TextStyleProps()
                                                        {
                                                            verticalAlignment = Props.Value(TMPro.VerticalAlignmentOptions.Capline),
                                                            horizontalAlignment = Props.Value(TMPro.HorizontalAlignmentOptions.Right)
                                                        }
                                                    })
                                                }),
                                                LabeledControl(new LabeledControlProps()
                                                {
                                                    label = Props.Value("Recorded At"),
                                                    labelWidth = Props.Value(240f),
                                                    control = Text(new TextProps()
                                                    {
                                                        layout = new() { flexibleWidth = Props.Value(1f) },
                                                        value = capture.recordedAt.ObservableSelect(x => x.ToString()),
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
                                                        flexibleWidth = Props.Value(1f),
                                                        minHeight = Props.Value(75f),
                                                    },
                                                    columns = Props.List(
                                                        LabeledButton(new LabeledButtonProps()
                                                        {
                                                            label = Props.Value("Clear Local Files "),
                                                            interactable = Observables.ObservableCombineValues(
                                                                capture.status,
                                                                capture.hasLocalFiles,
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
                                                                CaptureController.DeleteCapture(capture.id, capture.type.value).Forget();

                                                                if (capture.status.value == CaptureUploadStatus.NotUploaded)
                                                                {
                                                                    App.state.captures.Remove(capture.id);
                                                                    dialog.Dispose();
                                                                }
                                                                else
                                                                {
                                                                    capture.hasLocalFiles.value = false;
                                                                }
                                                            }
                                                        }),
                                                        LabeledButton(new LabeledButtonProps()
                                                        {
                                                            label = Observables.ObservableCombineValues(
                                                                capture.status,
                                                                capture.reconstruction,
                                                                capture.clientProgress,
                                                                capture.uploadBytesPerSecond,
                                                                capture.uploadQueuePosition,
                                                                capture.uploadQueueDepth,
                                                                CaptureStatusLabel
                                                            ),
                                                            interactable = capture.status.ObservableSelect(CaptureStatusIsActionable),
                                                            onClick = () => OnCaptureActionClicked(capture)
                                                        })
                                                    )
                                                }),
                                                ObjectInspector(new ObjectInspectorProps()
                                                {
                                                    target = ManifestHelpers.ExtractOptions(capture.reconstruction.value),
                                                    foldout = new FoldoutProps()
                                                    {
                                                        label = new TextProps() { value = Props.Value("Reconstruction Options") },
                                                        isOpen = Props.Value(false),
                                                        interactable = capture.reconstruction.ObservableSelect(x => x != null)
                                                    },
                                                    isReadonly = Props.Value(true)
                                                }),
                                                ObjectInspector(new ObjectInspectorProps()
                                                {
                                                    target = ManifestHelpers.ExtractMetrics(capture.reconstruction.value),
                                                    foldout = new FoldoutProps()
                                                    {
                                                        label = new TextProps() { value = Props.Value("Reconstruction Metrics") },
                                                        isOpen = Props.Value(false),
                                                        interactable = capture.reconstruction.ObservableSelect(x => x != null)
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
