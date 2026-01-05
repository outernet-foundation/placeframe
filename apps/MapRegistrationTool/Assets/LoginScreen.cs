using System;
using Cysharp.Threading.Tasks;
using Plerion.Core;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Outernet.MapRegistrationTool
{
    public class LoginScreen : MonoBehaviour
    {
        public TMP_InputField username;
        public TMP_InputField password;
        public TextMeshProUGUI errorText;
        public Button loginButton;

        private void Awake()
        {
            VisualPositioningSystem.Initialize(
                null,
                App.plerionApiUrl,
                App.plerionAuthUrl,
                App.plerionAuthClient,
                message => Debug.Log(message),
                message => Debug.LogWarning(message),
                message => Debug.LogError(message),
                (message, exception) => Debug.LogError($"{message}\n{exception}")
            );

            loginButton.onClick.AddListener(() => Login(username.text, password.text).Forget());

            App.state.loggedIn.OnChange(x =>
            {
                if (x)
                {
                    gameObject.SetActive(false);
                    return;
                }

                gameObject.SetActive(true);
                username.text = null;
                password.text = null;
            });
        }

        private async UniTask Login(string username, string password)
        {
            try
            {
                await Tasks.Login(username, password);
            }
            catch (Exception exc)
            {
                await UniTask.SwitchToMainThread();
                errorText.text = exc.Message;
                errorText.gameObject.SetActive(true);
                return;
            }
        }
    }
}
