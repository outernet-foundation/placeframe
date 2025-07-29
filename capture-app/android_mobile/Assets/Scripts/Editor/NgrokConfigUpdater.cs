using UnityEngine;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using System.IO;

[InitializeOnLoad]
static class NgrokConfigUpdater
{
    static NgrokConfigUpdater()
    {
        // 1) Update on compile / editor load
        UpdateConfig();

        // 2) Update whenever you hit Play
        EditorApplication.playModeStateChanged += state =>
        {
            if (state == PlayModeStateChange.EnteredPlayMode)
                UpdateConfig();
        };
    }

    // 3) Also expose a manual menu command
    [MenuItem("Tools/Ngrok/Refresh Config")]
    static void RefreshMenu() => UpdateConfig();

    public static void UpdateConfig()
    {
        // Locate your ngrok.yml
        var home = System.Environment.GetFolderPath(System.Environment.SpecialFolder.UserProfile);
        var yml = Path.Combine(home, "AppData", "Local", "ngrok", "ngrok.yml");
        if (!File.Exists(yml))
        {
            Debug.LogWarning($"[NgrokConfig] could not find {yml}");
            return;
        }

        // Naïve YAML‐style parse for tunnels.backend.hostname
        string hostname = null;
        bool inTunnels = false, inBackend = false;
        foreach (var raw in File.ReadAllLines(yml))
        {
            var line = raw.Trim();
            if (!inTunnels && line.StartsWith("tunnels:")) { inTunnels = true; continue; }
            if (inTunnels && !inBackend && line.StartsWith("backend:")) { inBackend = true; continue; }
            if (inBackend && line.StartsWith("hostname:"))
            {
                var parts = line.Split(':', 2);
                if (parts.Length == 2) hostname = parts[1].Trim();
                break;
            }
        }

        if (string.IsNullOrEmpty(hostname))
        {
            Debug.LogWarning("[NgrokConfig] could not parse hostname from ngrok.yml");
            return;
        }

        // get dir of unity project
        var projectDir = Path.GetDirectoryName(Application.dataPath);
        // write to Assets/Resources/ngrok
        var ngrokPath = Path.Combine(projectDir, "Assets", "Resources", "ngrok.txt");
        if (!Directory.Exists(Path.GetDirectoryName(ngrokPath)))
            Directory.CreateDirectory(Path.GetDirectoryName(ngrokPath));
        File.WriteAllText(ngrokPath, $"https://{hostname}");
    }
}

// Hook into build as well
class NgrokBuildProcessor : IPreprocessBuildWithReport
{
    public int callbackOrder => 0;
    public void OnPreprocessBuild(BuildReport report)
        => NgrokConfigUpdater.UpdateConfig();
}
