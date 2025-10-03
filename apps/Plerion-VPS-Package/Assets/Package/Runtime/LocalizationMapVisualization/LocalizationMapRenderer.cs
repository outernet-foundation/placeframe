using System;
using System.Linq;
using System.Threading;

using UnityEngine;
using UnityEngine.Rendering;

using Cysharp.Threading.Tasks;

namespace Plerion
{
    [RequireComponent(typeof(MeshRenderer))]
    [RequireComponent(typeof(MeshFilter))]
    [RequireComponent(typeof(Anchor))]
    public class LocalizationMapRenderer : MonoBehaviour
    {
        public string shaderColorProperty = "_Color";

        private Mesh _mesh;
        private MeshRenderer _meshRenderer;
        private CancellationTokenSource _loadCancellationTokenSource;

        private void Awake()
        {
            _mesh = new Mesh();
            _meshRenderer = GetComponent<MeshRenderer>();
            GetComponent<MeshFilter>().mesh = _mesh;
        }

        private void OnDestroy()
        {
            _loadCancellationTokenSource?.Cancel();
            _loadCancellationTokenSource?.Dispose();
        }

        public void SetColor(Color color)
            => _meshRenderer.material.SetColor(shaderColorProperty, color);

        public void Load(Guid id)
        {
            _loadCancellationTokenSource?.Cancel();
            _loadCancellationTokenSource?.Dispose();
            _loadCancellationTokenSource = new CancellationTokenSource();
            LoadMap(id, _loadCancellationTokenSource.Token).Forget();
        }

        public void Load(Vector3[] points)
            => Load("Untitled Map", points);

        public void Load(string mapName, Vector3[] points)
        {
            _loadCancellationTokenSource?.Cancel();
            _loadCancellationTokenSource?.Dispose();
            _loadCancellationTokenSource = new CancellationTokenSource();
            LoadPoints(mapName, points, _loadCancellationTokenSource.Token).Forget();
        }

        private async UniTask LoadMap(Guid id, CancellationToken cancellationToken = default)
        {
            Log.Info(LogGroup.MapVisualization, $"Downloading map {id}.");

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);

            var map = await PlerionAPI.GetMap(id, true);
            Log.Info(LogGroup.MapVisualization, $"Downloaded map {id}. Name: {map.Name}.");

            cancellationToken.ThrowIfCancellationRequested();

            await LoadPoints(map.Name, map.Points, cancellationToken);
        }

        private async UniTask LoadPoints(string mapName, Vector3[] points, CancellationToken cancellationToken = default)
        {
            Log.Info(LogGroup.MapVisualization, $"Loading points for map {mapName}.");

            await UniTask.SwitchToThreadPool();

            cancellationToken.ThrowIfCancellationRequested();

            var colors = new Color32[points.Length];
            var indices = Enumerable.Range(0, points.Length).ToArray();

            Vector3 min = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue);
            Vector3 max = new Vector3(float.MinValue, float.MinValue, float.MinValue);

            foreach (var point in points)
            {
                if (point.x > max.x)
                    max.x = point.x;

                if (point.y > max.y)
                    max.y = point.y;

                if (point.z > max.z)
                    max.z = point.z;

                if (point.x < min.x)
                    min.x = point.x;

                if (point.y < min.y)
                    min.y = point.y;

                if (point.z < min.z)
                    min.z = point.z;
            }

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);

            _mesh.Clear();
            _mesh.indexFormat = points.Length > 65535 ? IndexFormat.UInt32 : IndexFormat.UInt16;
            _mesh.vertices = points;
            _mesh.colors32 = colors;
            _mesh.SetIndices(indices, MeshTopology.Points, 0);
            _mesh.bounds = new Bounds((min + max) / 2f, max - min);

            Log.Info(LogGroup.MapVisualization, $"Finished loading map {mapName}.");
        }
    }
}