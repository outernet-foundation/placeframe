using UnityEngine;


namespace Outernet.Client
{
    [ExecuteAlways]
    public class PointHandleGeometry : HandleGeometry
    {
        public float radius
        {
            get => _radius;
            set
            {
                _radius = value;
                Update();
            }
        }

        [SerializeField]
        private Transform _model;

        [SerializeField]
        private SphereCollider _collider;

        [SerializeField]
        private float _radius;

        [SerializeField]
        private float _colliderRadiusPadding;

        private void Update()
        {
            _model.localScale = Vector3.one * 2f * radius;
            _collider.radius = radius + _colliderRadiusPadding;
        }
    }
}