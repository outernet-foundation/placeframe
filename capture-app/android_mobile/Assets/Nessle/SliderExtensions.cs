using ObserveThing;
using static Nessle.UIBuilder;
using SliderDirection = UnityEngine.UI.Slider.Direction;

namespace Nessle
{
    public static class SliderExtensions
    {
        public static T Value<T>(this T control, IValueObservable<float> value)
            where T : IControl<SliderProps>
        {
            control.props.value.From(value);
            return control;
        }

        public static T Value<T>(this T control, float value)
            where T : IControl<SliderProps>
        {
            control.props.value.value = value;
            return control;
        }

        public static T MinValue<T>(this T control, IValueObservable<float> minValue)
            where T : IControl<SliderProps>
        {
            control.props.minValue.From(minValue);
            return control;
        }

        public static T MinValue<T>(this T control, float minValue)
            where T : IControl<SliderProps>
        {
            control.props.minValue.value = minValue;
            return control;
        }

        public static T MaxValue<T>(this T control, IValueObservable<float> maxValue)
            where T : IControl<SliderProps>
        {
            control.props.maxValue.From(maxValue);
            return control;
        }

        public static T MaxValue<T>(this T control, float maxValue)
            where T : IControl<SliderProps>
        {
            control.props.maxValue.value = maxValue;
            return control;
        }

        public static T WholeNumbers<T>(this T control, IValueObservable<bool> wholeNumbers)
            where T : IControl<SliderProps>
        {
            control.props.wholeNumbers.From(wholeNumbers);
            return control;
        }

        public static T WholeNumbers<T>(this T control, bool wholeNumbers)
            where T : IControl<SliderProps>
        {
            control.props.wholeNumbers.value = wholeNumbers;
            return control;
        }

        public static T Direction<T>(this T control, IValueObservable<SliderDirection> direction)
            where T : IControl<SliderProps>
        {
            control.props.direction.From(direction);
            return control;
        }

        public static T Direction<T>(this T control, SliderDirection direction)
            where T : IControl<SliderProps>
        {
            control.props.direction.value = direction;
            return control;
        }
    }
}