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
    [RequireComponent(typeof(ParticleSystem), typeof(Anchor))]
    public class LocalizationMap : MonoBehaviour
    {
        private static readonly Color DefaultColor = Color.white;
        private static readonly float DefaultThickness = 0.01f;

        public Mesh cylinderMesh;
        public Material material;

        private CancellationTokenSource _loadCancellationTokenSource;
        private Anchor _anchor;
        private ParticleSystem _particleSystem;
        private ParticleSystemRenderer _particleSystemRenderer;
        private Vector3[] _framePositions = null;
        private bool _isVisible = true;

        private void Awake()
        {
            _anchor = GetComponent<Anchor>();
            _particleSystem = GetComponent<ParticleSystem>();
            _particleSystemRenderer = GetComponent<ParticleSystemRenderer>();
        }

        protected virtual void OnDestroy()
        {
            _loadCancellationTokenSource.Cancel();
            _loadCancellationTokenSource.Dispose();
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

        public void Initialize(Guid mapId)
        {
            if (_loadCancellationTokenSource != null)
            {
                throw new InvalidOperationException("ReconstructionVisualizer is already initialized.");
            }

            _loadCancellationTokenSource = new CancellationTokenSource();
            Load(mapId, _loadCancellationTokenSource.Token).Forget();
        }

        private async UniTask Load(Guid mapID, CancellationToken cancellationToken)
        {
            var mapData = await VisualPositioningSystem.GetMapData(mapID);

            SetEcefAnchor(
                new double3(mapData.PositionX, mapData.PositionY, mapData.PositionZ),
                new quaternion(
                    (float)mapData.RotationX,
                    (float)mapData.RotationY,
                    (float)mapData.RotationZ,
                    (float)mapData.RotationW
                )
            );

            (var pointPayload, var framePayload) = await UniTask.WhenAll(
                VisualPositioningSystem.GetReconstructionPoints(mapData.ReconstructionId),
                VisualPositioningSystem.GetReconstructionFramePoses(mapData.ReconstructionId)
            );

            await UniTask.SwitchToMainThread(cancellationToken);
            Load(pointPayload, framePayload);
        }

        public void Load(VisualPositioningSystem.ReconstructionPoint[] points, Vector3[] framePositions)
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

        public void SetEcefAnchor(double3 ecefPosition, quaternion ecefRotation)
        {
            _anchor.SetEcefTransform(ecefPosition, ecefRotation);
        }
    }
}
