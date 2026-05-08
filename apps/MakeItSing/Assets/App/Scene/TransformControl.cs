using System;
using FofX.Stateful;
using Nessle;
using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public struct TransformControlProps
    {
        public ElementProps element;
        public TransformProps transform;
        public IListObservable<IControl> children;
    }

    public struct TransformProps
    {
        public IValueObservable<Vector3> localPosition;
        public IValueObservable<Quaternion> localRotation;
        public IValueObservable<Vector3> localScale;
        public Action<Vector3> onLocalPositionChanged;
        public Action<Quaternion> onLocalRotationChanged;
        public Action<Vector3> onLocalScaleChanged;
    }

    public class TransformControl : Control<TransformControlProps>
    {
        private Vector3 _lastLocalPosition;
        private Quaternion _lastLocalRotation;
        private Vector3 _lastLocalScale;

        private void LateUpdate()
        {
            if (props.transform.onLocalPositionChanged != null && _lastLocalPosition != transform.localPosition)
            {
                _lastLocalPosition = transform.localPosition;
                props.transform.onLocalPositionChanged?.Invoke(_lastLocalPosition);
            }

            if (props.transform.onLocalRotationChanged != null && _lastLocalRotation != transform.localRotation)
            {
                _lastLocalRotation = transform.localRotation;
                props.transform.onLocalRotationChanged?.Invoke(_lastLocalRotation);
            }

            if (props.transform.onLocalScaleChanged != null && _lastLocalScale != transform.localScale)
            {
                _lastLocalScale = transform.localScale;
                props.transform.onLocalScaleChanged?.Invoke(_lastLocalScale);
            }
        }

        protected override void SetupInternal()
        {
            enabled =
                props.transform.onLocalPositionChanged != null ||
                props.transform.onLocalRotationChanged != null ||
                props.transform.onLocalScaleChanged != null;

            AddBinding(
                props.element.Subscribe(this),
                props.transform.localPosition?.Subscribe(x =>
                {
                    _lastLocalPosition = x;
                    transform.localPosition = x;
                }),
                props.transform.localRotation?.Subscribe(x =>
                {
                    _lastLocalRotation = x;
                    transform.localRotation = x;
                }),
                props.transform.localScale?.Subscribe(x =>
                {
                    _lastLocalScale = x;
                    transform.localScale = x;
                }),
                props.children?.SubscribeAsChildren(transform)
            );
        }
    }
}