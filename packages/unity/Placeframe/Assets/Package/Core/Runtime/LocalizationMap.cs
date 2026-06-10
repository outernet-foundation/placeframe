using System;
using System.Threading;
using Cysharp.Threading.Tasks;
using Unity.Mathematics;
using UnityEngine;
using Color = UnityEngine.Color;
using Quaternion = UnityEngine.Quaternion;
using Vector3 = UnityEngine.Vector3;

namespace Placeframe.Core
{
    [RequireComponent(typeof(MeshFilter))]
    [RequireComponent(typeof(MeshRenderer))]
    public class LocalizationMap : MonoBehaviour
    {
        private static readonly Color DefaultColor = Color.white;
        private static readonly float DefaultThickness = 0.01f;

        // Corner offsets for the two-triangle quad each point expands into. The
        // Placeframe/PointCloud shader scales these by _PointSize in view space.
        private static readonly Vector2[] QuadCorners =
        {
            new Vector2(-1, -1),
            new Vector2(-1, 1),
            new Vector2(1, 1),
            new Vector2(1, -1),
        };

        private static readonly int[] QuadTriangleOffsets = { 0, 1, 2, 0, 2, 3 };

        public Mesh cylinderMesh;
        public Material material;

        private CancellationTokenSource _loadCancellationTokenSource;
        private MeshFilter _meshFilter;
        private MeshRenderer _meshRenderer;
        private Mesh _pointMesh;
        private MaterialPropertyBlock _tintProperties;
        private MaterialPropertyBlock _cylinderProperties;
        private Vector3[] _framePositions = null;
        private bool _isVisible = true;

        private void Awake()
        {
            _meshFilter = GetComponent<MeshFilter>();
            _meshRenderer = GetComponent<MeshRenderer>();
            _cylinderProperties = new MaterialPropertyBlock();
            _cylinderProperties.SetColor("_Color", DefaultColor);
        }

        protected virtual void OnDestroy()
        {
            _loadCancellationTokenSource?.Cancel();
            _loadCancellationTokenSource?.Dispose();
            _loadCancellationTokenSource = null;

            if (_pointMesh != null)
                Destroy(_pointMesh);
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
                    properties: _cylinderProperties,
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
            _tintProperties ??= new MaterialPropertyBlock();
            _tintProperties.SetColor("_Tint", color);
            _meshRenderer.SetPropertyBlock(_tintProperties);
        }

        public void SetVisible(bool visible)
        {
            _isVisible = visible;
            _meshRenderer.enabled = visible;
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
            if (_pointMesh != null)
                Destroy(_pointMesh);

            _pointMesh = BuildPointMesh(points);
            _meshFilter.sharedMesh = _pointMesh;
            _framePositions = framePositions;
        }

        // Expands each reconstruction point into a four-vertex quad whose corners
        // are billboarded in the shader. Built once and uploaded to the GPU, so a
        // 300k-point cloud is a single static draw instead of a per-frame
        // particle-system simulation + sort + mesh rebuild.
        private static Mesh BuildPointMesh(VisualPositioningSystem.ReconstructionPoint[] points)
        {
            var vertices = new Vector3[points.Length * 4];
            var corners = new Vector2[points.Length * 4];
            var colors = new Color32[points.Length * 4];
            var indices = new int[points.Length * 6];

            var min = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue);
            var max = new Vector3(float.MinValue, float.MinValue, float.MinValue);

            for (var i = 0; i < points.Length; i++)
            {
                var point = points[i];
                var vertexBase = i * 4;

                for (var corner = 0; corner < 4; corner++)
                {
                    vertices[vertexBase + corner] = point.position;
                    corners[vertexBase + corner] = QuadCorners[corner];
                    colors[vertexBase + corner] = point.color;
                }

                var indexBase = i * 6;
                for (var offset = 0; offset < 6; offset++)
                    indices[indexBase + offset] = vertexBase + QuadTriangleOffsets[offset];

                min = Vector3.Min(min, point.position);
                max = Vector3.Max(max, point.position);
            }

            var mesh = new Mesh { indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            mesh.SetVertices(vertices);
            mesh.SetUVs(0, corners);
            mesh.SetColors(colors);
            mesh.SetIndices(indices, MeshTopology.Triangles, 0, calculateBounds: false);

            // Centers' AABB padded so view-space billboard expansion never clips
            // the cloud against frustum culling at edge points.
            var bounds = new Bounds();
            bounds.SetMinMax(min, max);
            bounds.Expand(1f);
            mesh.bounds = bounds;

            mesh.UploadMeshData(false);
            return mesh;
        }
    }
}
