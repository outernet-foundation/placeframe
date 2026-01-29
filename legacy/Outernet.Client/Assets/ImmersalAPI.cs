using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;

namespace Outernet.Client.AuthoringTools
{
    [Serializable]
    public struct ImmersalMapRequest
    {
        public int id;
        public string token;
    }

    [Serializable]
    public struct ImmersalMetadataResponse
    {
        public string name;
    }

    [Serializable]
    public struct ImmersalPose
    {
        public double tx;
        public double ty;
        public double tz;
    }

    [Serializable]
    public struct ImmersalPoses
    {
        [Serializable]
        public struct Pose
        {
            public double px;
            public double py;
            public double pz;
        }

        public List<Pose> poses;
    }

    public static class ImmersalAPI
    {
        private static string IMMERSAL_API_URL = "https://api.immersal.com";

        static public async UniTask<byte[]> GetImmersalMapBytes(string apiKey, int id) =>
            await RestClient.Get<byte[]>($"{IMMERSAL_API_URL}/map?token={apiKey}&id={id}");

        static public async UniTask<byte[]> GetImmersalMapPly(string apiKey, int id) =>
            await RestClient.Get<byte[]>($"{IMMERSAL_API_URL}/sparse?token={apiKey}&id={id}");

        static public async UniTask<ImmersalMetadataResponse> GetImmersalMapMetadata(string apiKey, int id) =>
            await RestClient.Post<ImmersalMapRequest, ImmersalMetadataResponse>(
                $"{IMMERSAL_API_URL}/metadataget",
                new ImmersalMapRequest { id = id, token = apiKey });

        static public async UniTask<ImmersalPoses> GetImmersalMapPoses(string apiKey, int id) =>
            await RestClient.Post<ImmersalMapRequest, ImmersalPoses>(
                $"{IMMERSAL_API_URL}/getposes",
                new ImmersalMapRequest { id = id, token = apiKey });
    }
}