using UnityEngine;
using UnityEditor;
using System;
using System.Collections.Generic;
using System.Linq;
using Cysharp.Threading.Tasks;

namespace Plerion.MakeItSing
{
    public class AssetBundleManagerWindow : EditorWindow
    {
        private bool _overrideVersion;
        private string _version;
        private int _platformMask;
        private bool _allowOverwriteOnUpload;
        private Vector2 _scrollPosition;
        private Dictionary<Platform, Action<string, string[], BuildAssetBundleOptions>> _buildMethods = new()
        {
            {Platform.Windows, BuildWindowsAssetBundles},
            {Platform.OSX, BuildOSXAssetBundles},
            {Platform.Linux, BuildLinuxAssetBundles},
            {Platform.MagicLeap, BuildMagicLeapAssetBundles},
            {Platform.AndroidMobile, BuildAndroidMobileAssetBundles}
        };

        private HashSet<string> _excludedAssetBundles = new HashSet<string>() { "ardebugmenu" };

        [MenuItem("Window/Asset Bundle Manager")]
        public static void ShowWindow()
        {
            GetWindow<AssetBundleManagerWindow>("Asset Bundle Manager");
        }

        public void OnGUI()
        {
            EditorGUILayout.LabelField("Supabase API Key", UnityEnv.GetOrCreateInstance().supabaseApiKey);

            if (_overrideVersion)
            {
                _version = EditorGUILayout.TextField("Version", _version);
            }
            else
            {
                EditorGUILayout.LabelField("Version", $"{Application.version} (from player settings)");
            }

            bool wasOverriding = _overrideVersion;
            _overrideVersion = EditorGUILayout.Toggle("Override Version", _overrideVersion);
            if (_overrideVersion && !wasOverriding && _version == null)
                _version = Application.version;

            _platformMask = EditorGUILayout.MaskField("Platforms", _platformMask, PlatformConfig.AllConfigs().Select(x => x.displayName).ToArray());
            _allowOverwriteOnUpload = EditorGUILayout.Toggle("Allow Overwrite On Upload", _allowOverwriteOnUpload);

            EditorGUILayout.LabelField("Asset Bundles");

            _scrollPosition = GUILayout.BeginScrollView(_scrollPosition, GUILayout.ExpandHeight(false));
            EditorGUI.indentLevel++;

            foreach (var assetBundle in AssetDatabase.GetAllAssetBundleNames())
            {
                bool included = EditorGUILayout.ToggleLeft(assetBundle, !_excludedAssetBundles.Contains(assetBundle));

                if (!included)
                {
                    _excludedAssetBundles.Add(assetBundle);
                }
                else
                {
                    _excludedAssetBundles.Remove(assetBundle);
                }
            }

            EditorGUI.indentLevel--;
            GUILayout.EndScrollView();

            EditorGUILayout.BeginHorizontal();

            if (GUILayout.Button("Build", GUILayout.Height(EditorGUIUtility.singleLineHeight * 1.5f)))
            {
                BuildAssetBundlesForTargets(
                    EnumerateActiveTargets(_platformMask).ToArray(),
                    AssetDatabase.GetAllAssetBundleNames().Except(_excludedAssetBundles).ToArray()
                );
            }

            if (GUILayout.Button("Upload", GUILayout.Height(EditorGUIUtility.singleLineHeight * 1.5f)))
            {
                UploadAssetBundlesForTargets(
                    EnumerateActiveTargets(_platformMask).ToArray(),
                    AssetDatabase.GetAllAssetBundleNames().Except(_excludedAssetBundles).ToArray(),
                    _allowOverwriteOnUpload
                );
            }

            if (GUILayout.Button("Build & Upload", GUILayout.Height(EditorGUIUtility.singleLineHeight * 1.5f)))
            {
                var assetBundlesToBuild = AssetDatabase.GetAllAssetBundleNames().Except(_excludedAssetBundles).ToArray();

                var successfulBuilds = BuildAssetBundlesForTargets(
                    EnumerateActiveTargets(_platformMask).ToArray(),
                    assetBundlesToBuild
                );

                UploadAssetBundlesForTargets(
                    successfulBuilds,
                    assetBundlesToBuild,
                    _allowOverwriteOnUpload
                );
            }
            EditorGUILayout.EndHorizontal();
        }

        private IEnumerable<Platform> EnumerateActiveTargets(int activeTargetMask)
        {
            var values = Enum.GetValues(typeof(Platform));
            for (int i = 0; i < values.Length; i++)
            {
                if ((activeTargetMask & (int)Mathf.Pow(2, i)) == 0)
                    continue;

                yield return (Platform)values.GetValue(i);
            }
        }

        private static void BuildWindowsAssetBundles(string ouputPath, string[] bundlesToBuild, BuildAssetBundleOptions options)
            => BuildAssetBundles(ouputPath, bundlesToBuild, options, BuildTarget.StandaloneWindows64);

        private static void BuildOSXAssetBundles(string ouputPath, string[] bundlesToBuild, BuildAssetBundleOptions options)
            => BuildAssetBundles(ouputPath, bundlesToBuild, options, BuildTarget.StandaloneOSX);

        private static void BuildLinuxAssetBundles(string ouputPath, string[] bundlesToBuild, BuildAssetBundleOptions options)
            => BuildAssetBundles(ouputPath, bundlesToBuild, options, BuildTarget.StandaloneLinux64);

        private static void BuildMagicLeapAssetBundles(string ouputPath, string[] bundlesToBuild, BuildAssetBundleOptions options)
        {
            Build.ConfigureForMagicLeap();
            BuildAssetBundles(ouputPath, bundlesToBuild, options, BuildTarget.Android);
        }

        private static void BuildAndroidMobileAssetBundles(string ouputPath, string[] bundlesToBuild, BuildAssetBundleOptions options)
        {
            Build.ConfigureForAndroidMobile();
            BuildAssetBundles(ouputPath, bundlesToBuild, options, BuildTarget.Android);
        }

        private static void BuildAssetBundles(string outputPath, string[] bundlesToBuild, BuildAssetBundleOptions options, BuildTarget target)
        {
            if (!System.IO.Directory.Exists($"{Application.dataPath}/{outputPath}"))
                System.IO.Directory.CreateDirectory($"{Application.dataPath}/{outputPath}");

            var assetBundleBuilds = bundlesToBuild.Select(x => new AssetBundleBuild()
            {
                assetBundleName = x,
                assetNames = AssetDatabase.GetAssetPathsFromAssetBundle(x),
            }).ToArray();

            var manifest = BuildPipeline.BuildAssetBundles($"{Application.dataPath}/{outputPath}", assetBundleBuilds, options, target);

            if (manifest == null)
                throw new Exception("Build Asset Bundles failed. Check the console for compiler errors.");
        }

        private async void UploadAssetBundlesForTargets(Platform[] targets, string[] assetBundlesToUpload, bool allowOverwrite)
        {
            SupabaseAPI.ProjectId = UnityEnv.GetOrCreateInstance().supabaseProjectId;
            SupabaseAPI.ApiKey = UnityEnv.GetOrCreateInstance().supabaseApiKey;

            foreach (var target in targets)
            {
                var config = PlatformConfig.GetConfig(target);

                foreach (var assetBundle in assetBundlesToUpload)
                {
                    Debug.Log($"Uploading {assetBundle} for platform {config.displayName}");
                    var file = System.IO.File.ReadAllBytes($"{Application.dataPath}/{config.assetBundleOutputPath}/{assetBundle}");
                    var resp = await SupabaseAPI.UploadDemoSceneAssetBundle(assetBundle, _overrideVersion ? _version : Application.version, config.supabaseBucket, file, allowOverwrite);
                    Debug.Log($"Upload response: {resp.result} Code: {resp.responseCode}");
                }
            }
        }

        private Platform[] BuildAssetBundlesForTargets(Platform[] targets, string[] assetBundlesToBuild)
        {
            var successfulBuilds = new List<Platform>();

            foreach (var target in targets)
            {
                var config = PlatformConfig.GetConfig(target);

                try
                {
                    _buildMethods[target](config.assetBundleOutputPath, assetBundlesToBuild, BuildAssetBundleOptions.None);
                }
                catch (Exception exc)
                {
                    Debug.LogException(exc);
                    Debug.LogError($"Build for {config.displayName} failed with above errors.");
                    continue;
                }

                Debug.Log($"Build for {config.displayName} succeeded.");
                successfulBuilds.Add(target);
            }

            AssetDatabase.Refresh();

            return successfulBuilds.ToArray();
        }
    }
}