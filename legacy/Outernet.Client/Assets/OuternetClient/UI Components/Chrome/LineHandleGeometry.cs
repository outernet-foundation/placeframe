
using UnityEngine;
using System;
using R3;

namespace Outernet.Client
{
    [ExecuteAlways]
    public class LineHandleGeometry : HandleGeometry
    {
        public float height
        {
            get => _height;
            set
            {
                _height = value;
                Update();
            }
        }

        public float radius
        {
            get => _radius;
            set
            {
                _radius = value;
                Update();
            }
        }

        public Axis axis
        {
            get => _axis;
            set
            {
                _axis = value;
                Update();
            }
        }

        [SerializeField]
        private MockCapsule _model;

        [SerializeField]
        private CapsuleCollider _collider;

        [SerializeField]
        private Axis _axis;

        [SerializeField]
        private float _height;

        [SerializeField]
        private float _radius;

        [SerializeField]
        private float _colliderRadiusPadding;

        private IDisposable subscriptions;

        protected new void Awake()
        {
            if (!Application.isPlaying) return;

            base.Awake();

            subscriptions = chrome.dimensionsSubject.Subscribe(value =>
                height = value[(int)axis] / chrome.transform.localScale[(int)axis] + chrome.lineHandleHeightPadding);
        }

        private void OnDestroy()
        {
            if (!Application.isPlaying) return;

            subscriptions?.Dispose();
        }

        private void Update()
        {
            _model.axis = axis;
            _model.radius = radius;
            _model.height = height;
            _collider.radius = radius + _colliderRadiusPadding;
            _collider.height = height + (_colliderRadiusPadding * 2);
            _collider.direction = (int)axis;
        }
    }
}