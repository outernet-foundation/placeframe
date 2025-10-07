using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Outernet.Client.AuthoringTools
{
    public class LoginScreen : MonoBehaviour
    {
        public TMP_InputField username;
        public TMP_InputField password;
        public Button loginButton;

        private void Awake()
        {
            loginButton.onClick.AddListener(() =>
            {
                VPSManager.Initialize(username.text, password.text);

                App.state.loggedIn.ExecuteSet(true);
            });

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
    }
}