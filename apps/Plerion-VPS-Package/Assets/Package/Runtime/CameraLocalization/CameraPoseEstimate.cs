

using System;
using Unity.Mathematics;
using UnityEngine;

namespace Plerion
{
    public struct CameraPoseEstimate
    {
        public Guid map;
        public double3 mapEcefPosition; // ECEF coordinates
        public quaternion mapEcefRotation; // ECEF coordinates
        public Vector3 originalCameraWorldPosition; // Unity coordinates
        public Quaternion originalCameraWorldRotation; // Unity coordinates
        public Vector3 estimatedCameraPosition; // Local to map
        public Quaternion estimatedCameraRotation; // Local to map
        public int confidence;
    }
}