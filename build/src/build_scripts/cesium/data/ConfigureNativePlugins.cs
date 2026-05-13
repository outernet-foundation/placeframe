using UnityEditor;
using UnityEngine;

public static class ConfigureNativePlugins
{
    struct PluginConfig
    {
        public string path;
        public bool isEditor;
        public BuildTarget platform;
        public string cpu;
        public string editorOS;
    }

    public static void Configure()
    {
        var plugins = new PluginConfig[]
        {
            // Linux Editor
            new PluginConfig {
                path = "Packages/com.cesium.unity/Editor/libCesiumForUnityNative-Editor.so",
                isEditor = true, platform = BuildTarget.NoTarget, cpu = "x86_64", editorOS = "Linux"
            },
            new PluginConfig {
                path = "Packages/com.cesium.unity/Editor/libCesiumForUnityNative-Runtime.so",
                isEditor = true, platform = BuildTarget.NoTarget, cpu = "x86_64", editorOS = "Linux"
            },
            // Windows Editor
            new PluginConfig {
                path = "Packages/com.cesium.unity/Editor/CesiumForUnityNative-Editor.dll",
                isEditor = true, platform = BuildTarget.NoTarget, cpu = "x86_64", editorOS = "Windows"
            },
            new PluginConfig {
                path = "Packages/com.cesium.unity/Editor/CesiumForUnityNative-Runtime.dll",
                isEditor = true, platform = BuildTarget.NoTarget, cpu = "x86_64", editorOS = "Windows"
            },
            // Linux Standalone
            new PluginConfig {
                path = "Packages/com.cesium.unity/Plugins/Standalone/libCesiumForUnityNative-Runtime.so",
                isEditor = false, platform = BuildTarget.StandaloneLinux64, cpu = null, editorOS = null
            },
            // Windows Standalone
            new PluginConfig {
                path = "Packages/com.cesium.unity/Plugins/Standalone/CesiumForUnityNative-Runtime.dll",
                isEditor = false, platform = BuildTarget.StandaloneWindows64, cpu = null, editorOS = null
            },
            // Android
            new PluginConfig {
                path = "Packages/com.cesium.unity/Plugins/Android/arm64/libCesiumForUnityNative-Runtime.so",
                isEditor = false, platform = BuildTarget.Android, cpu = "ARM64", editorOS = null
            },
            new PluginConfig {
                path = "Packages/com.cesium.unity/Plugins/Android/x86_64/libCesiumForUnityNative-Runtime.so",
                isEditor = false, platform = BuildTarget.Android, cpu = "X86_64", editorOS = null
            },
        };

        foreach (var plugin in plugins)
        {
            Debug.Log($"ConfigureNativePlugins: importing {plugin.path}");
            AssetDatabase.ImportAsset(plugin.path, ImportAssetOptions.ForceUpdate);

            var importer = AssetImporter.GetAtPath(plugin.path) as PluginImporter;
            if (importer == null)
            {
                Debug.LogError($"ConfigureNativePlugins: failed to get PluginImporter for {plugin.path}");
                EditorApplication.Exit(1);
                return;
            }

            importer.SetCompatibleWithAnyPlatform(false);

            if (plugin.isEditor)
            {
                importer.SetCompatibleWithEditor(true);
                importer.SetEditorData("CPU", plugin.cpu);
                importer.SetEditorData("OS", plugin.editorOS);
            }
            else
            {
                importer.SetCompatibleWithEditor(false);
                importer.SetCompatibleWithPlatform(plugin.platform, true);
                if (plugin.cpu != null)
                    importer.SetPlatformData(plugin.platform, "CPU", plugin.cpu);
            }

            importer.SaveAndReimport();
            Debug.Log($"ConfigureNativePlugins: configured {plugin.path}");
        }

        Debug.Log("ConfigureNativePlugins: all plugins configured successfully");
    }
}
