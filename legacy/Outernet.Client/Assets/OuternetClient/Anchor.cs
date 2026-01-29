// using Outernet.Client.Location;
// using Placeframe.Core;
// using Unity.Mathematics;
// using UnityEngine;

// namespace Outernet.Client
// {
//     public class Anchor : MonoBehaviour
//     {
//         public double3 EcefPosition { get; private set; }
//         public quaternion EcefRotation { get; private set; }

//         public void SetEcefTransform(double3 ecefPosition, quaternion ecefRotation)
//         {
//             EcefPosition = ecefPosition;
//             EcefRotation = ecefRotation;
//             SetLocalTransformFromEcefTransform();
//         }

//         public void SetLocalTransformFromEcefTransform()
//         {
//             var localTransform = ReferenceFrame.EcefToUnityWorld(EcefPosition, EcefRotation);
//             transform.position = localTransform.position;
//             transform.rotation = localTransform.rotation;
//         }

//         public void SetEcefTransformFromLocalTransform()
//         {
//             (EcefPosition, EcefRotation) = ReferenceFrame.UnityWorldToEcef(transform.position, transform.rotation);
//         }
//     }
// }
