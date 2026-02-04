using System;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX;
using Placeframe.Core;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Placeframe.MapRegistrationTool
{
    public class LoginScreen : MonoBehaviour
    {
        public TMP_InputField domain;
        public TMP_InputField username;
        public TMP_InputField password;
        public TextMeshProUGUI errorText;
        public Button loginButton;

        private TaskHandle _loginTask = TaskHandle.Complete;

        private void Awake()
        {
            App.state.settings.domain.OnChange(x => domain.text = x);
            App.state.settings.username.OnChange(x => username.text = x);
            App.state.settings.password.OnChange(x => password.text = x);
            App.state.authError.OnChange(x => errorText.text = x);
            App.state.authStatus.OnChange(x => errorText.gameObject.SetActive(x == AuthStatus.Error));
            App.state.loggedIn.OnChange(x => gameObject.SetActive(!x));

            domain.onValueChanged.AddListener(x => App.state.settings.domain.ExecuteSetOrDelay(x));
            username.onValueChanged.AddListener(x => App.state.settings.username.ExecuteSetOrDelay(x));
            password.onValueChanged.AddListener(x => App.state.settings.password.ExecuteSetOrDelay(x));

            loginButton.onClick.AddListener(() =>
            {
                _loginTask?.Cancel();
                _loginTask = TaskHandle.Execute(token => Login(
                    App.state.settings.domain.value,
                    App.state.settings.username.value,
                    App.state.settings.password.value,
                    token
                ));
            });
        }

        private async UniTask Login(string domain, string username, string password, CancellationToken cancellationToken = default)
        {
            App.ExecuteActionOrDelay(new SetAuthStatusAction(AuthStatus.LoggingIn));

            try
            {
                await VisualPositioningSystem.Login(domain, username, password);
            }
            catch (Exception exc)
            {
                App.ExecuteActionOrDelay(new SetAuthStatusAction(AuthStatus.Error, exc.Message));
                throw exc;
            }

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);
            App.state.authStatus.ExecuteSetOrDelay(AuthStatus.LoggedIn);
        }
    }
}
