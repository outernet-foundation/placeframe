using System;
using ObserveThing;
using FofX.Stateful;
using static Nessle.UIBuilder;

namespace Nessle
{
    public static class ToggleExtensions
    {
        public static T BindValue<T>(this T control, ObservablePrimitive<bool> bindTo)
            where T : IControl<ToggleProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.isOn.From(x.currentValue)),
                control.props.isOn.Subscribe(x => bindTo.ExecuteSetOrDelay(x.currentValue))
            );

            return control;
        }

        public static TControl BindValue<TControl, TValue>(this TControl control, ObservablePrimitive<TValue> bindTo, Func<bool, TValue> toState, Func<TValue, bool> toControl)
            where TControl : IControl<ToggleProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.isOn.From(toControl(x.currentValue))),
                control.props.isOn.Subscribe(x => bindTo.ExecuteSetOrDelay(toState(x.currentValue)))
            );

            return control;
        }
    }
}