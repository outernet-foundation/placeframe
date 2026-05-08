using UnityEditor;
using System.IO;

namespace Plerion
{
    public class CreateAssetBundles
    {
        [MenuItem("Build/Asset Bundles/Windows")]
        static void BuildAssetBundlesForWindows()
        {
            string assetBundleDirectory = "Assets/AssetBundles/Windows";
            if (!Directory.Exists(assetBundleDirectory))
                Directory.CreateDirectory(assetBundleDirectory);

            BuildAssetBundles(assetBundleDirectory, BuildTarget.StandaloneWindows64);
        }

        [MenuItem("Build/Asset Bundles/Linux")]
        static void BuildAssetBundlesForLinux()
        {
            string assetBundleDirectory = "Assets/AssetBundles/Linux";
            if (!Directory.Exists(assetBundleDirectory))
                Directory.CreateDirectory(assetBundleDirectory);

            BuildAssetBundles(assetBundleDirectory, BuildTarget.StandaloneLinux64);
        }

        [MenuItem("Build/Asset Bundles/Magic Leap")]
        static void BuildAssetBundlesForMagicLeap()
        {
            string assetBundleDirectory = "Assets/AssetBundles/MagicLeap";
            if (!Directory.Exists(assetBundleDirectory))
                Directory.CreateDirectory(assetBundleDirectory);

            Build.ConfigureForMagicLeap();
            BuildAssetBundles(assetBundleDirectory, BuildTarget.Android);
        }

        [MenuItem("Build/Asset Bundles/Android Mobile")]
        static void BuildAssetBundlesForAndroidMobile()
        {
            string assetBundleDirectory = "Assets/AssetBundles/AndroidMobile";
            if (!Directory.Exists(assetBundleDirectory))
                Directory.CreateDirectory(assetBundleDirectory);

            Build.ConfigureForAndroidMobile();
            BuildAssetBundles(assetBundleDirectory, BuildTarget.Android);
        }

        private static void BuildAssetBundles(string outputPath, BuildTarget buildTarget)
        {
            if (!Directory.Exists(outputPath))
                Directory.CreateDirectory(outputPath);

            BuildPipeline.BuildAssetBundles(outputPath,
                BuildAssetBundleOptions.None,
                buildTarget); // Change target as needed
        }
    }
}