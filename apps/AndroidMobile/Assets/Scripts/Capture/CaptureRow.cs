using System;

using UnityEngine;

using TMPro;

using FofX.Stateful;

using Nessle;

using ObserveThing;

using PlaceframeApiClient.Model;

using static Nessle.UIBuilder;

namespace Placeframe.Client
{
    public static partial class UIElements
    {
        public static string CaptureStatusLabel(CaptureUploadStatus status, ReconstructionManifest manifest) =>
            status switch
            {
                CaptureUploadStatus.NotUploaded => "Upload",
                CaptureUploadStatus.Initializing => "Initializing",
                CaptureUploadStatus.Uploading => "Uploading",
                CaptureUploadStatus.ReconstructionNotStarted => "Reconstruct",
                CaptureUploadStatus.Reconstructing => ReconstructingPhaseLabel(manifest),
                CaptureUploadStatus.Uploaded => "Create Map",
                CaptureUploadStatus.MapCreated => "Map Created",
                CaptureUploadStatus.Failed => "Failed",
                _ => throw new ArgumentOutOfRangeException(nameof(status), status, null)
            };

        public static bool CaptureStatusIsActionable(CaptureUploadStatus status) =>
            status == CaptureUploadStatus.NotUploaded
            || status == CaptureUploadStatus.ReconstructionNotStarted
            || status == CaptureUploadStatus.Uploaded;

        public static void OnCaptureActionClicked(CaptureState capture)
        {
            switch (capture.status.value)
            {
                case CaptureUploadStatus.NotUploaded:
                    CaptureController.RequestUpload(capture);
                    break;
                case CaptureUploadStatus.ReconstructionNotStarted:
                    CaptureController.RequestReconstruct(capture);
                    break;
                case CaptureUploadStatus.Uploaded:
                    CaptureController.RequestCreateMap(capture);
                    break;
            }
        }

        private static string ReconstructingPhaseLabel(ReconstructionManifest manifest)
        {
            if (manifest == null)
                return "Queued";

            return manifest.Status switch
            {
                ReconstructionManifest.StatusEnum.Queued => "Queued",
                ReconstructionManifest.StatusEnum.Pending => "Queued",
                ReconstructionManifest.StatusEnum.Downloading => "Downloading",
                ReconstructionManifest.StatusEnum.ExtractingFeatures => $"Extracting features{ProgressSuffix(manifest.PhaseProgress)}",
                ReconstructionManifest.StatusEnum.MatchingFeatures => $"Matching features{ProgressSuffix(manifest.PhaseProgress)}",
                ReconstructionManifest.StatusEnum.VerifyingGeometry => "Verifying geometry",
                ReconstructionManifest.StatusEnum.Reconstructing => $"Reconstructing{ProgressSuffix(manifest.PhaseProgress)}{AttemptSuffix(manifest.PhaseProgress)}",
                ReconstructionManifest.StatusEnum.TrainingOpqMatrix => "Training index",
                ReconstructionManifest.StatusEnum.TrainingProductQuantizer => "Training index",
                ReconstructionManifest.StatusEnum.Uploading => "Uploading model",
                ReconstructionManifest.StatusEnum.Succeeded => "Finalizing",
                ReconstructionManifest.StatusEnum.Failed => "Failed",
                _ => throw new ArgumentOutOfRangeException(nameof(manifest.Status), manifest.Status, null)
            };
        }

        private static string ProgressSuffix(PhaseProgress progress) =>
            progress == null ? "" : $" [{progress.Current}/{progress.Total}]";

        private static string AttemptSuffix(PhaseProgress progress) =>
            progress == null || progress.Attempt <= 1 ? "" : $" (attempt {progress.Attempt})";

        public static IControl CaptureRow(CaptureState capture)
        {
            return VerticalLayout(new()
            {
                childControlWidth = Props.Value(true),
                childControlHeight = Props.Value(true),
                spacing = Props.Value(10f),
                padding = Props.Value(new RectOffset(30, 30, 30, 30)),
                children = Props.List(
                    Image(new()
                    {
                        style = { color = Props.Value(new Color(.25f, .25f, .25f, 1f)) },
                        layout = Utility.FillParentProps(new() { ignoreLayout = Props.Value(true) })
                    }),
                    LabeledControl(new LabeledControlProps()
                    {
                        label = Props.Value("Name"),
                        labelWidth = Props.Value(240f),
                        control = HorizontalLayout(new()
                        {
                            layout = new() { flexibleWidth = Props.Value(1f) },
                            children = Props.List(
                                InputField(new InputFieldProps()
                                {
                                    layout = new() { flexibleWidth = Props.Value(1f) },
                                    value = capture.name,
                                    placeholderValue = Props.Value($"<i>Unnamed [{capture.id}]"),
                                    inputTextStyle = new TextStyleProps()
                                    {
                                        verticalAlignment = Props.Value(VerticalAlignmentOptions.Capline),
                                        textWrappingMode = Props.Value(TextWrappingModes.Normal),
                                        overflowMode = Props.Value(TextOverflowModes.Ellipsis)
                                    },
                                    placeholderTextStyle = new TextStyleProps()
                                    {
                                        verticalAlignment = Props.Value(VerticalAlignmentOptions.Capline),
                                        textWrappingMode = Props.Value(TextWrappingModes.Normal),
                                        overflowMode = Props.Value(TextOverflowModes.Ellipsis)
                                    },
                                    onEndEdit = x => capture.name.value = x
                                }),
                                RoundIconButton(new RoundIconButtonProps()
                                {
                                    icon = new ImageProps()
                                    {
                                        sprite = Props.Value(elements.moreMenuSprite),
                                        style = { preserveAspect = Props.Value(true) }
                                    },
                                    onClick = () => CaptureDataDialog(capture)
                                })
                            )
                        })
                    }),
                    LabeledControl(new LabeledControlProps()
                    {
                        label = Props.Value("Source"),
                        labelWidth = Props.Value(240f),
                        control = Text(new TextProps()
                        {
                            layout = new() { flexibleWidth = Props.Value(1f) },
                            value = capture.type.ObservableSelect(x => x == PlaceframeApiClient.Model.DeviceType.ARFoundation ? "Mobile" : "Zed"),
                            style = new TextStyleProps()
                            {
                                verticalAlignment = Props.Value(VerticalAlignmentOptions.Capline),
                                horizontalAlignment = Props.Value(HorizontalAlignmentOptions.Right)
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
                                verticalAlignment = Props.Value(VerticalAlignmentOptions.Capline),
                                horizontalAlignment = Props.Value(HorizontalAlignmentOptions.Right)
                            }
                        })
                    }),
                    Row(new()
                    {
                        layout = new() { flexibleWidth = Props.Value(1f) },
                        childAlignment = Props.Value(TextAnchor.MiddleRight),
                        children = Props.List(
                            LabeledButton(new LabeledButtonProps()
                            {
                                label = Observables.Combine(
                                    capture.status,
                                    capture.manifest,
                                    CaptureStatusLabel
                                ),
                                interactable = capture.status.ObservableSelect(CaptureStatusIsActionable),
                                onClick = () => OnCaptureActionClicked(capture)
                            })
                        )
                    })
                )
            });
        }
    }
}