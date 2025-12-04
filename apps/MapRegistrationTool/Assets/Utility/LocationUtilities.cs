using Unity.Mathematics;
using UnityEngine;

namespace Outernet.MapRegistrationTool
{
    public static class LocationUtilities
    {
        public static (Vector3 position, Quaternion rotation) EcefToUnityWorld(double3 ecefPosition, quaternion ecefRotation)
        {
            var (position, rotation) = Plerion.Core.LocationUtilities.EcefToUnityWorld(App.state.ecefToUnityWorldMatrix.value, ecefPosition, ecefRotation);
            return (new Vector3((float)position.x, (float)position.y, (float)position.z), new Quaternion((float)rotation.value.x, (float)rotation.value.y, (float)rotation.value.z, (float)rotation.value.w));
        }

        public static (double3 position, quaternion rotation) UnityWorldToEcef(float3 position, quaternion rotation)
            => Plerion.Core.LocationUtilities.UnityWorldToEcef(App.state.unityWorldToEcefMatrix.value, position, rotation);
    }
}
