using System;
using System.Collections.Generic;

namespace ObserveThing
{
    public interface IValueObservable<T>
    {
        IDisposable Subscribe(IObserver<IValueEventArgs<T>> observer);
    }

    public interface IValueEventArgs<T>
    {
        T currentValue { get; }
        T previousValue { get; }
    }

    public class ValueEventArgs<T> : IValueEventArgs<T>
    {
        public T currentValue { get; set; }
        public T previousValue { get; set; }
    }

    public enum OpType
    {
        Add,
        Remove
    }

    public interface ICollectionObservable<out T>
    {
        IDisposable Subscribe(IObserver<ICollectionEventArgs<T>> observer);
    }

    public interface ICollectionEventArgs<out T>
    {
        T element { get; }
        OpType operationType { get; }
    }

    public class CollectionEventArgs<T> : ICollectionEventArgs<T>
    {
        public T element { get; set; }
        public OpType operationType { get; set; }
    }

    public interface IDictionaryObservable<TKey, TValue> : ICollectionObservable<KeyValuePair<TKey, TValue>>
    {
        IDisposable Subscribe(IObserver<IDictionaryEventArgs<TKey, TValue>> observer);

        IDisposable ICollectionObservable<KeyValuePair<TKey, TValue>>.Subscribe(IObserver<ICollectionEventArgs<KeyValuePair<TKey, TValue>>> observer)
            => Subscribe(observer);
    }

    public interface IDictionaryEventArgs<TKey, TValue> : ICollectionEventArgs<KeyValuePair<TKey, TValue>>
    {
        TKey key { get; }
        TValue value { get; }
    }

    public class DictionaryEventArgs<TKey, TValue> : IDictionaryEventArgs<TKey, TValue>
    {
        public TKey key => element.Key;
        public TValue value => element.Value;
        public KeyValuePair<TKey, TValue> element { get; set; }
        public OpType operationType { set; get; }
    }

    public interface IListObservable<out T> : ICollectionObservable<T>
    {
        IDisposable Subscribe(IObserver<IListEventArgs<T>> observer);

        IDisposable ICollectionObservable<T>.Subscribe(IObserver<ICollectionEventArgs<T>> observer)
            => Subscribe(observer);
    }

    public interface IListEventArgs<out T> : ICollectionEventArgs<T>
    {
        int index { get; }
    }

    public class ListEventArgs<T> : IListEventArgs<T>
    {
        public int index { get; set; }
        public T element { get; set; }
        public OpType operationType { get; set; }
    }

    public static class Observables
    {
        public static IValueObservable<TResult> Combine<T1, T2, TResult>(IValueObservable<T1> v1, IValueObservable<T2> v2, Func<T1, T2, TResult> combine)
            => v1.SelectDynamic(x1 => v2.SelectDynamic(x2 => combine(x1, x2)));

        public static IValueObservable<TResult> Combine<T1, T2, T3, TResult>(IValueObservable<T1> v1, IValueObservable<T2> v2, IValueObservable<T3> v3, Func<T1, T2, T3, TResult> combine)
            => v1.SelectDynamic(x1 => v2.SelectDynamic(x2 => v3.SelectDynamic(x3 => combine(x1, x2, x3))));

        public static IValueObservable<TResult> Combine<T1, T2, T3, T4, TResult>(IValueObservable<T1> v1, IValueObservable<T2> v2, IValueObservable<T3> v3, IValueObservable<T4> v4, Func<T1, T2, T3, T4, TResult> combine)
            => v1.SelectDynamic(x1 => v2.SelectDynamic(x2 => v3.SelectDynamic(x3 => v4.SelectDynamic(x4 => combine(x1, x2, x3, x4)))));
    }

    public static class ObservableExtensions
    {
        public static IValueObservable<U> SelectDynamic<T, U>(this IValueObservable<T> source, Func<T, U> select)
            => new SelectValueObservable<T, U>(source, select);

        public static IValueObservable<U> SelectDynamic<T, U>(this IValueObservable<T> source, Func<T, IValueObservable<U>> select)
            => new SelectValueObservableReactive<T, U>(source, select);

        public static IValueObservable<U> CreateDynamic<T, U>(this IValueObservable<T> source, Func<T, U> select)
            where U : IDisposable => new CreateValueObservable<T, U>(source, select);

        public static IValueObservable<U> CreateDynamic<T, U>(this IValueObservable<T> source, Func<T, IValueObservable<U>> select)
            where U : IDisposable => new CreateValueObservableReactive<T, U>(source, select);

        public static ICollectionObservable<U> SelectDynamic<T, U>(this ICollectionObservable<T> source, Func<T, U> select)
            => new SelectCollectionObservable<T, U>(source, select);

        public static ICollectionObservable<U> SelectDynamic<T, U>(this ICollectionObservable<T> source, Func<T, IValueObservable<U>> select)
            => new SelectCollectionObservableReactive<T, U>(source, select);

        public static ICollectionObservable<U> CreateDynamic<T, U>(this ICollectionObservable<T> source, Func<T, U> select)
            where U : IDisposable => new CreateCollectionObservable<T, U>(source, select);

        public static ICollectionObservable<U> CreateDynamic<T, U>(this ICollectionObservable<T> source, Func<T, IValueObservable<U>> select)
            where U : IDisposable => new CreateCollectionObservableReactive<T, U>(source, select);

        public static ICollectionObservable<T> WhereDynamic<T>(this ICollectionObservable<T> source, Func<T, bool> where)
            => new WhereCollectionObservable<T>(source, where);

        public static ICollectionObservable<T> WhereDynamic<T>(this ICollectionObservable<T> source, Func<T, IValueObservable<bool>> where)
            => new WhereCollectionObservableReactive<T>(source, where);

        public static ICollectionObservable<T> ConcatDynamic<T>(this ICollectionObservable<T> source1, IEnumerable<T> source2)
            => new ConcatCollectionObservable<T>(source1, source2);

        public static ICollectionObservable<T> ConcatDynamic<T>(this ICollectionObservable<T> source1, ICollectionObservable<T> source2)
            => new ConcatCollectionObservableReactive<T>(source1, source2);

        public static ICollectionObservable<U> SelectManyDynamic<T, U>(this ICollectionObservable<T> source, Func<T, IEnumerable<U>> selectMany)
            => new SelectManyCollectionObservable<T, U>(source, selectMany);

        public static ICollectionObservable<U> SelectManyDynamic<T, U>(this ICollectionObservable<T> source, Func<T, ICollectionObservable<U>> selectMany)
            => new SelectManyCollectionObservableReactive<T, U>(source, selectMany);

        public static ICollectionObservable<T> DistinctDynamic<T>(this ICollectionObservable<T> source)
            => new DistinctCollectionObservable<T>(source);

        public static IValueObservable<int> CountDynamic<T>(this ICollectionObservable<T> source)
            => new CountCollectionObservable<T>(source);

        public static IValueObservable<(T1 value1, T2 value2)> WithDynamic<T1, T2>(this IValueObservable<T1> source1, IValueObservable<T2> source2)
            => new WithValueObservable<T1, T2>(source1, source2);

        public static IValueObservable<(bool keyPresent, TValue value)> TrackDynamic<TKey, TValue>(this IDictionaryObservable<TKey, TValue> source, TKey key)
            => new TrackValueObservable<TKey, TValue>(source, key);

        public static IValueObservable<(bool keyPresent, TValue value)> TrackDynamic<TKey, TValue>(this IDictionaryObservable<TKey, TValue> source, IValueObservable<TKey> key)
            => new TrackValueObservableReactive<TKey, TValue>(source, key);

        public static ICollectionObservable<TValue> TrackDynamic<TKey, TValue>(this IDictionaryObservable<TKey, TValue> source, ICollectionObservable<TKey> keys)
            => keys.SelectDynamic(x => source.TrackDynamic(x)).WhereDynamic(x => x.keyPresent).SelectDynamic(x => x.value);

        public static IListObservable<T> OrderByDynamic<T, U>(this ICollectionObservable<T> source, Func<T, U> orderBy)
            => new OrderByCollectionObservable<T, U>(source, orderBy);

        public static IListObservable<T> OrderByDynamic<T, U>(this ICollectionObservable<T> source, Func<T, IValueObservable<U>> orderBy)
            => new OrderByCollectionObservableReactive<T, U>(source, orderBy);

        public static IValueObservable<bool> ContainsDynamic<T>(this ICollectionObservable<T> source, T contains)
            => new ContainsCollectionObservable<T>(source, contains);

        public static IValueObservable<bool> ContainsDynamic<T>(this ICollectionObservable<T> source, IValueObservable<T> contains)
            => new ContainsCollectionObservableReactive<T>(source, contains);

        public static IValueObservable<int> IndexOfDynamic<T>(this IListObservable<T> source, T value)
            => new IndexOfObservable<T>(source, value);

        public static IDisposable Subscribe<T>(this IValueObservable<T> source, Action<IValueEventArgs<T>> observer = default, Action<Exception> onError = default, Action onDispose = default)
            => source.Subscribe(new Observer<IValueEventArgs<T>>() { onNext = observer, onError = onError, onDispose = onDispose });

        public static IDisposable Subscribe<T>(this ICollectionObservable<T> source, Action<ICollectionEventArgs<T>> observer = default, Action<Exception> onError = default, Action onDispose = default)
            => source.Subscribe(new Observer<ICollectionEventArgs<T>>() { onNext = observer, onError = onError, onDispose = onDispose });

        public static IDisposable Subscribe<T>(this IListObservable<T> source, Action<IListEventArgs<T>> observer = default, Action<Exception> onError = default, Action onDispose = default)
            => source.Subscribe(new Observer<IListEventArgs<T>>() { onNext = observer, onError = onError, onDispose = onDispose });

        public static IDisposable Subscribe<TKey, TValue>(this IDictionaryObservable<TKey, TValue> source, Action<IDictionaryEventArgs<TKey, TValue>> observer = default, Action<Exception> onError = default, Action onDispose = default)
            => source.Subscribe(new Observer<IDictionaryEventArgs<TKey, TValue>>() { onNext = observer, onError = onError, onDispose = onDispose });

        public static IValueObservable<T> AsObservable<T>(this IValueObservable<T> observable)
            => observable;

        public static ICollectionObservable<T> AsObservable<T>(this ICollectionObservable<T> observable)
            => observable;

        public static IListObservable<T> AsObservable<T>(this IListObservable<T> observable)
            => observable;

        public static IDictionaryObservable<TKey, TValue> AsObservable<TKey, TValue>(this IDictionaryObservable<TKey, TValue> observable)
            => observable;

        public static T Peek<T>(this IValueObservable<T> source)
        {
            T result = default;
            source.Subscribe(x => result = x.currentValue).Dispose();
            return result;
        }
    }

    public class Disposable : IDisposable
    {
        private bool _disposed;
        private Action _onDispose;

        public Disposable(Action onDispose)
        {
            _onDispose = onDispose;
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _disposed = true;
            _onDispose?.Invoke();
        }
    }

    public class ComposedDisposable : IDisposable
    {
        private bool _disposed;
        private IDisposable[] _disposables;

        public ComposedDisposable(params IDisposable[] disposables)
        {
            _disposables = disposables;
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _disposed = true;

            foreach (var disposable in _disposables)
                disposable?.Dispose();
        }
    }
}