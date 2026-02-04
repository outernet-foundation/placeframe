using FofX.Stateful;

namespace Placeframe.Client
{
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