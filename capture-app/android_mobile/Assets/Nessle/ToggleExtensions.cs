using UnityEngine;
using static Nessle.UIBuilder;
using ObserveThing;
using System;

namespace Nessle
{
    public static class ToggleExtensions
    {
        public static T IsOn<T>(this T control, bool isOn)
            where T : IControl<ToggleProps>
        {
            control.props.isOn.value = isOn;
            return control;
        }

        public static T IsOn<T>(this T control, IValueObservable<bool> isOn)
            where T : IControl<ToggleProps>
        {
            control.props.isOn.From(isOn);
            return control;
        }

        public static T OnChange<T>(this T control, Action<bool> onChange)
            where T : IControl<ToggleProps>
        {
            control.AddBinding(control.props.isOn.Subscribe(x => onChange(x.currentValue)));
            return control;
        }
    }
}