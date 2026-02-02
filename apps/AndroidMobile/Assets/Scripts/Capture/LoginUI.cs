using UnityEngine;
using Nessle;
using TMPro;

using static Nessle.UIBuilder;
using ObserveThing;
using UnityEngine.UI;
using FofX.Stateful;
using ObserveThing.StatefulExtensions;

namespace Placeframe.Client
{
    public static partial class UIElements
    {
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
                                    layout = new() { flexibleWidth = Props.Value(true) },
                                    value = App.state.username.AsObservable(),
                                    onValueChanged = x => App.state.username.ExecuteSetOrDelay(x)
                                })
                            }),
                            LabeledControl(new LabeledControlProps()
                            {
                                label = Props.Value("Password"),
                                labelWidth = Props.Value(225f),
                                control = InputField(new InputFieldProps()
                                {
                                    layout = new() { flexibleWidth = Props.Value(true) },
                                    value = App.state.password.AsObservable(),
                                    contentType = Props.Value(TMP_InputField.ContentType.Password),
                                    onValueChanged = x => App.state.password.ExecuteSetOrDelay(x)
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
                                        label = Props.Value("Log In"),
                                        onClick = () => App.state.loginRequested.ExecuteSetOrDelay(true)
                                    })
                                )
                            }),
                            Text(new TextProps()
                            {
                                value = App.state.authError.AsObservable(),
                                element = new() { active = App.state.authError.AsObservable().SelectDynamic(x => !string.IsNullOrEmpty(x)) },
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
    }
}