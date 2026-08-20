using System;
using System.Threading;
using Cysharp.Threading.Tasks;

namespace R3
{
    static public class EventStream
    {
        public static Observable<(T1, T2)> CombineLatest<T1, T2>(Observable<T1> source1, Observable<T2> source2)
            => Observable.CombineLatest(source1, source2, (item1, item2) => (item1, item2));

        public static Observable<(T1, T2, T3)> CombineLatest<T1, T2, T3>(Observable<T1> source1, Observable<T2> source2, Observable<T3> source3)
            => Observable.CombineLatest(source1, source2, source3, (item1, item2, item3) => (item1, item2, item3));

        public static Observable<(T1, T2, T3, T4)> CombineLatest<T1, T2, T3, T4>(Observable<T1> source1, Observable<T2> source2, Observable<T3> source3, Observable<T4> source4)
            => Observable.CombineLatest(source1, source2, source3, source4, (item1, item2, item3, item4) => (item1, item2, item3, item4));

        public static IDisposable Subscribe<T>(this Observable<T> source, Action onNext)
            => ObservableSubscribeExtensions.Subscribe(source, (_) => onNext());

        public static IDisposable SubscribeAwait<T>(this Observable<T> source, Func<CancellationToken, UniTask> onNextAsync)
            => source.SubscribeAwait((_, cancellationToken) => onNextAsync(cancellationToken));

        public static IDisposable SubscribeAwait<T>(this Observable<T> source, Func<CancellationToken, UniTask> onNextAsync, Action<Exception> onErrorResume)
            => source.SubscribeAwait((_, cancellationToken) => onNextAsync(cancellationToken), onErrorResume, _ => { });

        public static IDisposable SubscribeCancellable<T>(this Observable<T> source, Func<CancellationTokenSource, UniTask> onNextAsync, Action<Exception> onErrorResume)
        {
            return source.SubscribeAwait(
                async (cancellationToken) =>
                {
                    var cancellationTokenSource = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);

                    try
                    {
                        await onNextAsync(cancellationTokenSource);
                    }
                    finally
                    {
                        cancellationTokenSource.Dispose();
                    }
                },
                onErrorResume
            );
        }
    }
}