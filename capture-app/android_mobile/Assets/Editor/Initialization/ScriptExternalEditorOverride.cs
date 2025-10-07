using System.Diagnostics;
using System.IO;
using R3;
using UnityEditor;
using UnityEditor.Callbacks;
using UnityEngine;

public class SolutionGenerator : AssetPostprocessor
{
    // Called by Unity when a script is double clicked in the editor
    [OnOpenAsset(0)]
    private static bool OnOpenAsset(int instanceID, int line)
    {
        var projectDirectory = Application.dataPath.Substring(0, Application.dataPath.Length - "Assets".Length);

        string assetPath = AssetDatabase.GetAssetPath(instanceID);

        if (assetPath.EndsWith(".cs"))
        {
            if (assetPath.StartsWith("Packages/"))
            {
                var packageInfo = UnityEditor.PackageManager.PackageInfo.FindForAssetPath(assetPath);
                assetPath = Path.Combine(packageInfo.resolvedPath, Path.GetRelativePath($"Packages/{packageInfo.name}", assetPath));
            }
            else
            {
                assetPath = Path.Combine(projectDirectory, assetPath);
            }

            var workspaceFolder = projectDirectory;
            while (!Directory.Exists(Path.Combine(workspaceFolder, ".git")))
            {
                var parent = Directory.GetParent(workspaceFolder);
                if (parent == null)
                {
                    break;
                }

                workspaceFolder = parent.FullName;
            }
            var folderUri = new System.Uri(workspaceFolder).AbsoluteUri;

            string arguments = line < 0
                ? $"-g \"{assetPath}\" --folder-uri \"{folderUri}\""
                : $"-g \"{assetPath}:{line}\" --folder-uri \"{folderUri}\"";


            Process.Start(new ProcessStartInfo
            {
#if UNITY_EDITOR_WIN
                FileName = "cmd.exe",
                Arguments = $"/c code {arguments}",
#elif UNITY_EDITOR_LINUX
                FileName = "code",
                Arguments = arguments,
#endif
                CreateNoWindow = true,
                UseShellExecute = false
            });

            return true;
        }

        return false;
    }
}
