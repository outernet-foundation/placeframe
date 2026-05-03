using Unity.Mathematics;
using UnityEngine;

namespace Placeframe.Core
{
    [ExecuteInEditMode]
    public class GeoPose : MonoBehaviour
    {
        public double3 ecefPosition
        {
            get => _ecefPosition;
            set
            {
                if (Equals(_ecefPosition, value))
                    return;

                _ecefPosition = value;
                ApplyEcefTransform();
            }
        }

        public quaternion ecefRotation
        {
            get => _ecefRotation;
            set
            {
                if (Equals(_ecefRotation, value))
                    return;

                _ecefRotation = value;
                ApplyEcefTransform();
            }
        }

        [SerializeField, HideInInspector]
        private double3 _ecefPosition;

        [SerializeField, HideInInspector]
        private quaternion _ecefRotation;

        [SerializeField, HideInInspector]
        private Vector3 _lastKnownPosition;

        [SerializeField, HideInInspector]
        private Quaternion _lastKnownRotation;

        [SerializeField, HideInInspector]
        private bool _positionInitialized;

        private void Awake()
        {
            if (!Application.isPlaying && _positionInitialized)
                return;

            var ecef = VisualPositioningSystem.UnityWorldToEcef(transform.position, transform.rotation);
            _ecefPosition = ecef.position;
            _ecefRotation = ecef.rotation;

            _lastKnownPosition = transform.position;
            _lastKnownRotation = transform.rotation;

            _positionInitialized = true;
        }

        private void OnEnable()
        {
            VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated += ApplyEcefTransform;
            ApplyEcefTransform();
        }

        private void OnDisable()
        {
            VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated -= ApplyEcefTransform;
        }

        private void LateUpdate()
        {
            if (transform.position != _lastKnownPosition || transform.rotation != _lastKnownRotation)
            {
                var ecef = VisualPositioningSystem.UnityWorldToEcef(transform.position, transform.rotation);
                _ecefPosition = ecef.position;
                _ecefRotation = ecef.rotation;
                _lastKnownPosition = transform.position;
                _lastKnownRotation = transform.rotation;
            }
        }

        public void SetEcefTransform(double3 ecefPosition, quaternion ecefRotation)
        {
            _ecefPosition = ecefPosition;
            _ecefRotation = ecefRotation;
            ApplyEcefTransform();
        }

        private void ApplyEcefTransform()
        {
            var local = VisualPositioningSystem.EcefToUnityWorld(_ecefPosition, _ecefRotation);
            transform.position = local.position;
            transform.rotation = local.rotation;
            _lastKnownPosition = transform.position;
            _lastKnownRotation = transform.rotation;
        }
    }
}
