using System;
using System.Buffers;
using System.Buffers.Binary;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using Cysharp.Threading.Tasks;
using PlerionApiClient.Api;
using PlerionApiClient.Model;
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

        private bool _loadingMap = false;
        private CancellationTokenSource _loadMapCancellationTokenSource;
        private ParticleSystem _particleSystem;
        private List<Vector3> _framePositions = new List<Vector3>();

        private void Awake()
        {
            _particleSystem = GetComponent<ParticleSystem>();
        }

        private void Update()
        {
            for (int i = 0; i < _framePositions.Count - 1; i++)
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

        protected virtual void OnDestroy()
        {
            _loadMapCancellationTokenSource?.Cancel();
            _loadMapCancellationTokenSource?.Dispose();
        }

        public void SetColor(Color color)
        {
            var m = _particleSystem.main;
            m.startColor = color;
        }

        public async UniTask Load(DefaultApi api, Guid reconstructionId, CancellationToken cancellationToken = default)
        {
            if (_loadingMap)
            {
                _loadMapCancellationTokenSource.Cancel();
                _loadMapCancellationTokenSource.Dispose();
            }

            _loadMapCancellationTokenSource = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            var loadCancellationToken = _loadMapCancellationTokenSource.Token;
            _loadingMap = true;

            byte[] pointPayload = null;
            byte[] framePayload = null;

            try
            {
                (pointPayload, framePayload) = await UniTask.WhenAll(
                    FetchPayloadAsync(
                        api.GetReconstructionPointsAsync(reconstructionId, AxisConvention.UNITY).AsUniTask(),
                        bytesPerElement: (3 * sizeof(float)) + 3,
                        loadCancellationToken
                    ),
                    FetchPayloadAsync(
                        api.GetReconstructionFramePosesAsync(reconstructionId, AxisConvention.UNITY).AsUniTask(),
                        bytesPerElement: (3 * sizeof(float)) + (4 * sizeof(float)),
                        loadCancellationToken
                    )
                );

                await UniTask.SwitchToMainThread(cancellationToken: loadCancellationToken);

                PopulateFromPayload(pointPayload, framePayload);
            }
            finally
            {
                if (pointPayload != null)
                    ArrayPool<byte>.Shared.Return(pointPayload);

                if (framePayload != null)
                    ArrayPool<byte>.Shared.Return(framePayload);

                _loadingMap = false;
            }
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

        private void PopulateFromPayload(byte[] pointPayload, byte[] framePayload)
        {
            var pointCount = (int)BinaryPrimitives.ReadUInt32LittleEndian(pointPayload.AsSpan(0, 4));
            var positionsByteCount = pointCount * 3 * sizeof(float);

            var positions = MemoryMarshal.Cast<byte, float>(pointPayload.AsSpan(4, positionsByteCount));
            var colors = pointPayload.AsSpan(4 + positionsByteCount, pointCount * 3);

            var particles = ArrayPool<ParticleSystem.Particle>.Shared.Rent(pointCount);
            try
            {
                for (var i = 0; i < pointCount; i++)
                {
                    var index = i * 3;
                    particles[i].position = new Vector3(
                        positions[index + 0],
                        positions[index + 1],
                        positions[index + 2]
                    );
                    particles[i].startColor = new Color32(colors[index + 0], colors[index + 1], colors[index + 2], 255);
                    particles[i].startSize = 10000;
                    particles[i].startLifetime = float.MaxValue;
                    particles[i].remainingLifetime = float.MaxValue;
                }

                _particleSystem.SetParticles(particles, pointCount);
            }
            finally
            {
                ArrayPool<ParticleSystem.Particle>.Shared.Return(particles);
            }

            var frameCount = (int)BinaryPrimitives.ReadUInt32LittleEndian(framePayload.AsSpan(0, 4));
            positionsByteCount = frameCount * 3 * sizeof(float);

            positions = MemoryMarshal.Cast<byte, float>(framePayload.AsSpan(4, positionsByteCount));

            _framePositions.Clear();
            if (_framePositions.Capacity < frameCount)
                _framePositions.Capacity = frameCount;

            for (var i = 0; i < frameCount; i++)
            {
                var index = i * 3;
                _framePositions.Add(new Vector3(positions[index + 0], positions[index + 1], positions[index + 2]));
            }
        }
    }

    internal static class StreamExtensions
    {
        public static async UniTask ReadExactlyAsync(
            this Stream stream,
            byte[] buffer,
            int offset,
            int count,
            CancellationToken cancellationToken = default
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
