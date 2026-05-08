using UnityEngine;
using UnityEditor;
using System;
using Cysharp.Threading.Tasks;
using Placeframe.Core;
using SimpleJSON;
using System.Linq;

namespace Plerion.MakeItSing
{
    public class ReconstructionDownloadHelperWindow : EditorWindow
    {
        private string _domain;
        private string _username;
        private string _password;
        private string _reconstructionID;
        private string _destination;
        private bool _initialized;

        [MenuItem("Window/Reconstruction Download Helper")]
        public static void ShowWindow()
        {
            GetWindow<ReconstructionDownloadHelperWindow>("Reconstruction Download Helper");
        }

        public void OnGUI()
        {
            if (!_initialized)
            {
                var env = UnityEnv.GetOrCreateInstance();
                _domain = env.domain;
                _username = env.username;
                _password = env.password;
            }

            _domain = EditorGUILayout.TextField("Domain", _domain);
            _username = EditorGUILayout.TextField("Username", _username);
            _password = EditorGUILayout.TextField("Password", _password);
            _reconstructionID = EditorGUILayout.TextField("Reconstruction ID", _reconstructionID);
            _destination = EditorGUILayout.TextField("Output", _destination);

            if (GUILayout.Button("Download & Save"))
                DownloadAndSave(_domain, _username, _password, Guid.Parse(_reconstructionID), _destination).Forget();
        }

        private async UniTask DownloadAndSave(string domain, string username, string password, Guid reconstructionID, string outputPath)
        {
            if (!Auth.Initialized)
            {
                VisualPositioningSystem.Initialize(
                    new NoOpCameraProvider(),
                    "placeframe-api",
                    x => Debug.Log(x),
                    x => Debug.LogWarning(x),
                    x => Debug.LogError(x)
                );

                await VisualPositioningSystem.Login(domain, username, password);
            }

            var result = await VisualPositioningSystem.GetReconstructionPoints(reconstructionID);

            Mesh mesh = new Mesh();

            mesh.SetVertices(result.Select(x => x.position).ToArray());
            mesh.SetColors(result.Select(x => (Color)x.color).ToArray());

            var indices = result.Select((_, index) => index).ToArray();

            mesh.SetIndices(indices, MeshTopology.Points, 0);
            mesh.UploadMeshData(false);

            AssetDatabase.CreateAsset(mesh, $"Assets/{outputPath}");
            AssetDatabase.Refresh();
        }
    }
}