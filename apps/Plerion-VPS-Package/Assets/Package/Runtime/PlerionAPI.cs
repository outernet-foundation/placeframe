using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using Unity.Mathematics;
using UnityEngine;

namespace Plerion
{
    public class LocalizationMapModel
    {
        public int Id;
        public Guid Uuid;
        public string Name;
        public bool Active;
        public int Lighting;
        public long Color;
        public double Position_X;
        public double Position_Y;
        public double Position_Z;
        public double Rotation_X;
        public double Rotation_Y;
        public double Rotation_Z;
        public double Rotation_W;
        public Vector3[] Points;

        public double3 EcefPosition => new double3(Position_X, Position_Y, Position_Z);
        public quaternion EcefRotation => new quaternion((float)Rotation_X, (float)Rotation_Y, (float)Rotation_Z, (float)Rotation_W);
    }

    [Serializable]
    public class LocalizeResponse
    {
        public Guid mapID;
        public double3 mapEcefPosition;
        public quaternion mapEcefRotation;
        public Vector3 estimatedCameraPosition;
        public Quaternion estimatedCameraRotation;
        public int confidence;
    }

    [Serializable]
    public class LocalizeRequest
    {
        public double latitude;
        public double longitude;
        public float elevation;
        public Guid[] maps;
        public int width;
        public int height;
        public Vector4 intrinsics;
        public Quaternion cameraRotation;
        public byte[] cameraImage;
    }

    static public class PlerionAPI
    {
        public static async UniTask UpdateMapsFromLocation(double latitude, double longitude, double height, double radius, Lighting lighting, bool additive = false)
        {
            throw new NotImplementedException();
        }

        public static async UniTask UpdateMapsFromList(Guid[] maps, bool additive = false)
        {
            throw new NotImplementedException();
        }

        public static async UniTask<List<LocalizationMapModel>> GetLoadedMaps(bool includePoints = false)
        {
            throw new NotImplementedException();
        }

        public static async UniTask<LocalizationMapModel> GetMap(Guid id, bool includePoints = false)
        {
            throw new NotImplementedException();
        }

        public static async UniTask<LocalizeResponse> Localize(int imageWidth, int imageHeight, Vector4 intrinsics, Quaternion cameraRotation, Quaternion cameraOrientation, byte[] cameraImage)
        {
            throw new NotImplementedException();
        }
    }
}