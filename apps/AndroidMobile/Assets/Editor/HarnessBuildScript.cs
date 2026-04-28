using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace Placeframe.Client
{
    // Harness APK build. Validates AndroidBoundHttpHandler's JNI code path on
    // real hardware — Editor Play Mode can't, because AndroidJavaObject is a no-op
    // off-device.
    //
    // Invoke from a shell with ADB_SERVER_SOCKET unset. Unity's Android build module
    // runs `adb kill-server` on teardown, and in a --with-adb slot that kill message
    // propagates to (and terminates) the host-side adb server:
    //   env -u ADB_SERVER_SOCKET Unity -batchmode -nographics -quit \
    //     -projectPath apps/AndroidMobile \
    //     -executeMethod Placeframe.Client.HarnessBuild.BuildHandlerTest \
    //     -buildTarget Android
    //
    // The harness APK shares com.outernet.captureapp with the production Capture
    // Tool, so `adb install -r` replaces production. Harness is version code 1;
    // if the installed production build is a release build at higher version,
    // `adb uninstall com.outernet.captureapp` first to sidestep the downgrade
    // block (the `-d` flag won't help for release builds).
    public static class HarnessBuild
    {
        private const string HarnessScenePath = "Assets/Scenes/HandlerTest.unity";

        public static void BuildHandlerTest()
        {
            CreateHarnessScene();

            PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.OpenGLES3 });
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64 | AndroidArchitecture.X86_64;
            PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel29;
            PlayerSettings.Android.targetSdkVersion = AndroidSdkVersions.AndroidApiLevelAuto;
            EditorUserBuildSettings.androidBuildSubtarget = MobileTextureSubtarget.ASTC;

            string outputPath = "Build/HandlerTest.apk";
            Directory.CreateDirectory("Build");

            BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { HarnessScenePath },
                locationPathName = outputPath,
                target = BuildTarget.Android,
                targetGroup = BuildTargetGroup.Android,
                options = BuildOptions.Development,
            });
        }

        private static void CreateHarnessScene()
        {
            Directory.CreateDirectory("Assets/Scenes");
            var scene = EditorSceneManager.NewScene(
                NewSceneSetup.EmptyScene,
                NewSceneMode.Single
            );

            var runnerObject = new GameObject("HandlerTestRunner");
            runnerObject.AddComponent<HandlerTestRunner>();

            EditorSceneManager.SaveScene(scene, HarnessScenePath);
        }
    }
}
