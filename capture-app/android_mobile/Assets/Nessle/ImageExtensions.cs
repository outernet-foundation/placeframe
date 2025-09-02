using ObserveThing;
using UnityEngine;

using static Nessle.UIBuilder;

namespace Nessle
{
    public static class ImageExtensions
    {
        public static T Sprite<T>(this T control, IValueObservable<Sprite> sprite)
            where T : IControl<ImageProps>
        {
            control.props.sprite.From(sprite);
            return control;
        }

        public static T Sprite<T>(this T control, Sprite sprite)
            where T : IControl<ImageProps>
        {
            control.props.sprite.value = sprite;
            return control;
        }

        public static T Color<T>(this T control, IValueObservable<Color> color)
            where T : IControl<ImageProps>
        {
            control.props.style.color.From(color);
            return control;
        }

        public static T Color<T>(this T control, Color color)
            where T : IControl<ImageProps>
        {
            control.props.style.color.value = color;
            return control;
        }

        public static T Alpha<T>(this T control, float alpha)
            where T : IControl<ImageProps>
        {
            control.props.style.color.value = control.props.style.color.value.Alpha(alpha);
            return control;
        }

        public static T Alpha<T>(this T control, IValueObservable<float> alpha)
            where T : IControl<ImageProps>
        {
            control.props.style.color.From(alpha.SelectDynamic(x => control.props.style.color.value.Alpha(x)));
            return control;
        }

        public static T Style<T>(this T control, IValueObservable<ImageStyleProps> style)
            where T : IControl<ImageProps>
        {
            control.AddBinding(style.Subscribe(x =>
            {
                control.props.style.color.From(x.currentValue.color);
                control.props.style.pixelsPerUnitMultiplier.From(x.currentValue.pixelsPerUnitMultiplier);
                control.props.style.preserveAspect.From(x.currentValue.preserveAspect);
                control.props.style.imageType.From(x.currentValue.imageType);
            }));

            return control;
        }

        public static T Style<T>(this T control, IValueObservable<ImageProps> style)
            where T : IControl<ImageProps>
        {
            return control;
        }
    }
}
