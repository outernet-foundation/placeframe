using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using FofX;
using FofX.Stateful;
using Outernet.Logging;
using Placeframe.Core;
using PlaceframeApiClient.Model;

namespace Placeframe.Client
{
    public static class AuthManager
    {
        private static TaskHandle _connectTask = TaskHandle.Complete;
        private static TaskHandle _loginTask = TaskHandle.Complete;
        private static IDisposable _connectSubscription;
        private static IDisposable _loginSubscription;

        public static void Initialize()
        {
            _connectSubscription = App.state.connectRequested.SubscribeOperations(HandleConnectRequestedChanged);
            _loginSubscription = App.state.loginRequested.SubscribeOperations(HandleLoginRequestedChanged);
        }

        public static void Shutdown()
        {
            _connectSubscription?.Dispose();
            _loginSubscription?.Dispose();
            _connectSubscription = null;
            _loginSubscription = null;
            _connectTask.Cancel();
            _loginTask.Cancel();
        }

        private static void HandleConnectRequestedChanged(IReadOnlyList<IStateOperation> args)
        {
            _connectTask.Cancel();

            if (!App.state.connectRequested.value)
                return;

            _connectTask = TaskHandle.Execute(token => Connect(App.state.settings.apiUrl.value, token));
        }

        private static async UniTask Connect(string apiUrl, CancellationToken cancellationToken = default)
        {
            App.ExecuteTransaction(new SetAuthStatusAction(AuthStatus.Connecting));

            ServerInfo serverInfo;
            try
            {
                serverInfo = await VisualPositioningSystem.Discover(apiUrl, cancellationToken);
            }
            catch (Exception exception)
            {
                if (cancellationToken.IsCancellationRequested)
                    return;

                App.ExecuteTransaction(new SetAuthStatusAction(AuthStatus.Error, DescribeDiscoveryFailure(exception)));
                return;
            }

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);
            App.state.serverInfo.value = serverInfo;
            App.ExecuteTransaction(new SetAuthStatusAction(AuthStatus.Connected));

            if (serverInfo.AuthMode == ServerInfo.AuthModeEnum.Disabled)
                App.state.loginRequested.value = true;
        }

        private static void HandleLoginRequestedChanged(IReadOnlyList<IStateOperation> args)
        {
            _loginTask.Cancel();

            if (!App.state.loginRequested.value)
                return;

            _loginTask = TaskHandle.Execute(token => LogIn(
                App.state.settings.apiUrl.value,
                App.state.serverInfo.value,
                App.state.settings.username.value,
                App.state.settings.password.value,
                token
            ));
        }

        private static async UniTask LogIn(string apiUrl, ServerInfo serverInfo, string username, string password, CancellationToken cancellationToken = default)
        {
            App.ExecuteTransaction(new SetAuthStatusAction(AuthStatus.LoggingIn));

            try
            {
                await VisualPositioningSystem.Login(apiUrl, serverInfo, username, password);
            }
            catch (Exception exc) when (exc is not TaskCanceledException)
            {
                App.ExecuteTransaction(new SetAuthStatusAction(AuthStatus.Error, exc.Message));
                return;
            }

            Logger<LogGroup>.EnableLoki(apiUrl, VisualPositioningSystem.CreateBackendAuthHandler(serverInfo));

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);
            App.state.authStatus.value = AuthStatus.LoggedIn;
        }

        private static string DescribeDiscoveryFailure(Exception exception)
        {
            if (exception is UriFormatException)
                return "That doesn't look like a valid URL.";

            // ApiException means something answered but with a non-2xx status or a body that isn't
            // ServerInfo — a wrong host, or a Placeframe server too old to expose /server-info.
            if (exception is PlaceframeApiClient.Client.ApiException)
                return "This doesn't look like a Placeframe server, or it's too old.";

            // Transport failures (connection refused, DNS, timeout) — nothing answered at all.
            return "Couldn't reach a backend at this URL.";
        }
    }
}
