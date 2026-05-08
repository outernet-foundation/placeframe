using UnityEngine;
using UnityEditor;
using System;
using Cysharp.Threading.Tasks;
using Placeframe.Core;
using SimpleJSON;
using System.IO;

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
            _destination = EditorGUILayout.TextField("Save To", _destination);

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

            var result = await UniTask.WhenAll(
                VisualPositioningSystem.GetReconstructionPoints(reconstructionID),
                VisualPositioningSystem.GetReconstructionFramePoses(reconstructionID)
            );

            JSONArray points = new JSONArray();
            foreach (var point in result.Item1)
            {
                var pointJSON = new JSONObject();
                pointJSON["position"] = JSONSerializers.ToJSON(point.position);
                pointJSON["color"] = JSONSerializers.ToJSON((Color)point.color);

                points.Add(pointJSON);
            }

            JSONArray frames = new JSONArray();
            foreach (var point in result.Item2)
                frames.Add(JSONSerializers.ToJSON(point));

            var json = new JSONObject();
            json["points"] = points;
            json["frames"] = frames;

            File.WriteAllText(outputPath, json.ToString());
        }
    }
}