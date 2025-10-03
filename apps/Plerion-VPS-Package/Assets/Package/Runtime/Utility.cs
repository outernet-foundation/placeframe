using Unity.Mathematics;
using UnityEngine;

using System;

namespace Plerion
{
    public static class Utility
    {
        const double WGS84_A = 6378137.0; // Semi-major axis
        const double WGS84_E_SQUARED = 0.00669437999014; // Eccentricity squared
        private static readonly double3 WGS84_One_Over_Radii_Squared = new double3(
            1.0 / (6378137.0 * 6378137.0),
            1.0 / (6378137.0 * 6378137.0),
            1.0 / (6356752.3142451793 * 6356752.3142451793)
        );

        public static double4x4 LlhToEcefTransformationMatrix(double latitude, double longitude, double height)
            => EcefPositionToTransformationMatrix(LlhToEcefPosition(latitude, longitude, height));

        public static double4x4 EcefPositionToTransformationMatrix(double3 ecefPosition)
            => Double4x4.FromTranslationRotation(ecefPosition, EcefPositionToEunRotation(ecefPosition));

        public static double3 LlhToEcefPosition(double latitude, double longitude, double height)
        {
            latitude *= Mathf.Deg2Rad;
            longitude *= Mathf.Deg2Rad;

            double N = WGS84_A / Math.Sqrt(1 - WGS84_E_SQUARED * Math.Sin(latitude) * Math.Sin(latitude));

            double x = (N + height) * Math.Cos(latitude) * Math.Cos(longitude);
            double y = (N + height) * Math.Cos(latitude) * Math.Sin(longitude);
            double z = (N * (1 - WGS84_E_SQUARED) + height) * Math.Sin(latitude);

            return new double3(x, y, z);
        }

        // Adapted from eastNorthUpToFixedFrame in this file https://github.com/CesiumGS/cesium-native/blob/main/CesiumGeospatial/src/GlobeTransforms.cpp
        // and Ellipsoid at https://github.com/CesiumGS/cesium-native/blob/main/CesiumGeospatial/src/Ellipsoid.cpp
        public static Quaternion EcefPositionToEunRotation(double3 ecefPosition)
        {
            var up = math.normalize(ecefPosition * WGS84_One_Over_Radii_Squared);
            var east = math.normalize(new double3(-ecefPosition.y, ecefPosition.x, 0));
            var north = math.cross(up, east);

            // Negatives here are to account for handedness difference
            return Quaternion.LookRotation(-north.ToFloats(), -up.ToFloats());
        }

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

    public static class ExtensionMethods
    {
        public static Matrix4x4 SwitchHandedness(this ref Matrix4x4 b)
        {
            Matrix4x4 identity = Matrix4x4.identity;
            identity.m00 = -1f;
            b = identity * b * identity;
            return b;
        }

        public static double4x4 SwitchHandedness(this ref double4x4 b)
        {
            double4x4 identity = double4x4.identity;
            identity.c0.x = -1.0;
            b = math.mul(identity, math.mul(b, identity));
            return b;
        }

        public static Quaternion SwitchHandedness(this ref Quaternion b)
        {
            Matrix4x4 b2 = Matrix4x4.Rotate(b);
            b2.SwitchHandedness();
            b = b2.rotation;
            return b;
        }

        public static Vector3 SwitchHandedness(this ref Vector3 b)
        {
            Matrix4x4 b2 = Matrix4x4.TRS(b, Quaternion.identity, Vector3.one);
            b2.SwitchHandedness();
            b = b2.GetColumn(3);
            return b;
        }
    }

    public static class Double4x4
    {
        public static Vector3 ToFloats(this double3 vector) => new Vector3((float)vector.x, (float)vector.y, (float)vector.z);
        public static double3 ToDoubles(this Vector3 vector) => new double3(vector.x, vector.y, vector.z);

        public static double4x4 FromTranslationRotation(Vector3 translation, Quaternion rotation)
        {
            return FromTranslationRotation(
                new double3(translation.x, translation.y, translation.z),
                new quaternion(rotation.x, rotation.y, rotation.z, rotation.w)
            );
        }

        public static double4x4 FromTranslationRotation(double3 translation, quaternion rotation)
        {
            return FromTranslationRotationScale(translation, rotation, new double3(1.0, 1.0, 1.0));
        }

        public static double4x4 FromTranslationRotationScale(double3 translation, quaternion rotation, double3 scale)
        {
            double3x3 scaleMatrix = new double3x3(
                new double3(scale.x, 0.0, 0.0),
                new double3(0.0, scale.y, 0.0),
                new double3(0.0, 0.0, scale.z));
            double3x3 rotationMatrix = new float3x3(rotation);
            double3x3 scaleAndRotate = math.mul(rotationMatrix, scaleMatrix);

            return new double4x4(
                new double4(scaleAndRotate.c0, 0.0),
                new double4(scaleAndRotate.c1, 0.0),
                new double4(scaleAndRotate.c2, 0.0),
                new double4(translation, 1.0));
        }

        public static double3 Position(this double4x4 matrix) => matrix.c3.xyz;
        public static Quaternion Rotation(this double4x4 matrix)
        {

            MatrixToRotationAndScale(
                new double3x3(matrix.c0.xyz, matrix.c1.xyz, matrix.c2.xyz),
                out Quaternion rotation,
                out double3 scale);

            return rotation;
        }

        static void MatrixToRotationAndScale(double3x3 matrix, out Quaternion rotation, out double3 scale)
        {
            double lengthColumn0 = math.length(matrix.c0);
            double lengthColumn1 = math.length(matrix.c1);
            double lengthColumn2 = math.length(matrix.c2);

            float3x3 rotationMatrix = new float3x3(
                (float3)(matrix.c0 / lengthColumn0),
                (float3)(matrix.c1 / lengthColumn1),
                (float3)(matrix.c2 / lengthColumn2));

            scale = new double3(lengthColumn0, lengthColumn1, lengthColumn2);

            double3 cross = math.cross(matrix.c0, matrix.c1);
            if (math.dot(cross, matrix.c2) < 0.0)
            {
                rotationMatrix *= -1.0f;
                scale *= -1.0f;
            }

            rotation = math.quaternion(rotationMatrix);
        }
    }
}