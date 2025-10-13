using System;
using ObserveThing;
using FofX.Stateful;
using UnityEngine;
using static Nessle.UIBuilder;

namespace Nessle
{
    public static class ScrollRectExtensions
    {
        public static T BindValue<T>(this T control, ObservablePrimitive<Vector2> bindTo)
            where T : IControl<ScrollRectProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.value.From(x.currentValue)),
                control.props.value.Subscribe(x => bindTo.ExecuteSetOrDelay(x.currentValue))
            );

            return control;
        }

        public static TControl BindValue<TControl, TValue>(this TControl control, ObservablePrimitive<TValue> bindTo, Func<Vector2, TValue> toState, Func<TValue, Vector2> toControl)
            where TControl : IControl<ScrollRectProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.value.From(toControl(x.currentValue))),
                control.props.value.Subscribe(x => bindTo.ExecuteSetOrDelay(toState(x.currentValue)))
            );

            return control;
        }
    }
}