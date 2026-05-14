using UnityEngine;
using UnityEngine.Events;

using Nessle;

using ObserveThing;

using static Nessle.UIBuilder;
using static Nessle.Props;

namespace Plerion.MakeItSing
{
    public static partial class UIElements
    {
        public struct LoginUIProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<string> domain;
            public IValueObservable<string> username;
            public IValueObservable<string> password;
            public IValueObservable<string> loginErrorMessage;
            public UnityAction<string> onDomainChanged;
            public UnityAction<string> onUsernameChanged;
            public UnityAction<string> onPasswordChanged;
            public UnityAction onLoginSelected;
        }

        public static IControl LoginUI(LoginUIProps props)
        {
            return Control(
                "LoginUI",
                new()
                {
                    element = props.element,
                    layout = props.layout,
                    children = List(
                        Image(new()
                        {
                            style = { color = Value(elements.backgroundColor) },
                            layout = FillParentProps()
                        }),
                        VerticalLayout(new()
                        {
                            layout = FillParentProps(),
                            childAlignment = Value(TextAnchor.MiddleCenter),
                            childControlWidth = Value(true),
                            childControlHeight = Value(true),
                            padding = Value(new RectOffset(20, 20, 0, 0)),
                            spacing = Value(10f),
                            children = List(
                                Text(new()
                                {
                                    value = Value("Outernet"),
                                    style =
                                    {
                                        fontSize = Value(20f),
                                        horizontalAlignment = Value(TMPro.HorizontalAlignmentOptions.Center)
                                    }
                                }),
                                VerticalLayout(new()
                                {
                                    layout =
                                    {
                                        flexibleWidth = Value(0f),
                                        preferredWidth = Value(600f)
                                    },
                                    spacing = Value(10f),
                                    childAlignment = Value(TextAnchor.MiddleCenter),
                                    childControlWidth = Value(true),
                                    childControlHeight = Value(true),
                                    children = List(
                                        LabeledProperty(new()
                                        {
                                            label = Value("Domain"),
                                            labelWidth = Value(75f),
                                            content = Value(PlatformInputField(new()
                                            {
                                                inputField =
                                                {
                                                    value = props.domain,
                                                    layout = { flexibleWidth = Value(1f) },
                                                    onValueChanged = props.onDomainChanged
                                                }
                                            }))
                                        }),
                                        LabeledProperty(new()
                                        {
                                            label = Value("Username"),
                                            labelWidth = Value(75f),
                                            content = Value(PlatformInputField(new()
                                            {
                                                inputField =
                                                {
                                                    value = props.username,
                                                    layout = { flexibleWidth = Value(1f) },
                                                    onValueChanged = props.onUsernameChanged
                                                }
                                            }))
                                        }),
                                        LabeledProperty(new()
                                        {
                                            label = Value("Password"),
                                            labelWidth = Value(75f),
                                            content = Value(PlatformInputField(new()
                                            {
                                                inputField =
                                                {
                                                    value = props.password,
                                                    layout = { flexibleWidth = Value(1f) },
                                                    contentType = Value(TMPro.TMP_InputField.ContentType.Password),
                                                    onValueChanged = props.onPasswordChanged
                                                }
                                            }))
                                        }),
                                        HorizontalLayout(new()
                                        {
                                            childControlHeight = Value(true),
                                            childControlWidth = Value(true),
                                            childAlignment = Value(TextAnchor.MiddleCenter),
                                            children = List(
                                                Button(new()
                                                {
                                                    onClick = props.onLoginSelected,
                                                    content = List(Text(new() { value = Value("Login") }))
                                                })
                                            )
                                        }),
                                        Text(new()
                                        {
                                            element = { active = props.loginErrorMessage.ObservableSelect(x => !string.IsNullOrEmpty(x)) },
                                            value = props.loginErrorMessage,
                                            style =
                                            {
                                                color = Value(Color.red),
                                                horizontalAlignment = Value(TMPro.HorizontalAlignmentOptions.Center),
                                                verticalAlignment = Value(TMPro.VerticalAlignmentOptions.Baseline)
                                            }
                                        })
                                    )
                                })
                            )
                        })
                    )
                }
            );
        }
    }
}