using UnityEngine;
using Nessle;

using static Nessle.UIBuilder;
using ObserveThing;
using System;
using TMPro;
using UnityEngine.Events;
using System.Collections.Generic;
using System.Security.Cryptography;

namespace PlerionClient.Client
{
    public static partial class UIElements
    {
        public static UIElementSet elements;

        public struct LabeledButtonProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<string> label;
            public TextStyleProps labelStyle;
            public UnityAction onClick;
            public IValueObservable<bool> interactable;
            public ImageProps background;
        }

        public static IControl LabeledButton(LabeledButtonProps props = default)
        {
            props.labelStyle.horizontalAlignment = props.labelStyle.horizontalAlignment ?? Props.Value(HorizontalAlignmentOptions.Center);
            props.labelStyle.verticalAlignment = props.labelStyle.verticalAlignment ?? Props.Value(VerticalAlignmentOptions.Capline);

            return Button(new ButtonProps()
            {
                interactable = props.interactable,
                background = props.background,
                onClick = props.onClick,
                element = props.element,
                layout = props.layout,
                content = Props.List(
                    Text(new TextProps()
                    {
                        style = props.labelStyle,
                        value = props.label
                    })
                )
            });
        }

        public static IControl Row(LayoutGroupProps props = default, Control<LayoutGroupProps> prefab = default)
        {
            if (prefab == null)
                prefab = primitives.horizontalLayout;

            props.childControlWidth = props.childControlWidth ?? Props.Value(true);
            props.childControlHeight = props.childControlHeight ?? Props.Value(true);
            props.childAlignment = props.childAlignment ?? Props.Value(TextAnchor.MiddleLeft);
            props.spacing = props.spacing ?? Props.Value(10f);
            return HorizontalLayout(prefab, props);
        }

        public struct DialogProps
        {
            public ElementProps element;
            public IValueObservable<bool> useBackground;
            public IValueObservable<Color> backgroundColor;
            public Func<IDisposable, IValueObservable<IControl>> contentConstructor;
        }

        public static IControl Dialog(DialogProps props)
        {
            var children = new ListObservable<IControl>(
                Image(new()
                {
                    layout = Utility.FillParentProps(),
                    style = { color = props.backgroundColor },
                    element = { active = props.useBackground }
                })
            );

            var control = OrderedCanvas(new()
            {
                element = props.element,
                children = children
            });

            control.AddBinding(
                props.contentConstructor?.Invoke(control).Subscribe(x =>
                {
                    children.Remove(x.currentValue);
                    children.Add(x.currentValue);
                })
            );

            return control;
        }

        public struct SafeAreaProps
        {
            public ElementProps element;
            public IListObservable<IControl> children;
        }

        public static IControl SafeArea(SafeAreaProps props)
            => Control(new GameObject("Safe Area", typeof(SafeArea)), new() { element = props.element, children = props.children });

        public class EditableLabelProps
        {
            public InputFieldProps inputField;
            public TextStyleProps label;
            public IValueObservable<bool> inputFieldActive;
        }

        // public static IControl PropertyLabel(IControl label, IControl control)
        // {
        //     return HorizontalLayout(new LayoutProps()
        //     {
        //         childScaleHeight = Props.Value(true),
        //         childControlWidth = Props.Value(true),
        //         childForceExpandHeight = Props.Value(true),
        //         spacing = Props.Value(10f)
        //     }).Children(label, control.FlexibleWidth(true));
        // }

        public static IControl Title(TextProps props)
            => Title(primitives.text, props);

        public static IControl Title(Control<TextProps> prefab, TextProps props)
        {
            props.style.horizontalAlignment = props.style.horizontalAlignment ?? Props.Value(HorizontalAlignmentOptions.Center);
            props.style.verticalAlignment = props.style.verticalAlignment ?? Props.Value(VerticalAlignmentOptions.Capline);
            props.style.fontSize = props.style.fontSize ?? Props.Value(48f);

            return Text(prefab, props);
        }

        public static IControl TightRowsWideColumns(LayoutGroupProps props)
            => TightRowsWideColumns(primitives.verticalLayout, props);

        public static IControl TightRowsWideColumns(Control<LayoutGroupProps> prefab, LayoutGroupProps props)
        {
            props.childControlWidth = props.childControlWidth ?? Props.Value(true);
            props.childControlHeight = props.childControlHeight ?? Props.Value(true);
            props.childForceExpandWidth = props.childForceExpandWidth ?? Props.Value(true);
            props.spacing = props.spacing ?? Props.Value(30f);

            return VerticalLayout(prefab, props);
        }

        public struct LabeledControlProps
        {
            public IValueObservable<string> label;
            public TextStyleProps labelStyle;
            public IValueObservable<float> labelWidth;
            public IControl control;
        }

        public static IControl LabeledControl(LabeledControlProps props = default)
        {
            props.labelStyle.verticalAlignment = props.labelStyle.verticalAlignment ?? Props.Value(VerticalAlignmentOptions.Capline);
            props.labelStyle.overflowMode = props.labelStyle.overflowMode ?? Props.Value(TextOverflowModes.Ellipsis);
            props.labelStyle.textWrappingMode = props.labelStyle.textWrappingMode ?? Props.Value(TextWrappingModes.NoWrap);

            props.labelWidth = props.labelWidth ?? Props.Value(200f);

            var control = HorizontalLayout(new()
            {
                childAlignment = Props.Value(TextAnchor.MiddleLeft),
                childControlWidth = Props.Value(true),
                childControlHeight = Props.Value(true),
                children = Props.List(
                    Text(new()
                    {
                        value = props.label,
                        style = props.labelStyle,
                        layout = new()
                        {
                            minWidth = props.labelWidth,
                            preferredWidth = props.labelWidth
                        }
                    }),
                    props.control
                )
            });

            return control;
        }

        public struct RoundIconButtonProps
        {
            public ImageProps icon;
            public UnityAction onClick;
            public IValueObservable<bool> interactable;
            public ImageProps background;
        }

        public static IControl RoundIconButton(RoundIconButtonProps props = default)
        {
            return RoundButton(new ButtonProps()
            {
                background = props.background,
                interactable = props.interactable,
                onClick = props.onClick,
                content = Props.List(Image(props.icon))
            });
        }

        public static IControl RoundButton(ButtonProps props = default)
            => Control(elements.roundButton, props);

        public static IControl Foldout(FoldoutProps props = default)
            => Control(elements.foldout, props);

        // public static IControl AdaptiveLabel(IControl label, IControl content)
        // {
        //     return VerticalLayout().Style(root =>
        //     {
        //         root.props.childControlWidth.From(true);
        //         root.props.childControlHeight.From(true);
        //         IControl narrowContentRegion = HorizontalLayout("narrowContent").Style(narrowContentRegion =>
        //         {
        //             narrowContentRegion.props.childControlWidth.From(true);
        //             narrowContentRegion.props.childControlHeight.From(true);
        //             narrowContentRegion.FlexibleWidth(true);
        //             narrowContentRegion.FlexibleHeight(true);
        //         });

        //         IControl wideContentRegion = VerticalLayout("wideContent").Style(wideContentRegion =>
        //         {
        //             wideContentRegion.FlexibleWidth(true);
        //             wideContentRegion.props.childControlWidth.From(true);
        //             wideContentRegion.props.childControlHeight.From(true);
        //         });

        //         var contentIsWide = Observables.Combine(
        //             content.rect, narrowContentRegion.rect,
        //             (_, region) =>
        //             {
        //                 var tooWide = LayoutUtility.GetPreferredWidth(content.rectTransform) > region.width;
        //                 var tooTall = LayoutUtility.GetPreferredHeight(content.rectTransform) > region.height;
        //                 return tooWide || tooTall;
        //             }
        //         );

        //         wideContentRegion.Active(contentIsWide);
        //         narrowContentRegion.Active(contentIsWide.SelectDynamic(x => !x));
        //         content.parent.From(contentIsWide.SelectDynamic(x => x ? wideContentRegion : narrowContentRegion));

        //         root.Children(
        //             Row().Children(label, narrowContentRegion),
        //             wideContentRegion
        //         );

        //         content.FillParent();
        //     });
        // }

        public struct ColumnsProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<float> spacing;
            public IListObservable<IControl> columns;
        }

        public static IControl Columns(ColumnsProps props)
        {
            props.spacing = props.spacing ?? Props.Value(0f);
            List<IControl> columns = new List<IControl>();
            float spacingValue = 0;

            var control = Control("Columns", new()
            {
                element = props.element,
                layout = props.layout,
                children = props.columns
            });

            control.AddBinding(
                Observables.Any(props.columns, props.spacing).Subscribe(x =>
                {
                    if (x.source == props.spacing)
                    {
                        spacingValue = ((IValueEventArgs<float>)x).currentValue;
                    }
                    else
                    {
                        var args = (IListEventArgs<IControl>)x;
                        if (args.operationType == OpType.Add)
                        {
                            columns.Insert(args.index, args.element);
                        }
                        else if (args.operationType == OpType.Remove)
                        {
                            columns.RemoveAt(args.index);
                        }
                    }

                    float step = 1f / columns.Count;

                    for (int i = 0; i < columns.Count; i++)
                    {
                        var child = columns[i];
                        child.rectTransform.anchorMin = new Vector2(step * i, 0);
                        child.rectTransform.anchorMax = new Vector2(step * (i + 1), 1);

                        child.rectTransform.offsetMin = new Vector2(Mathf.Lerp(0f, spacingValue, i * step), 0);
                        child.rectTransform.offsetMax = new Vector2(Mathf.Lerp(-spacingValue, 0f, (i + 1) * step), 0);
                    }
                })
            );

            return control;
        }

        private static int _lastCanvasSortOrder = -1;

        public static IControl OrderedCanvas(CanvasProps props)
            => OrderedCanvas(primitives.canvas, props);

        public static IControl OrderedCanvas(Control<CanvasProps> prefab, CanvasProps props)
        {
            props.sortingOrder = Props.Value(_lastCanvasSortOrder + 1);
            _lastCanvasSortOrder++;
            return Canvas(prefab, props);
        }
    }
}