using System;
using System.Collections.Generic;
using System.Linq;
using Cysharp.Threading.Tasks;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Plerion.MakeItSing
{
    public class DemoSceneSetup : MonoBehaviour
    {
        public static IEnumerable<GameObject> SceneViews => _instance._sceneViews;
        private static DemoSceneSetup _instance;

        [SerializeField]
        private List<GameObject> _sceneViews;

        private void Awake()
        {
            if (_instance != null)
            {
                Destroy(gameObject);
                throw new System.Exception($"Only one instance of {nameof(DemoSceneSetup)} allowed in a scene at a time! This will lead to major errors! Abort!");
            }

            _instance = this;

#if UNITY_EDITOR
            if (!App.AppInitialized)
                InitializeApp().Forget();
#endif
        }

        private void OnDestroy()
        {
            if (_instance == this)
                _instance = null;
        }

#if UNITY_EDITOR
        private async UniTask InitializeApp()
        {
            var scene = SceneManager.GetActiveScene();

            await SceneManager.LoadSceneAsync("Main", LoadSceneMode.Additive);

            await UniTask.WaitUntil(() => App.AppInitialized);

            App.ExecuteTransaction(state =>
            {
                var room = state.rooms.Add(Guid.NewGuid());
                room.name.value = $"{SceneManager.GetActiveScene().name}-TEMP";
                room.version.value = Application.version;
                room.demoScene.value = $"EDITOR://{scene.path}";
                room.isLocal.value = true;

                state.roomID.value = room.id;
            });
        }

        public void UpdateViewList()
        {
            var views = gameObject.scene.GetRootGameObjects()
                .SelectMany(x => x.GetComponentsInChildren<ISceneObjectViewComponent>(true))
                .Select(x => x.gameObject)
                .Distinct();

            foreach (var view in views)
            {
                if (_sceneViews.Contains(view))
                    continue;

                _sceneViews.Add(view);
            }
        }
#endif
    }
}