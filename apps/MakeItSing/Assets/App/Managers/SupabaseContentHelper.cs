using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using FofX;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class SupabaseContentHelper : MonoBehaviour
    {
        private TaskHandle _pollTask = TaskHandle.Complete;

        private void Awake()
        {
            _pollTask = TaskHandle.Execute(token => PollContent(10f, token));
        }

        private void OnDestroy()
        {
            _pollTask.Cancel();
        }

        private async UniTask PollContent(float pollDelay, CancellationToken cancellationToken = default)
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                float pollTime = Time.time;

                try
                {
                    GetRoomResponse[] rooms = default;
                    FileData[] demoScenes = default;

                    await UniTask.WhenAll(
                        SupabaseAPI.GetRooms(version: App.state.version.value).ContinueWith(x => rooms = x),
                        SupabaseAPI.GetDemoScenes(App.state.version.value, PlatformConfig.GetConfig(App.state.platform.value).supabaseBucket).ContinueWith(x => demoScenes = x)
                    );

                    await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);

                    App.ExecuteTransaction(
                        new SetRoomsAction(rooms),
                        new SetDemoScenesAction(demoScenes.Select(x => x.name).ToArray())
                    );
                }
                catch (Exception exc)
                {
                    if (exc is TaskCanceledException)
                        break;

                    Debug.LogException(exc);
                }

                if (Time.time - pollTime < pollDelay)
                    await UniTask.WaitForSeconds(pollDelay - (Time.time - pollTime));
            }
        }
    }
}