using Unity.Mathematics;
using UnityEngine;

namespace Outernet.MapRegistrationTool
{
    public static class LocationUtilities
    {
        private static readonly float3x3 basisUnity = float3x3.identity;
        private static readonly float3x3 basisEcef = new float3x3(
            1f, 0f, 0f,
            0f, -1f, 0f,
            0f, 0f, 1f
        );

        private static readonly double3x3 basisChangeUnityFromEcef = math.mul(math.transpose(basisUnity), basisEcef);
        private static readonly double3x3 basisChangeEcefFromUnity = math.transpose(basisChangeUnityFromEcef);

        private static (double3x3, double3) ChangeBasisEcefToUnity(double3x3 rotation, double3 translation)
            => (math.mul(basisChangeUnityFromEcef, math.mul(rotation, basisChangeEcefFromUnity)), math.mul(basisChangeUnityFromEcef, translation));

        private static (double3x3, double3) ChangeBasisUnityToEcef(double3x3 rotation, double3 translation)
            => (math.mul(basisChangeEcefFromUnity, math.mul(rotation, basisChangeUnityFromEcef)), math.mul(basisChangeEcefFromUnity, translation));

        public static (Vector3 position, Quaternion rotation) EcefToUnityWorld(double3 ecefPosition, quaternion ecefRotation)
                    => EcefToUnityWorld(App.state.ecefToUnityWorldMatrix.value, ecefPosition, ecefRotation);

        public static (Vector3 position, Quaternion rotation) EcefToUnityWorld(double4x4 ecefToUnityTransform, double3 ecefPosition, quaternion ecefRotation)
        {
            var (rot, pos) = ChangeBasisEcefToUnity(new float3x3(ecefRotation), ecefPosition);
            var ecefTransform = Double4x4.FromTranslationRotation(pos, new quaternion(new float3x3(rot)));
            var unityTransform = math.mul(ecefToUnityTransform, ecefTransform);
            return (unityTransform.Position().ToFloats(), unityTransform.Rotation());
        }

        public static (double3 position, quaternion rotation) UnityWorldToEcef(Vector3 position, Quaternion rotation)
            => UnityWorldToEcef(App.state.unityWorldToEcefMatrix.value, position, rotation);

        public static (double3 position, quaternion rotation) UnityWorldToEcef(double4x4 unityToEcefTransform, Vector3 position, Quaternion rotation)
        {
            var unityTransform = Double4x4.FromTranslationRotation(position, rotation);
            var ecefTransform = math.mul(unityToEcefTransform, unityTransform);
            var (rot, pos) = ChangeBasisUnityToEcef(new float3x3(ecefTransform.Rotation()), ecefTransform.Position());
            return (pos, new quaternion(new float3x3(rot)));
        }
    }
}
