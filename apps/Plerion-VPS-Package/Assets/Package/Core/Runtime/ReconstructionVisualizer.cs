using System;
using System.Buffers;
using System.Threading;
using Cysharp.Threading.Tasks;
using UnityEngine;
using Color = UnityEngine.Color;
using Quaternion = UnityEngine.Quaternion;
using Vector3 = UnityEngine.Vector3;

namespace Plerion.Core
{
    [RequireComponent(typeof(ParticleSystem))]
    public class ReconstructionVisualizer : MonoBehaviour
    {
        private static readonly Color DefaultColor = Color.white;
        private static readonly float DefaultThickness = 0.01f;

        public Mesh cylinderMesh;
        public Material material;

        private readonly AsyncLifecycleGuard _loadGuard = new AsyncLifecycleGuard();
        private ParticleSystem _particleSystem;
        private Vector3[] _framePositions = null;

        private void Awake()
        {
            _particleSystem = GetComponent<ParticleSystem>();
        }

        private void Update()
        {
            if (_framePositions == null)
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

        protected virtual void OnDestroy()
        {
            if (
                _loadGuard.State == AsyncLifecycleGuard.LifecycleState.Starting
                || _loadGuard.State == AsyncLifecycleGuard.LifecycleState.Running
            )
            {
                _loadGuard.StopAsync(() => UniTask.CompletedTask).Forget();
            }
        }

        public void SetColor(Color color)
        {
            var m = _particleSystem.main;
            m.startColor = color;
        }

        public async UniTask Load(Guid reconstructionId, CancellationToken cancellationToken = default)
        {
            if (
                _loadGuard.State == AsyncLifecycleGuard.LifecycleState.Starting
                || _loadGuard.State == AsyncLifecycleGuard.LifecycleState.Running
            )
            {
                await _loadGuard.StopAsync(() => UniTask.CompletedTask);
            }

            await _loadGuard.StartAsync(
                loadGuardCancellationToken => LoadInternal(reconstructionId, loadGuardCancellationToken),
                cancellationToken
            );
        }

        private async UniTask LoadInternal(Guid reconstructionId, CancellationToken cancellationToken = default)
        {
            (var pointPayload, var framePayload) = await UniTask.WhenAll(
                VisualPositioningSystem.GetReconstructionPoints(reconstructionId),
                VisualPositioningSystem.GetReconstructionFramePoses(reconstructionId)
            );

            await UniTask.SwitchToMainThread(cancellationToken);
            PopulateFromPayload(pointPayload, framePayload);
        }

        private void PopulateFromPayload(VisualPositioningSystem.ReconstructionPoint[] pointPayload, Vector3[] framePayload)
        {
            var particles = ArrayPool<ParticleSystem.Particle>.Shared.Rent(pointPayload.Length);
            try
            {
                for (var i = 0; i < pointPayload.Length; i++)
                {
                    var point = pointPayload[i];
                    particles[i].position = point.position;
                    particles[i].startColor = point.color;
                    particles[i].startSize = 10000;
                    particles[i].startLifetime = float.MaxValue;
                    particles[i].remainingLifetime = float.MaxValue;
                }

                _particleSystem.SetParticles(particles, pointPayload.Length);
            }
            finally
            {
                ArrayPool<ParticleSystem.Particle>.Shared.Return(particles);
            }

            _framePositions = framePayload;
        }
    }
}
