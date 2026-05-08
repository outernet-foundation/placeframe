using System;
using System.Collections.Generic;
using Nessle;
using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class SceneViewManager : MonoBehaviour
    {
        private Dictionary<SceneObjectId, GameObject> _views = new Dictionary<SceneObjectId, GameObject>();
        private IDisposable _subscriptions;

        private void Awake()
        {
            _subscriptions = new ComposedDisposable(

                Observables.ObservableCombineValues(
                    App.state.roomDemoSceneInitialized,
                    App.state.roomStateInitialized,
                    (sceneInit, stateInit) => sceneInit && stateInit
                ).Subscribe(
                    setupViews =>
                    {
                        if (!setupViews)
                            return;

                        int nextSceneObjectId = -1;

                        // TODO: Investigate
                        foreach (var sceneObjectView in DemoSceneSetup.SceneViews)
                        {
                            var id = new SceneObjectId(nextSceneObjectId);
                            nextSceneObjectId--;

                            if (sceneObjectView == null)
                                continue;

                            if (!App.state.scene.objects.ContainsKey(id))
                            {
                                Destroy(sceneObjectView.gameObject);
                                continue;
                            }

                            foreach (var viewComponent in sceneObjectView.GetComponents<ISceneObjectViewComponent>())
                                viewComponent.Setup(id);

                            _views.Add(id, sceneObjectView);
                        }
                    }
                ),

                App.state.scene.objects.Subscribe(
                    onAdd: obj =>
                    {
                        // if viewPrefab is null, this object was loaded with the scene and
                        // should already be in the _views dictionary
                        if (obj.Value.viewPrefab.value == null)
                            return;

                        var view = CreateView(obj.Value.viewPrefab.value);
                        _views.Add(obj.Key, view);

                        foreach (var viewComponent in view.GetComponents<ISceneObjectViewComponent>())
                            viewComponent.Setup(obj.Key);
                    },
                    onRemove: obj =>
                    {
                        var view = _views[obj.Key];
                        _views.Remove(obj.Key);

                        foreach (var viewComponent in view.GetComponents<ISceneObjectViewComponent>())
                            viewComponent.Teardown();

                        Destroy(view);
                    }
                )
            );
        }

        private void OnDestroy()
        {
            _subscriptions.Dispose();
        }

        private GameObject CreateView(string viewPrefab)
            => Instantiate(Resources.Load<GameObject>(viewPrefab));
    }
}