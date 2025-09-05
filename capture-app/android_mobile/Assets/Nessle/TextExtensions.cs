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
            control.props.style.fontSize.From(style.fontSize);
            control.props.style.color.From(style.color);
            control.props.style.alignment.From(style.alignment);
            control.props.style.font.From(style.font);
            control.props.style.fontStyle.From(style.fontStyle);
            control.props.style.margin.From(style.margin);
            control.props.style.wrappingMode.From(style.wrappingMode);
            control.props.style.overflowMode.From(style.overflowMode);
            control.props.style.fontWeight.From(style.fontWeight);
            return control;
        }

        public static T Style<T>(this T control, IValueObservable<TextStyleProps> style)
            where T : IControl<TextProps>
        {
            control.AddBinding(style.Subscribe(x =>
            {
                control.props.style.fontSize.From(x.currentValue.fontSize);
                control.props.style.color.From(x.currentValue.color);
                control.props.style.alignment.From(x.currentValue.alignment);
                control.props.style.font.From(x.currentValue.font);
                control.props.style.fontStyle.From(x.currentValue.fontStyle);
                control.props.style.margin.From(x.currentValue.margin);
                control.props.style.wrappingMode.From(x.currentValue.wrappingMode);
                control.props.style.overflowMode.From(x.currentValue.overflowMode);
                control.props.style.fontWeight.From(x.currentValue.fontWeight);
            }));

            return control;
        }
    }
}

