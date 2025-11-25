using UnityEngine;
using Nessle;
using Nessle.StatefulExtensions;
using TMPro;

using static Nessle.UIBuilder;
using ObserveThing;
using UnityEngine.UI;
using FofX.Stateful;
using ObserveThing.StatefulExtensions;

namespace PlerionClient.Client
{
    public static partial class UIElements
    {
        public static IControl LoginUI()
        {
            return Control("loginUI").Setup(loginUI =>
            {
                loginUI.Children(
                    Image().Setup(background =>
                    {
                        background.props.color.From(elements.midgroundColor);
                        background.FillParent();
                        background.Children(
                            TightRowsWideColumns("login").Setup(content =>
                            {
                                content.Anchor(new Vector2(0.5f, 0.66f));
                                content.SetPivot(new Vector2(0.5f, 1f));
                                content.AnchoredPosition(Vector2.zero);
                                content.SizeDelta(new Vector2(900, 0));
                                content.FitContentVertical(ContentSizeFitter.FitMode.PreferredSize);
                                content.Children(
                                    LabeledControl("Username", 225, InputField().Setup(username => username.BindValue(x => x.inputText.text, App.state.username))),
                                    LabeledControl("Password", 225, InputField().Setup(password =>
                                    {
                                        password.props.contentType.From(TMP_InputField.ContentType.Password);
                                        password.BindValue(x => x.inputText.text, App.state.password);
                                    })),
                                    HorizontalLayout().Setup(loginBar =>
                                    {
                                        loginBar.props.childControlWidth.From(true);
                                        loginBar.props.childControlHeight.From(true);
                                        loginBar.props.childAlignment.From(TextAnchor.UpperRight);
                                        loginBar.Children(
                                            Button().Setup(loginButton =>
                                            {
                                                loginButton.LabelFrom("Log In");
                                                loginButton.props.onClick.From(() => App.state.loginRequested.ExecuteSetOrDelay(true));
                                            })
                                        );
                                    }),
                                    Text().Setup(errorText =>
                                    {
                                        errorText.props.style.color.From(Color.red);
                                        errorText.Active(App.state.authError.AsObservable().SelectDynamic(x => !string.IsNullOrEmpty(x)));
                                        errorText.props.text.From(App.state.authError.AsObservable());
                                        errorText.props.style.horizontalAlignment.From(HorizontalAlignmentOptions.Center);
                                    })
                                );
                            })
                        );
                    })
                );
            });
        }
    }
}