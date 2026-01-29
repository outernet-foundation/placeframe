#if !UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.Linq;
using Cysharp.Threading.Tasks;
using UnityEngine;

namespace Outernet.Client.Location
{
    class WifiScanner
    {
        private AndroidJavaObject wifi;

        public async UniTask<List<WifiAccessPoint>> ScanAsync()
        {
            if (wifi == null)
            {
                var unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer");
                var currentActivity = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity");
                wifi = currentActivity.Call<AndroidJavaObject>("getSystemService", "wifi");
            }
            else
            {
                wifi.Call<bool>("startScan");
                await UniTask.Delay(10000);
            }

            AndroidJavaObject wifiScanResults = wifi.Call<AndroidJavaObject>("getScanResults");

            var wifiAccessPoints = Enumerable
                .Range(0, wifiScanResults.Call<int>("size"))
                .Select(index =>
                {
                    var wifiNetwork = wifiScanResults.Call<AndroidJavaObject>("get", index);

                    return new WifiAccessPoint
                    {
                        macAddress = wifiNetwork.Get<string>("BSSID"),
                        signalStrength = wifiNetwork.Get<int>("level"),
                    };
                })
                .ToList();

          Log.Info(LogGroup.Localizer, "Found {Count} nearby WiFi access points: {AccessPoints}",
                wifiAccessPoints.Count, string.Join(", ", wifiAccessPoints.Select(ap => ap.macAddress)));

            return wifiAccessPoints;
        }
    }
}
#endif