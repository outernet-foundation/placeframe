using Unity.Mathematics;
using UnityEngine;

namespace Placeframe.MapRegistrationTool
{
    public static class LocationUtilities
    {
        public static (Vector3 position, Quaternion rotation) UnityFromEcef(double3 ecefPosition, quaternion ecefRotation)
        {
            var (position, rotation) = Placeframe.Core.LocationUtilities.UnityFromEcef(App.state.ecefToUnityWorldMatrix.value, ecefPosition, ecefRotation);
            return (new Vector3((float)position.x, (float)position.y, (float)position.z), new Quaternion(rotation.value.x, rotation.value.y, rotation.value.z, rotation.value.w));
        }

        public static (double3 position, quaternion rotation) EcefFromUnity(float3 unityPosition, quaternion unityRotation)
            => Placeframe.Core.LocationUtilities.EcefFromUnity(App.state.unityWorldToEcefMatrix.value, unityPosition, unityRotation);
    }
}
