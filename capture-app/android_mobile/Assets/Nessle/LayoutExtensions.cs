using ObserveThing;
using UnityEngine;
using static Nessle.UIBuilder;

namespace Nessle
{
    public static class LayoutExtensions
    {
        public static T Padding<T>(this T control, RectOffset padding)
            where T : IControl<LayoutProps>
        {
            control.props.padding.value = padding;
            return control;
        }

        public static T Padding<T>(this T control, IValueObservable<RectOffset> padding)
            where T : IControl<LayoutProps>
        {
            control.props.padding.From(padding);
            return control;
        }

        public static T Spacing<T>(this T control, float spacing)
            where T : IControl<LayoutProps>
        {
            control.props.spacing.value = spacing;
            return control;
        }

        public static T Spacing<T>(this T control, IValueObservable<float> spacing)
            where T : IControl<LayoutProps>
        {
            control.props.spacing.From(spacing);
            return control;
        }

        public static T ChildAlignment<T>(this T control, TextAnchor childAlignment)
            where T : IControl<LayoutProps>
        {
            control.props.childAlignment.value = childAlignment;
            return control;
        }

        public static T ChildAlignment<T>(this T control, IValueObservable<TextAnchor> childAlignment)
            where T : IControl<LayoutProps>
        {
            control.props.childAlignment.From(childAlignment);
            return control;
        }

        public static T ReverseArrangement<T>(this T control, bool reverseArrangement)
            where T : IControl<LayoutProps>
        {
            control.props.reverseArrangement.value = reverseArrangement;
            return control;
        }

        public static T ReverseArrangement<T>(this T control, IValueObservable<bool> reverseArrangement)
            where T : IControl<LayoutProps>
        {
            control.props.reverseArrangement.From(reverseArrangement);
            return control;
        }

        public static T ChildForceExpandHeight<T>(this T control, bool childForceExpandHeight)
            where T : IControl<LayoutProps>
        {
            control.props.childForceExpandHeight.value = childForceExpandHeight;
            return control;
        }

        public static T ChildForceExpandHeight<T>(this T control, IValueObservable<bool> childForceExpandHeight)
            where T : IControl<LayoutProps>
        {
            control.props.childForceExpandHeight.From(childForceExpandHeight);
            return control;
        }

        public static T ChildForceExpandWidth<T>(this T control, bool childForceExpandWidth)
            where T : IControl<LayoutProps>
        {
            control.props.childForceExpandWidth.value = childForceExpandWidth;
            return control;
        }

        public static T ChildForceExpandWidth<T>(this T control, IValueObservable<bool> childForceExpandWidth)
            where T : IControl<LayoutProps>
        {
            control.props.childForceExpandWidth.From(childForceExpandWidth);
            return control;
        }

        public static T ChildControlWidth<T>(this T control, bool childControlWidth)
            where T : IControl<LayoutProps>
        {
            control.props.childControlWidth.value = childControlWidth;
            return control;
        }

        public static T ChildControlWidth<T>(this T control, IValueObservable<bool> childControlWidth)
            where T : IControl<LayoutProps>
        {
            control.props.childControlWidth.From(childControlWidth);
            return control;
        }

        public static T ChildControlHeight<T>(this T control, bool childControlHeight)
            where T : IControl<LayoutProps>
        {
            control.props.childControlHeight.value = childControlHeight;
            return control;
        }

        public static T ChildControlHeight<T>(this T control, IValueObservable<bool> childControlHeight)
            where T : IControl<LayoutProps>
        {
            control.props.childControlHeight.From(childControlHeight);
            return control;
        }

        public static T ChildScaleWidth<T>(this T control, bool childScaleWidth)
            where T : IControl<LayoutProps>
        {
            control.props.childScaleWidth.value = childScaleWidth;
            return control;
        }

        public static T ChildScaleWidth<T>(this T control, IValueObservable<bool> childScaleWidth)
            where T : IControl<LayoutProps>
        {
            control.props.childScaleWidth.From(childScaleWidth);
            return control;
        }

        public static T ChildScaleHeight<T>(this T control, bool childScaleHeight)
            where T : IControl<LayoutProps>
        {
            control.props.childScaleHeight.value = childScaleHeight;
            return control;
        }

        public static T ChildScaleHeight<T>(this T control, IValueObservable<bool> childScaleHeight)
            where T : IControl<LayoutProps>
        {
            control.props.childScaleHeight.From(childScaleHeight);
            return control;
        }
    }
}