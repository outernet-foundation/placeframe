using System;
using System.Collections.Generic;
using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class NetworkSmoothObservable<T> : IDisposable
    {
        private IValueObserver<T> _receiver;
        private IDisposable _subscription;
        private T _reserveValue = default;
        private bool _hasReserveValue = false;
        private ObservableValue<T> _targetValue;
        private InterpolationObservable<T> _internalObservable;
        private bool _initialized;
        private bool _interpolating;
        private bool _disposed;

        public NetworkSmoothObservable(IValueObservable<T> source, IValueObservable<float> interpolationRate, IValueObservable<AnimationCurve> curve, Func<T, T, float> calcDelta, Func<T, T, float, T> interpolate, IValueObserver<T> receiver)
        {
            _receiver = receiver;
            _targetValue = new ObservableValue<T>(source.Peek());

            _internalObservable = new InterpolationObservable<T>(
                _targetValue,
                interpolationRate,
                curve,
                calcDelta,
                interpolate,
                new ValueObserver<T>(
                    onNext: HandleInternalObservableChanged,
                    onError: receiver.OnError
                )
            );

            _subscription = source.Subscribe(
                onNext: HandleSourceChanged,
                onError: receiver.OnError,
                onDispose: Dispose
            );

            _initialized = true;
        }

        private void HandleInternalObservableChanged(T value)
        {
            _receiver.OnNext(value);

            if (Equals(value, _targetValue.value))
            {
                if (_hasReserveValue)
                {
                    _targetValue.value = _reserveValue;
                    _hasReserveValue = false;
                }
                else
                {
                    _interpolating = false;
                }
            }
        }

        private void HandleSourceChanged(T value)
        {
            if (!_initialized)
                return;

            if (!_interpolating)
            {
                _targetValue.value = value;
                _interpolating = true;
            }
            else if (!_hasReserveValue)
            {
                _reserveValue = value;
                _hasReserveValue = true;
            }
            else
            {
                _targetValue.value = _reserveValue;
                _reserveValue = value;
            }
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _disposed = true;
            _subscription.Dispose();
            _targetValue.Dispose();
            _internalObservable.Dispose();
            _receiver.OnDispose();
        }
    }
}