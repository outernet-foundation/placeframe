using System;
using System.Collections.Generic;
using System.Threading;
using Cysharp.Threading.Tasks;
using UnityEngine;

namespace Plerion.Core
{
    public class LocalizationMapManager : MonoBehaviour
    {
        public LocalizationMap localizationMapPrefab;
        private Dictionary<Guid, CancellationTokenSource> _loadOperations = new Dictionary<Guid, CancellationTokenSource>();
        private Dictionary<Guid, LocalizationMap> _visualizers = new Dictionary<Guid, LocalizationMap>();

        private void Awake()
        {
            VisualPositioningSystem.SetLocalizationMapManager(this);
        }

        private async UniTask AddMapAndLoad(Guid mapID, CancellationToken cancellationToken)
        {
            LocalizationMap localizationMap = null;
            try
            {
                localizationMap = Instantiate(
                    localizationMapPrefab,
                    Vector3.zero,
                    Quaternion.identity
                );

                localizationMap.gameObject.SetActive(enabled);
                await localizationMap.Load(mapID, cancellationToken);
                _visualizers.Add(mapID, localizationMap);
            }
            catch (Exception exception)
            {
                if (localizationMap != null)
                    Destroy(localizationMap.gameObject);

                if (exception is not OperationCanceledException)
                    throw;
            }
            finally
            {
                if (_loadOperations.TryGetValue(mapID, out var cancellationTokenSource))
                {
                    cancellationTokenSource.Dispose();
                    _loadOperations.Remove(mapID);
                }
            }
        }

        public void AddMap(Guid mapID)
        {
            if (_loadOperations.ContainsKey(mapID) || _visualizers.ContainsKey(mapID))
                return;

            var tokenSource = new CancellationTokenSource();
            _loadOperations.Add(mapID, tokenSource);
            AddMapAndLoad(mapID, tokenSource.Token).Forget();
        }

        public void RemoveMap(Guid mapID)
        {
            if (_loadOperations.TryGetValue(mapID, out var loadOperation))
            {
                _loadOperations.Remove(mapID);
                loadOperation.Cancel();
            }

            if (_visualizers.TryGetValue(mapID, out var visualizer))
            {
                _visualizers.Remove(mapID);
                Destroy(visualizer.gameObject);
            }
        }
    }
}