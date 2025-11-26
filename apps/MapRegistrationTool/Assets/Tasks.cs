using Cysharp.Threading.Tasks;

namespace Outernet.MapRegistrationTool
{
    public static class Tasks
    {
        public static async UniTask Login(string apiUrl, string username, string password)
        {
            Auth.tokenUrl = $"{apiUrl}/auth/realms/plerion-dev/protocol/openid-connect/token";
            Auth.username = username;
            Auth.password = password;
            await Auth.Login();
            await UniTask.SwitchToMainThread();
            App.state.loggedIn.ExecuteSet(true);
        }
    }
}