using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Outernet.Client
{
    public enum Axis
    {
        X,
        Y,
        Z
    }

    [ExecuteAlways]
    public class MockCapsule : MonoBehaviour
    {
        public float height
        {
            get => _height;
            set
            {
                _height = value;
                UpdateCapsule();
            }
        }

        public float radius
        {
            get => _radius;
            set
            {
                _radius = value;
                UpdateCapsule();
            }
        }

        public Axis axis
        {
            get => _axis;
            set
            {
                _axis = value;
                UpdateCapsule();
            }
        }

        [SerializeField]
        private Transform _endcap1;

        [SerializeField]
        private Transform _endcap2;

        [SerializeField]
        private Transform _cylinder;

        [SerializeField]
        private float _height;

        [SerializeField]
        private float _radius;

        [SerializeField]
        private Axis _axis;

        private void Awake()
        {
            if (Application.isPlaying)
                UpdateCapsule();
        }

        void Update()
        {
            if (Application.isPlaying)
                return;

            if (_endcap1 == null ||
                _endcap2 == null ||
                _cylinder == null)
            {
                return;
            }

            UpdateCapsule();
        }

        private void UpdateCapsule()
        {
            float diameter = radius * 2f;

            _cylinder.localScale = new Vector3(
                diameter,
                (height * 0.5f) - radius,
                diameter
            );

            _endcap1.localScale = Vector3.one * diameter;
            _endcap2.localScale = Vector3.one * diameter;

            Vector3 facing = new Vector3(
                axis == Axis.X ? 1 : 0,
                axis == Axis.Y ? 1 : 0,
                axis == Axis.Z ? 1 : 0
            );

            _endcap1.localPosition = facing * ((height * 0.5f) - radius);
            _endcap2.localPosition = facing * ((height * -0.5f) + radius);

            if (axis == Axis.X)
            {
                _cylinder.localRotation = Quaternion.AngleAxis(90f, Vector3.forward);
            }
            else if (axis == Axis.Y)
            {
                _cylinder.localRotation = Quaternion.identity;
            }
            else
            {
                _cylinder.localRotation = Quaternion.AngleAxis(90f, Vector3.right);
            }
        }
    }
}