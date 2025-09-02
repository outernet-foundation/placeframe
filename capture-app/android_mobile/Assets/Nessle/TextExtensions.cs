using ObserveThing;
using TMPro;
using UnityEngine;

using static Nessle.UIBuilder;

namespace Nessle
{
    public static class TextExtensions
    {
        public static T Value<T, U>(this T control, IValueObservable<U> text)
            where T : IControl<TextProps>
        {
            control.props.text.From(text.SelectDynamic(x => x.ToString()));
            return control;
        }

        public static T Value<T>(this T control, IValueObservable<string> text)
            where T : IControl<TextProps>
        {
            control.props.text.From(text);
            return control;
        }

        public static T Value<T>(this T control, string text)
            where T : IControl<TextProps>
        {
            control.props.text.value = text;
            return control;
        }

        public static T Color<T>(this T control, IValueObservable<Color> color)
            where T : IControl<TextProps>
        {
            control.props.style.color.From(color);
            return control;
        }

        public static T Color<T>(this T control, Color color)
            where T : IControl<TextProps>
        {
            control.props.style.color.value = color;
            return control;
        }

        public static T Style<T>(this T control, TextStyleProps style)
            where T : IControl<TextProps>
        {
            return control;
        }

        public static T Style<T>(this T control, IValueObservable<TextStyleProps> style)
            where T : IControl<TextProps>
        {
            return control;
        }
    }
}

