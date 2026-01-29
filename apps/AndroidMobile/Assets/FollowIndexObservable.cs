using System.Collections.Generic;
using ObserveThing;

namespace Placeframe.Client
{
    public class FollowIndexObservable<T> : IValueObservable<int>
    {
        public IListObservable<T> list;
        public int index;

        public FollowIndexObservable(IListObservable<T> list, int index)
        {
            this.list = list;
            this.index = index;
        }

        public System.IDisposable Subscribe(IObserver<IValueEventArgs<int>> observer) =>
            new Instance(this, list, index, observer);

        private class Instance : System.IDisposable
        {
            private System.IDisposable _listStream;
            private int _index;
            private IObserver<IValueEventArgs<int>> _observer;
            private ValueEventArgs<int> _args = new ValueEventArgs<int>();
            private bool _disposed = false;

            public Instance(
                IObservable source,
                IListObservable<T> list,
                int index,
                IObserver<IValueEventArgs<int>> observer
            )
            {
                _index = index;
                _observer = observer;
                _args.source = source;
                _args.previousValue = -1;
                _args.currentValue = index;
                _listStream = list.Subscribe(HandleSourceChanged, HandleSourceError, HandleSourceDisposed);
            }

            private void HandleSourceChanged(IListEventArgs<T> args)
            {
                int newIndex = _args.currentValue;

                if (args.operationType == OpType.Add)
                {
                    if (args.index <= _args.currentValue)
                        newIndex = _args.currentValue + 1;
                }
                else if (args.operationType == OpType.Remove)
                {
                    if (args.index == _args.currentValue)
                    {
                        newIndex = -1;
                    }
                    else if (args.index < _args.currentValue)
                    {
                        newIndex = _args.previousValue - 1;
                    }
                }

                if (newIndex == _args.currentValue)
                    return;

                _args.previousValue = _args.currentValue;
                _args.currentValue = newIndex;

                _observer.OnNext(_args);
            }

            private void HandleSourceError(System.Exception error)
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

                _listStream.Dispose();
                _observer.OnDispose();
            }
        }
    }
}
