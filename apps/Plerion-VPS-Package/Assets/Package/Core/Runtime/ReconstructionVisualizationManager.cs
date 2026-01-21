using System;
using System.Collections.Generic;
using System.Threading;
using Cysharp.Threading.Tasks;
using UnityEngine;

using Unity.Mathematics;

namespace Plerion.Core
{
    public class ReconstructionVisualizationManager : MonoBehaviour
    {
        public ReconstructionVisualizer reconstructionVisualizerPrefab;
        private Dictionary<Guid, CancellationTokenSource> _loadOperations = new Dictionary<Guid, CancellationTokenSource>();
        private Dictionary<Guid, ReconstructionVisualizer> _visualizers = new Dictionary<Guid, ReconstructionVisualizer>();

        private void Awake()
        {
            VisualPositioningSystem.SetReconstructionVisualizationManager(this);
        }

        private async UniTask AddMapAndLoad(Guid mapID, CancellationToken cancellationToken)
        {
            ReconstructionVisualizer reconstructionVisualizer = null;
            try
            {
                var mapData = await VisualPositioningSystem.GetMapData(mapID);

                if (cancellationToken.IsCancellationRequested)
                    return;

                reconstructionVisualizer = GameObject.Instantiate(
                    reconstructionVisualizerPrefab,
                    Vector3.zero,
                    Quaternion.identity
                );

                reconstructionVisualizer.gameObject.SetActive(enabled);

                await reconstructionVisualizer.Load(mapData.ReconstructionId, cancellationToken);

                reconstructionVisualizer
                    .GetComponent<Anchor>()
                    .SetEcefTransform(
                        new double3(mapData.PositionX, mapData.PositionY, mapData.PositionZ),
                        new quaternion(
                            (float)mapData.RotationX,
                            (float)mapData.RotationY,
                            (float)mapData.RotationZ,
                            (float)mapData.RotationW
                        )
                    );

                _visualizers.Add(mapID, reconstructionVisualizer);
            }
            catch (Exception exception)
            {
                if (reconstructionVisualizer != null)
                    GameObject.Destroy(reconstructionVisualizer);

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