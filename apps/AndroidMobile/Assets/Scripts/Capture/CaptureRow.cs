using System;
using FofX.Stateful;
using Nessle;
using ObserveThing;
using ObserveThing.StatefulExtensions;
using TMPro;
using UnityEngine;
using static Nessle.UIBuilder;

namespace Placeframe.Client
{
    public static partial class UIElements
    {
        public static IControl CaptureRow(CaptureState capture)
        {
            return VerticalLayout(
                new()
                {
                    childControlWidth = Props.Value(true),
                    childControlHeight = Props.Value(true),
                    spacing = Props.Value(10f),
                    padding = Props.Value(new RectOffset(30, 30, 30, 30)),
                    children = Props.List(
                        Image(
                            new()
                            {
                                style = { color = Props.Value(new Color(.25f, .25f, .25f, 1f)) },
                                layout = Utility.FillParentProps(new() { ignoreLayout = Props.Value(true) }),
                            }
                        ),
                        LabeledControl(
                            new LabeledControlProps()
                            {
                                label = Props.Value("Name"),
                                labelWidth = Props.Value(240f),
                                control = HorizontalLayout(
                                    new()
                                    {
                                        layout = new() { flexibleWidth = Props.Value(true) },
                                        children = Props.List(
                                            InputField(
                                                new InputFieldProps()
                                                {
                                                    layout = new() { flexibleWidth = Props.Value(true) },
                                                    value = capture.name.AsObservable(),
                                                    placeholderValue = Props.Value($"<i>Unnamed [{capture.id}]"),
                                                    inputTextStyle = new TextStyleProps()
                                                    {
                                                        verticalAlignment = Props.Value(
                                                            VerticalAlignmentOptions.Capline
                                                        ),
                                                        textWrappingMode = Props.Value(TextWrappingModes.Normal),
                                                        overflowMode = Props.Value(TextOverflowModes.Ellipsis),
                                                    },
                                                    placeholderTextStyle = new TextStyleProps()
                                                    {
                                                        verticalAlignment = Props.Value(
                                                            VerticalAlignmentOptions.Capline
                                                        ),
                                                        textWrappingMode = Props.Value(TextWrappingModes.Normal),
                                                        overflowMode = Props.Value(TextOverflowModes.Ellipsis),
                                                    },
                                                    onEndEdit = x => capture.name.ExecuteSetOrDelay(x),
                                                }
                                            ),
                                            RoundIconButton(
                                                new RoundIconButtonProps()
                                                {
                                                    icon = new ImageProps()
                                                    {
                                                        sprite = Props.Value(elements.moreMenuSprite),
                                                        style = { preserveAspect = Props.Value(true) },
                                                    },
                                                    onClick = () => CaptureDataDialog(capture),
                                                }
                                            )
                                        ),
                                    }
                                ),
                            }
                        ),
                        LabeledControl(
                            new LabeledControlProps()
                            {
                                label = Props.Value("Source"),
                                labelWidth = Props.Value(240f),
                                control = Text(
                                    new TextProps()
                                    {
                                        layout = new() { flexibleWidth = Props.Value(true) },
                                        value = capture
                                            .type.AsObservable()
                                            .SelectDynamic(x =>
                                                x == PlaceframeApiClient.Model.DeviceType.ARFoundation
                                                    ? "Mobile"
                                                    : "Zed"
                                            ),
                                        style = new TextStyleProps()
                                        {
                                            verticalAlignment = Props.Value(VerticalAlignmentOptions.Capline),
                                            horizontalAlignment = Props.Value(HorizontalAlignmentOptions.Right),
                                        },
                                    }
                                ),
                            }
                        ),
                        LabeledControl(
                            new LabeledControlProps()
                            {
                                label = Props.Value("Created At"),
                                labelWidth = Props.Value(240f),
                                control = Text(
                                    new TextProps()
                                    {
                                        layout = new() { flexibleWidth = Props.Value(true) },
                                        value = capture.createdAt.AsObservable().SelectDynamic(x => x.ToString()),
                                        style = new TextStyleProps()
                                        {
                                            verticalAlignment = Props.Value(VerticalAlignmentOptions.Capline),
                                            horizontalAlignment = Props.Value(HorizontalAlignmentOptions.Right),
                                        },
                                    }
                                ),
                            }
                        ),
                        Row(
                            new()
                            {
                                layout = new() { flexibleWidth = Props.Value(true) },
                                childAlignment = Props.Value(TextAnchor.MiddleRight),
                                children = Props.List(
                                    LabeledButton(
                                        new LabeledButtonProps()
                                        {
                                            label = capture
                                                .status.AsObservable()
                                                .SelectDynamic(x =>
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
                                                        _ => throw new ArgumentOutOfRangeException(nameof(x), x, null),
                                                    }
                                                ),
                                            interactable = capture
                                                .status.AsObservable()
                                                .SelectDynamic(x =>
                                                    x == CaptureUploadStatus.NotUploaded
                                                    || x == CaptureUploadStatus.ReconstructionNotStarted
                                                    || x == CaptureUploadStatus.Uploaded
                                                ),
                                            onClick = () =>
                                            {
                                                if (capture.status.value == CaptureUploadStatus.NotUploaded)
                                                {
                                                    capture.status.ExecuteSetOrDelay(
                                                        CaptureUploadStatus.UploadRequested
                                                    );
                                                }
                                                else if (
                                                    capture.status.value == CaptureUploadStatus.ReconstructionNotStarted
                                                )
                                                {
                                                    capture.status.ExecuteSetOrDelay(
                                                        CaptureUploadStatus.ReconstructRequested
                                                    );
                                                }
                                                else if (capture.status.value == CaptureUploadStatus.Uploaded)
                                                {
                                                    capture.status.ExecuteSetOrDelay(
                                                        CaptureUploadStatus.CreateMapRequested
                                                    );
                                                }
                                            },
                                        }
                                    )
                                ),
                            }
                        )
                    ),
                }
            );
        }
    }
}
