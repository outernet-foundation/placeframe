using System;
using System.Collections.Generic;

namespace ObserveThing
{
    public class ValueObservable<T> : IValueObservable<T>
    {
        public T value
        {
            get => _value;
            private set
            {
                if (Equals(_value, value))
                    return;

                _args.previousValue = _value;
                _value = value;
                _args.currentValue = value;

                foreach (var instance in _instances)
                    instance.OnNext(_args);
            }
        }

        private T _value = default;
        private ValueEventArgs<T> _args = new ValueEventArgs<T>();
        private List<Instance> _instances = new List<Instance>();
        private bool _disposed;
        private IDisposable _fromSubscription;

        public ValueObservable() : this(default) { }
        public ValueObservable(T startValue)
        {
            _value = startValue;
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _fromSubscription?.Dispose();

            _disposed = true;

            foreach (var instance in _instances)
                instance.Dispose();

            _instances.Clear();
        }

        public void From(T source)
        {
            _fromSubscription?.Dispose();
            value = source;
        }

        public void From(IValueObservable<T> source)
        {
            _fromSubscription?.Dispose();
            _fromSubscription = source.Subscribe(x => value = x.currentValue);
        }

        public IDisposable Subscribe(IObserver<IValueEventArgs<T>> observer)
        {
            var instance = new Instance(observer, x =>
            {
                if (!_disposed)
                    _instances.Remove(x);
            });

            _instances.Add(instance);

            _args.previousValue = default;
            _args.currentValue = _value;

            instance.OnNext(_args);
            return instance;
        }

        private class Instance : IDisposable
        {
            private IObserver<IValueEventArgs<T>> _observer;
            private Action<Instance> _onDispose;

            public Instance(IObserver<IValueEventArgs<T>> observer, Action<Instance> onDispose)
            {
                _observer = observer;
                _onDispose = onDispose;
            }

            public void OnNext(IValueEventArgs<T> args)
            {
                _observer?.OnNext(args);
            }

            public void OnError(Exception error)
            {
                _observer?.OnError(error);
            }

            public void Dispose()
            {
                if (_observer == null)
                    return;

                _observer.OnDispose();
                _observer = null;

                _onDispose(this);
            }
        }
    }
}