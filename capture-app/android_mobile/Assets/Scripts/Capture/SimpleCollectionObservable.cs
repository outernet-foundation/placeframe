using System.Collections;
using System.Collections.Generic;
using ObserveThing;

namespace PlerionClient.Client
{
    public class CollectionObservable<T> : ICollectionObservable<T>, IEnumerable<T>, System.IDisposable
    {
        public int count => _collection.Count;

        public IEnumerator<T> GetEnumerator() => _collection.GetEnumerator();
        IEnumerator IEnumerable.GetEnumerator() => _collection.GetEnumerator();

        private List<T> _collection = new List<T>();
        private CollectionEventArgs<T> _args = new CollectionEventArgs<T>();
        private List<Instance> _instances = new List<Instance>();
        private bool _disposed;

        public CollectionObservable() { }
        public CollectionObservable(IEnumerable<T> values)
        {
            _collection.AddRange(values);
        }

        public bool Contains(T element)
        {
            if (_disposed)
                throw new System.ObjectDisposedException(nameof(CollectionObservable<T>));

            return _collection.Contains(element);
        }

        public void Clear()
        {
            if (_disposed)
                throw new System.ObjectDisposedException(nameof(CollectionObservable<T>));

            foreach (var element in _collection.ToArray())
                Remove(element);
        }

        public void Add(T added)
        {
            if (_disposed)
                throw new System.ObjectDisposedException(nameof(CollectionObservable<T>));

            _collection.Add(added);
            _args.element = added;
            _args.operationType = OpType.Add;
            foreach (var instance in _instances)
                instance.OnNext(_args);
        }

        public void Remove(T removed)
        {
            if (_disposed)
                throw new System.ObjectDisposedException(nameof(CollectionObservable<T>));

            if (!_collection.Remove(removed))
                return;

            _args.element = removed;
            _args.operationType = OpType.Remove;
            foreach (var instance in _instances)
                instance.OnNext(_args);
        }

        public void Dispose()
        {
            if (_disposed)
                throw new System.ObjectDisposedException(nameof(CollectionObservable<T>));

            _disposed = true;

            foreach (var instance in _instances)
                instance.Dispose();

            _instances.Clear();
        }

        public System.IDisposable Subscribe(IObserver<ICollectionEventArgs<T>> observer)
        {
            if (_disposed)
                throw new System.ObjectDisposedException(nameof(CollectionObservable<T>));

            var instance = new Instance(observer, x =>
            {
                if (!_disposed)
                    _instances.Remove(x);
            });

            _instances.Add(instance);

            foreach (var kvp in _collection)
            {
                _args.element = kvp;
                _args.operationType = OpType.Add;
                instance.OnNext(_args);
            }

            return instance;
        }

        private class Instance : System.IDisposable
        {
            private IObserver<ICollectionEventArgs<T>> _observer;
            private System.Action<Instance> _onDispose;

            public Instance(IObserver<ICollectionEventArgs<T>> observer, System.Action<Instance> onDispose)
            {
                _observer = observer;
                _onDispose = onDispose;
            }

            public void OnNext(ICollectionEventArgs<T> args)
            {
                _observer?.OnNext(args);
            }

            public void OnError(System.Exception error)
            {
                _observer?.OnError(error);
            }

            public void Dispose()
            {
                if (_observer == null)
                    throw new System.Exception("ALREADY DISPOSED");

                _observer.OnDispose();
                _observer = null;

                _onDispose(this);
            }
        }
    }
}
