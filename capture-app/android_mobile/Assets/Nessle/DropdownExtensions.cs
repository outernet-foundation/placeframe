using System.Collections.Generic;

using static Nessle.UIBuilder;
using ObserveThing;
using System;
using FofX.Stateful;

namespace Nessle
{
    public static class DropdownExtensions
    {
        public static T Value<T>(this T control, IValueObservable<int> value)
            where T : IControl<DropdownProps>
        {
            control.props.value.From(value);
            return control;
        }

        public static T Value<T>(this T control, int value)
            where T : IControl<DropdownProps>
        {
            control.props.value.value = value;
            return control;
        }

        public static T AllowMultiselect<T>(this T control, IValueObservable<bool> allowMultiselect)
            where T : IControl<DropdownProps>
        {
            control.props.allowMultiselect.From(allowMultiselect);
            return control;
        }

        public static T AllowMultiselect<T>(this T control, bool allowMultiselect)
            where T : IControl<DropdownProps>
        {
            control.props.allowMultiselect.value = allowMultiselect;
            return control;
        }

        public static T Options<T>(this T control, params string[] options)
            where T : IControl<DropdownProps> => control.Options((IEnumerable<string>)options);

        public static T Options<T>(this T control, IEnumerable<string> options)
            where T : IControl<DropdownProps>
        {
            foreach (var option in options)
                control.props.options.Add(option);

            return control;
        }

        public static T Options<T>(this T control, IListObservable<string> options)
            where T : IControl<DropdownProps>
        {
            control.props.options.From(options);
            return control;
        }

        public static T Interactable<T>(this T control, bool interactable)
            where T : IControl<DropdownProps>
        {
            control.props.interactable.value = interactable;
            return control;
        }

        public static T Interactable<T>(this T control, IValueObservable<bool> interactable)
            where T : IControl<DropdownProps>
        {
            control.props.interactable.From(interactable);
            return control;
        }

        public static T OnChange<T>(this T control, Action<int> onChange)
            where T : IControl<DropdownProps>
        {
            control.AddBinding(control.props.value.Subscribe(x => onChange(x.currentValue)));
            return control;
        }

        public static T BindValue<T>(this T control, ObservablePrimitive<int> bindTo)
            where T : IControl<DropdownProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.value.value = x.currentValue),
                control.props.value.Subscribe(x => bindTo.ExecuteSetOrDelay(x.currentValue))
            );

            return control;
        }

        public static TControl BindValue<TControl, TValue>(this TControl control, ObservablePrimitive<TValue> bindTo, Func<int, TValue> toState, Func<TValue, int> toControl)
            where TControl : IControl<DropdownProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.value.value = toControl(x.currentValue)),
                control.props.value.Subscribe(x => bindTo.ExecuteSetOrDelay(toState(x.currentValue)))
            );

            return control;
        }
    }
}