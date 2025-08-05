using System.Diagnostics;
using System.IO;
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
        var workspaceFile = Path.Combine(projectDirectory, "../../plerion.code-workspace");

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

            string codeCommand = line < 0
                ? $"code -r \"{workspaceFile}\" -g \"{assetPath}\""
                : $"code -r \"{workspaceFile}\" -g \"{assetPath}:{line}\"";

            Process.Start(new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = $"/c {codeCommand}",
                CreateNoWindow = true,
                UseShellExecute = false
            });

            return true;
        }

        return false;
    }
}
