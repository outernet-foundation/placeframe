using TMPro;
using UnityEngine;
using UnityEngine.UI;
using Plerion.VPS;
using Cysharp.Threading.Tasks;
using System;

namespace Outernet.Client.AuthoringTools
{
    public class LoginScreen : MonoBehaviour
    {
        public TMP_InputField username;
        public TMP_InputField password;
        public TextMeshProUGUI errorText;
        public Button loginButton;

        private void Awake()
        {
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
            Auth.username = username;
            Auth.password = password;

            try
            {
                await Auth.Login();
            }
            catch (Exception exc)
            {
                await UniTask.SwitchToMainThread();
                errorText.text = exc.Message;
                errorText.gameObject.SetActive(true);
                return;
            }

            await UniTask.SwitchToMainThread();
            VisualPositioningSystem.Initialize(username, password);
            App.state.loggedIn.ExecuteSet(true);
        }
    }
}