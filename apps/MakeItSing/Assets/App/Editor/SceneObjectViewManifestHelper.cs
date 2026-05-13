using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;

namespace Plerion.MakeItSing
{
    [InitializeOnLoad]
    public class SceneObjectViewManifestHelper
    {
        static SceneObjectViewManifestHelper()
        {
            EditorSceneManager.sceneSaving += HandleSceneSaving;
            EditorApplication.playModeStateChanged += HandlePlayModeChanged;
        }

        private static void HandlePlayModeChanged(PlayModeStateChange change)
        {
            if (change == PlayModeStateChange.ExitingEditMode)
                UpdateSceneObjectViewManifests(SceneManager.GetActiveScene());
        }

        private static void HandleSceneSaving(UnityEngine.SceneManagement.Scene scene, string path)
        {
            UpdateSceneObjectViewManifests(scene);
        }

        private static void UpdateSceneObjectViewManifests(UnityEngine.SceneManagement.Scene scene)
        {
            foreach (var root in scene.GetRootGameObjects())
            {
                var manifest = root.GetComponentInChildren<DemoSceneSetup>(true);
                if (manifest == null)
                    continue;

                manifest.UpdateViewList();
            }
        }
    }
}