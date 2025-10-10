using ObserveThing;
using ScrollbarDirection = UnityEngine.UI.Scrollbar.Direction;
using static Nessle.UIBuilder;

namespace Nessle
{
    public static class ScrollbarExtensions
    {
        public static T Value<T>(this T control, IValueObservable<float> value)
            where T : IControl<ScrollbarProps>
        {
            control.props.value.From(value);
            return control;
        }

        public static T Value<T>(this T control, float value)
            where T : IControl<ScrollbarProps>
        {
            control.props.value.value = value;
            return control;
        }

        public static T Direction<T>(this T control, IValueObservable<ScrollbarDirection> direction)
            where T : IControl<ScrollbarProps>
        {
            control.props.direction.From(direction);
            return control;
        }

        public static T Direction<T>(this T control, ScrollbarDirection direction)
            where T : IControl<ScrollbarProps>
        {
            control.props.direction.value = direction;
            return control;
        }

        public static T Size<T>(this T control, IValueObservable<float> size)
            where T : IControl<ScrollbarProps>
        {
            control.props.size.From(size);
            return control;
        }

        public static T Size<T>(this T control, float size)
            where T : IControl<ScrollbarProps>
        {
            control.props.size.value = size;
            return control;
        }

        public static T Interactable<T>(this T control, IValueObservable<bool> interactable)
            where T : IControl<ScrollbarProps>
        {
            control.props.interactable.From(interactable);
            return control;
        }

        public static T Interactable<T>(this T control, bool interactable)
            where T : IControl<ScrollbarProps>
        {
            control.props.interactable.value = interactable;
            return control;
        }
    }
}