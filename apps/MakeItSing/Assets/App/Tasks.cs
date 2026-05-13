using System;
using Cysharp.Threading.Tasks;
using Placeframe.Core;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public static class Tasks
    {
        public static async UniTask Login()
        {
            App.state.loginStatus.value = LoginStatus.LoggingIn;

            try
            {
                await VisualPositioningSystem.Login(
                    App.state.userSettings.domain.value,
                    App.state.userSettings.username.value,
                    App.state.userSettings.password.value
                );

                Outernet.Logging.Logger<LogGroup>.EnableLoki(
                    App.state.userSettings.domain.value,
                    tokenProvider: () => Auth.GetOrRefreshToken()
                );
            }
            catch (Exception exc)
            {
                await UniTask.SwitchToMainThread();

                App.ExecuteTransaction(state =>
                {
                    state.loginStatus.value = LoginStatus.Error;
                    state.loginError.value = exc.Message;
                });

                return;
            }

            App.state.loginStatus.value = LoginStatus.LoggedIn;
        }
    }
}