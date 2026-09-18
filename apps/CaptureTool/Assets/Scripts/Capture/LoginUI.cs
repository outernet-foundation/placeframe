using UnityEngine;
using Nessle;
using TMPro;

using static Nessle.UIBuilder;
using ObserveThing;
using UnityEngine.UI;
using FofX.Stateful;

namespace Placeframe.Client
{
    public static partial class UIElements
    {
        public static IControl ConnectUI()
        {
            return Control(new GameObject("Connect UI"), new()
            {
                layout = Utility.FillParentProps(),
                children = Props.List(
                    Image(new ImageProps()
                    {
                        style = { color = Props.Value(elements.midgroundColor) },
                        layout = Utility.FillParentProps(new() { ignoreLayout = Props.Value(true) })
                    }),
                    TightRowsWideColumns(new()
                    {
                        layout = new()
                        {
                            anchorMin = Props.Value(new Vector2(0.5f, 0.66f)),
                            anchorMax = Props.Value(new Vector2(0.5f, 0.66f)),
                            pivot = Props.Value(new Vector2(0.5f, 1f)),
                            sizeDelta = Props.Value(new Vector2(900, 0)),
                            fitContentVertical = Props.Value(ContentSizeFitter.FitMode.PreferredSize)
                        },
                        children = Props.List(
                            LabeledControl(new LabeledControlProps()
                            {
                                label = Props.Value("API URL"),
                                labelWidth = Props.Value(225f),
                                control = InputField(new InputFieldProps()
                                {
                                    layout = new() { flexibleWidth = Props.Value(1f) },
                                    value = App.state.settings.apiUrl,
                                    onValueChanged = x => App.state.settings.apiUrl.value = x
                                })
                            }),
                            HorizontalLayout(new LayoutGroupProps()
                            {
                                childControlWidth = Props.Value(true),
                                childControlHeight = Props.Value(true),
                                childAlignment = Props.Value(TextAnchor.UpperRight),
                                children = Props.List(
                                    LabeledButton(new LabeledButtonProps()
                                    {
                                        label = App.state.authStatus.ObservableSelect(
                                            x => IsBusy(x) ? "Connecting…" : "Connect"),
                                        interactable = App.state.authStatus.ObservableSelect(x => !IsBusy(x)),
                                        onClick = () => App.state.connectRequested.value = true
                                    })
                                )
                            }),
                            Text(new TextProps()
                            {
                                value = App.state.authError,
                                element = new() { active = App.state.authError.ObservableSelect(x => !string.IsNullOrEmpty(x)) },
                                style = new TextStyleProps()
                                {
                                    color = Props.Value(Color.red),
                                    horizontalAlignment = Props.Value(HorizontalAlignmentOptions.Center)
                                }
                            })
                        )
                    })
                )
            });
        }

        public static IControl LoginUI()
        {
            return Control(new GameObject("Login UI"), new()
            {
                layout = Utility.FillParentProps(),
                children = Props.List(
                    Image(new ImageProps()
                    {
                        style = { color = Props.Value(elements.midgroundColor) },
                        layout = Utility.FillParentProps(new() { ignoreLayout = Props.Value(true) })
                    }),
                    TightRowsWideColumns(new()
                    {
                        layout = new()
                        {
                            anchorMin = Props.Value(new Vector2(0.5f, 0.66f)),
                            anchorMax = Props.Value(new Vector2(0.5f, 0.66f)),
                            pivot = Props.Value(new Vector2(0.5f, 1f)),
                            sizeDelta = Props.Value(new Vector2(900, 0)),
                            fitContentVertical = Props.Value(ContentSizeFitter.FitMode.PreferredSize)
                        },
                        children = Props.List(
                            LabeledControl(new LabeledControlProps()
                            {
                                label = Props.Value("Username"),
                                labelWidth = Props.Value(225f),
                                control = InputField(new InputFieldProps()
                                {
                                    layout = new() { flexibleWidth = Props.Value(1f) },
                                    value = App.state.settings.username,
                                    onValueChanged = x => App.state.settings.username.value = x
                                })
                            }),
                            LabeledControl(new LabeledControlProps()
                            {
                                label = Props.Value("Password"),
                                labelWidth = Props.Value(225f),
                                control = InputField(new InputFieldProps()
                                {
                                    layout = new() { flexibleWidth = Props.Value(1f) },
                                    value = App.state.settings.password,
                                    contentType = Props.Value(TMP_InputField.ContentType.Password),
                                    onValueChanged = x => App.state.settings.password.value = x
                                })
                            }),
                            HorizontalLayout(new LayoutGroupProps()
                            {
                                childControlWidth = Props.Value(true),
                                childControlHeight = Props.Value(true),
                                childAlignment = Props.Value(TextAnchor.UpperRight),
                                spacing = Props.Value(10f),
                                children = Props.List(
                                    LabeledButton(new LabeledButtonProps()
                                    {
                                        label = Props.Value("Change Server"),
                                        onClick = () =>
                                        {
                                            App.state.serverInfo.value = null;
                                            App.ExecuteTransaction(new SetAuthStatusAction(AuthStatus.Disconnected));
                                        }
                                    }),
                                    LabeledButton(new LabeledButtonProps()
                                    {
                                        label = Props.Value("Log In"),
                                        onClick = () => App.state.loginRequested.value = true
                                    })
                                )
                            }),
                            Text(new TextProps()
                            {
                                value = App.state.authError,
                                element = new() { active = App.state.authError.ObservableSelect(x => !string.IsNullOrEmpty(x)) },
                                style = new TextStyleProps()
                                {
                                    color = Props.Value(Color.red),
                                    horizontalAlignment = Props.Value(HorizontalAlignmentOptions.Center)
                                }
                            })
                        )
                    })
                )
            });
        }

        private static bool IsBusy(AuthStatus status) =>
            status == AuthStatus.Connecting || status == AuthStatus.LoggingIn;
    }
}
