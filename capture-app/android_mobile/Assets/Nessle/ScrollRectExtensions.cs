using UnityEngine;
using ObserveThing;
using static Nessle.UIBuilder;

namespace Nessle
{
    public static class ScrollRectExtensions
    {
        public static T Value<T>(this T control, IValueObservable<Vector2> value)
            where T : IControl<ScrollRectProps>
        {
            control.props.value.From(value);
            return control;
        }

        public static T Value<T>(this T control, Vector2 value)
            where T : IControl<ScrollRectProps>
        {
            control.props.value.value = value;
            return control;
        }

        public static T Horizontal<T>(this T control, IValueObservable<bool> horizontal)
            where T : IControl<ScrollRectProps>
        {
            control.props.horizontal.From(horizontal);
            return control;
        }

        public static T Horizontal<T>(this T control, bool horizontal)
            where T : IControl<ScrollRectProps>
        {
            control.props.horizontal.value = horizontal;
            return control;
        }

        public static T Vertical<T>(this T control, IValueObservable<bool> vertical)
            where T : IControl<ScrollRectProps>
        {
            control.props.vertical.From(vertical);
            return control;
        }

        public static T Vertical<T>(this T control, bool vertical)
            where T : IControl<ScrollRectProps>
        {
            control.props.vertical.value = vertical;
            return control;
        }

        public static T Content<T>(this T control, IValueObservable<IControl> content)
            where T : IControl<ScrollRectProps>
        {
            control.props.content.From(content);
            return control;
        }

        public static T Content<T>(this T control, IControl content)
            where T : IControl<ScrollRectProps>
        {
            control.props.content.value = content;
            return control;
        }
    }
}