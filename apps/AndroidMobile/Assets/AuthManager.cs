using System;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX;
using FofX.Stateful;
using Placeframe.Core;
using UnityEngine;

namespace Placeframe.Client
{
    public class AuthManager : MonoBehaviour
    {
        private TaskHandle _loginTask = TaskHandle.Complete;

        private void Awake()
        {
            App.RegisterObserver(HandleLoginRequestedChanged, App.state.loginRequested);
        }

        private void OnDestroy()
        {
            App.DeregisterObserver(HandleLoginRequestedChanged);
            _loginTask.Cancel();
        }

        private void HandleLoginRequestedChanged(NodeChangeEventArgs args)
        {
            _loginTask.Cancel();

            if (!App.state.loginRequested.value)
                return;

            _loginTask = TaskHandle.Execute(token => LogIn(App.state.domain.value, App.state.username.value, App.state.password.value, token));
        }

        private async UniTask LogIn(string domain, string username, string password, CancellationToken cancellationToken = default)
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
