using System.Linq;
using UnityEngine;
using Cysharp.Threading.Tasks;
using UnityEngine.InputSystem;

namespace Outernet.Client.AuthoringTools
{
    public class AuthoringToolsApp : MonoBehaviour
    {
        private bool _unsavedChangesIgnored = false;

        private void Awake()
        {
            Application.wantsToQuit += HandleApplicationWantsToQuit;
        }

        private bool HandleApplicationWantsToQuit()
        {
            if (App.state.authoringTools.hasUnsavedChanges.value && !_unsavedChangesIgnored)
            {
                ShowSaveDialog();
                return false;
            }

            return true;
        }

        private void ShowSaveDialog()
        {
            Dialogs.UnsavedChangesDialog(
                title: "Unsaved Changes",
                text: "Would you like to save your changes before quitting?",
                allowCancel: true,
                binding: props => Bindings.OnRelease(() =>
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
                constructControls: props => UIBuilder.Text("Please wait", horizontalAlignment: TMPro.HorizontalAlignmentOptions.Center)
            );

            App.state.authoringTools.saveRequested.ExecuteSetOrDelay(true);

            await UniTask.WaitUntil(() => !App.state.authoringTools.hasUnsavedChanges.value);

            Destroy(popup.gameObject);
            Application.Quit();
        }

        public static void SetSelectedObjects(params System.Guid[] sceneObjects)
        {
            if (sceneObjects.Length == App.state.authoringTools.selectedObjects.count &&
                sceneObjects.All(x => App.state.authoringTools.selectedObjects.Contains(x)))
            {
                return;
            }

            UndoRedoManager.RegisterUndo(sceneObjects.Length == 0 ? "Deselect" : "Select Object");
            App.ExecuteAction(new SetSelectedObjectIDAction(sceneObjects));
        }

        public static void AddSelectedObject(System.Guid sceneObject)
        {
            if (App.state.authoringTools.selectedObjects.Contains(sceneObject))
                return;

            UndoRedoManager.RegisterUndo("Select Object");
            App.ExecuteAction(new SetSelectedObjectIDAction(App.state.authoringTools.selectedObjects.Append(sceneObject).ToArray()));
        }

        public static void RemoveSelectedObject(System.Guid sceneObject)
        {
            if (!App.state.authoringTools.selectedObjects.Contains(sceneObject))
                return;

            UndoRedoManager.RegisterUndo("Deselect");
            App.ExecuteAction(new SetSelectedObjectIDAction(App.state.authoringTools.selectedObjects.Where(x => x != sceneObject).ToArray()));
        }
    }
}