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
        public static quaternion ToMathematicsQuaternion(this PlerionApiClient.Model.Quaternion quaternion)
            => new quaternion((float)quaternion.X, (float)quaternion.Y, (float)quaternion.Z, (float)quaternion.W);

        public static float3 ToFloat3(this Vector3 vector3)
            => new float3(vector3.x, vector3.y, vector3.z);

        public static double3 ToDouble3(this PlerionApiClient.Model.Vector3 vector3)
            => new double3(vector3.X, vector3.Y, vector3.Z);

        public static Vector3 ToVector3(this PlerionApiClient.Model.Vector3 vector3)
            => new Vector3((float)vector3.X, (float)vector3.Y, (float)vector3.Z);

        public static Vector3 ToVector3(this float3 floats)
            => new Vector3(floats.x, floats.y, floats.z);

        public static Color ToUnityColor(this PlerionApiClient.Model.Color color)
            => new Color(color.R / 255f, color.G / 255f, color.B / 255f);
    }
}