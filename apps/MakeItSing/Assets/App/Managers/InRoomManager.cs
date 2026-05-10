using System;
using System.Collections.Generic;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX;
using FofX.Stateful;
using ObserveThing;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.SceneManagement;

namespace Plerion.MakeItSing
{
    public class InRoomManager : MonoBehaviour
    {
        private string _loadedSceneID = null;
        private Scene _loadedScene = default;
        private TaskHandle _loadRoomTask = TaskHandle.Complete;
        private IDisposable _subscription;

        private void Awake()
        {
            PlayerIdHelpers.Setup(
                App.state.playerID.value,
                App.state.scene.objects.ObservableSelect(x => x.Key),
                App.state.scene.highFrequencyPrimitives.ObservableSelect(x => x.Value.id)
            );

            _subscription = new ComposedDisposable(

                StateObservables.ObservableCombineOperations(
                    App.state.rooms,
                    App.state.roomID,
                    App.state.inRoom,
                    App.state.isMasterClient,
                    App.state.roomStateInitialized
                ).Subscribe(HandleShouldInitializeRoomSceneChanged),

                StateObservables.ObservableCombineOperations(
                    App.state.roomDemoSceneInitialized,
                    App.state.roomStateInitialized,
                    App.state.isMasterClient
                ).Subscribe(HandleShouldInitializeRoomState)

            );
        }

        private void OnDestroy()
        {
            PlayerIdHelpers.Reset();

            _subscription.Dispose();
            _loadRoomTask.Cancel();

            if (_loadedScene.IsValid())
            {
                SceneManager.UnloadSceneAsync(_loadedScene);
                _loadedScene = default;
                _loadedSceneID = null;
            }
        }

        private void HandleShouldInitializeRoomSceneChanged(IReadOnlyList<IStateOperation> ops)
        {
            if (!App.state.inRoom.value)
                return;

            if (!App.state.isMasterClient.value && !App.state.roomStateInitialized.value)
                return;

            if (!App.state.rooms.TryGetValue(App.state.roomID.value, out var roomData))
                return;

            string roomDemoSceneID = roomData.demoScene.value;

            if (_loadedSceneID == roomDemoSceneID)
                return;

            _loadRoomTask.Cancel();

            if (_loadedScene.IsValid())
            {
                SceneManager.UnloadSceneAsync(_loadedScene);
                _loadedScene = default;
            }

            if (string.IsNullOrEmpty(roomDemoSceneID))
                return;

            // load scene here
            _loadedSceneID = roomDemoSceneID;
            _loadRoomTask = TaskHandle.Execute(token => LoadScene(roomDemoSceneID, token));
        }

        private void HandleShouldInitializeRoomState(IReadOnlyList<IStateOperation> ops)
        {
            if (!App.state.isMasterClient.value || App.state.roomStateInitialized.value || !App.state.roomDemoSceneInitialized.value)
                return;

            SceneState sceneState = new SceneState();
            sceneState.Initialize(new ObservationContext(), new DefaultLogger(), "scene");
            sceneState.startTime.value = App.state.roomConnectionTime.value;

            int nextSceneObjectId = -1;

            foreach (var sceneObjectView in DemoSceneSetup.SceneViews)
            {
                var id = new SceneObjectId(nextSceneObjectId);
                nextSceneObjectId--;

                if (sceneObjectView == null)
                    continue;

                sceneState.objects.Add(id);

                foreach (var viewComponent in sceneObjectView.GetComponents<ISceneObjectViewComponent>())
                    viewComponent.WriteInitialState(sceneState, id);
            }

            App.ExecuteTransaction(new ApplyInitialSceneStateAction(sceneState));
        }

        private async UniTask LoadScene(string roomSceneID, CancellationToken cancellationToken = default)
        {
            Scene loadedScene;

            if (roomSceneID.StartsWith("EDITOR://"))
            {
                var path = roomSceneID.Substring(9);
                loadedScene = SceneManager.GetSceneByPath(path);
                if (!loadedScene.IsValid())
                {
                    await SceneManager.LoadSceneAsync(path, LoadSceneMode.Additive);
                    loadedScene = SceneManager.GetSceneByPath(path);
                }
            }
            else if (roomSceneID.StartsWith("EMBEDDED://"))
            {
                int sceneBuildIndex = int.Parse(roomSceneID.Substring(11));
                await SceneManager.LoadSceneAsync(sceneBuildIndex, LoadSceneMode.Additive);
                loadedScene = SceneManager.GetSceneByBuildIndex(sceneBuildIndex);
            }
            else if (App.state.loadedDemoScenes.TryGetValue(roomSceneID, out var pathState))
            {
                string path = pathState.value;
                await SceneManager.LoadSceneAsync(path, LoadSceneMode.Additive);
                loadedScene = SceneManager.GetSceneByPath(path);
            }
            else if (roomSceneID.StartsWith("FILE://"))
            {
                var request = UnityWebRequestAssetBundle.GetAssetBundle(new Uri(roomSceneID));
                await request.SendWebRequest().ToUniTask(cancellationToken: cancellationToken);
                var path = DownloadHandlerAssetBundle.GetContent(request).GetAllScenePaths()[0];
                await SceneManager.LoadSceneAsync(path, LoadSceneMode.Additive);
                loadedScene = SceneManager.GetSceneByPath(path);

                App.state.loadedDemoScenes.Add(roomSceneID).value = path;
            }
            else
            {
                if (!SupabaseAPI.IsConfigured)
                {
                    Debug.LogWarning($"[InRoomManager] Cannot load demo scene '{roomSceneID}': Supabase is not configured. Skipping room load.");
                    return;
                }

                var assetBundle = await SupabaseAPI.GetDemoSceneAssetBundle(App.state.version.value, PlatformConfig.GetConfig(App.state.platform.value).supabaseBucket, roomSceneID);
                var path = assetBundle.GetAllScenePaths()[0];
                await SceneManager.LoadSceneAsync(path, LoadSceneMode.Additive);
                loadedScene = SceneManager.GetSceneByPath(path);

                App.state.loadedDemoScenes.Add(roomSceneID).value = path;
            }

            await UniTask.SwitchToMainThread(cancellationToken);

            SceneManager.SetActiveScene(loadedScene);
            _loadedScene = loadedScene;

            GameObject sceneViewManager = new GameObject("SceneViewManager", typeof(SceneOrigin), typeof(SceneViewManager));

            foreach (var root in _loadedScene.GetRootGameObjects())
                root.transform.SetParent(sceneViewManager.transform);

            App.state.roomDemoSceneInitialized.value = true;
        }
    }
}