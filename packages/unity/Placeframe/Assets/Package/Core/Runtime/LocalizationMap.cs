using System;
using System.Buffers;
using System.Threading;
using Cysharp.Threading.Tasks;
using Unity.Mathematics;
using UnityEngine;
using Color = UnityEngine.Color;
using Quaternion = UnityEngine.Quaternion;
using Vector3 = UnityEngine.Vector3;

namespace Placeframe.Core
{
    [RequireComponent(typeof(ParticleSystem))]
    public class LocalizationMap : MonoBehaviour
    {
        private static readonly Color DefaultColor = Color.white;
        private static readonly float DefaultThickness = 0.01f;

        public Mesh cylinderMesh;
        public Material material;

        private CancellationTokenSource _loadCancellationTokenSource;
        private ParticleSystem _particleSystem;
        private ParticleSystemRenderer _particleSystemRenderer;
        private Vector3[] _framePositions = null;
        private bool _isVisible = true;

        private void Awake()
        {
            _particleSystem = GetComponent<ParticleSystem>();
            _particleSystemRenderer = GetComponent<ParticleSystemRenderer>();
        }

        protected virtual void OnDestroy()
        {
            _loadCancellationTokenSource?.Cancel();
            _loadCancellationTokenSource?.Dispose();
            _loadCancellationTokenSource = null;
        }

        private void Update()
        {
            if (_framePositions == null || !_isVisible)
                return;

            for (int i = 0; i < _framePositions.Length - 1; i++)
            {
                var from = transform.TransformPoint(_framePositions[i]);
                var to = transform.TransformPoint(_framePositions[i + 1]);

                if (from == to)
                    return;

                var properties = new MaterialPropertyBlock();
                properties.SetColor("_Color", DefaultColor);

                Graphics.DrawMesh(
                    mesh: cylinderMesh,
                    matrix: Matrix4x4.TRS(
                        from,
                        Quaternion.LookRotation(to - from),
                        new Vector3(DefaultThickness, DefaultThickness, Vector3.Magnitude(from - to))
                    ),
                    material: material,
                    layer: 0,
                    camera: null,
                    submeshIndex: 0,
                    properties: properties,
                    castShadows: UnityEngine.Rendering.ShadowCastingMode.Off,
                    receiveShadows: false,
                    probeAnchor: null,
                    lightProbeUsage: UnityEngine.Rendering.LightProbeUsage.Off,
                    lightProbeProxyVolume: null
                );
            }
        }

        public void SetColor(Color color)
        {
            var m = _particleSystem.main;
            m.startColor = color;
        }

        public void SetVisible(bool visible)
        {
            _isVisible = visible;
            _particleSystemRenderer.enabled = visible;
        }

        public void Load(Guid mapId)
        {
            _loadCancellationTokenSource?.Cancel();
            _loadCancellationTokenSource?.Dispose();
            _loadCancellationTokenSource = new CancellationTokenSource();
            DownloadMapAndLoad(mapId, _loadCancellationTokenSource.Token).Forget();
        }

        public void Load(VisualPositioningSystem.ReconstructionPoint[] points, Vector3[] framePositions)
        {
            _loadCancellationTokenSource?.Cancel();
            _loadCancellationTokenSource?.Dispose();
            _loadCancellationTokenSource = new CancellationTokenSource();
            try
            {
                LoadPoints(points, framePositions);
            }
            catch (Exception exception)
            {
                VisualPositioningSystem.LogError(
                    $"LocalizationMap.Load(points, frames) threw"
                        + $" pointCount={points.Length} frameCount={framePositions.Length}"
                        + $" exception={exception}"
                );
            }
        }

        private async UniTask DownloadMapAndLoad(Guid mapID, CancellationToken cancellationToken)
        {
            VisualPositioningSystem.LogDebug($"LocalizationMap.DownloadMapAndLoad start mapId={mapID}");
            try
            {
                var mapData = await VisualPositioningSystem.GetMapData(mapID);
                cancellationToken.ThrowIfCancellationRequested();
                VisualPositioningSystem.LogDebug(
                    $"LocalizationMap got map data mapId={mapID} reconstructionId={mapData.ReconstructionId}"
                );

                var local = VisualPositioningSystem.EcefToUnityWorld(
                    new double3(mapData.PositionX, mapData.PositionY, mapData.PositionZ),
                    new quaternion(
                        (float)mapData.RotationX,
                        (float)mapData.RotationY,
                        (float)mapData.RotationZ,
                        (float)mapData.RotationW
                    )
                );

                transform.position = local.position;
                transform.rotation = local.rotation;

                VisualPositioningSystem.LogDebug(
                    $"LocalizationMap fetching points mapId={mapID} reconstructionId={mapData.ReconstructionId}"
                );
                var pointPayload = await VisualPositioningSystem.GetReconstructionPoints(
                    mapData.ReconstructionId,
                    cancellationToken
                );
                VisualPositioningSystem.LogDebug(
                    $"LocalizationMap got points mapId={mapID} pointCount={pointPayload.Length}"
                );

                VisualPositioningSystem.LogDebug(
                    $"LocalizationMap fetching frames mapId={mapID} reconstructionId={mapData.ReconstructionId}"
                );
                var framePayload = await VisualPositioningSystem.GetReconstructionFramePoses(
                    mapData.ReconstructionId,
                    cancellationToken
                );
                VisualPositioningSystem.LogDebug(
                    $"LocalizationMap got frames mapId={mapID} frameCount={framePayload.Length}"
                );

                VisualPositioningSystem.LogDebug(
                    $"LocalizationMap downloaded mapId={mapID}"
                        + $" pointCount={pointPayload.Length} frameCount={framePayload.Length}"
                );

                await UniTask.SwitchToMainThread(cancellationToken);
                LoadPoints(pointPayload, framePayload);

                VisualPositioningSystem.LogDebug(
                    $"LocalizationMap rendered mapId={mapID} pointCount={pointPayload.Length}"
                );
            }
            catch (OperationCanceledException)
            {
                VisualPositioningSystem.LogDebug($"LocalizationMap.DownloadMapAndLoad cancelled mapId={mapID}");
            }
            catch (Exception exception)
            {
                VisualPositioningSystem.LogError(
                    $"LocalizationMap.DownloadMapAndLoad threw mapId={mapID} exception={exception}"
                );
            }
        }

        private void LoadPoints(VisualPositioningSystem.ReconstructionPoint[] points, Vector3[] framePositions)
        {
            var particles = ArrayPool<ParticleSystem.Particle>.Shared.Rent(points.Length);
            try
            {
                for (var i = 0; i < points.Length; i++)
                {
                    var point = points[i];
                    particles[i].position = point.position;
                    particles[i].startColor = point.color;
                    particles[i].startSize = 10000;
                    particles[i].startLifetime = float.MaxValue;
                    particles[i].remainingLifetime = float.MaxValue;
                }

                _particleSystem.SetParticles(particles, points.Length);
            }
            finally
            {
                ArrayPool<ParticleSystem.Particle>.Shared.Return(particles);
            }

            _framePositions = framePositions;
        }
    }
}
