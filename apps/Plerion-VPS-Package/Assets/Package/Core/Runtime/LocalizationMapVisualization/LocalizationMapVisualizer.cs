using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using UnityEngine;
using Unity.Mathematics;

namespace Plerion.VPS
{
    public class LocalizationMapVisualizer : MonoBehaviour
    {
        public static LocalizationMapRenderer theMap;

        public LocalizationMapRenderer mapRendererPrefab;

        private Dictionary<Guid, LocalizationMapRenderer> _mapsByID =
            new Dictionary<Guid, LocalizationMapRenderer>();

        private CancellationTokenSource _pollCancellationTokenSource;

        private void OnEnable()
        {
            if (_pollCancellationTokenSource != null)
                return;

            _pollCancellationTokenSource = new CancellationTokenSource();
            PollMaps(_pollCancellationTokenSource.Token).Forget();
        }

        private void OnDisable()
        {
            _pollCancellationTokenSource?.Cancel();
            _pollCancellationTokenSource?.Dispose();
            _pollCancellationTokenSource = null;
        }

        private async UniTask PollMaps(CancellationToken cancellationToken = default)
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                await UniTask.WaitUntil(() => VisualPositioningSystem.LocalizationSessionActive, cancellationToken: cancellationToken);

                try
                {
                    var maps = await VisualPositioningSystem.GetLoadedLocalizationMapsAsync(includePoints: false);

                    await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);

                    if (maps == null || maps.Length == 0)
                    {
                        foreach (var map in _mapsByID.Values)
                            Destroy(map.gameObject);
                    }
                    else
                    {
                        var removedMaps = _mapsByID.Keys.Where(x => !maps.Any(y => y.id == x)).ToArray();
                        foreach (var removedMap in removedMaps)
                        {
                            Destroy(_mapsByID[removedMap].gameObject);
                            _mapsByID.Remove(removedMap);
                        }

                        var addedMaps = maps.Where(x => !_mapsByID.ContainsKey(x.id)).ToArray();
                        foreach (var addedMap in addedMaps)
                        {
                            var local = VisualPositioningSystem.EcefToUnityWorld(addedMap.ecefPosition, addedMap.ecefRotation);
                            var mapView = Instantiate(mapRendererPrefab, local.position, local.rotation);
                            theMap = mapView;
                            mapView.gameObject.name = addedMap.name;
                            mapView.Load(addedMap.id);
                            _mapsByID.Add(addedMap.id, mapView);
                        }
                    }
                }
                catch (Exception exc)
                {
                    if (exc is TaskCanceledException)
                        break;

                    Log.Error(LogGroup.MapVisualization, exc);
                }

                await UniTask.WaitForSeconds(10, cancellationToken: cancellationToken);
            }
        }
    }
}
