using System;
using System.IO;

using Cysharp.Threading.Tasks;

using UnityEngine;

using TMPro;

using FofX.Stateful;

using Nessle;

using Newtonsoft.Json;

using ObserveThing;

using PlaceframeApiClient.Model;

using static Nessle.UIBuilder;

namespace Placeframe.Client
{
    public static partial class UIElements
    {
        public static string CaptureStatusLabel(CaptureUploadStatus status, ReconstructionRead reconstruction) =>
            status switch
            {
                CaptureUploadStatus.NotUploaded => "Upload",
                CaptureUploadStatus.Initializing => "Initializing",
                CaptureUploadStatus.Uploading => "Uploading",
                CaptureUploadStatus.ReconstructionNotStarted => "Reconstruct",
                CaptureUploadStatus.Reconstructing => ReconstructingPhaseLabel(reconstruction),
                CaptureUploadStatus.Uploaded => "Create Map",
                CaptureUploadStatus.MapCreated => "Map Created",
                CaptureUploadStatus.Failed => "Retry",
                _ => throw new ArgumentOutOfRangeException(nameof(status), status, null)
            };

        public static bool CaptureStatusIsActionable(CaptureUploadStatus status) =>
            status == CaptureUploadStatus.NotUploaded
            || status == CaptureUploadStatus.ReconstructionNotStarted
            || status == CaptureUploadStatus.Uploaded
            || status == CaptureUploadStatus.Failed;

        public static void OnCaptureActionClicked(CaptureState capture)
        {
            switch (capture.status.value)
            {
                case CaptureUploadStatus.NotUploaded:
                    PromptOptionsThen(capture, options => CaptureController.Upload(capture, options).Forget());
                    break;
                case CaptureUploadStatus.ReconstructionNotStarted:
                    PromptOptionsThen(capture, options => CaptureController.Reconstruct(capture, options).Forget());
                    break;
                case CaptureUploadStatus.Uploaded:
                    CaptureController.CreateMap(capture).Forget();
                    break;
                case CaptureUploadStatus.Failed:
                    if (!capture.serverCaptureExists.value)
                        PromptOptionsThen(capture, options => CaptureController.Upload(capture, options).Forget());
                    else if (capture.reconstruction.value == null)
                        PromptOptionsThen(capture, options => CaptureController.Reconstruct(capture, options).Forget());
                    else if (capture.reconstruction.value?.Status == ReconstructionStatus.Succeeded)
                        CaptureController.CreateMap(capture).Forget();
                    else
                        CaptureController.Retry(capture).Forget();
                    break;
            }
        }

        private static void PromptOptionsThen(CaptureState capture, Action<ReconstructionOptions> onConfirmed) =>
            ReconstructionOptionsDialog(new ReconstructionOptionsDialogProps()
            {
                capture = capture,
                options = File.Exists(Path.Join(Application.persistentDataPath, "reconstructionOptions.json"))
                    ? JsonConvert.DeserializeObject<ReconstructionOptions>(File.ReadAllText(Path.Join(Application.persistentDataPath, "reconstructionOptions.json")))
                    : new ReconstructionOptions()
                    {
                        NeighborsCount = 12,
                        RansacMaxError = 2.0,
                        RansacMinInlierRatio = 0.15,
                        TriangulationMinimumAngle = 3.0,
                        TriangulationCompleteMaxReprojectionError = 2.0,
                        TriangulationMergeMaxReprojectionError = 4.0,
                        MapperFilterMaxReprojectionError = 2.0,
                        UsePriorPosition = true,
                        RigVerification = true,
                    },
                onDialogComplete = updated =>
                {
                    File.WriteAllText(Path.Join(Application.persistentDataPath, "reconstructionOptions.json"), updated.ToJson());
                    onConfirmed(updated);
                },
            });

        private static string ReconstructingPhaseLabel(ReconstructionRead reconstruction)
        {
            if (reconstruction == null)
                return "Queued";

            return reconstruction.Status switch
            {
                ReconstructionStatus.Queued => "Queued",
                ReconstructionStatus.Downloading => "Downloading",
                ReconstructionStatus.ExtractingFeatures => $"Extracting features{ProgressSuffix(reconstruction)}",
                ReconstructionStatus.MatchingFeatures => $"Matching features{ProgressSuffix(reconstruction)}",
                ReconstructionStatus.VerifyingGeometry => "Verifying geometry",
                ReconstructionStatus.Reconstructing => $"Reconstructing{ProgressSuffix(reconstruction)}{AttemptSuffix(reconstruction)}",
                ReconstructionStatus.TrainingOpqMatrix => "Training index",
                ReconstructionStatus.TrainingProductQuantizer => "Training index",
                ReconstructionStatus.Uploading => "Uploading model",
                ReconstructionStatus.Succeeded => "Finalizing",
                ReconstructionStatus.Failed => "Failed",
                ReconstructionStatus.Cancelled => "Cancelled",
                _ => throw new ArgumentOutOfRangeException(nameof(reconstruction.Status), reconstruction.Status, null)
            };
        }

        private static string ProgressSuffix(ReconstructionRead reconstruction) =>
            reconstruction.ProgressTotal == null ? "" : $" [{reconstruction.ProgressCurrent}/{reconstruction.ProgressTotal}]";

        private static string AttemptSuffix(ReconstructionRead reconstruction) =>
            reconstruction.ProgressAttempt == null || reconstruction.ProgressAttempt <= 1 ? "" : $" (attempt {reconstruction.ProgressAttempt})";

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
                                label = Observables.ObservableCombineValues(
                                    capture.status,
                                    capture.reconstruction,
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
