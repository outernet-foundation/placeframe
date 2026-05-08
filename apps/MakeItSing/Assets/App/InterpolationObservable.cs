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
        private T _targetValue;
        private T _currentValue;
        private Func<T, T, bool> _checkInterpolationComplete;
        private Func<T, T, float, T> _interpolate;
        private IValueObserver<T> _receiver;
        private IDisposable _subscriptions;
        private TaskHandle _interpolationTask = TaskHandle.Complete;
        private bool _initialized = false;
        private bool _disposed;

        public InterpolationObservable(IValueObservable<T> source, IValueObservable<float> interpolationRate, Func<T, T, bool> checkInterpolationComplete, Func<T, T, float, T> interpolate, IValueObserver<T> receiver)
        {
            _checkInterpolationComplete = checkInterpolationComplete;
            _interpolate = interpolate;
            _receiver = receiver;

            _subscriptions = new ComposedDisposable(
                source.Subscribe(UpdateTargetValue),
                interpolationRate.Subscribe(UpdateInterpolationRate)
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

            if (_interpolationTask.pending || !_initialized)
                return;

            _interpolationTask = TaskHandle.Execute(Interpolate);
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

        private async UniTask Interpolate(CancellationToken token = default)
        {
            float elapsedTime = 0;

            while (!_checkInterpolationComplete(_currentValue, _targetValue))
            {
                elapsedTime += Time.deltaTime * _interpolationRate;
                _currentValue = _interpolate(_currentValue, _targetValue, elapsedTime);
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