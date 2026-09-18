using System;
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.XR.Management;
using UnityEditor.XR.Management.Metadata;
using UnityEngine;
using UnityEngine.Rendering;

namespace Placeframe.Client
{
    public static class Build
    {
        public static void BuildForAndroidMobile()
        {
            ApplyConfigType();

            var settings = XRGeneralSettingsPerBuildTarget.XRGeneralSettingsForBuildTarget(BuildTargetGroup.Android);
            XRPackageMetadataStore.AssignLoader(settings.Manager, "Unity.XR.ARCore.ARCoreLoader", BuildTargetGroup.Android);

            PlayerSettings.SetScriptingDefineSymbols(NamedBuildTarget.Android, "");
            PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.OpenGLES3 });
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            EditorUserBuildSettings.androidBuildSubtarget = MobileTextureSubtarget.ASTC;

            string sanitizedName = Regex.Replace(PlayerSettings.productName, @"[^a-zA-Z0-9._-]", "_");
            string outputPath = $"Build/{sanitizedName}.apk";
            Directory.CreateDirectory("Build");

            Placeframe.BuildUtility.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { "Assets/Scenes/Main.unity" },
                locationPathName = outputPath,
                target = BuildTarget.Android,
                targetGroup = BuildTargetGroup.Android,
            });
        }

        private static void ApplyConfigType()
        {
            const string targetDirectory = "Assets/_LocalWorkspace/Resources";
            const string targetPath = targetDirectory + "/default-settings.json";

            if (File.Exists(targetPath)) File.Delete(targetPath);
            if (File.Exists(targetPath + ".meta")) File.Delete(targetPath + ".meta");

            var configType = Environment.GetEnvironmentVariable("CONFIG_TYPE");
            if (string.IsNullOrEmpty(configType) || configType == "default")
            {
                AssetDatabase.Refresh();
                Debug.Log("[BuildScript] No CONFIG_TYPE set; SettingsManager will use hardcoded defaults on first launch");
                return;
            }

            string sourcePath = configType switch
            {
                "air-gapped" => "Assets/BuildConfigs/airgapped-settings.json",
                _ => throw new BuildFailedException($"Unknown CONFIG_TYPE '{configType}' (expected 'default' or 'air-gapped')")
            };

            Directory.CreateDirectory(targetDirectory);
            File.Copy(sourcePath, targetPath);
            AssetDatabase.Refresh();
            Debug.Log($"[BuildScript] Applied CONFIG_TYPE '{configType}' from {sourcePath}");
        }
    }
}
