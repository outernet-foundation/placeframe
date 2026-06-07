using System.Globalization;

namespace Placeframe.Client
{
    public static class ByteFormatting
    {
        public static string FormatBytes(long bytes)
        {
            if (bytes < 1024) return $"{bytes} B";
            double value = bytes;
            string[] units = { "KB", "MB", "GB", "TB" };
            int unit = 0;
            value /= 1024;
            while (value >= 1024 && unit < units.Length - 1)
            {
                value /= 1024;
                unit++;
            }
            return string.Format(CultureInfo.InvariantCulture, "{0:0.0} {1}", value, units[unit]);
        }

        public static string FormatBytesPerSecond(double bytesPerSecond) =>
            FormatBytes((long)bytesPerSecond) + "/s";
    }
}
