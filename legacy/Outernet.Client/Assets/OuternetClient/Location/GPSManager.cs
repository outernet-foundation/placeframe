using System.Threading;

using Unity.Mathematics;
using UnityEngine;
#if UNITY_ANDROID
using UnityEngine.Android;
#endif

using FofX;

using Cysharp.Threading.Tasks;

namespace Outernet.Client.Location
{
    public class GPSManager : MonoBehaviour
    {
        private TaskHandle _gpsTask = TaskHandle.Complete;

        private void Awake()
        {
#if UNITY_EDITOR
            return;
#elif MAGIC_LEAP
            _gpsTask = TaskHandle.Execute(token => WifiGeolocalization(token));
#else   
            _gpsTask = TaskHandle.Execute(token => LocationService(5, 5, token));
#endif
        }

        private void OnDestroy()
        {
            _gpsTask.Cancel();
        }

        private async UniTask WifiGeolocalization(CancellationToken cancellationToken = default)
        {
            WifiScanner scanner = new WifiScanner();
            while (!cancellationToken.IsCancellationRequested)
            {
                var wifiAccessPoints = await scanner.ScanAsync();

                if (cancellationToken.IsCancellationRequested)
                    return;

                var geolocation = await GeolocationAPI.Geolocate(wifiAccessPoints);

                if (cancellationToken.IsCancellationRequested)
                    return;

                if (geolocation.HasValue)
                {
                    await UniTask.SwitchToMainThread();

                    if (cancellationToken.IsCancellationRequested)
                        return;

                    App.state.roughGrainedLocation.ExecuteSet(new double2(geolocation.Value.latitude, geolocation.Value.longitude));
                }
            }
        }

        private async UniTask LocationService(float desiredAccuracy, float updateDistance, CancellationToken cancellationToken = default)
        {
            Debug.Log("EP: STARTING LOCATION SERVICE");
#if UNITY_ANDROID
            if (!Permission.HasUserAuthorizedPermission(Permission.FineLocation))
                Permission.RequestUserPermission(Permission.FineLocation);
#endif
            Debug.Log("EP: GOT PERMISSION");
            Input.location.Start(desiredAccuracy, updateDistance);

            while (!cancellationToken.IsCancellationRequested &&
                Input.location.status != LocationServiceStatus.Running &&
                Input.location.status != LocationServiceStatus.Failed)
            {
                await UniTask.WaitForEndOfFrame();
            }

            Debug.Log("EP: LOCATION SERVICE RUNNING OR FAILED");

            if (cancellationToken.IsCancellationRequested)
                return;

            if (Input.location.status == LocationServiceStatus.Failed)
                throw new System.Exception("User denied access to location services");

            Debug.Log("EP: LOCATION SERVICE RUNNING");

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);

            while (!cancellationToken.IsCancellationRequested)
            {
                await UniTask.WaitUntil(() =>
                    App.state.roughGrainedLocation.value.x != Input.location.lastData.latitude ||
                    App.state.roughGrainedLocation.value.y != Input.location.lastData.longitude,
                    cancellationToken: cancellationToken
                );

                cancellationToken.ThrowIfCancellationRequested();

                App.state.roughGrainedLocation.ExecuteSet(new double2(
                    Input.location.lastData.latitude,
                    Input.location.lastData.longitude
                ));

                await UniTask.WaitForEndOfFrame(cancellationToken: cancellationToken);
            }
        }
    }
}