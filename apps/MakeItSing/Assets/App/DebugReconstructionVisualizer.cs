using System.Linq;
using SimpleJSON;
using UnityEngine;

namespace Plerion.MakeItSing
{
    [RequireComponent(typeof(MeshFilter))]
    [RequireComponent(typeof(MeshRenderer))]
    [ExecuteAlways]
    public class DebugReconstructionVisualizer : MonoBehaviour
    {
        public TextAsset reconstruction;
        public bool refresh;
        private TextAsset _loadedReconstruction;

        private void Update()
        {
            if (reconstruction != _loadedReconstruction || refresh)
            {
                refresh = false;
                _loadedReconstruction = reconstruction;

                if (reconstruction == null)
                {
                    GetComponent<MeshFilter>().sharedMesh?.Clear();
                    return;
                }

                UpdateReconstructionMesh(JSON.Parse(reconstruction.text));
            }
        }

        private void OnEnable()
        {
            _loadedReconstruction = reconstruction;
            UpdateReconstructionMesh(JSON.Parse(reconstruction.text));
        }

        private void UpdateReconstructionMesh(JSONNode reconstructionJSON)
        {
            Mesh mesh = GetComponent<MeshFilter>().sharedMesh ?? new Mesh();

            var points = reconstructionJSON["points"].Linq.Select(x => JSONSerializers.ToVector3(x.Value["position"])).ToArray();
            var colors = reconstructionJSON["points"].Linq.Select(x => JSONSerializers.ToColor(x.Value["color"])).ToArray();
            mesh.SetVertices(points);
            mesh.SetColors(colors);

            var indices = points.Select((_, index) => index).ToArray();
            mesh.SetIndices(indices, MeshTopology.Points, 0);
            mesh.UploadMeshData(false);

            GetComponent<MeshFilter>().sharedMesh = mesh;
        }
    }
}