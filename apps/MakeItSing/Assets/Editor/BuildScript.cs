using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using Unity.Plastic.Newtonsoft.Json;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.XR.Management;
using UnityEditor.XR.Management.Metadata;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.XR.Hands.OpenXR;
using UnityEngine.XR.OpenXR;
using UnityEngine.XR.OpenXR.Features;
using UnityEngine.XR.OpenXR.Features.Interactions;
using MagicLeap.OpenXR.Features;
using MagicLeap.OpenXR.InteractionProfiles;
using MagicLeap.OpenXR.Features.LocalizationMaps;
using MagicLeap.OpenXR.Features.MarkerUnderstanding;
using MagicLeap.OpenXR.Features.Planes;
using MagicLeap.OpenXR.Features.UserCalibration;
using UnityEditor.Build;
using UnityEngine.XR.Management;

namespace Plerion
{
    public static class Build
    {
        public static void BuildForMagicLeap()
        {
            ConfigureForMagicLeap();
            BuildMain("MagicLeap");
        }

        public static void BuildForAndroidMobile()
        {
            ConfigureForAndroidMobile();
            BuildMain("AndroidMobile");
        }

        // [MenuItem("Build/MagicLeap", priority = 0)]
        // public static void StartBuildForMagicLeap()
        // {
        //     StartBuild("MagicLeap");
        // }

        // [MenuItem("Build/AndroidMobile", priority = 1)]
        // public static void StartBuildForAndroidMobile()
        // {
        //     StartBuild("AndroidMobile");
        // }

        [MenuItem("Build/Configure/MagicLeap", priority = 10)]
        public static void ConfigureForMagicLeap()
        {
            PlayerSettings.SetScriptingDefineSymbols(NamedBuildTarget.Android, "PLERION_MAGIC_LEAP;USE_INPUT_SYSTEM_POSE_CONTROL;USE_STICK_CONTROL_THUMBSTICKS;MAGIC_LEAP;USE_ML_OPENXR");
            var settings = XRGeneralSettingsPerBuildTarget.XRGeneralSettingsForBuildTarget(BuildTargetGroup.Android);
            XRPackageMetadataStore.RemoveLoader(settings.AssignedSettings, "UnityEngine.XR.ARCore.ARCoreLoader", BuildTargetGroup.Android);
            XRPackageMetadataStore.AssignLoader(settings.AssignedSettings, "UnityEngine.XR.OpenXR.OpenXRLoader", BuildTargetGroup.Android);

            var openXRSettings = OpenXRSettings.GetSettingsForBuildTargetGroup(BuildTargetGroup.Android);

            foreach (var feature in openXRSettings.GetFeatures<OpenXRFeature>())
            {
                feature.enabled = false;
            }

            openXRSettings.GetFeature<HandTracking>().enabled = true;
            openXRSettings.GetFeature<HandInteractionProfile>().enabled = true;
            openXRSettings.GetFeature<MagicLeapFeature>().enabled = true;
            openXRSettings.GetFeature<MagicLeapRenderingExtensionsFeature>().enabled = true;
            openXRSettings.GetFeature<MagicLeapControllerProfile>().enabled = true;
            openXRSettings.GetFeature<MagicLeapLocalizationMapFeature>().enabled = true;
            openXRSettings.GetFeature<MagicLeapMarkerUnderstandingFeature>().enabled = true;
            openXRSettings.GetFeature<MagicLeapPlanesFeature>().enabled = true;
            openXRSettings.GetFeature<MagicLeapReferenceSpacesFeature>().enabled = true;
            openXRSettings.GetFeature<MagicLeapUserCalibrationFeature>().enabled = true;

            PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.Vulkan });
            PlayerSettings.SetNormalMapEncoding(NamedBuildTarget.Android, NormalMapEncoding.DXT5nm);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.X86_64;
            EditorUserBuildSettings.androidBuildSubtarget = MobileTextureSubtarget.DXT;
            GraphicsSettings.defaultRenderPipeline = AssetDatabase.LoadAssetAtPath<RenderPipelineAsset>("Assets/Settings/MagicLeap_PipelineAsset.asset");
            QualitySettings.renderPipeline = AssetDatabase.LoadAssetAtPath<RenderPipelineAsset>("Assets/Settings/MagicLeap_PipelineAsset.asset");
        }

        [MenuItem("Build/Configure/AndroidMobile", priority = 11)]
        public static void ConfigureForAndroidMobile()
        {
            PlayerSettings.SetScriptingDefineSymbols(NamedBuildTarget.Android, "PLERION_ANDROID_MOBILE;USE_INPUT_SYSTEM_POSE_CONTROL");
            var settings = XRGeneralSettingsPerBuildTarget.XRGeneralSettingsForBuildTarget(BuildTargetGroup.Android);
            XRPackageMetadataStore.RemoveLoader(settings.AssignedSettings, "UnityEngine.XR.OpenXR.OpenXRLoader", BuildTargetGroup.Android);
            XRPackageMetadataStore.AssignLoader(settings.AssignedSettings, "UnityEngine.XR.ARCore.ARCoreLoader", BuildTargetGroup.Android);

            PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.OpenGLES3 });
            PlayerSettings.SetNormalMapEncoding(NamedBuildTarget.Android, NormalMapEncoding.DXT5nm);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            EditorUserBuildSettings.androidBuildSubtarget = MobileTextureSubtarget.ASTC;
            GraphicsSettings.defaultRenderPipeline = AssetDatabase.LoadAssetAtPath<RenderPipelineAsset>("Assets/Settings/AndroidMobile_PipelineAsset.asset");
            QualitySettings.renderPipeline = AssetDatabase.LoadAssetAtPath<RenderPipelineAsset>("Assets/Settings/AndroidMobile_PipelineAsset.asset");
        }

        private static void StartBuild(string platform)
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = $"/C ubt --platform {platform} --wait-for-process-id {Process.GetCurrentProcess().Id} --reopen-with-build-target {EditorUserBuildSettings.activeBuildTarget}",
                UseShellExecute = true,
                WindowStyle = ProcessWindowStyle.Normal // Ensure the window is brought to the front
            });

            EditorApplication.Exit(0);
        }

        // public class LogHandler : ILogHandler
        // {
        //     private ILogHandler defaultLogHandler = UnityEngine.Debug.unityLogger.logHandler;

        //     public void LogException(Exception exception, UnityEngine.Object context)
        //     {
        //         defaultLogHandler.LogException(exception, context);
        //     }

        //     public void LogFormat(LogType logType, UnityEngine.Object context, string format, params object[] args)
        //     {
        //         string logMessage = string.Format(format, args);

        //         // Suppress Cesium package warnings like
        //         // "Plugin 'Packages/com.cesium.unity/Plugins/iOS/lib/libabsl_log_internal_nullguard.a' doesn't have CPU architecture set, since it's a native plugin, valid architecture is required, skipping."
        //         if (logMessage.Contains("Plugin 'Packages/com.cesium.unity")) return;

        //         // Suppress Cesium package warnings like
        //         // ""Shader warning in 'Cesium/CesiumUnlitTilesetShader': implicit truncation of vector type at Files/Unity/Hub/Editor/2022.3.27f1/Editor/Data/CGIncludes/UnityShadowLibrary.cginc(63)"
        //         if (logMessage.Contains("Shader warning in 'Cesium")) return;

        //         defaultLogHandler.LogFormat(logType, context, format, args);
        //     }
        // }

        private static void BuildMain(string platform)
        {
            try
            {
                // Set the log handler to suppress specific messages
                // UnityEngine.Debug.unityLogger.logHandler = new LogHandler();

                string buildTarget = "Android";
                string outputPath = $"Build/{platform}/";
                if (buildTarget == "Android")
                {
                    outputPath += "OgmentUnity.apk";
                }

                // Perform the build
                BuildReport report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
                {
                    scenes = new string[] { "Assets/OuternetClient/Main.unity" },
                    locationPathName = outputPath,
                    target = (BuildTarget)Enum.Parse(typeof(BuildTarget), buildTarget),
                    targetGroup = (BuildTargetGroup)Enum.Parse(typeof(BuildTargetGroup), buildTarget),
                    options = BuildOptions.Development
                });

                // Write the build report to a file
                SerializableBuildReport serializableReport = new SerializableBuildReport();
                serializableReport.result = report.summary.result.ToString();
                (serializableReport.steps, serializableReport.messages) = BuildStepTree(new List<BuildStep>(report.steps), -1);
                File.WriteAllText($"Build/{platform}/BuildReport.json", JsonConvert.SerializeObject(serializableReport, Formatting.Indented));
            }
            catch (Exception e)
            {
                UnityEngine.Debug.LogError(e);
            }
        }

        [Serializable]
        public class SerializableBuildReport
        {
            public string result;
            public List<Step> steps;
            public List<Message> messages;
        }

        [Serializable]
        public class Step
        {
            public string name;
            public string duration;
            [JsonProperty(NullValueHandling = NullValueHandling.Ignore)] public List<Step> steps;

        }

        [Serializable]
        public class Message
        {
            public string content;
            public string type;
            public string step;
        }

        private static (List<Step>, List<Message>) BuildStepTree(List<BuildStep> reportBuildSteps, int depth)
        {
            List<Step> steps = new List<Step>();
            List<Message> messages = new List<Message>();

            while (reportBuildSteps.Count > 0)
            {
                if (reportBuildSteps[0].depth <= depth) break;

                BuildStep reportBuildStep = reportBuildSteps[0];
                reportBuildSteps.RemoveAt(0);

                messages.AddRange(reportBuildStep.messages
                    .Select(m => new Message
                    {
                        content = m.content,
                        type = m.type.ToString(),
                        step = reportBuildStep.name
                    }));

                var (subSteps, subMessages) = BuildStepTree(reportBuildSteps, reportBuildStep.depth);
                messages.AddRange(subMessages);

                steps.Add(new Step
                {
                    name = reportBuildStep.name,
                    duration = reportBuildStep.duration.TotalSeconds.ToString(),
                    steps = subSteps.Count > 0 ? subSteps : null
                });
            }

            return (steps, messages);
        }
    }
}