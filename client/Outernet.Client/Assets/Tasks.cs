using Plerion.VPS;
using Cysharp.Threading.Tasks;

namespace Outernet.Client.AuthoringTools
{
    public static class Tasks
    {
        public static async UniTask Login(string apiUrl, string username, string password)
        {
            Auth.tokenUrl = $"{apiUrl}/auth/realms/plerion-dev/protocol/openid-connect/token";
            Auth.username = username;
            Auth.password = password;

            await UniTask.WhenAll(
                Auth.Login(),
                VisualPositioningSystem.Initialize(
                    apiUrl,
                    $"{apiUrl}/auth/realms/plerion-dev/protocol/openid-connect/token",
                    username,
                    password
                )
            );

            await UniTask.SwitchToMainThread();
            App.state.loggedIn.ExecuteSet(true);
        }
    }
}