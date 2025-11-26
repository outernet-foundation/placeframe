using System;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX;
using UnityEngine;

namespace Outernet.MapRegistrationTool
{
    public interface ISmoother<T>
    {
        T currentValue { get; set; }
        T targetValue { get; set; }
        bool smoothing { get; }
        float speed { get; set; }
        void JumpToTarget();
        void JumpToTarget(T target);
    }

    public abstract class Smoother<T> : ISmoother<T>
    {
        public T currentValue
        {
            get => _currentValue;
            set
            {
                if (Equals(value, _currentValue))
                    return;

                _currentValue = value;

                if (!_applyingFromSmoother)
                    HandleShouldSmoothChanged();

                _apply.Invoke(value);

                if (Equals(_currentValue, _targetValue))
                    OnReachedTargetValue();
            }
        }

        public T targetValue
        {
            get => _targetValue;
            set
            {
                if (Equals(value, _targetValue))
                    return;

                _targetValue = value;
                HandleShouldSmoothChanged();

                if (Equals(_currentValue, _targetValue))
                    OnReachedTargetValue();
            }
        }

        public float speed
        {
            get => _speed;
            set
            {
                _speed = value;

                if (value <= 0)
                    JumpToTarget();
            }
        }

        public bool smoothing => !_smoothTask.complete;

        private T _currentValue;
        private T _targetValue;
        private float _speed;

        private Action<T> _apply;

        private bool _applyingFromSmoother;
        private TaskHandle _smoothTask = TaskHandle.Complete;

        public Smoother(Action<T> apply, float speed = 0f, T currentValue = default, T targetValue = default)
        {
            _apply = apply;
            _speed = speed;
            _currentValue = currentValue;
            _targetValue = targetValue;

            HandleShouldSmoothChanged();
        }

        private void HandleShouldSmoothChanged()
        {
            if (Equals(_currentValue, _targetValue))
            {
                if (!_smoothTask.complete)
                    _smoothTask.Cancel();

                return;
            }

            if (speed == 0)
            {
                currentValue = targetValue;
                return;
            }

            InitializeSmoothValues();

            if (_smoothTask.complete)
                _smoothTask = TaskHandle.Execute(SmoothApply);
        }

        protected virtual void InitializeSmoothValues() { }
        protected abstract T GetSmoothedValue();
        protected virtual void OnReachedTargetValue() { }

        private async UniTask SmoothApply(CancellationToken cancellationToken)
        {
            while (!Equals(currentValue, targetValue))
            {
                _applyingFromSmoother = true;
                currentValue = GetSmoothedValue();
                _applyingFromSmoother = false;
                await UniTask.WaitForEndOfFrame(cancellationToken);
            }
        }

        public void JumpToTarget()
        {
            currentValue = targetValue;
        }

        public void JumpToTarget(T target)
        {
            targetValue = target;
            currentValue = target;
        }
    }

    public static class Smooth
    {
        private delegate T MoveTowardsDelegate<T>(T currentValue, T targetValue, float maxDistanceDelta);

        private class MoveTowardsSmoother<T> : Smoother<T>
        {
            private MoveTowardsDelegate<T> _moveTowards;
            private Func<T, T, float> _getDeltaMagnitude;

            private float _maxDistanceDelta;

            public MoveTowardsSmoother(Action<T> apply, MoveTowardsDelegate<T> moveTowards, Func<T, T, float> getDeltaMagnitude, float speed = 0f, T currentValue = default, T targetValue = default)
                : base(apply, speed, currentValue, targetValue)
            {
                _moveTowards = moveTowards;
                _getDeltaMagnitude = getDeltaMagnitude;
            }

            protected override void InitializeSmoothValues()
            {
                _maxDistanceDelta = _getDeltaMagnitude(currentValue, targetValue) / speed;
            }

            protected override T GetSmoothedValue()
            {
                return _moveTowards(currentValue, targetValue, _maxDistanceDelta);
            }
        }

        private delegate T SmoothDampDelegate<T>(T currentValue, T targetValue, ref T velocity, float smoothTime);

        private class SmoothDampSmoother<T> : Smoother<T>
        {
            private SmoothDampDelegate<T> _smoothDamp;
            private Func<T, T, float> _getDeltaMagnitude;

            private float _smoothTime;
            private T _velocity = default;

            public SmoothDampSmoother(Action<T> apply, SmoothDampDelegate<T> smoothDamp, Func<T, T, float> getDeltaMagnitude, float speed = 0f, T currentValue = default, T targetValue = default)
                : base(apply, speed, currentValue, targetValue)
            {
                _smoothDamp = smoothDamp;
                _getDeltaMagnitude = getDeltaMagnitude;
            }

            protected override void InitializeSmoothValues()
            {
                _smoothTime = _getDeltaMagnitude(currentValue, targetValue) / speed;
            }

            protected override T GetSmoothedValue()
            {
                return _smoothDamp(currentValue, targetValue, ref _velocity, _smoothTime);
            }

            protected override void OnReachedTargetValue()
            {
                _velocity = default;
            }
        }

        public static ISmoother<float> MoveTowardsFloat(Action<float> apply, float speed = 0f, float currentValue = default, float targetValue = default)
            => new MoveTowardsSmoother<float>(apply, Mathf.MoveTowards, (x, y) => Mathf.Abs(x - y), speed, currentValue, targetValue);

        public static ISmoother<Vector2> MoveTowardsVector2(Action<Vector2> apply, float speed = 0f, Vector2 currentValue = default, Vector2 targetValue = default)
            => new MoveTowardsSmoother<Vector2>(apply, Vector2.MoveTowards, Vector2.Distance, speed, currentValue, targetValue);

        public static ISmoother<Vector3> MoveTowardsVector3(Action<Vector3> apply, float speed = 0f, Vector3 currentValue = default, Vector3 targetValue = default)
            => new MoveTowardsSmoother<Vector3>(apply, Vector3.MoveTowards, Vector3.Distance, speed, currentValue, targetValue);

        public static ISmoother<Quaternion> MoveTowardsQuaternion(Action<Quaternion> apply, float speed = 0f, Quaternion currentValue = default, Quaternion targetValue = default)
            => new MoveTowardsSmoother<Quaternion>(apply, Quaternion.RotateTowards, Quaternion.Angle, speed, currentValue, targetValue);

        public static ISmoother<float> SmoothDampFloat(Action<float> apply, float speed = 0f, float currentValue = default, float targetValue = default)
            => new SmoothDampSmoother<float>(apply, Mathf.SmoothDamp, (x, y) => Mathf.Abs(x - y), speed, currentValue, targetValue);

        public static ISmoother<Vector2> SmoothDampVector2(Action<Vector2> apply, float speed = 0f, Vector2 currentValue = default, Vector2 targetValue = default)
            => new SmoothDampSmoother<Vector2>(apply, Vector2.SmoothDamp, Vector2.Distance, speed, currentValue, targetValue);

        public static ISmoother<Vector3> SmoothDampVector3(Action<Vector3> apply, float speed = 0f, Vector3 currentValue = default, Vector3 targetValue = default)
            => new SmoothDampSmoother<Vector3>(apply, Vector3.SmoothDamp, Vector3.Distance, speed, currentValue, targetValue);
    }
}