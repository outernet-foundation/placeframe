using ObserveThing;

using FofX.Stateful;
using System;

using static Nessle.UIBuilder;
using static Nessle.Props;

namespace Plerion.MakeItSing
{
    public static class Extentions
    {
        public static ICollectionObservable<T> ObservableExcept<T>(this ICollectionObservable<T> source, ICollectionObservable<T> except)
            => source.ObservableWhere(x => except.ObservableContains(x).ObservableSelect(x => !x));

        public static IListObservable<T> ObservableExcept<T>(this IListObservable<T> source, ICollectionObservable<T> except)
            => source.ObservableWhere(x => except.ObservableContains(x).ObservableSelect(x => !x)).ObservableOrderBy(x => source.ObservableIndexOf(x));

        public static IListObservable<T> ObservableExcept<T>(this IListObservable<T> source, IListObservable<T> except)
            => source.ObservableWhere(x => except.ObservableContains(x).ObservableSelect(x => !x)).ObservableOrderBy(x => source.ObservableIndexOf(x));

        public static IValueObservable<int> ObservableCount<T>(this ICollectionObservable<T> source, Func<T, bool> predicate)
            => source.ObservableWhere(predicate).ObservableCount();

        public static IValueObservable<int> ObservableCount<T>(this ICollectionObservable<T> source, Func<T, IValueObservable<bool>> predicate)
            => source.ObservableWhere(predicate).ObservableCount();

        public static IListObservable<T> ObservableWhere<T>(this IListObservable<T> source, Func<T, IValueObservable<bool>> where)
            => ((ICollectionObservable<T>)source).ObservableWhere(where).ObservableOrderBy(x => source.ObservableIndexOf(x));

        public static IDictionaryObservable<TKey, TValue> ObservableToDictionary<T, TKey, TValue>(this ICollectionObservable<T> source, Func<T, IValueObservable<TKey>> selectKey, Func<T, TValue> selectValue)
            => new DictionaryOperator<TKey, TValue>(receiver => new ToDictionaryObservable<T, TKey, TValue>(source, selectKey, x => Value(selectValue(x)), receiver));

        public static IDictionaryObservable<TKey, TValue> ObservableToDictionary<T, TKey, TValue>(this ICollectionObservable<T> source, Func<T, TKey> selectKey, Func<T, IValueObservable<TValue>> selectValue)
            => new DictionaryOperator<TKey, TValue>(receiver => new ToDictionaryObservable<T, TKey, TValue>(source, x => Value(selectKey(x)), selectValue, receiver));

        public static IDictionaryObservable<TKey, TValue> ObservableToDictionary<T, TKey, TValue>(this ICollectionObservable<T> source, Func<T, TKey> selectKey, Func<T, TValue> selectValue)
            => new DictionaryOperator<TKey, TValue>(receiver => new ToDictionaryObservable<T, TKey, TValue>(source, x => Value(selectKey(x)), x => Value(selectValue(x)), receiver));

        public static IDictionaryObservable<TKey, TValue> ObservableToDictionary<T, TKey, TValue>(this ICollectionObservable<T> source, Func<T, IValueObservable<TKey>> selectKey, Func<T, IValueObservable<TValue>> selectValue)
            => new DictionaryOperator<TKey, TValue>(receiver => new ToDictionaryObservable<T, TKey, TValue>(source, selectKey, selectValue, receiver));

        public static ICollectionObservable<T> With<T>(this ICollectionObservable<T> source, params T[] with)
            => source.With(List(with));

        public static ICollectionObservable<T> With<T>(this ICollectionObservable<T> source, ICollectionObservable<T> with)
        {
            if (with == null)
                return source;

            if (source == null)
                return with;

            return source.ObservableConcat(with);
        }

        public static IValueObservable<int> ObservableIndexOf<T, U>(this IListObservable<T> source, Func<T, U> selector, U value)
            => source.ObservableIndexOf(x => Value(selector(x)), Value(value));

        public static IValueObservable<int> ObservableIndexOf<T, U>(this IListObservable<T> source, Func<T, IValueObservable<U>> selector, U value)
            => source.ObservableIndexOf(x => selector(x), Value(value));

        public static IValueObservable<int> ObservableIndexOf<T, U>(this IListObservable<T> source, Func<T, U> selector, IValueObservable<U> value)
            => source.ObservableIndexOf(x => Value(selector(x)), value);

        public static IValueObservable<int> ObservableIndexOf<T, U>(this IListObservable<T> source, Func<T, IValueObservable<U>> selector, IValueObservable<U> value)
            => source.ObservableIndexOf(source.ObservableFirstOrDefault(x => Observables.ObservableCombineValues(selector(x), value, (source, value) => Equals(source, value))));

        public static IValueObservable<int> ObservableIndexOf<T>(this IListObservable<T> source, Func<T, bool> validate)
            => source.ObservableIndexOf(source.ObservableFirstOrDefault(x => validate(x)));

        public static IValueObservable<int> ObservableIndexOf<T>(this IListObservable<T> source, Func<T, IValueObservable<bool>> validate)
            => source.ObservableIndexOf(source.ObservableFirstOrDefault(x => validate(x)));
    }
}