using UnityEngine;

using static Nessle.UIBuilder;
using static Nessle.Props;
using Nessle;
using ObserveThing;
using System;
using TMPro;
using UnityEngine.Events;
using UnityEngine.UI;
using Cysharp.Threading.Tasks;

using Outernet.Client.AuthoringTools;
using UnityEngine.XR.Interaction.Toolkit.Samples.SpatialKeyboard;

namespace Outernet.Client
{
    public static class UIElements
    {
        public struct LoginScreenProps
        {
            public ElementProps element;
            public LayoutProps layout;

            public IValueObservable<float> contentWidth;
            public IValueObservable<float> contentWidthPercent;
            public IValueObservable<RectOffset> contentPadding;

            public IValueObservable<string> domain;
            public IValueObservable<string> username;
            public IValueObservable<string> password;

            public UnityAction<string> onDomainChanged;
            public UnityAction<string> onUsernameChanged;
            public UnityAction<string> onPasswordChanged;

            public Func<string, string, string, UniTask> loginMethod;
        }

        public static IControl LoginScreen(LoginScreenProps props)
        {
            ValueObservable<string> errorMessage = new ValueObservable<string>();
            string domain = default;
            string username = default;
            string password = default;

            LayoutProps contentLayoutProps = new()
            {
                pivot = Value(new Vector2(0.5f, 0.5f)),
                position = Value(Vector2.zero),
                fitContentVertical = Value(ContentSizeFitter.FitMode.PreferredSize)
            };

            if (props.contentWidth != null)
            {
                contentLayoutProps.anchorMin = Value(new Vector2(0.5f, 0.5f));
                contentLayoutProps.anchorMax = Value(new Vector2(0.5f, 0.5f));
                contentLayoutProps.sizeDelta = props.contentWidth.ObservableSelect(x => new Vector2(x, 0));
            }
            else if (props.contentWidthPercent != null)
            {
                contentLayoutProps.anchorMin = props.contentWidthPercent.ObservableSelect(x => new Vector2(0.5f + (-x * 0.5f), 0.5f));
                contentLayoutProps.anchorMax = props.contentWidthPercent.ObservableSelect(x => new Vector2(0.5f + (x * 0.5f), 0.5f));
                contentLayoutProps.offsetMin = Value(Vector2.zero);
                contentLayoutProps.offsetMax = Value(Vector2.zero);
            }
            else
            {
                contentLayoutProps.anchorMin = Value(new Vector2(0, 0.5f));
                contentLayoutProps.anchorMax = Value(new Vector2(1, 0.5f));
                contentLayoutProps.offsetMin = Value(Vector2.zero);
                contentLayoutProps.offsetMax = Value(Vector2.zero);
            }

            return Control("LoginScreen", new()
            {
                element = props.element,
                layout = props.layout,
                children = List(
                    Image(new ImageProps()
                    {
                        style = { color = Value(new Color(0.2196079f, 0.2196079f, 0.2196079f, 1f)) },
                        layout = FillParent()
                    }),
                    TightRowsWideColumns(new()
                    {
                        spacing = Value(10f),
                        layout = contentLayoutProps,
                        padding = props.contentPadding,
                        children = List(
                            Text(new()
                            {
                                value = Value("Log In"),
                                style =
                                {
                                    horizontalAlignment = Value(HorizontalAlignmentOptions.Center),
                                    fontSize = Value(25f)
                                }
                            }),
                            Control("Spacer", new()),
                            LabeledControl(new LabeledControlProps()
                            {
                                label = Value("Domain"),
                                labelWidth = Value(100f),
                                control = PlatformInputField(new()
                                {
                                    inputField =
                                    {
                                        layout = new() { flexibleWidth = Value(true) },
                                        value = props.domain,
                                        onValueChanged = x =>
                                        {
                                            Debug.Log("EP: setting domain from view "+x);
                                            domain = x;
                                            props.onDomainChanged?.Invoke(x);
                                        }
                                    }
                                })
                            }),
                            LabeledControl(new()
                            {
                                label = Value("Username"),
                                labelWidth = Value(100f),
                                control = PlatformInputField(new()
                                {
                                    inputField =
                                    {
                                        layout = new() { flexibleWidth = Value(true) },
                                        value = props.username,
                                        onValueChanged = x =>
                                        {
                                            username = x;
                                            props.onUsernameChanged?.Invoke(x);
                                        }
                                    }
                                })
                            }),
                            LabeledControl(new LabeledControlProps()
                            {
                                label = Value("Password"),
                                labelWidth = Value(100f),
                                control = PlatformInputField(new()
                                {
                                    inputField =
                                    {
                                        layout = new() { flexibleWidth = Value(true) },
                                        value = props.password,
                                        contentType = Value(TMP_InputField.ContentType.Password),
                                        onValueChanged = x =>
                                        {
                                            password = x;
                                            props.onPasswordChanged?.Invoke(x);
                                        }
                                    }
                                })
                            }),
                            HorizontalLayout(new LayoutGroupProps()
                            {
                                childControlWidth = Value(true),
                                childControlHeight = Value(true),
                                childAlignment = Value(TextAnchor.UpperRight),
                                children = List(
                                    LabeledButton(new LabeledButtonProps()
                                    {
                                        label = Value("Log In"),
                                        onClick = async () =>
                                        {
                                            if (props.loginMethod == null)
                                                return;

                                            try
                                            {
                                                await props.loginMethod(domain, username, password);
                                            }
                                            catch (Exception exc)
                                            {
                                                errorMessage.value = exc.Message;
                                            }
                                        }
                                    })
                                )
                            }),
                            Text(new TextProps()
                            {
                                value = errorMessage,
                                element = new() { active = errorMessage.ObservableSelect(x => !string.IsNullOrEmpty(x)) },
                                style = new TextStyleProps()
                                {
                                    color = Value(Color.red),
                                    horizontalAlignment = Value(HorizontalAlignmentOptions.Center)
                                }
                            })
                        )
                    })
                )
            });
        }

        public struct PlatformInputFieldProps
        {
            public InputFieldProps inputField;

            // The below values are ignored if we're not on magic leap
            public IValueObservable<bool> useSceneKeyboard;
            public IValueObservable<XRKeyboard> keyboard;
            public IValueObservable<bool> updateOnKeyPress;
            public IValueObservable<bool> alwaysObserveKeyboard;
            public IValueObservable<bool> monitorInputFieldCharacterLimit;
            public IValueObservable<bool> clearTextOnSubmit;
            public IValueObservable<bool> clearTextOnOpen;
        }

        public static IControl PlatformInputField(PlatformInputFieldProps props)
        {
            var inputField = InputField(props.inputField);

#if OUTERNET_MAGIC_LEAP
            var keyboardDisplay = inputField.gameObject.AddComponent<XRKeyboardDisplay>();
            keyboardDisplay.inputField = inputField.gameObject.GetComponent<TMP_InputField>();

            inputField.AddBinding(
                props.useSceneKeyboard?.Subscribe(x => keyboardDisplay.useSceneKeyboard = x),
                props.keyboard?.Subscribe(x => keyboardDisplay.keyboard = x),
                props.updateOnKeyPress?.Subscribe(x => keyboardDisplay.updateOnKeyPress = x),
                props.alwaysObserveKeyboard?.Subscribe(x => keyboardDisplay.alwaysObserveKeyboard = x),
                props.monitorInputFieldCharacterLimit?.Subscribe(x => keyboardDisplay.monitorInputFieldCharacterLimit = x),
                props.clearTextOnSubmit?.Subscribe(x => keyboardDisplay.clearTextOnSubmit = x),
                props.clearTextOnOpen?.Subscribe(x => keyboardDisplay.clearTextOnOpen = x)
            );
#endif

            return inputField;
        }

        public static IControl TightRowsWideColumns(LayoutGroupProps props)
        {
            props.childControlWidth = props.childControlWidth ?? Value(true);
            props.childControlHeight = props.childControlHeight ?? Value(true);
            props.childForceExpandWidth = props.childForceExpandWidth ?? Value(true);
            props.spacing = props.spacing ?? Value(30f);

            return VerticalLayout(props);
        }

        public struct LabeledButtonProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<string> label;
            public TextStyleProps labelStyle;
            public UnityAction onClick;
            public IValueObservable<bool> interactable;
            public ImageProps background;
        }

        public static IControl LabeledButton(LabeledButtonProps props = default)
        {
            props.labelStyle.horizontalAlignment = props.labelStyle.horizontalAlignment ?? Value(HorizontalAlignmentOptions.Center);
            props.labelStyle.verticalAlignment = props.labelStyle.verticalAlignment ?? Value(VerticalAlignmentOptions.Capline);

            return Button(new ButtonProps()
            {
                interactable = props.interactable,
                background = props.background,
                onClick = props.onClick,
                element = props.element,
                layout = props.layout,
                content = List(
                    Text(new TextProps()
                    {
                        style = props.labelStyle,
                        value = props.label
                    })
                )
            });
        }

        public struct LabeledControlProps
        {
            public IValueObservable<string> label;
            public TextStyleProps labelStyle;
            public IValueObservable<float> labelWidth;
            public IValueObservable<float> spacing;
            public IControl control;
        }

        public static IControl LabeledControl(LabeledControlProps props = default)
        {
            props.labelStyle.verticalAlignment = props.labelStyle.verticalAlignment ?? Value(VerticalAlignmentOptions.Capline);
            props.labelStyle.overflowMode = props.labelStyle.overflowMode ?? Value(TextOverflowModes.Ellipsis);
            props.labelStyle.textWrappingMode = props.labelStyle.textWrappingMode ?? Value(TextWrappingModes.NoWrap);

            props.labelWidth = props.labelWidth ?? Value(200f);

            var control = HorizontalLayout(new()
            {
                spacing = props.spacing,
                childAlignment = Value(TextAnchor.MiddleLeft),
                childControlWidth = Value(true),
                childControlHeight = Value(true),
                children = List(
                    Text(new()
                    {
                        value = props.label,
                        style = props.labelStyle,
                        layout = new()
                        {
                            minWidth = props.labelWidth,
                            preferredWidth = props.labelWidth
                        }
                    }),
                    props.control
                )
            });

            return control;
        }

        public static LayoutProps FillParent()
        {
            return new LayoutProps()
            {
                offsetMin = Value(new Vector2(0, 0)),
                offsetMax = Value(new Vector2(0, 0)),
                anchorMin = Value(new Vector2(0, 0)),
                anchorMax = Value(new Vector2(1, 1))
            };
        }

        public static IControl TransformControl(TransformControlProps props)
        {
            var gameObject = new GameObject("TransformControl");
            var control = gameObject.AddComponent<TransformControl>();
            control.Setup(props);
            return control;
        }
    }
}