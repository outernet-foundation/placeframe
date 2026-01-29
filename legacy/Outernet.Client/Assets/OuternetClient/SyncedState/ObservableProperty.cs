using System;
using System.Threading;
using R3;

namespace Outernet.Client
{
    public class ObservableProperty<T> : Observable<T>
    {
        private static void Set(object state)
        {
            var (property, value) = ((ReactiveProperty<T>, T))state;
            property.Value = value;
        }

        static readonly SendOrPostCallback setCallback = Set;

        private QueueSynchronizationContext context;
        private ReactiveProperty<T> property;
        public T Value => property.Value;

        public ObservableProperty(QueueSynchronizationContext context, T initialValue)
        {
            this.context = context;
            property = new ReactiveProperty<T>(initialValue);
        }

        public void EnqueueSet(T value)
            => context.Post(setCallback, (property, value));

        protected override IDisposable SubscribeCore(Observer<T> observer)
            => ObservableSubscribeExtensions.Subscribe(property.ObserveOn(context), observer.OnNext);

        public static implicit operator ReadOnlyReactiveProperty<T>(ObservableProperty<T> observableProperty)
            => observableProperty.property;
    }
}