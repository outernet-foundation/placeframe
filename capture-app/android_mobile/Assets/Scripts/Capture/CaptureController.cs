using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Linq;

using UnityEngine;
using UnityEngine.UI;

using Cysharp.Threading.Tasks;
using TMPro;
using PlerionClient.Api;

using FofX;
using FofX.Stateful;
using Nessle;
using ObserveThing;
using static Nessle.UIBuilder;
using static PlerionClient.Client.UIPresets;

namespace PlerionClient.Client
{
    public class CaptureController : MonoBehaviour
    {
        public Canvas canvas;
        [SerializeField][Range(0, 5)] float captureIntervalSeconds = 0.5f;

        private DefaultApi capturesApi;
        private IControl ui;
        private TaskHandle currentCaptureTask = TaskHandle.Complete;

        private string localCaptureNamePath => $"{Application.persistentDataPath}/LocalCaptureNames.json";

        void Awake()
        {
            capturesApi = new DefaultApi(new Configuration { BasePath = App.state.plerionAPIBaseUrl.value });

            DefaultButtonStyle = StyleButton;
            DefaultScrollbarStyle = StyleScrollBar;
            DefaultInputFieldStyle = StyleInputField;
            DefaultTextStyle = StyleText;
            DefaultScrollRectStyle = StyleScrollRect;
            DefaultDropdownStyle = StyleDropdown;
            DefaultSliderStyle = StyleSlider;

            ui = ConstructUI(canvas);

            App.RegisterObserver(HandleLoggedInChanged, App.state.loggedIn);
            App.RegisterObserver(HandleCaptureStatusChanged, App.state.captureStatus);
            App.RegisterObserver(HandleCapturesChanged, App.state.captures);
        }

        void OnDestroy()
        {
            ui.Dispose();
            currentCaptureTask.Cancel();
        }

        private void HandleLoggedInChanged(NodeChangeEventArgs args)
        {
            if (App.state.loggedIn.value)
            {
                UpdateCaptureList().Forget();
            }
            else
            {
                App.state.captures.ExecuteActionOrDelay(x => x.Clear());
            }
        }

        private void HandleCaptureStatusChanged(NodeChangeEventArgs args)
        {


            switch (App.state.captureStatus.value)
            {
                case CaptureStatus.Idle:
                    break;

                case CaptureStatus.Starting:
                    currentCaptureTask = TaskHandle.Execute(async token =>
                    {
                        await StartCapture(App.state.captureMode.value, token);
                        App.state.ExecuteActionOrDelay(new SetCaptureStatusAction(CaptureStatus.Capturing));
                    });
                    break;

                case CaptureStatus.Stopping:
                    currentCaptureTask = TaskHandle.Execute(async token =>
                    {
                        await StopCapture(App.state.captureMode.value, token);
                        await UpdateCaptureList();

                        App.state.ExecuteActionOrDelay(new SetCaptureStatusAction(CaptureStatus.Idle));
                    });
                    break;
            }
        }

        private void HandleCapturesChanged(NodeChangeEventArgs args)
        {
            var json = new SimpleJSON.JSONObject();

            foreach (var kvp in App.state.captures.Where(x => !x.Value.uploaded.value))
                json[kvp.Key.ToString()] = kvp.Value.name.value;

            File.WriteAllText(localCaptureNamePath, json.ToString());
        }

        private async UniTask StopCapture(CaptureType captureType, CancellationToken cancellationToken = default)
        {
            switch (captureType)
            {
                case CaptureType.Local:
                    LocalCaptureController.StopCapture();
                    break;
                case CaptureType.Zed:
                    await ZedCaptureController.StopCapture(cancellationToken);
                    break;
                default:
                    throw new Exception($"Unhandled capture type {captureType}");
            }
        }

        private async UniTask StartCapture(CaptureType captureType, CancellationToken cancellationToken = default)
        {
            switch (captureType)
            {
                case CaptureType.Local:
                    await LocalCaptureController.StartCapture(cancellationToken, captureIntervalSeconds);
                    break;
                case CaptureType.Zed:
                    await ZedCaptureController.StartCapture(captureIntervalSeconds, cancellationToken);
                    break;
                default:
                    throw new Exception($"Unhandled capture type {captureType}");
            }
        }

        private async UniTask UpdateCaptureList()
        {
            Dictionary<Guid, string> captureNames = new Dictionary<Guid, string>();

            if (File.Exists(localCaptureNamePath))
            {
                var data = File.ReadAllText(localCaptureNamePath);
                var json = SimpleJSON.JSONNode.Parse(data);

                foreach (var kvp in json)
                    captureNames.Add(Guid.Parse(kvp.Key), kvp.Value);
            }

            var localCaptures = LocalCaptureController.GetCaptures().ToList();
            var remoteCaptureList = await capturesApi.GetCapturesAsync(localCaptures);

            var captureData = localCaptures.ToDictionary(x => x, x => remoteCaptureList.FirstOrDefault(y => y.Id == x));

            // var captureData = new Dictionary<Guid, Model.CaptureModel>();

            // for (int i = 0; i < 20; i++)
            // {
            //     var capture = new Model.CaptureModel(Guid.NewGuid(), i.ToString());
            //     captureData.Add(capture.Id, capture);
            // }

            await UniTask.SwitchToMainThread();

            App.state.captures.ExecuteActionOrDelay(
                captureData,
                (captures, state) =>
                {
                    state.SetFrom(
                        captures,
                        refreshOldEntries: true,
                        copy: (key, remote, local) =>
                        {
                            if (remote == null) //capture is local only
                            {
                                local.name.value = captureNames.TryGetValue(key, out var name) ? name : null;
                                local.type.value = CaptureType.Local;
                                local.uploaded.value = false;
                                return;
                            }

                            local.name.value = remote.Filename;
                            local.type.value = CaptureType.Local;
                            local.uploaded.value = true;
                        }
                    );
                }
            );
        }

        private async UniTask UploadCapture(Guid id, string name, CaptureType type, CancellationToken cancellationToken)
        {
            var response = await capturesApi.CreateCaptureAsync(new Model.BodyCreateCapture(id: id, filename: name));

            if (type == CaptureType.Zed)
            {
                var captureData = await ZedCaptureController.GetCapture(id, cancellationToken);
                await capturesApi.UploadCaptureTarAsync(response.Id, captureData, cancellationToken);
            }
            else if (type == CaptureType.Local)
            {
                var captureData = await LocalCaptureController.GetCapture(id);
                await capturesApi.UploadCaptureTarAsync(response.Id, captureData, cancellationToken);
            }

            await UpdateCaptureList();
        }

        private IControl ConstructUI(Canvas canvas)
        {
            return new Control(canvas.gameObject).Children(SafeArea().FillParent().Children(
                Image().FillParent().Color(UIResources.PanelColor),
                Control("content").FillParent().Children(App.state.loggedIn.SelectDynamic(loggedIn =>
                    loggedIn ? ConstructCaptureListAndUI() : ConstructLoginScreen()
                ))
            ));
        }

        private class LoginScreenProps : IDisposable
        {
            public ValueObservable<string> username { get; private set; } = new ValueObservable<string>();
            public ValueObservable<string> password { get; private set; } = new ValueObservable<string>();

            public void Dispose()
            {
                username.Dispose();
                password.Dispose();
            }
        }

        private IControl ConstructLoginScreen()
        {
            var props = new LoginScreenProps();
            return Control(props).Children(VerticalLayout()
                .FillParent()
                .Anchor(new Vector2(0.5f, 0.5f))
                .SizeDelta(new Vector2(300, 150)).Style(x =>
                {
                    x.childAlignment.value = TextAnchor.MiddleCenter;
                    x.childControlWidth.value = true;
                    x.childControlHeight.value = true;
                    x.spacing.value = 10;
                })
                .Children(
                    Row().Children(
                        Text()
                            .Value("Username")
                            .PreferredWidth(70),
                        InputField()
                            .Text(props.username)
                            .FlexibleWidth(true)
                            .PreferredHeight(23)
                            .OnChange(x => props.username.value = x)
                    ),
                    Row().Children(
                        Text()
                            .Value("Password")
                            .PreferredWidth(70),
                        InputField()
                            .Text(props.password)
                            .FlexibleWidth(true)
                            .PreferredHeight(23)
                            .ContentType(TMP_InputField.ContentType.Password)
                            .OnChange(x => props.password.value = x)
                    ),
                    Button().Children(Text().Value("Log In")).OnClick(() =>
                    {
                        // login here
                        App.state.loggedIn.ExecuteSet(true);
                    })
                )
            );
        }

        private IControl ConstructCaptureListAndUI()
        {
            return VerticalLayout()
                .Style(x =>
                {
                    x.childControlWidth.value = true;
                    x.childControlHeight.value = true;
                    x.childForceExpandWidth.value = true;
                    x.spacing.value = 10;
                    x.padding.value = new RectOffset(10, 10, 10, 10);
                })
                .FillParent()
                .Children(
                    ScrollRect().Style(x => x.horizontal.value = false).FlexibleHeight(true).Content(
                        VerticalLayout().FillParentWidth().FitContentVertical(ContentSizeFitter.FitMode.PreferredSize).Style(x =>
                        {
                            x.childForceExpandWidth.value = true;
                            x.childControlWidth.value = true;
                            x.childControlHeight.value = true;
                            x.spacing.value = 10;
                        }).Children(
                            App.state.captures
                                .CreateDynamic(x => ConstructCaptureRow(x.Value).WithMetadata(x.Value.name))
                                .OrderByDynamic(x => x.metadata.AsObservable())
                        )
                    ),
                    Row().Children(
                        Button()
                            .Interactable(App.state.captureStatus.SelectDynamic(x => x == CaptureStatus.Idle || x == CaptureStatus.Capturing))
                            .Children(Text().Value(App.state.captureStatus.SelectDynamic(x =>
                                x switch
                                {
                                    CaptureStatus.Idle => "Start Capture",
                                    CaptureStatus.Starting => "Starting...",
                                    CaptureStatus.Capturing => "Stop Capture",
                                    CaptureStatus.Stopping => "Stopping...",
                                    _ => throw new ArgumentOutOfRangeException(nameof(x), x, null)
                                }
                            )))
                            .OnClick(() =>
                            {
                                if (App.state.captureStatus.value == CaptureStatus.Idle)
                                    App.state.ExecuteAction(new SetCaptureStatusAction(CaptureStatus.Starting));
                                else if (App.state.captureStatus.value == CaptureStatus.Capturing)
                                    App.state.ExecuteAction(new SetCaptureStatusAction(CaptureStatus.Stopping));
                            }),
                        Dropdown()
                            .PreferredWidth(100)
                            .PreferredHeight(29.65f)
                            .Options(Enum.GetNames(typeof(CaptureType)))
                            .Interactable(App.state.captureStatus.SelectDynamic(x => x == CaptureStatus.Idle))
                            .BindValue(App.state.captureMode, x => (CaptureType)x, x => (int)x)
                    )
                );
        }

        private IControl<LayoutProps> ConstructCaptureRow(CaptureState capture)
        {
            return Row().Children(
                EditableLabel()
                    .MinHeight(25)
                    .FlexibleWidth(true)
                    .BindValue(
                        capture.name,
                        x => IsDefaultRowLabel(x, capture.id) ? null : x,
                        x => string.IsNullOrEmpty(x) ? DefaultRowLabel(capture.id) : x
                    ),
                Text()
                    .Value(capture.type)
                    .MinHeight(25)
                    .PreferredWidth(100),
                Button()
                    .Interactable(capture.uploaded.AsObservable().SelectDynamic(x => !x))
                    .PreferredWidth(100)
                    .Children(Text().Style(x => x.style.alignment.value = TextAlignmentOptions.CaplineGeoAligned).Value(capture.uploaded.SelectDynamic(x => x ? "Uploaded" : "Upload")))
                    .OnClick(() => UploadCapture(capture.id, capture.name.value ?? capture.id.ToString(), capture.type.value, default).Forget())
            );
        }

        private string DefaultRowLabel(Guid id)
            => $"<i>Unnamed [{id}]";

        private bool IsDefaultRowLabel(string source, Guid id)
            => source == DefaultRowLabel(id);
    }
}