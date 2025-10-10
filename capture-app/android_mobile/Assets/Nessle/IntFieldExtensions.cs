using System;
using ObserveThing;
using FofX.Stateful;
using static Nessle.UIBuilder;

namespace Nessle
{
    public static class IntFieldExtensions
    {
        public static T Value<T>(this T control, int text)
            where T : IControl<IntFieldProps>
        {
            control.props.value.value = text;
            return control;
        }

        public static T Value<T>(this T control, IValueObservable<int> text)
            where T : IControl<IntFieldProps>
        {
            control.props.value.From(text);
            return control;
        }

        public static T OnChange<T>(this T control, Action<int> onChange)
            where T : IControl<IntFieldProps>
        {
            control.AddBinding(control.props.value.Subscribe(x => onChange(x.currentValue)));
            return control;
        }

        public static T ReadOnly<T>(this T control, bool readOnly)
            where T : IControl<IntFieldProps>
        {
            control.props.readOnly.value = readOnly;
            return control;
        }

        public static T ReadOnly<T>(this T control, IValueObservable<bool> readOnly)
            where T : IControl<IntFieldProps>
        {
            control.props.readOnly.From(readOnly);
            return control;
        }

        public static T Interactable<T>(this T control, bool interactable)
            where T : IControl<IntFieldProps>
        {
            control.props.interactable.value = interactable;
            return control;
        }

        public static T Interactable<T>(this T control, IValueObservable<bool> interactable)
            where T : IControl<IntFieldProps>
        {
            control.props.interactable.From(interactable);
            return control;
        }

        public static T PlaceholderText<T>(this T control, string placeholderText)
            where T : IControl<IntFieldProps>
        {
            control.props.placeholderText.value = placeholderText;
            return control;
        }

        public static T PlaceholderText<T>(this T control, IValueObservable<string> placeholderText)
            where T : IControl<IntFieldProps>
        {
            control.props.placeholderText.From(placeholderText);
            return control;
        }

        public static T BindValue<T>(this T control, ObservablePrimitive<int> bindTo)
            where T : IControl<IntFieldProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.value.value = x.currentValue),
                control.props.value.Subscribe(x => bindTo.ExecuteSetOrDelay(x.currentValue))
            );

            return control;
        }

        public static TControl BindValue<TControl, TValue>(this TControl control, ObservablePrimitive<TValue> bindTo, Func<int, TValue> toState, Func<TValue, int> toControl)
            where TControl : IControl<IntFieldProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.value.value = toControl(x.currentValue)),
                control.props.value.Subscribe(x => bindTo.ExecuteSetOrDelay(toState(x.currentValue)))
            );

            return control;
        }
    }
}
