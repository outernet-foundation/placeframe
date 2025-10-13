using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;

namespace ObserveThing
{
    public class DictionaryObservable<TKey, TValue> : IDictionaryObservable<TKey, TValue>, IEnumerable<KeyValuePair<TKey, TValue>>
    {
        IEnumerator<KeyValuePair<TKey, TValue>> IEnumerable<KeyValuePair<TKey, TValue>>.GetEnumerator() => _dictionary.GetEnumerator();
        IEnumerator IEnumerable.GetEnumerator() => _dictionary.GetEnumerator();

        private Dictionary<TKey, TValue> _dictionary = new Dictionary<TKey, TValue>();
        private DictionaryEventArgs<TKey, TValue> _args = new DictionaryEventArgs<TKey, TValue>();
        private List<Instance> _instances = new List<Instance>();
        private bool _disposed;
        private IDisposable _fromSubscription;

        public void Add(TKey key, TValue value)
        {
            _dictionary.Add(key, value);
            _args.element = new KeyValuePair<TKey, TValue>(key, value);
            _args.operationType = OpType.Add;
            foreach (var instance in _instances)
                instance.OnNext(_args);
        }

        public bool Remove(TKey key)
        {
            if (!_dictionary.TryGetValue(key, out var value))
                return false;

            _dictionary.Remove(key);
            _args.element = new KeyValuePair<TKey, TValue>(key, value);
            _args.operationType = OpType.Remove;
            foreach (var instance in _instances)
                instance.OnNext(_args);

            return true;
        }

        public void Clear()
        {
            foreach (var key in _dictionary.Keys.ToArray())
                Remove(key);
        }

        public void From(IEnumerable<KeyValuePair<TKey, TValue>> source)
        {
            _fromSubscription?.Dispose();
            Clear();

            foreach (var element in source)
                Add(element.Key, element.Value);
        }

        public void From(IDictionaryObservable<TKey, TValue> source)
        {
            _fromSubscription?.Dispose();
            _fromSubscription = source.Subscribe(
                x =>
                {
                    if (x.operationType == OpType.Add)
                        Add(x.key, x.value);
                    else if (x.operationType == OpType.Remove)
                        Remove(x.key);
                }
            );
        }

        public IDisposable Subscribe(IObserver<IDictionaryEventArgs<TKey, TValue>> observer)
        {
            var instance = new Instance(observer, x =>
            {
                if (!_disposed)
                    _instances.Remove(x);
            });

            _instances.Add(instance);

            foreach (var kvp in _dictionary)
            {
                _args.element = kvp;
                _args.operationType = OpType.Add;
                instance.OnNext(_args);
            }

            return instance;
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _disposed = true;

            foreach (var instance in _instances)
                instance.Dispose();

            _instances.Clear();
            _fromSubscription?.Dispose();
        }

        private class Instance : IDisposable
        {
            private IObserver<IDictionaryEventArgs<TKey, TValue>> _observer;
            private Action<Instance> _onDispose;

            public Instance(IObserver<IDictionaryEventArgs<TKey, TValue>> observer, Action<Instance> onDispose)
            {
                _observer = observer;
                _onDispose = onDispose;
            }

            public void OnNext(IDictionaryEventArgs<TKey, TValue> args)
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