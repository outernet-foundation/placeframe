using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Plerion.MakeItSing.LiveKitSpike
{
    public static class BuildSpike
    {
        private const string ScenePath = "Assets/_LiveKitSpike/SmokeScene.unity";

        public static void BuildSpikeForMagicLeap()
        {
            EnsureSpikeScene();
            PointBuildAtSpike();
            Plerion.Build.BuildForMagicLeap();
        }

        private static void EnsureSpikeScene()
        {
            if (File.Exists(ScenePath))
            {
                return;
            }

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var spike = new GameObject("Spike");
            spike.AddComponent<SmokeScene>();
            EditorSceneManager.SaveScene(scene, ScenePath);
        }

        private static void PointBuildAtSpike()
        {
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(ScenePath, true),
            };
        }
    }
}
