using Unity.Mathematics;
using UnityEngine;

namespace Placeframe.Core
{
    [ExecuteInEditMode]
    public class Anchor : MonoBehaviour
    {
        public double3 ecefPosition
        {
            get => _ecefPosition;
            set
            {
                if (Equals(_ecefPosition, value))
                    return;

                _ecefPosition = value;
                SetEcefTransform(_ecefPosition, _ecefRotation);
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
                SetEcefTransform(_ecefPosition, _ecefRotation);
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

        private Vector3 _targetPosition;
        private Quaternion _targetRotation;

        private void Awake()
        {
            if (!Application.isPlaying && _positionInitialized)
                return;

            var ecef = VisualPositioningSystem.UnityWorldToEcef(transform.position, transform.rotation);

            _lastKnownPosition = transform.position;
            _lastKnownRotation = transform.rotation;

            _targetPosition = transform.position;
            _targetRotation = transform.rotation;

            ecefPosition = ecef.position;
            ecefRotation = ecef.rotation;

            _positionInitialized = true;
        }

        private void OnEnable()
        {
            VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated += HandleReferenceFrameChanged;

            SetEcefTransform(_ecefPosition, _ecefRotation);
            JumpToTarget();
        }

        private void OnDisable()
        {
            VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated -= HandleReferenceFrameChanged;
        }

        private void LateUpdate()
        {
            if (transform.position != _lastKnownPosition || transform.rotation != _lastKnownRotation)
            {
                _lastKnownPosition = transform.position;
                _lastKnownRotation = transform.rotation;

                _targetPosition = transform.position;
                _targetRotation = transform.rotation;

                var ecef = VisualPositioningSystem.UnityWorldToEcef(transform.position, transform.rotation);
                _ecefPosition = ecef.position;
                _ecefRotation = ecef.rotation;
            }

            if (Application.isPlaying)
            {
                transform.position = Vector3.Lerp(transform.position, _targetPosition, Time.deltaTime * 5f);
                transform.rotation = Quaternion.Lerp(transform.rotation, _targetRotation, Time.deltaTime * 5);

                _lastKnownPosition = transform.position;
                _lastKnownRotation = transform.rotation;
            }
            else
            {
                JumpToTarget();
            }
        }

        private void HandleReferenceFrameChanged()
        {
            SetEcefTransform(ecefPosition, ecefRotation);
        }

        public void SetEcefTransform(double3 ecefPosition, quaternion ecefRotation)
        {
            _ecefPosition = ecefPosition;
            _ecefRotation = ecefRotation;

            var local = VisualPositioningSystem.EcefToUnityWorld(ecefPosition, ecefRotation);

            _targetPosition = local.position;
            _targetRotation = local.rotation;

            if (
                (_targetPosition - transform.position).magnitude > 10
                || Quaternion.Angle(_targetRotation, transform.rotation) > 90f
            )
            {
                JumpToTarget();
            }
        }

        private void JumpToTarget()
        {
            _lastKnownPosition = _targetPosition;
            _lastKnownRotation = _targetRotation;
            transform.position = _targetPosition;
            transform.rotation = _targetRotation;
        }
    }
}
