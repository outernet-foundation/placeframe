using System;
using ObserveThing;
using FofX.Stateful;
using static Nessle.UIBuilder;

namespace Nessle
{
    public static class InputFieldExtensions
    {
        public static T BindValue<T>(this T control, ObservablePrimitive<string> bindTo)
            where T : IControl<InputFieldProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.inputText.From(x.currentValue)),
                control.props.inputText.Subscribe(x => bindTo.ExecuteSetOrDelay(x.currentValue))
            );

            return control;
        }

        public static TControl BindValue<TControl, TValue>(this TControl control, ObservablePrimitive<TValue> bindTo, Func<string, TValue> toState, Func<TValue, string> toControl)
            where TControl : IControl<InputFieldProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.inputText.From(toControl(x.currentValue))),
                control.props.inputText.Subscribe(x => bindTo.ExecuteSetOrDelay(toState(x.currentValue)))
            );

            return control;
        }
    }
}
