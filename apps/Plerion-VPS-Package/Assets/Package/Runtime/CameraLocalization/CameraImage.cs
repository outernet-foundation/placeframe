using System;
using UnityEngine;

namespace Plerion
{
    public struct CameraImage
    {
        public int imageWidth;
        public int imageHeight;
        public byte[] pixelBuffer;
        public Vector2 focalLength;
        public Vector2 principalPoint;
        public Quaternion cameraOrientation;
    }
}