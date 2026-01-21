using System;
using System.Buffers;
using System.Buffers.Binary;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using Cysharp.Threading.Tasks;
using PlerionApiClient.Model;
using Unity.Mathematics;
using UnityEngine;
using Color = UnityEngine.Color;
using Quaternion = UnityEngine.Quaternion;
using Vector3 = UnityEngine.Vector3;

namespace Plerion.Core
{
    [RequireComponent(typeof(ParticleSystem))]
    public class LocalizationMap : MonoBehaviour
    {
        struct Point
        {
            public Vector3 Position;
            public Color32 Color;
        }

        private static readonly Color DefaultColor = Color.white;
        private static readonly float DefaultThickness = 0.01f;

        private LocalizationMapRead _metadata;
        private CancellationTokenSource _loadCancellationTokenSource;
        private ParticleSystem _particleSystem;
        private Vector3[] _framePositions = null;

        public void Initialize(Guid mapId)
        {
            if (_loadCancellationTokenSource != null)
            {
                throw new InvalidOperationException("ReconstructionVisualizer is already initialized.");
            }

            _loadCancellationTokenSource = new CancellationTokenSource();
            Load(mapId, _loadCancellationTokenSource.Token).Forget();
        }

        public void SetColor(Color color)
        {
            var m = _particleSystem.main;
            m.startColor = color;
        }

        private void Awake()
        {
            _particleSystem = GetComponent<ParticleSystem>();
        }

        protected virtual void OnDestroy()
        {
            _loadCancellationTokenSource.Cancel();
            _loadCancellationTokenSource.Dispose();
            _loadCancellationTokenSource = null;
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
                    mesh: VisualPositioningSystem.Prefabs.CylinderMesh,
                    matrix: Matrix4x4.TRS(
                        from,
                        Quaternion.LookRotation(to - from),
                        new Vector3(DefaultThickness, DefaultThickness, Vector3.Magnitude(from - to))
                    ),
                    material: VisualPositioningSystem.Prefabs.GizmoMaterial,
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

        private async UniTask Load(Guid mapId, CancellationToken cancellationToken)
        {
            _metadata = await VisualPositioningSystem.Api.GetLocalizationMapAsync(mapId, cancellationToken).AsUniTask();

            var (framePayload, pointPayload) = await UniTask.WhenAll(
                FetchPayloadAsync(
                    VisualPositioningSystem
                        .Api.GetReconstructionFramePosesAsync(_metadata.ReconstructionId, AxisConvention.UNITY)
                        .AsUniTask(),
                    bytesPerElement: (3 * sizeof(float)) + (4 * sizeof(float)),
                    cancellationToken
                ),
                FetchPayloadAsync(
                    VisualPositioningSystem
                        .Api.GetReconstructionPointsAsync(_metadata.ReconstructionId, AxisConvention.UNITY)
                        .AsUniTask(),
                    bytesPerElement: (3 * sizeof(float)) + 3,
                    cancellationToken
                )
            );

            await UniTask.SwitchToMainThread(cancellationToken);

            GetComponent<Anchor>()
                .SetEcefTransform(
                    new double3(_metadata.PositionX, _metadata.PositionY, _metadata.PositionZ),
                    new quaternion(
                        (float)_metadata.RotationX,
                        (float)_metadata.RotationY,
                        (float)_metadata.RotationZ,
                        (float)_metadata.RotationW
                    )
                );

            var frames = ReadFrames(framePayload);
            var points = ReadPoints(pointPayload);

            _framePositions = frames;

            var particles = new ParticleSystem.Particle[points.positions.Length];
            for (var i = 0; i < points.positions.Length; i++)
            {
                particles[i].position = points.positions[i];
                particles[i].startColor = points.colors[i];
                particles[i].startSize = 0.1f;
                particles[i].startLifetime = float.MaxValue;
                particles[i].remainingLifetime = float.MaxValue;
            }
            _particleSystem.SetParticles(particles, particles.Length);
        }

        private static async UniTask<byte[]> FetchPayloadAsync(
            UniTask<PlerionApiClient.Client.FileParameter> responseTask,
            int bytesPerElement,
            CancellationToken cancellationToken
        )
        {
            var response = await responseTask;
            var stream = response.Content;
            try
            {
                var header = new byte[4];
                await stream.ReadExactlyAsync(header, 0, 4, cancellationToken);

                var count = (int)BinaryPrimitives.ReadUInt32LittleEndian(header);
                var payloadByteCount = 4 + (count * bytesPerElement);

                var payload = ArrayPool<byte>.Shared.Rent(payloadByteCount);
                Buffer.BlockCopy(header, 0, payload, 0, 4);
                await stream.ReadExactlyAsync(payload, 4, payloadByteCount - 4, cancellationToken);

                return payload;
            }
            finally
            {
                stream.Dispose();
            }
        }

        private (Vector3[] positions, Color32[] colors) ReadPoints(byte[] pointPayload)
        {
            var pointCount = (int)BinaryPrimitives.ReadUInt32LittleEndian(pointPayload.AsSpan(0, 4));
            var positionsByteCount = pointCount * 3 * sizeof(float);

            var positionsSpan = MemoryMarshal.Cast<byte, float>(pointPayload.AsSpan(4, positionsByteCount));
            var colorsSpan = pointPayload.AsSpan(4 + positionsByteCount, pointCount * 3);

            Vector3[] positions = new Vector3[pointCount];
            Color32[] colors = new Color32[pointCount];

            for (var i = 0; i < pointCount; i++)
            {
                var index = i * 3;
                positions[i] = new Vector3(
                    positionsSpan[index + 0],
                    positionsSpan[index + 1],
                    positionsSpan[index + 2]
                );
                colors[i] = new Color32(colorsSpan[index + 0], colorsSpan[index + 1], colorsSpan[index + 2], 255);
            }

            return (positions, colors);
        }

        private Vector3[] ReadFrames(byte[] framePayload)
        {
            var frameCount = (int)BinaryPrimitives.ReadUInt32LittleEndian(framePayload.AsSpan(0, 4));
            var positionsByteCount = frameCount * 3 * sizeof(float);

            var positionsSpan = MemoryMarshal.Cast<byte, float>(framePayload.AsSpan(4, positionsByteCount));

            Vector3[] positions = new Vector3[frameCount];

            for (var i = 0; i < frameCount; i++)
            {
                var index = i * 3;
                positions[i] = new Vector3(
                    positionsSpan[index + 0],
                    positionsSpan[index + 1],
                    positionsSpan[index + 2]
                );
            }

            return positions;
        }
    }

    internal static class StreamExtensions
    {
        public static async UniTask ReadExactlyAsync(
            this Stream stream,
            byte[] buffer,
            int offset,
            int count,
            CancellationToken cancellationToken
        )
        {
            while (count > 0)
            {
                var read = await stream.ReadAsync(buffer, offset, count, cancellationToken);
                if (read == 0)
                    throw new EndOfStreamException();
                offset += read;
                count -= read;
            }
        }
    }
}
