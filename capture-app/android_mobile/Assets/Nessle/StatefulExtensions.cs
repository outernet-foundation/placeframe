using ObserveThing;
using UnityEngine;
using FofX.Stateful;
using System;

namespace Nessle
{
    public static class StatefulExtensions
    {
        public static TControl BindValue<TControl, TView, TState>(this TControl valueObservable, ObservablePrimitive<TState> primitive, Func<TView, TState> toState, Func<TState, TView> toView)
            where TControl : IValueControl<TView>
        {
            return valueObservable
                .OnChange((TView x) => primitive.ExecuteSetOrDelay(toState(x)))
                .Value(primitive.SelectDynamic(x => toView(x)));
        }

        public static TControl BindValue<TControl, TValue>(this TControl valueObservable, ObservablePrimitive<TValue> primitive)
            where TControl : IValueControl<TValue>
        {
            return valueObservable
                .OnChange((TValue x) => primitive.ExecuteSetOrDelay(x))
                .Value(primitive.AsObservable());
        }
    }
}