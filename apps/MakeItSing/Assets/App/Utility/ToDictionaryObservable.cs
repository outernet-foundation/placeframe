using System;
using System.Collections.Generic;
using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class ToDictionaryObservable<T, TKey, TValue> : IDisposable
    {
        private IDisposable _subscription;
        private IDictionaryObserver<TKey, TValue> _receiver;
        private bool _disposed;

        public ToDictionaryObservable(ICollectionObservable<T> source, Func<T, IValueObservable<TKey>> selectKey, Func<T, IValueObservable<TValue>> selectValue, IDictionaryObserver<TKey, TValue> receiver)
        {
            _receiver = receiver;
            _subscription = source.ObservableSelect(
                x => Observables.ObservableCombineValues(
                    selectKey(x),
                    selectValue(x),
                    (key, value) => new KeyValuePair<TKey, TValue>(key, value)
                )
            ).SubscribeWithId(
                onAdd: _receiver.OnAdd,
                onRemove: _receiver.OnRemove,
                onError: receiver.OnError,
                onDispose: Dispose
            );
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _disposed = true;

            _subscription.Dispose();

            _receiver.OnDispose();
        }
    }
}