using Unity.Mathematics;

namespace Plerion.Core
{
    public static class Double4x4
    {
        public static double4x4 FromTranslationRotationScale(double3 translation, double3x3 rotation, double3 scale)
        {
            double3x3 scaleMatrix = new double3x3(
                new double3(scale.x, 0.0, 0.0),
                new double3(0.0, scale.y, 0.0),
                new double3(0.0, 0.0, scale.z)
            );
            double3x3 scaleAndRotate = math.mul(rotation, scaleMatrix);

            return new double4x4(
                new double4(scaleAndRotate.c0, 0.0),
                new double4(scaleAndRotate.c1, 0.0),
                new double4(scaleAndRotate.c2, 0.0),
                new double4(translation, 1.0)
            );
        }

        public static double4x4 FromTranslationRotation(double3 translation, quaternion rotation)
        {
            return FromTranslationRotationScale(translation, rotation.ToDouble3x3(), new double3(1.0, 1.0, 1.0));
        }

        public static double4x4 FromTranslationRotation(double3 translation, double3x3 rotation)
        {
            return FromTranslationRotationScale(translation, rotation, new double3(1.0, 1.0, 1.0));
        }
    }

    public static class ExtensionMethods
    {
        public static double3x3 ToDouble3x3(this quaternion quat) => new double3x3(new float3x3(quat));

        public static quaternion ToQuaternion(this double3x3 matrix) => new quaternion(new float3x3(matrix));

        public static double3 ToFloats(this double3 vector) =>
            new double3((float)vector.x, (float)vector.y, (float)vector.z);

        public static double3 Position(this double4x4 matrix) => matrix.c3.xyz;

        public static quaternion RotationQuaternion(this double4x4 matrix) => matrix.RotationMatrix().ToQuaternion();

        public static double3x3 RotationMatrix(this double4x4 matrix) =>
            new double3x3(matrix.c0.xyz, matrix.c1.xyz, matrix.c2.xyz);

        public static double3 ToDouble3(this PlerionApiClient.Model.Float3 vector3) =>
            new double3(vector3.X, vector3.Y, vector3.Z);

        public static quaternion ToMathematicsQuaternion(this PlerionApiClient.Model.Float4 quaternion) =>
            new quaternion((float)quaternion.X, (float)quaternion.Y, (float)quaternion.Z, (float)quaternion.W);
    }

    public static class LocationUtilities
    {
        private static readonly double3x3 basisUnity = double3x3.identity;
        private static readonly double3x3 basisOpenCV = new double3x3(1f, 0f, 0f, 0f, -1f, 0f, 0f, 0f, 1f);
        private static readonly double3x3 basisEcef = new double3x3(1f, 0f, 0f, 0f, -1f, 0f, 0f, 0f, 1f);

        private static readonly double3x3 basisChangeUnityFromOpenCV = math.mul(
            math.transpose(basisUnity),
            basisOpenCV
        );
        private static readonly double3x3 basisChangeOpenCVFromUnity = math.transpose(basisChangeUnityFromOpenCV);
        private static readonly double3x3 basisChangeUnityFromEcef = math.mul(math.transpose(basisUnity), basisEcef);
        private static readonly double3x3 basisChangeEcefFromUnity = math.transpose(basisChangeUnityFromEcef);

        public static (double3, double3x3) ChangeBasisUnityFromOpenCV(double3 translation, double3x3 rotation) =>
            (
                math.mul(basisChangeUnityFromOpenCV, translation),
                math.mul(basisChangeUnityFromOpenCV, math.mul(rotation, basisChangeOpenCVFromUnity))
            );

        public static (double3, double3x3) ChangeBasisOpenCVFromUnity(double3 translation, double3x3 rotation) =>
            (
                math.mul(basisChangeOpenCVFromUnity, translation),
                math.mul(basisChangeOpenCVFromUnity, math.mul(rotation, basisChangeUnityFromOpenCV))
            );

        public static (double3, double3x3) ChangeBasisUnityFromEcef(double3 translation, double3x3 rotation) =>
            (
                math.mul(basisChangeUnityFromEcef, translation),
                math.mul(basisChangeUnityFromEcef, math.mul(rotation, basisChangeEcefFromUnity))
            );

        public static (double3, double3x3) ChangeBasisEcefFromUnity(double3 translation, double3x3 rotation) =>
            (
                math.mul(basisChangeEcefFromUnity, translation),
                math.mul(basisChangeEcefFromUnity, math.mul(rotation, basisChangeUnityFromEcef))
            );

        public static double4x4 ComputeUnityFromEcefTransform(
            double3 translationCameraFromMap,
            double3x3 rotationCameraFromMap,
            double3 translationEcefFromMap,
            double3x3 rotationEcefFromMap,
            float3 translationUnityWorldFromCamera,
            double3x3 rotationUnityWorldFromCamera
        )
        {
            // (translationCameraFromMap, rotationCameraFromMap) = ChangeBasisUnityFromOpenCV(
            //     translationCameraFromMap,
            //     rotationCameraFromMap
            // );
            (translationEcefFromMap, rotationEcefFromMap) = ChangeBasisUnityFromEcef(
                translationEcefFromMap,
                rotationEcefFromMap
            );

            // Constrain both camera rotations to be gravity-aligned
            // rotationCameraFromMap = rotationCameraFromMap.RemovePitchAndRoll();
            // rotationUnityWorldFromCamera = rotationUnityWorldFromCamera.RemovePitchAndRoll();

            var rotationUnityFromMap = math.mul(rotationUnityWorldFromCamera, rotationCameraFromMap);
            var translationUnityFromMap =
                math.mul(rotationUnityWorldFromCamera, translationCameraFromMap) + translationUnityWorldFromCamera;
            var transformUnityFromMap = Double4x4.FromTranslationRotation(
                translationUnityFromMap,
                rotationUnityFromMap
            );
            var transformEcefFromMap = Double4x4.FromTranslationRotation(translationEcefFromMap, rotationEcefFromMap);
            var transformMapFromEcef = math.inverse(transformEcefFromMap);

            return math.mul(transformUnityFromMap, transformMapFromEcef);
        }

        // public static double3x3 RemovePitchAndRoll(this double3x3 rotation)
        // {
        //     float3 up = new float3(0f, 1f, 0f);
        //     float3 right = math.mul(rotation.ToQuaternion(), new float3(1f, 0f, 0f));
        //     float3 forward = math.normalize(math.cross(right, up));
        //     return quaternion.LookRotationSafe(forward, up).ToDouble3x3();
        // }

        public static (double3 position, quaternion rotation) UnityFromEcef(
            double4x4 unityFromEcefTransformUnityBasis,
            double3 ecefPosition,
            quaternion ecefRotation
        )
        {
            var (ecefPositionUnityBasis, ecefRotationUnityBasis) = ChangeBasisUnityFromEcef(
                ecefPosition,
                ecefRotation.ToDouble3x3()
            );
            var ecefTransformUnityBasis = Double4x4.FromTranslationRotation(
                ecefPositionUnityBasis,
                ecefRotationUnityBasis
            );
            var unityTransform = math.mul(unityFromEcefTransformUnityBasis, ecefTransformUnityBasis);
            return (unityTransform.Position(), unityTransform.RotationQuaternion());
        }

        public static (double3 position, quaternion rotation) EcefFromUnity(
            double4x4 ecefFromUnityTransformUnityBasis,
            double3 unityPosition,
            quaternion unityRotation
        )
        {
            var unityTransform = Double4x4.FromTranslationRotation(unityPosition, unityRotation);
            var ecefTransformUnityBasis = math.mul(ecefFromUnityTransformUnityBasis, unityTransform);
            var (ecefPosition, ecefRotation) = ChangeBasisEcefFromUnity(
                ecefTransformUnityBasis.Position(),
                ecefTransformUnityBasis.RotationMatrix()
            );
            return (ecefPosition, ecefRotation.ToQuaternion());
        }
    }
}
