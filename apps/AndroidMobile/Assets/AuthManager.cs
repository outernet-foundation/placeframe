using System;
using System.Collections.Generic;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX;
using FofX.Stateful;
using Outernet.Logging;
using Placeframe.Core;

namespace Placeframe.Client
{
    public static class AuthManager
    {
        private static TaskHandle _loginTask = TaskHandle.Complete;
        private static IDisposable _subscription;

        public static void Initialize()
        {
            _subscription = App.state.loginRequested.SubscribeOperations(HandleLoginRequestedChanged);
        }

        public static void Shutdown()
        {
            _subscription?.Dispose();
            _subscription = null;
            _loginTask.Cancel();
        }

        private static void HandleLoginRequestedChanged(IReadOnlyList<IStateOperation> args)
        {
            _loginTask.Cancel();

            if (!App.state.loginRequested.value)
                return;

            _loginTask = TaskHandle.Execute(token => LogIn(App.state.settings.domain.value, App.state.settings.username.value, App.state.settings.password.value, token));
        }

        private static async UniTask LogIn(string domain, string username, string password, CancellationToken cancellationToken = default)
        {
            App.ExecuteTransaction(new SetAuthStatusAction(AuthStatus.LoggingIn));

            try
            {
                await VisualPositioningSystem.Login(domain, username, password);
            }
            catch (Exception exc)
            {
                App.ExecuteTransaction(new SetAuthStatusAction(AuthStatus.Error, exc.Message));
                throw exc;
            }

            Logger<LogGroup>.EnableLoki(
                domain,
                tokenProvider: () => Auth.GetOrRefreshToken(),
                labels: new[]
                {
                    ("app", "capture-tool"),
#if UNITY_EDITOR
                    ("platform", "editor"),
#else
                    ("platform", "android-mobile"),
#endif
                },
                handler: InternetBoundHandler.Create()
            );

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);
            App.state.authStatus.value = AuthStatus.LoggedIn;
        }
    }
}
