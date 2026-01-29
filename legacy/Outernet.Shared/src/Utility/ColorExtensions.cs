using UnityEngine;

namespace Outernet.Shared
{
    public static class ColorExtensions
    {
        static int Clamp(int value, int min, int max) => value < min ? min : value > max ? max : value;

        public static long ToLong(this Color color)
        {
            int a = Clamp((int)(color.a * 65535), 0, 65535);
            int r = Clamp((int)(color.r * 65535), 0, 65535);
            int g = Clamp((int)(color.g * 65535), 0, 65535);
            int b = Clamp((int)(color.b * 65535), 0, 65535);

            return ((long)a << 48) | ((long)r << 32) | ((long)g << 16) | (long)b;
        }

        public static Color ToColor(long colorLong)
        {
            float a = ((colorLong >> 48) & 0xFFFF) / 65535f;
            float r = ((colorLong >> 32) & 0xFFFF) / 65535f;
            float g = ((colorLong >> 16) & 0xFFFF) / 65535f;
            float b = (colorLong & 0xFFFF) / 65535f;

            return new Color(r, g, b, a);
        }
    }
}