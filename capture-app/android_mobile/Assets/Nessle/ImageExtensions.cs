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
            control.props.color.From(color);
            return control;
        }

        public static T Color<T>(this T control, Color color)
            where T : IControl<ImageProps>
        {
            control.props.color.value = color;
            return control;
        }

        public static T Alpha<T>(this T control, float alpha)
            where T : IControl<ImageProps>
        {
            control.props.color.value = control.props.color.value.Alpha(alpha);
            return control;
        }

        public static T Alpha<T>(this T control, IValueObservable<float> alpha)
            where T : IControl<ImageProps>
        {
            control.props.color.From(alpha.SelectDynamic(x => control.props.color.value.Alpha(x)));
            return control;
        }
    }
}
