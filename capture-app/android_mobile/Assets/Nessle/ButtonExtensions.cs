using System;
using ObserveThing;
using UnityEngine;

using static Nessle.UIBuilder;

namespace Nessle
{
    public static class ButtonExtensions
    {
        public static T OnClick<T>(this T control, Action onClick)
            where T : IControl<ButtonProps>
        {
            control.props.onClick += onClick;
            return control;
        }

        public static T Label<T>(this T control, IValueObservable<string> label)
            where T : IControl<ButtonProps>
        {
            control.Children(Text().Style(x => x.text.From(label)));
            return control;
        }

        public static T Label<T>(this T control, string label)
            where T : IControl<ButtonProps>
        {
            control.Children(Text().Style(x => x.text.value = label));
            return control;
        }

        public static T Icon<T>(this T control, Sprite icon)
            where T : IControl<ButtonProps>
        {
            control.Children(Image().Style(x => x.sprite.value = icon));
            return control;
        }

        public static T Icon<T>(this T control, IValueObservable<Sprite> icon)
            where T : IControl<ButtonProps>
        {
            control.Children(Image().Style(x => x.sprite.From(icon)));
            return control;
        }

        public static T Interactable<T>(this T control, bool interactable)
            where T : IControl<ButtonProps>
        {
            control.props.interactable.value = interactable;
            return control;
        }

        public static T Interactable<T>(this T control, IValueObservable<bool> interactable)
            where T : IControl<ButtonProps>
        {
            control.props.interactable.From(interactable);
            return control;
        }

        public static T Background<T>(this T control, IValueObservable<ImageProps> image)
            where T : IControl<ButtonProps>
        {

        }

        public static T Background<T>(this T control, IValueObservable<ImageStyleProps> image)
            where T : IControl<ButtonProps>
        {

        }
    }
}
