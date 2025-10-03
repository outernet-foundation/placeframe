using System;
using Unity.Mathematics;
using UnityEngine;

namespace Plerion
{
    [ExecuteInEditMode]
    public class Anchor : MonoBehaviour
    {
        public double3 ecefPosition => _ecefPosition;

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

            _lastKnownPosition = transform.position;
            _lastKnownRotation = transform.rotation;

            _ecefPosition = ecef.position;
            _ecefRotation = ecef.rotation;

            _positionInitialized = true;
        }

        private void OnEnable()
        {
            VisualPositioningSystem.OnReferenceFrameUpdated +=
                HandleLocalizedReferenceFrameChanged;

            HandleLocalizedReferenceFrameChanged();
        }

        private void OnDisable()
        {
            VisualPositioningSystem.OnReferenceFrameUpdated -=
                HandleLocalizedReferenceFrameChanged;
        }

        private void LateUpdate()
        {
            if (transform.position != _lastKnownPosition ||
                transform.rotation != _lastKnownRotation)
            {
                var ecef = VisualPositioningSystem.UnityWorldToEcef(transform.position, transform.rotation);
                _lastKnownPosition = transform.position;
                _lastKnownRotation = transform.rotation;
                _ecefPosition = ecef.position;
                _ecefRotation = ecef.rotation;
            }
        }

        private void HandleLocalizedReferenceFrameChanged()
        {
            var local = VisualPositioningSystem.EcefToUnityWorld(_ecefPosition, _ecefRotation);
            _lastKnownPosition = local.position;
            _lastKnownRotation = local.rotation;
            transform.position = local.position;
            transform.rotation = local.rotation;
        }
    }
}