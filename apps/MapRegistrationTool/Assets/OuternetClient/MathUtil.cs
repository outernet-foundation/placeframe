using Unity.Mathematics;
using UnityEngine;

namespace Outernet.MapRegistrationTool
{
    // public static class ExtensionMethods
    // {
    //     public static Matrix4x4 SwitchHandedness(this ref Matrix4x4 b)
    //     {
    //         Matrix4x4 identity = Matrix4x4.identity;
    //         identity.m00 = -1f;
    //         b = identity * b * identity;
    //         return b;
    //     }

    //     public static double4x4 SwitchHandedness(this ref double4x4 b)
    //     {
    //         double4x4 identity = double4x4.identity;
    //         identity.c0.x = -1.0;
    //         b = math.mul(identity, math.mul(b, identity));
    //         return b;
    //     }

    //     public static Quaternion SwitchHandedness(this ref Quaternion b)
    //     {
    //         Matrix4x4 b2 = Matrix4x4.Rotate(b);
    //         b2.SwitchHandedness();
    //         b = b2.rotation;
    //         return b;
    //     }

    //     public static Vector3 SwitchHandedness(this ref Vector3 b)
    //     {
    //         Matrix4x4 b2 = Matrix4x4.TRS(b, Quaternion.identity, Vector3.one);
    //         b2.SwitchHandedness();
    //         b = b2.GetColumn(3);
    //         return b;
    //     }

    //     public static double3 SwitchHandedness(this ref double3 b)
    //     {
    //         double4x4 b2 = Double4x4.FromTranslationRotation(b, quaternion.identity);
    //         b2.SwitchHandedness();
    //         b = new double3(b2.c3.x, b2.c3.y, b2.c3.z);
    //         return b;
    //     }
    // }

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