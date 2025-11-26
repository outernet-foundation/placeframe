using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;

namespace Outernet.MapRegistrationTool
{
    public static class CesiumAPI
    {
        [Serializable]
        private class HeightRequest
        {
            [Serializable]
            public class Coordinate
            {
                public double latitude;
                public double longitude;
            }

            public List<Coordinate> coordinates;
        }

        [Serializable]
        private class HeightResponse
        {
            public List<double> heights;
        }

        public static async UniTask<List<double>> GetHeights(List<(double latitude, double longitude)> coordinates)
        {
            try
            {
                var heightResponse = await RestClient.Post<HeightRequest, HeightResponse>("http://52.200.81.198:5001/height",
                    new HeightRequest
                    {
                        coordinates = coordinates.ConvertAll(c => new HeightRequest.Coordinate { latitude = c.latitude, longitude = c.longitude })
                    }
                );

                Log.Info(LogGroup.Localizer, "Heights API response: {Heights}", heightResponse.heights);
                return heightResponse.heights;
            }
            catch (Exception exception)
            {
                Log.Warn(LogGroup.Localizer, exception, "Cesium Heights API request failed");
                return null;
            }
        }
    }
}