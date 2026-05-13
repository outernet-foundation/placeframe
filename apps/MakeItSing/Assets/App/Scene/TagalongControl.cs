using System;
using Nessle;
using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public struct TagalongProps
    {
        public ElementProps element;
        public IValueObservable<Camera> targetCamera;
        public IValueObservable<Vector3> targetRegionMin;
        public IValueObservable<Vector3> targetRegionMax;
        public IValueObservable<float> paddingFront;
        public IValueObservable<float> paddingBack;
        public IValueObservable<float> paddingLeft;
        public IValueObservable<float> paddingRight;
        public IValueObservable<float> paddingTop;
        public IValueObservable<float> paddingBottom;
        public IValueObservable<bool> lookAtCamera;
        public IValueObservable<float> moveRate;
        public IValueObservable<float> lookRate;
        public IListObservable<IControl> children;
    }

    public class TagalongControl : Control<TagalongProps>
    {
        public Camera targetCamera;

        public Vector3 targetRegionMin;
        public Vector3 targetRegionMax;

        [Min(0)]
        public float paddingFront;

        [Min(0)]
        public float paddingBack;

        [Min(0)]
        public float paddingLeft;

        [Min(0)]
        public float paddingRight;

        [Min(0)]
        public float paddingTop;

        [Min(0)]
        public float paddingBottom;

        public bool lookAtCamera;

        public float moveRate;

        public float lookRate;

        private bool _repositioning;

        public void OnDrawGizmos()
        {
            if (targetCamera == null)
                return;

            Gizmos.color = Color.yellow;

            Vector3 maxRegionMin = targetRegionMin - new Vector3(paddingLeft, paddingBottom, paddingBack);
            Vector3 maxRegionMax = targetRegionMax + new Vector3(paddingRight, paddingTop, paddingFront);

            DrawWorldLine(new Vector3(maxRegionMin.x, maxRegionMin.y, maxRegionMin.z), new Vector3(maxRegionMax.x, maxRegionMin.y, maxRegionMin.z));
            DrawWorldLine(new Vector3(maxRegionMin.x, maxRegionMin.y, maxRegionMin.z), new Vector3(maxRegionMin.x, maxRegionMax.y, maxRegionMin.z));
            DrawWorldLine(new Vector3(maxRegionMin.x, maxRegionMin.y, maxRegionMin.z), new Vector3(maxRegionMin.x, maxRegionMin.y, maxRegionMax.z));

            DrawWorldLine(new Vector3(maxRegionMin.x, maxRegionMax.y, maxRegionMin.z), new Vector3(maxRegionMax.x, maxRegionMax.y, maxRegionMin.z));
            DrawWorldLine(new Vector3(maxRegionMax.x, maxRegionMin.y, maxRegionMin.z), new Vector3(maxRegionMax.x, maxRegionMax.y, maxRegionMin.z));
            DrawWorldLine(new Vector3(maxRegionMax.x, maxRegionMin.y, maxRegionMin.z), new Vector3(maxRegionMax.x, maxRegionMin.y, maxRegionMax.z));

            DrawWorldLine(new Vector3(maxRegionMin.x, maxRegionMin.y, maxRegionMax.z), new Vector3(maxRegionMax.x, maxRegionMin.y, maxRegionMax.z));
            DrawWorldLine(new Vector3(maxRegionMin.x, maxRegionMin.y, maxRegionMax.z), new Vector3(maxRegionMin.x, maxRegionMax.y, maxRegionMax.z));
            DrawWorldLine(new Vector3(maxRegionMin.x, maxRegionMax.y, maxRegionMin.z), new Vector3(maxRegionMin.x, maxRegionMax.y, maxRegionMax.z));

            DrawWorldLine(new Vector3(maxRegionMin.x, maxRegionMax.y, maxRegionMax.z), new Vector3(maxRegionMax.x, maxRegionMax.y, maxRegionMax.z));
            DrawWorldLine(new Vector3(maxRegionMax.x, maxRegionMin.y, maxRegionMax.z), new Vector3(maxRegionMax.x, maxRegionMax.y, maxRegionMax.z));
            DrawWorldLine(new Vector3(maxRegionMax.x, maxRegionMax.y, maxRegionMin.z), new Vector3(maxRegionMax.x, maxRegionMax.y, maxRegionMax.z));

            Gizmos.color = Color.green;

            DrawWorldLine(new Vector3(targetRegionMin.x, targetRegionMin.y, targetRegionMin.z), new Vector3(targetRegionMax.x, targetRegionMin.y, targetRegionMin.z));
            DrawWorldLine(new Vector3(targetRegionMin.x, targetRegionMin.y, targetRegionMin.z), new Vector3(targetRegionMin.x, targetRegionMax.y, targetRegionMin.z));
            DrawWorldLine(new Vector3(targetRegionMin.x, targetRegionMin.y, targetRegionMin.z), new Vector3(targetRegionMin.x, targetRegionMin.y, targetRegionMax.z));

            DrawWorldLine(new Vector3(targetRegionMin.x, targetRegionMax.y, targetRegionMin.z), new Vector3(targetRegionMax.x, targetRegionMax.y, targetRegionMin.z));
            DrawWorldLine(new Vector3(targetRegionMax.x, targetRegionMin.y, targetRegionMin.z), new Vector3(targetRegionMax.x, targetRegionMax.y, targetRegionMin.z));
            DrawWorldLine(new Vector3(targetRegionMax.x, targetRegionMin.y, targetRegionMin.z), new Vector3(targetRegionMax.x, targetRegionMin.y, targetRegionMax.z));

            DrawWorldLine(new Vector3(targetRegionMin.x, targetRegionMin.y, targetRegionMax.z), new Vector3(targetRegionMax.x, targetRegionMin.y, targetRegionMax.z));
            DrawWorldLine(new Vector3(targetRegionMin.x, targetRegionMin.y, targetRegionMax.z), new Vector3(targetRegionMin.x, targetRegionMax.y, targetRegionMax.z));
            DrawWorldLine(new Vector3(targetRegionMin.x, targetRegionMax.y, targetRegionMin.z), new Vector3(targetRegionMin.x, targetRegionMax.y, targetRegionMax.z));

            DrawWorldLine(new Vector3(targetRegionMin.x, targetRegionMax.y, targetRegionMax.z), new Vector3(targetRegionMax.x, targetRegionMax.y, targetRegionMax.z));
            DrawWorldLine(new Vector3(targetRegionMax.x, targetRegionMin.y, targetRegionMax.z), new Vector3(targetRegionMax.x, targetRegionMax.y, targetRegionMax.z));
            DrawWorldLine(new Vector3(targetRegionMax.x, targetRegionMax.y, targetRegionMin.z), new Vector3(targetRegionMax.x, targetRegionMax.y, targetRegionMax.z));
        }

        private void DrawWorldLine(Vector3 fromViewport, Vector3 toViewport)
        {
            Gizmos.DrawLine(targetCamera.ViewportToWorldPoint(fromViewport), targetCamera.ViewportToWorldPoint(toViewport));
        }

        private void LateUpdate()
        {
            if (targetCamera == null)
                return;

            var viewportPoint = targetCamera.WorldToViewportPoint(transform.position);

            if (!_repositioning)
            {
                var maxBounds = new Bounds()
                {
                    min = targetRegionMin - new Vector3(paddingLeft, paddingBottom, paddingBack),
                    max = targetRegionMax + new Vector3(paddingRight, paddingTop, paddingFront)
                };

                if (maxBounds.Contains(viewportPoint))
                    return;

                _repositioning = true;
            }

            if (_repositioning)
            {
                var targetBounds = new Bounds()
                {
                    min = targetRegionMin,
                    max = targetRegionMax
                };

                bool positionArrived = false;
                bool rotationArrived = false;

                var targetPoint = targetCamera.ViewportToWorldPoint(targetBounds.ClosestPoint(viewportPoint));
                transform.position = Vector3.Lerp(transform.position, targetPoint, Time.deltaTime * moveRate);
                positionArrived = (transform.position - targetPoint).sqrMagnitude <= (0.001f * 0.001f);

                if (lookAtCamera)
                {
                    var lookRotation = Quaternion.LookRotation(targetCamera.transform.position - targetPoint, Vector3.up);
                    transform.rotation = Quaternion.Lerp(transform.rotation, lookRotation, Time.deltaTime * lookRate);
                    rotationArrived = Quaternion.Angle(lookRotation, transform.rotation) < 2f;
                }

                if (positionArrived && (rotationArrived || !lookAtCamera))
                    _repositioning = false;
            }
        }

        protected override void SetupInternal()
        {
            AddBinding(
                props.element.Subscribe(this),
                props.targetRegionMin?.Subscribe(x => targetRegionMin = x),
                props.targetRegionMax?.Subscribe(x => targetRegionMax = x),
                props.paddingFront?.Subscribe(x => paddingFront = x),
                props.paddingBack?.Subscribe(x => paddingBack = x),
                props.paddingLeft?.Subscribe(x => paddingLeft = x),
                props.paddingRight?.Subscribe(x => paddingRight = x),
                props.paddingTop?.Subscribe(x => paddingTop = x),
                props.paddingBottom?.Subscribe(x => paddingBottom = x),
                props.lookAtCamera?.Subscribe(x => lookAtCamera = x),
                props.moveRate?.Subscribe(x => moveRate = x),
                props.moveRate?.Subscribe(x => lookRate = x),
                props.children?.SubscribeAsChildren(transform),
                props.targetCamera?.Subscribe(x =>
                {
                    targetCamera = x;
                    Recenter();
                })
            );
        }

        private void Recenter()
        {
            var targetBounds = new Bounds()
            {
                min = targetRegionMin,
                max = targetRegionMax
            };

            transform.position = targetCamera.ViewportToWorldPoint(targetBounds.center);

            if (lookAtCamera)
                transform.LookAt(targetCamera.transform);
        }
    }
}