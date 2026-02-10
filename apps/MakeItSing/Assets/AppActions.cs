using FofX.Stateful;

namespace Plerion.MakeItSing
{
    public class RequestConnectionAction : ObservableNodeAction<ConnectionState>
    {
        private string _connectionString;

        public RequestConnectionAction(string connectionString)
        {
            _connectionString = connectionString;
        }

        public override void Execute(ConnectionState target)
        {
            target.connectionString.value = _connectionString;
            target.shouldBeConnected.value = true;
        }
    }

    public class SetConnectionStatusAction : ObservableNodeAction<ConnectionState>
    {
        private ConnectionStatus _status;
        private string _error;

        public SetConnectionStatusAction(ConnectionStatus status, string error = default)
        {
            _status = status;
            _error = error;
        }

        public override void Execute(ConnectionState target)
        {
            target.status.value = _status;
            target.error.value = _status == ConnectionStatus.Error ? _error : null;
        }
    }

    public class ConnectedToRoomAction : ObservableNodeAction<AppState>
    {
        private int _playerID;
        private bool _isMasterClient;

        public ConnectedToRoomAction(int playerID, bool isMasterClient)
        {
            _playerID = playerID;
            _isMasterClient = isMasterClient;
        }

        public override void Execute(AppState target)
        {
            target.playerID.value = _playerID;
            target.isMasterClient.value = _isMasterClient;
            target.roomConnection.status.value = ConnectionStatus.Connected;
        }
    }
}