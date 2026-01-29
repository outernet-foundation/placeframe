using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using System.Linq;

namespace Outernet.Client.Location
{
    static public class GeolocationAPI
    {
        [Serializable]
        private class GeolocationRequest
        {
            public bool considerIp = false;
            public List<WifiAccessPoint> wifiAccessPoints;
        }

        [Serializable]
        private class GeolocationResponse
        {
            public class LatLng
            {
                public double Lat;
                public double Lng;
            }

            public LatLng Location;
            public float Accuracy;
        }

        static readonly string googleGeolocationApiKey = "AIzaSyDzjw16iFtb4UMtsVBNfBo-pkTJ0q742M8";
        static readonly string googleGeolocationApiUrl = $"https://www.googleapis.com/geolocation/v1/geolocate?key={googleGeolocationApiKey}";

        public static async UniTask<(double latitude, double longitude, float accuracy)?> Geolocate(List<WifiAccessPoint> wifiAccessPoints)
        {
            try
            {
                var googleAPIResponse = await RestClient.Post<GeolocationRequest, GeolocationResponse>(
                    googleGeolocationApiUrl,
                    new GeolocationRequest { wifiAccessPoints = wifiAccessPoints });

                Log.Info(
                    LogGroup.Localizer,
                    "Geolocation API response: ({Latitude}, {Longitude}) with accuracy {Accuracy}",
                    googleAPIResponse.Location.Lat, googleAPIResponse.Location.Lng, googleAPIResponse.Accuracy);

                return (googleAPIResponse.Location.Lat, googleAPIResponse.Location.Lng, googleAPIResponse.Accuracy);
            }
            catch (Exception exception)
            {
                Log.Warn(LogGroup.Localizer, exception, "Geolocation API request failed");
                return null;
            }
        }
    }
}