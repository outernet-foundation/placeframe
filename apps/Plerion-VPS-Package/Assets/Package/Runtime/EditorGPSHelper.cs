using Cysharp.Threading.Tasks;
using Unity.Mathematics;
using UnityEngine;

namespace Plerion
{
    [ExecuteInEditMode]
    public class EditorGPSHelper : MonoBehaviour
    {
        [Delayed]
        public double editorLatitude;

        [Delayed]
        public double editorLongitude;


        [Delayed]
        public float editorHeight;

        [Delayed]
        public float editorRotation;

        [Delayed]
        public float editorMapRadius = 25f;

        public Lighting editorLighting = Lighting.Day;
        public bool updateMapsDuringPlayMode = true;

        private double _lastEditorLatitude;
        private double _lastEditorLongitude;
        private float _lastEditorHeight;
        private float _lastEditorRotation;
        private float _lastEditorMapRadius;
        private Lighting _lastEditorLighting;

        private void OnEnable()
        {
            UpdateLocalizedReferenceFrame();
        }

        private void Update()
        {
            if (_lastEditorLatitude != editorLatitude ||
                _lastEditorLongitude != editorLongitude ||
                _lastEditorHeight != editorHeight ||
                _lastEditorRotation != editorRotation ||
                _lastEditorMapRadius != editorMapRadius ||
                _lastEditorLighting != editorLighting)
            {
                UpdateLocalizedReferenceFrame();
            }
        }

        private void UpdateLocalizedReferenceFrame()
        {
            _lastEditorLatitude = editorLatitude;
            _lastEditorLongitude = editorLongitude;
            _lastEditorHeight = editorHeight;
            _lastEditorRotation = editorRotation;
            _lastEditorMapRadius = editorMapRadius;
            _lastEditorLighting = editorLighting;

            if (updateMapsDuringPlayMode && Application.isPlaying)
            {
                PlerionAPI.UpdateMapsFromLocation(
                    _lastEditorLatitude,
                    _lastEditorLongitude,
                    _lastEditorHeight,
                    _lastEditorMapRadius,
                    _lastEditorLighting
                ).Forget();
            }

            var ecefPosition = Utility.LlhToEcefPosition(editorLatitude, editorLongitude, editorHeight);

            VisualPositioningSystem.SetUnityWorldToEcefTransform(
                ecefPosition,
                Utility.EcefPositionToEunRotation(ecefPosition) * Quaternion.AngleAxis(editorRotation, Vector3.up)
            );
        }
    }
}