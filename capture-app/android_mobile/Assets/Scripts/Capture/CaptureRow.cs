using System;

using UnityEngine;

using Cysharp.Threading.Tasks;
using TMPro;
// using PlerionClient.Model;

using FofX.Stateful;

using Nessle;

using ObserveThing;
using ObserveThing.StatefulExtensions;

using static Nessle.UIBuilder;

namespace PlerionClient.Client
{
    public static partial class UIElements
    {
        public static IControl<LayoutProps> CaptureRow(CaptureState capture)
        {
            return VerticalLayout().Setup(element =>
            {
                element.props.childControlWidth.From(true);
                element.props.childControlHeight.From(true);
                element.props.spacing.From(10);
                element.props.padding.From(new RectOffset(30, 30, 30, 30));
                element.Children(
                    Image().Setup(background =>
                    {
                        background.props.color.From(new UnityEngine.Color(.25f, .25f, .25f, 1f));
                        background.IgnoreLayout(true);
                        background.FillParent();
                    }),
                    LabeledControl(
                        "Name",
                        240,
                        InputField().Setup(inputField =>
                        {
                            inputField.FlexibleWidth(true);

                            inputField.props.inputText.style.verticalAlignment.From(VerticalAlignmentOptions.Capline);
                            inputField.props.inputText.style.textWrappingMode.From(TextWrappingModes.Normal);
                            inputField.props.inputText.style.overflowMode.From(TextOverflowModes.Ellipsis);

                            inputField.props.placeholderText.style.verticalAlignment.From(VerticalAlignmentOptions.Capline);
                            inputField.props.placeholderText.style.textWrappingMode.From(TextWrappingModes.Normal);
                            inputField.props.placeholderText.style.overflowMode.From(TextOverflowModes.Ellipsis);
                            inputField.props.placeholderText.text.From($"<i>Unnamed [{capture.id}]");

                            inputField.props.onEndEdit.From(x => capture.name.ExecuteSetOrDelay(x));
                            inputField.AddBinding(capture.name.AsObservable().Subscribe(x => inputField.props.inputText.text.From(x.currentValue)));
                        })
                    ),
                    LabeledControl(
                        "Source",
                        240,
                        Text().Setup(text =>
                        {
                            text.props.text.From(capture.type.AsObservable().SelectDynamic(x => x == PlerionApiClient.Model.DeviceType.ARFoundation ? "Mobile" : "Zed"));
                            text.props.style.verticalAlignment.From(VerticalAlignmentOptions.Capline);
                            text.props.style.horizontalAlignment.From(HorizontalAlignmentOptions.Right);
                        })
                    ),
                    LabeledControl(
                        "Created At",
                        240,
                        Text().Setup(text =>
                        {
                            text.props.text.From(capture.createdAt.AsObservable().SelectDynamic(x => x.ToString()));
                            text.props.style.verticalAlignment.From(VerticalAlignmentOptions.Capline);
                            text.props.style.horizontalAlignment.From(HorizontalAlignmentOptions.Right);
                        })
                    ),
                    Row().Setup(controls =>
                    {
                        controls.FlexibleWidth(true);
                        controls.props.childControlWidth.From(true);
                        controls.props.childControlHeight.From(true);
                        controls.props.childAlignment.From(TextAnchor.MiddleRight);
                        controls.Children(
                            Button().Setup(removeLocalFilesButton =>
                            {
                                removeLocalFilesButton.Active(capture.hasLocalFiles.AsObservable());
                                removeLocalFilesButton.LabelFrom("Remove Local Files");
                                removeLocalFilesButton.props.interactable.From(capture.status.AsObservable().SelectDynamic(x =>
                                    x == CaptureUploadStatus.NotUploaded ||
                                    x == CaptureUploadStatus.ReconstructionNotStarted ||
                                    x == CaptureUploadStatus.Uploaded ||
                                    x == CaptureUploadStatus.MapCreated ||
                                    x == CaptureUploadStatus.Failed
                                ));

                                removeLocalFilesButton.props.onClick.From(() =>
                                {
                                    if (capture.type.value == PlerionApiClient.Model.DeviceType.ARFoundation)
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
                                });
                            }),
                            Button().Setup(uploadButton =>
                            {
                                uploadButton.props.interactable.From(capture.status.AsObservable().SelectDynamic(x =>
                                    x == CaptureUploadStatus.NotUploaded ||
                                    x == CaptureUploadStatus.ReconstructionNotStarted ||
                                    x == CaptureUploadStatus.Uploaded
                                ));

                                uploadButton.LabelFrom(capture.status.AsObservable().SelectDynamic(x =>
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
                                ));

                                uploadButton.PreferredWidth(320);
                                uploadButton.props.onClick.From(() =>
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
                                });
                            })
                        );
                    })
                );
            });
        }
    }
}