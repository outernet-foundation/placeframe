using System.Collections.Generic;

using static Nessle.UIBuilder;
using ObserveThing;
using System;
using FofX.Stateful;

namespace Nessle
{
    public static class DropdownExtensions
    {
        public static T BindValue<T>(this T control, ObservablePrimitive<int> bindTo)
            where T : IControl<DropdownProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.value.From(x.currentValue)),
                control.props.value.Subscribe(x => bindTo.ExecuteSetOrDelay(x.currentValue))
            );

            return control;
        }

        public static TControl BindValue<TControl, TValue>(this TControl control, ObservablePrimitive<TValue> bindTo, Func<int, TValue> toState, Func<TValue, int> toControl)
            where TControl : IControl<DropdownProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.value.From(toControl(x.currentValue))),
                control.props.value.Subscribe(x => bindTo.ExecuteSetOrDelay(toState(x.currentValue)))
            );

            return control;
        }
    }
}