using System;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX;
using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class InterpolationObservable<T> : IDisposable
    {
        private float _interpolationRate;
        private AnimationCurve _curve;
        private T _targetValue;
        private T _currentValue;
        private Func<T, T, float> _calcDelta;
        private Func<T, T, float, T> _interpolate;
        private IValueObserver<T> _receiver;
        private IDisposable _subscriptions;
        private TaskHandle _interpolationTask = TaskHandle.Complete;
        private bool _initialized = false;
        private bool _disposed;

        public InterpolationObservable(IValueObservable<T> source, IValueObservable<float> interpolationRate, IValueObservable<AnimationCurve> curve, Func<T, T, float> calcDelta, Func<T, T, float, T> interpolate, IValueObserver<T> receiver)
        {
            _calcDelta = calcDelta;
            _interpolate = interpolate;
            _receiver = receiver;

            _subscriptions = new ComposedDisposable(
                source.Subscribe(UpdateTargetValue),
                interpolationRate.Subscribe(UpdateInterpolationRate),
                curve.Subscribe(UpdateCurve)
            );

            _initialized = true;
        }

        private void UpdateTargetValue(T value)
        {
            _targetValue = value;

            if (_interpolationRate < 0 || !_initialized)
            {
                _currentValue = _targetValue;
                _receiver.OnNext(_currentValue);
                return;
            }

            _interpolationTask.Cancel();
            _interpolationTask = TaskHandle.Execute(token => Interpolate(_currentValue, _targetValue, token));
        }

        private void UpdateInterpolationRate(float interpolationRate)
        {
            _interpolationRate = interpolationRate;

            if (_interpolationRate > 0 || !_initialized)
                return;

            if (_interpolationTask.pending)
                _interpolationTask.Cancel();

            _currentValue = _targetValue;
            _receiver.OnNext(_currentValue);
        }

        private void UpdateCurve(AnimationCurve curve)
        {
            _curve = curve ?? AnimationCurve.Linear(0, 0, 1, 1);
        }

        private async UniTask Interpolate(T startValue, T targetValue, CancellationToken token = default)
        {
            var elapsedTime = 0f;
            var duration = _calcDelta(startValue, targetValue);

            while (elapsedTime <= duration)
            {
                elapsedTime += Time.deltaTime * _interpolationRate;
                _currentValue = _interpolate(startValue, targetValue, _curve.Evaluate(elapsedTime / duration));
                _receiver.OnNext(_currentValue);

                await UniTask.Yield(PlayerLoopTiming.LastPostLateUpdate);

                if (token.IsCancellationRequested)
                    break;
            }

            if (token.IsCancellationRequested)
                return;

            _currentValue = _targetValue;
            _receiver.OnNext(_targetValue);
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _disposed = true;
            _subscriptions.Dispose();
            _interpolationTask.Cancel();
            _receiver.OnDispose();
        }
    }
}