using System;
using System.Linq;
using System.Net.Http;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX;
using FofX.Stateful;
using Placeframe.Core;
using PlaceframeApiClient.Api;
using UnityEngine;

namespace Placeframe.MapRegistrationTool
{
    public class App : AppBase<AppState>
    {
        public static DefaultApi API { get; private set; }

        private bool _unsavedChangesIgnored = false;

        protected override void InitializeState(AppState state) =>
            state.Initialize("root", new ObservableNodeContext(new ChannelLogger() { logGroup = LogGroup.Stateful }));

        private void Start()
        {
            RegisterObserver(HandleLoggedInChanged, state.loggedIn);
            Application.wantsToQuit += WantsToQuit;
        }

        private void HandleLoggedInChanged(NodeChangeEventArgs args)
        {
            if (!state.loggedIn.value)
            {
                API = null;
                return;
            }

            API = new DefaultApi(
                new HttpClient(new AuthHttpHandler() { InnerHandler = new HttpClientHandler() })
                {
                    BaseAddress = new Uri($"https://{state.settings.domain.value}"),
                },
                $"https://{state.settings.domain.value}"
            );
        }

        protected override void Update()
        {
            base.Update();

            UnityMainThreadDispatcher.Flush();
        }

        private bool WantsToQuit()
        {
            if (state.hasUnsavedChanges.value && !_unsavedChangesIgnored)
            {
                ShowSaveDialog();
                return false;
            }

            Logger.Terminate();
            return true;
        }

        private void ShowSaveDialog()
        {
            Dialogs.UnsavedChangesDialog(
                title: "Unsaved Changes",
                text: "Would you like to save your changes before quitting?",
                allowCancel: true,
                binding: props =>
                    Bindings.OnRelease(() =>
                    {
                        if (props.status.value != DialogStatus.Complete)
                            return;

                        if (props.saveRequested.value)
                        {
                            SaveWithPopup().Forget();
                        }
                        else
                        {
                            _unsavedChangesIgnored = true;
                            Application.Quit();
                        }
                    })
            );
        }

        private async UniTask SaveWithPopup()
        {
            var popup = Dialogs.Show(
                title: "Saving",
                allowCancel: false,
                minimumWidth: 200,
                constructControls: props =>
                    UIBuilder.Text("Please wait", horizontalAlignment: TMPro.HorizontalAlignmentOptions.Center)
            );

            App.state.saveRequested.ExecuteSetOrDelay(true);

            await UniTask.WaitUntil(() => !App.state.hasUnsavedChanges.value);

            Destroy(popup.gameObject);
            Application.Quit();
        }

        public static void SetSelectedObjects(params System.Guid[] sceneObjects)
        {
            if (
                sceneObjects.Length == App.state.selectedObjects.count
                && sceneObjects.All(x => App.state.selectedObjects.Contains(x))
            )
            {
                return;
            }

            UndoRedoManager.RegisterUndo(sceneObjects.Length == 0 ? "Deselect" : "Select Object");
            App.ExecuteAction(new SetSelectedObjectIDAction(sceneObjects));
        }

        public static void AddSelectedObject(System.Guid sceneObject)
        {
            if (App.state.selectedObjects.Contains(sceneObject))
                return;

            UndoRedoManager.RegisterUndo("Select Object");
            App.ExecuteAction(new SetSelectedObjectIDAction(App.state.selectedObjects.Append(sceneObject).ToArray()));
        }

        public static void RemoveSelectedObject(System.Guid sceneObject)
        {
            if (!App.state.selectedObjects.Contains(sceneObject))
                return;

            UndoRedoManager.RegisterUndo("Deselect");
            App.ExecuteAction(
                new SetSelectedObjectIDAction(App.state.selectedObjects.Where(x => x != sceneObject).ToArray())
            );
        }
    }
}
