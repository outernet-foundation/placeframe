using System;
using System.Collections.Generic;

namespace Plerion.MakeItSing
{
    public class PlatformConfig
    {
        private static Dictionary<Platform, PlatformConfig> _configs = new Dictionary<Platform, PlatformConfig>()
        {
            { Platform.Windows, new PlatformConfig(Platform.Windows, "Windows", "AssetBundles/Windows", "Windows") },
            { Platform.OSX, new PlatformConfig(Platform.OSX, "OSX", "AssetBundles/OSX", "OSX") },
            { Platform.Linux, new PlatformConfig(Platform.Linux, "Linux", "AssetBundles/Linux", "Linux") },
            { Platform.MagicLeap, new PlatformConfig(Platform.MagicLeap, "Magic Leap", "AssetBundles/MagicLeap", "MagicLeap") },
            { Platform.AndroidMobile, new PlatformConfig(Platform.AndroidMobile, "Android Mobile", "AssetBundles/AndroidMobile", "AndroidMobile") },
        };

        private static Array _enumValues = Enum.GetValues(typeof(Platform));
        public static int platformCount => _enumValues.Length;
        public static PlatformConfig GetConfig(int index) => _configs[(Platform)index];
        public static PlatformConfig GetConfig(Platform platform) => _configs[platform];

        public static IEnumerable<PlatformConfig> AllConfigs()
        {
            for (int i = 0; i < platformCount; i++)
                yield return GetConfig(i);
        }

        public Platform platform { get; }
        public string displayName { get; }
        public string assetBundleOutputPath { get; }
        public string supabaseBucket { get; }

        private PlatformConfig(Platform platform, string displayName, string assetBundleOutputPath, string supabaseBucket)
        {
            this.platform = platform;
            this.displayName = displayName;
            this.assetBundleOutputPath = assetBundleOutputPath;
            this.supabaseBucket = supabaseBucket;
        }
    }
}