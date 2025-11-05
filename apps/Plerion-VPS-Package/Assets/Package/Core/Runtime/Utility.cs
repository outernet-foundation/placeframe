using Unity.Mathematics;
using UnityEngine;

using System;
using System.Collections.Generic;

namespace Plerion.VPS
{
    public static class Utility
    {
        const double WGS84_A = 6378137.0; // Semi-major axis
        const double WGS84_E_SQUARED = 0.00669437999014; // Eccentricity squared

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
    }

    public static class ExtensionMethods
    {
        public static quaternion ToMathematicsQuaternion(this PlerionClient.Model.Quaternion quaternion)
            => new quaternion((float)quaternion.X, (float)quaternion.Y, (float)quaternion.Z, (float)quaternion.W);

        public static float3 ToFloat3(this Vector3 vector3)
            => new float3(vector3.x, vector3.y, vector3.z);

        public static float3 ToFloat3(this PlerionClient.Model.Vector3 vector3)
            => new float3((float)vector3.X, (float)vector3.Y, (float)vector3.Z);

        public static Color ToUnityColor(this PlerionClient.Model.Color color)
            => new Color(color.R / 255f, color.G / 255f, color.B / 255f);
    }

    public static class Double4x4
    {
        public static Vector3 ToFloats(this double3 vector) => new Vector3((float)vector.x, (float)vector.y, (float)vector.z);

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

        public static quaternion Rotation(this double4x4 matrix)
            => new quaternion(new float3x3(math.normalize(matrix.c0.xyz).ToFloats(), math.normalize(matrix.c1.xyz).ToFloats(), math.normalize(matrix.c2.xyz).ToFloats()));
    }
}