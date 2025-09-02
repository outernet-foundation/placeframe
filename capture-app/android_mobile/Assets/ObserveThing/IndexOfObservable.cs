using System;

namespace ObserveThing
{
    public class IndexOfObservable<T> : IValueObservable<int>
    {
        public IListObservable<T> source;
        public T indexOf;

        public IndexOfObservable(IListObservable<T> source, T indexOf)
        {
            this.source = source;
            this.indexOf = indexOf;
        }

        public IDisposable Subscribe(IObserver<IValueEventArgs<int>> observer)
            => new Instance(source, indexOf, observer);

        private class Instance : IDisposable
        {
            private IDisposable _source;
            private T _indexOf;
            private IObserver<IValueEventArgs<int>> _observer;
            private ValueEventArgs<int> _args = new ValueEventArgs<int>();
            private bool _disposed = false;

            public Instance(IListObservable<T> source, T indexOf, IObserver<IValueEventArgs<int>> observer)
            {
                _indexOf = indexOf;
                _observer = observer;
                _args.previousValue = -1;
                _args.currentValue = -1;
                _source = source.Subscribe(HandleSourceChanged, HandleSourceError, HandleSourceDisposed);
            }

            private void HandleSourceChanged(IListEventArgs<T> args)
            {
                if (Equals(args.element, _indexOf))
                {
                    if (args.operationType == OpType.Add)
                    {
                        _args.previousValue = _args.currentValue;
                        _args.currentValue = args.index;
                        _observer.OnNext(_args);
                    }
                    else
                    {
                        _args.previousValue = _args.currentValue;
                        _args.currentValue = -1;
                        _observer.OnNext(_args);
                    }

                    return;
                }

                if (args.index > _args.currentValue)
                    return;

                _args.previousValue = _args.currentValue;
                _args.currentValue = _args.currentValue++;
            }

            private void HandleSourceError(Exception error)
            {
                _observer.OnError(error);
            }

            private void HandleSourceDisposed()
            {
                Dispose();
            }

            public void Dispose()
            {
                if (_disposed)
                    return;

                _disposed = true;

                _source.Dispose();
                _observer.OnDispose();
            }
        }
    }
}