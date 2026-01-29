using Cysharp.Threading.Tasks;
using Placeframe.Core;
using UnityEngine;

namespace Outernet.MapRegistrationTool
{
    public static class Tasks
    {
        public static async UniTask Login(string username, string password)
        {
            await Auth.Login(username, password);
            await UniTask.SwitchToMainThread();
            App.state.loggedIn.ExecuteSet(true);
        }
    }
}
