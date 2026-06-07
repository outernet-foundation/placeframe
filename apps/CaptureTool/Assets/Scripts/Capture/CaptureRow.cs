using System;

using Cysharp.Threading.Tasks;

using UnityEngine;

using TMPro;

using FofX.Stateful;

using Nessle;

using ObserveThing;

using Placeframe.Core;

using PlaceframeApiClient.Client;

using PlaceframeApiClient.Model;

using static Nessle.UIBuilder;

using DeviceType = PlaceframeApiClient.Model.DeviceType;

namespace Placeframe.Client
{
    public static partial class UIElements
    {
        public static string CaptureStatusLabel(
            CaptureUploadStatus status,
            ReconstructionReadWithQueue reconstruction,
            float? clientProgress,
            double? uploadBytesPerSecond,
            int? uploadQueuePosition,
            int? uploadQueueDepth) =>
            status switch
            {
                CaptureUploadStatus.NotUploaded => "Upload",
                CaptureUploadStatus.Queued => $"Upload Queued{UploadQueuedSuffix(uploadQueuePosition, uploadQueueDepth)}",
                CaptureUploadStatus.Uploading => "Uploading" + ClientProgressSuffix(clientProgress) + UploadSpeedSuffix(uploadBytesPerSecond),
                CaptureUploadStatus.ReconstructionNotStarted => "Reconstruct",
                CaptureUploadStatus.Reconstructing => ReconstructingPhaseLabel(reconstruction),
                CaptureUploadStatus.Uploaded => "Create Map",
                CaptureUploadStatus.MapCreated => "Map Created",
                CaptureUploadStatus.Failed => "Retry",
                _ => throw new ArgumentOutOfRangeException(nameof(status), status, null)
            };

        private static string UploadQueuedSuffix(int? position, int? depth) =>
            position == null || depth == null ? "" : $" [{position}/{depth}]";

        private static string ClientProgressSuffix(float? clientProgress) =>
            clientProgress is float p && p >= 0f ? $" {p:0}%" : "";

        private static string UploadSpeedSuffix(double? uploadBytesPerSecond) =>
            uploadBytesPerSecond is double bps && bps > 0 ? " · " + ByteFormatting.FormatBytesPerSecond(bps) : "";

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
                    CaptureController.EnqueueUpload(capture).Forget();
                    break;
                case CaptureUploadStatus.ReconstructionNotStarted:
                    Reconstruct(capture).Forget();
                    break;
                case CaptureUploadStatus.Uploaded:
                    CreateMap(capture).Forget();
                    break;
                case CaptureUploadStatus.Failed:
                    if (!capture.serverCaptureExists.value)
                        CaptureController.EnqueueUpload(capture).Forget();
                    else if (capture.reconstruction.value == null)
                        Reconstruct(capture).Forget();
                    else if (capture.reconstruction.value?.Status == ReconstructionStatus.Succeeded)
                        CreateMap(capture).Forget();
                    else
                        Retry(capture).Forget();
                    break;
            }
        }

        private static readonly TimeSpan UploadCheckpointInterval = TimeSpan.FromSeconds(30);

        public static async UniTask Upload(CaptureState capture)
        {
            var id = capture.id;
            UploadProgress lastProgress = default;
            var lastCheckpoint = DateTime.UtcNow;
            try
            {
                var type = capture.type.value;

                // Progress<T> captures the current SynchronizationContext at construction;
                // Upload runs on the main thread, so reports marshal back to the main thread
                // regardless of which worker the handler chain reports from.
                var progress = new Progress<UploadProgress>(p =>
                {
                    capture.clientProgress.value = p.Percent;
                    capture.uploadBytesPerSecond.value = p.BytesPerSecond;
                    lastProgress = p;
                    Log.Info(
                        LogGroup.Capture,
                        "Upload tick capture={CaptureId} sent={BytesSent}B total={BytesTotal}B percent={Percent}",
                        id,
                        p.BytesSent,
                        p.BytesTotal,
                        p.Percent ?? -1f);
                    var now = DateTime.UtcNow;
                    if (now - lastCheckpoint >= UploadCheckpointInterval)
                    {
                        lastCheckpoint = now;
                        Log.Info(
                            LogGroup.Capture,
                            "Upload checkpoint capture={CaptureId} sent={BytesSent}B total={BytesTotal}B speed={BytesPerSecond:F0}B/s percent={Percent:F1}",
                            id,
                            p.BytesSent,
                            p.BytesTotal,
                            p.BytesPerSecond ?? 0,
                            p.Percent ?? 0);
                    }
                });

                capture.clientPhase.value = CaptureClientPhase.Uploading;
                capture.clientProgress.value = null;
                capture.uploadBytesPerSecond.value = null;

                var captureData = type switch
                {
                    DeviceType.Zed => await ZedCaptureController.GetCapture(id),
                    DeviceType.ARFoundation => await CaptureManager.GetCaptureTar(id),
                    _ => throw new ArgumentException($"Unknown DeviceType {type}"),
                };

                await UniTask.SwitchToMainThread();

                Log.Info(LogGroup.Capture, "Upload starting capture={CaptureId} size={BytesTotal}B", id, capture.sessionSizeBytes.value);

                CaptureSessionRead captureSession;
                using (HttpProgressContext.Set(progress))
                {
                    captureSession = await VisualPositioningSystem.Api
                        .CreateCaptureSessionAsync(
                            type,
                            captureData,
                            id: id,
                            name: capture.name.value,
                            recordedAt: capture.recordedAt.value);
                }

                Log.Info(LogGroup.Capture, "Upload finished capture={CaptureId} sent={BytesSent}B", id, lastProgress.BytesSent);

                capture.serverCaptureExists.value = true;

                var reconstruction = await CreateReconstruction(captureSession.Id);
                capture.reconstruction.value = reconstruction;
                capture.clientPhase.value = CaptureClientPhase.Idle;
                capture.clientProgress.value = null;
                capture.uploadBytesPerSecond.value = null;
            }
            catch (Exception ex)
            {
                Log.Info(
                    LogGroup.Capture,
                    ex,
                    "Upload failed capture={CaptureId} sent={BytesSent}B total={BytesTotal}B lastSpeed={BytesPerSecond:F0}B/s",
                    id,
                    lastProgress.BytesSent,
                    lastProgress.BytesTotal,
                    lastProgress.BytesPerSecond ?? 0);
                capture.clientPhase.value = CaptureClientPhase.Failed;
                throw;
            }
        }

        public static async UniTask Reconstruct(CaptureState capture)
        {
            try
            {
                var reconstruction = await CreateReconstruction(capture.id);
                capture.reconstruction.value = reconstruction;
                capture.clientPhase.value = CaptureClientPhase.Idle;
            }
            catch
            {
                capture.clientPhase.value = CaptureClientPhase.Failed;
                throw;
            }
        }

        public static async UniTask Retry(CaptureState capture)
        {
            try
            {
                var reconstruction = await VisualPositioningSystem.Api
                    .RetryReconstructionAsync(capture.reconstruction.value.Id);
                capture.reconstruction.value = reconstruction;
                capture.clientPhase.value = CaptureClientPhase.Idle;
            }
            catch
            {
                capture.clientPhase.value = CaptureClientPhase.Failed;
                throw;
            }
        }

        public static async UniTask CreateMap(CaptureState capture)
        {
            try
            {
                var map = await VisualPositioningSystem.Api
                    .CreateLocalizationMapAsync(
                        new LocalizationMapCreate(capture.reconstruction.value.Id, 0, 0, 0, 0, 0, 0, 1, 0)
                        {
                            Name = capture.name.value,
                        });
                capture.localizationMapId.value = map.Id;
            }
            catch
            {
                capture.clientPhase.value = CaptureClientPhase.Failed;
                throw;
            }
        }

        private static UniTask<ReconstructionReadWithQueue> CreateReconstruction(Guid captureId) =>
            VisualPositioningSystem.Api
                .CreateReconstructionAsync(new ReconstructionCreateWithOptions(new ReconstructionCreate(captureId)));

        private static string ReconstructingPhaseLabel(ReconstructionReadWithQueue reconstruction)
        {
            if (reconstruction == null)
                return "Reconstruction Queued";

            return reconstruction.Status switch
            {
                ReconstructionStatus.Queued => $"Reconstruction Queued{QueuedSuffix(reconstruction)}",
                ReconstructionStatus.ExtractingFeatures => $"Extracting features{ProgressSuffix(reconstruction)}",
                ReconstructionStatus.MatchingFeatures => $"Matching features{ProgressSuffix(reconstruction)}",
                ReconstructionStatus.VerifyingGeometry => $"Verifying geometry{ProgressSuffix(reconstruction)}",
                ReconstructionStatus.Reconstructing => $"Reconstructing{ProgressSuffix(reconstruction)}{AttemptSuffix(reconstruction)}",
                ReconstructionStatus.TrainingOpqMatrix => "Training index",
                ReconstructionStatus.TrainingProductQuantizer => "Training index",
                ReconstructionStatus.Succeeded => "Finalizing",
                ReconstructionStatus.Failed => "Failed",
                ReconstructionStatus.Cancelled => "Cancelled",
                _ => throw new ArgumentOutOfRangeException(nameof(reconstruction.Status), reconstruction.Status, null)
            };
        }

        private static string ProgressSuffix(ReconstructionReadWithQueue reconstruction) =>
            reconstruction.ProgressTotal == null ? "" : $" [{reconstruction.ProgressCurrent}/{reconstruction.ProgressTotal}]";

        private static string QueuedSuffix(ReconstructionReadWithQueue reconstruction) =>
            reconstruction.QueuePosition == null || reconstruction.QueueDepth == null
                ? ""
                : $" [{reconstruction.QueuePosition}/{reconstruction.QueueDepth}]";

        private static string AttemptSuffix(ReconstructionReadWithQueue reconstruction) =>
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
                        label = Props.Value("Size"),
                        labelWidth = Props.Value(240f),
                        control = Text(new TextProps()
                        {
                            layout = new() { flexibleWidth = Props.Value(1f) },
                            value = capture.sessionSizeBytes.ObservableSelect(x => x is long bytes ? ByteFormatting.FormatBytes(bytes) : "—"),
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
                    })
                )
            });
        }
    }
}
