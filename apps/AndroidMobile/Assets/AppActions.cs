using FofX.Stateful;

namespace Placeframe.Client
{
    public class LogInAction : ObservableNodeAction<AppState>
    {
        private string _username;
        private string _password;

        public LogInAction(string username, string password)
        {
            _username = username;
            _password = password;
        }

        public override void Execute(AppState target)
        {
            target.username.value = _username;
            target.password.value = _password;
            target.loginRequested.value = true;
        }
    }

    public class LogOutAction : ObservableNodeAction<AppState>
    {
        public override void Execute(AppState target)
        {
            target.username.Reset();
            target.password.Reset();
            target.authStatus.value = AuthStatus.LoggedOut;
            target.loginRequested.value = false;
        }
    }

    public class SetAuthStatusAction : ObservableNodeAction<AppState>
    {
        private AuthStatus _status;
        private string _error;

        public SetAuthStatusAction(AuthStatus status, string error = null)
        {
            _status = status;
            _error = error;
        }

        public override void Execute(AppState target)
        {
            target.authStatus.value = _status;
            target.authError.value = _status == AuthStatus.Error ? _error : null;
        }
    }
}