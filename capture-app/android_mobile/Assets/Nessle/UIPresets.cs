using UnityEngine;
using Nessle;
using TMPro;

using static Nessle.UIBuilder;
using ObserveThing;
using System;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace PlerionClient.Client
{
    public static class UIPresets
    {
        public static Action<SliderProps> DefaultSliderStyle;

        public static SliderProps DefaultSliderProps()
        {
            var props = new SliderProps();
            DefaultSliderStyle?.Invoke(props);
            return props;
        }

        public static void StyleButton(ButtonProps button)
        {
            StylePill(button.background);
            button.background.style.color.value = UIResources.ButtonColor;
            button.padding.value = new RectOffset(13, 13, 7, 7);
        }

        public static void StyleInputField(InputFieldProps inputField)
        {
            StylePill(inputField.background);
            inputField.background.style.pixelsPerUnitMultiplier.value = 2.8f;
            inputField.background.style.color.value = UIResources.InputFieldColor;
            inputField.inputText.style.margin.value = new Vector4(10, 0, 0, 0);
            inputField.placeholder.style.margin.value = new Vector4(10, 0, 0, 0);
        }

        public static void StyleScrollBar(ScrollbarProps scrollbar)
        {
            StylePill(scrollbar.handle);
            StylePill(scrollbar.background);

            scrollbar.handle.style.pixelsPerUnitMultiplier.value = 8;
            scrollbar.handle.style.color.value = UIResources.ScrollBarHandleColor;

            scrollbar.background.style.pixelsPerUnitMultiplier.value = 8;
            scrollbar.background.style.color.value = UIResources.ScrollBarBackgroundColor;
        }

        public static void StyleText(TextProps text)
        {
            text.style.color.value = UIResources.TextColor;
            text.style.fontSize.value = 14;
            text.style.alignment.value = TextAlignmentOptions.CaplineLeft;
        }

        public static void StyleScrollRect(ScrollRectProps scrollRect)
        {
            scrollRect.background.style.color.value = UIResources.PanelColor;
        }

        public static void StyleDropdown(DropdownProps dropdown)
        {
            StylePill(dropdown.background);

            dropdown.background.style.color.value = UIResources.ButtonColor;
            dropdown.template.background.style.color.value = UIResources.ButtonColor;
            dropdown.itemBackground.style.color.value = UIResources.ButtonColor;
        }

        public static void StyleSlider(SliderProps slider)
        {
            slider.foreground.style.color.value = UIResources.ScrollBarHandleColor;
            slider.foreground.sprite.value = UIResources.RoundedBox;
            slider.foreground.style.imageType.value = UnityEngine.UI.Image.Type.Sliced;
            slider.foreground.style.pixelsPerUnitMultiplier.value = 3.7f;

            slider.background.style.color.value = UIResources.ScrollBarBackgroundColor;
            slider.background.sprite.value = UIResources.RoundedBox;
            slider.background.style.imageType.value = UnityEngine.UI.Image.Type.Sliced;
            slider.background.style.pixelsPerUnitMultiplier.value = 3.7f;

            slider.showHandle.value = false;
            slider.handleSize.value = 20f;
        }

        public static IControl<ImageProps> Pill()
            => Image().Style(StylePill);

        public static void StylePill(ImageProps image)
        {
            image.sprite.value = UIResources.RoundedBox;
            image.style.imageType.value = UnityEngine.UI.Image.Type.Sliced;
            image.style.pixelsPerUnitMultiplier.value = 2.8f;
        }

        public static IControl<LayoutProps> Row()
            => HorizontalLayout().Style(StyleRow);

        public static void StyleRow(LayoutProps layout)
        {
            layout.childControlWidth.value = true;
            layout.childControlHeight.value = true;
            layout.childAlignment.value = TextAnchor.MiddleLeft;
            layout.spacing.value = 10;
        }

        public static IControl<TextProps> Title()
            => Text().Style(StyleTitle);

        public static void StyleTitle(TextProps text)
        {
            text.style.fontSize.value = 64;
            text.style.alignment.value = TextAlignmentOptions.MidlineGeoAligned;
        }

        public static Control SafeArea()
            => new Control("Safe Area", typeof(SafeArea));

        public static Control<InputFieldProps> EditableLabel(InputFieldProps props = default)
        {
            var control = new Control<InputFieldProps>(props ?? DefaultInputFieldProps(), new GameObject("Editable Label"));
            ValueObservable<bool> inputFieldActive = new ValueObservable<bool>();

            control.Children(
                InputField(control.props)
                    .FillParent()
                    .Active(inputFieldActive)
                    .Selected(inputFieldActive)
                    .OnDeselect(_ => inputFieldActive.value = false)
                    .OnEndEdit(_ => inputFieldActive.value = false),
                Text()
                    .Value(control.props.inputText.text)
                    .FillParent()
                    .Active(inputFieldActive.SelectDynamic(x => !x))
                    .OnPointerClick(x =>
                    {
                        if (x.clickCount > 1)
                            inputFieldActive.value = true;
                    })
            );

            return control;
        }

        public class SliderProps
        {
            public ValueObservable<float> value { get; } = new ValueObservable<float>();

            public ValueObservable<bool> showHandle { get; } = new ValueObservable<bool>(true);
            public ImageProps handle { get; } = DefaultImageProps();
            public ValueObservable<float> handleSize { get; } = new ValueObservable<float>(10);

            public ValueObservable<bool> showForeground { get; } = new ValueObservable<bool>(true);
            public ImageProps foreground { get; } = DefaultImageProps();

            public ImageProps background { get; } = DefaultImageProps();
        }

        public static Control<SliderProps> Slider(SliderProps props = default)
        {
            props = props ?? DefaultSliderProps();
            var control = Control("Slider", props);

            Action<PointerEventData> handlePointerInput = x =>
            {
                if (!RectTransformUtility.ScreenPointToLocalPointInRectangle(control.transform, x.position, x.pressEventCamera, out var pos))
                    return;

                var maxValue = control.transform.rect.width - props.handleSize.value;
                var clampedX = Mathf.Clamp(pos.x - (control.transform.rect.position.x + (props.handleSize.value * 0.5f)), 0, maxValue);
                props.value.value = clampedX / maxValue;
            };

            var valueWithHandleSize = Observables.Combine(
                props.value,
                props.handleSize,
                control.rect,
                (value, handleSize, rect) => (value, handleSize: rect.width == 0 ? 0 : handleSize / rect.width)
            );

            return control
                .OnPointerDown(handlePointerInput)
                .OnDrag(handlePointerInput)
                .Children(
                    Image(props.background)
                        .Name("Background")
                        .SetPivot(new Vector2(0, 0.5f))
                        .FillParent(),
                    Image(props.foreground)
                        .Name("Foreground")
                        .Active(props.showForeground)
                        .SizeDelta(Vector2.zero)
                        .AnchorMin(Vector2.zero)
                        .AnchorMax(valueWithHandleSize.SelectDynamic(x => props.showHandle.SelectDynamic(showHandle =>
                        {
                            var min = showHandle ? x.handleSize * 0.5f : x.handleSize;
                            var max = showHandle ? 1 - (x.handleSize * 0.5f) : 1;
                            return new Vector2(Mathf.Lerp(min, max, x.value), 1f);
                        }))),
                    Image(props.handle)
                        .Name("Handle")
                        .Active(props.showHandle)
                        .SizeDelta(props.handleSize.SelectDynamic(x => Vector2.one * x))
                        .Anchor(valueWithHandleSize.SelectDynamic(x => new Vector2(Mathf.Lerp(x.handleSize * 0.5f, 1 - (x.handleSize * 0.5f), x.value), 0.5f)))
                );
        }

        public class FloatFieldProps
        {
            public ValueObservable<float> value { get; } = new ValueObservable<float>();
            public InputFieldProps inputField { get; } = DefaultInputFieldProps();

            public FloatFieldProps()
            {
                inputField.contentType.value = TMP_InputField.ContentType.DecimalNumber;
            }
        }

        public static Control<FloatFieldProps> FloatField(FloatFieldProps props = default)
        {
            props = props ?? new FloatFieldProps();
            var inputField = InputField(props.inputField);
            var control = new Control<FloatFieldProps>(props, inputField.gameObject);

            control.Children(inputField);
            control.AddBinding(
                control.props.value.Subscribe(x => control.props.inputField.inputText.text.value = x.currentValue.ToString()),
                control.props.inputField.inputText.text.Subscribe(x =>
                {
                    if (!float.TryParse(x.currentValue, out var value))
                    {
                        control.props.inputField.inputText.text.value = "0";
                        return;
                    }

                    control.props.value.value = value;
                })
            );

            return control;
        }

        public static T OnChanged<T>(this T control, Action<float> onChange)
            where T : IControl<FloatFieldProps>
        {
            control.AddBinding(control.props.value.Subscribe(x => onChange(x.currentValue)));
            return control;
        }

        public static IControl PropertyLabel(IControl<TextProps> label, IControl control)
        {
            return HorizontalLayout().Style(x =>
            {
                x.childControlHeight.value = true;
                x.childControlWidth.value = true;
                x.childForceExpandHeight.value = true;
                x.spacing.value = 10;
            }).Children(label, control.FlexibleWidth(true));
        }

        public class Vector3Props
        {
            public ValueObservable<Vector3> value { get; } = new ValueObservable<Vector3>();
            public LayoutProps layout { get; } = new LayoutProps();

            public TextProps xLabel { get; } = DefaultTextProps();
            public TextProps yLabel { get; } = DefaultTextProps();
            public TextProps zLabel { get; } = DefaultTextProps();

            public FloatFieldProps xField { get; } = new FloatFieldProps();
            public FloatFieldProps yField { get; } = new FloatFieldProps();
            public FloatFieldProps zField { get; } = new FloatFieldProps();
        }

        public static Control<Vector3Props> Vector3(Vector3Props props = default)
        {
            props = props ?? new Vector3Props();
            var control = Control("Vector3", props)
                .PreferredHeight(30)
                .Columns(
                    10,
                    PropertyLabel(
                        Text(props.xLabel).Value("X"),
                        FloatField(props.xField)
                            .OnChanged(x => props.value.value = new Vector3(x, props.value.value.y, props.value.value.z))
                    ),
                    PropertyLabel(
                        Text(props.yLabel).Value("Y"),
                        FloatField(props.yField)
                            .OnChanged(x => props.value.value = new Vector3(props.value.value.x, x, props.value.value.z))
                    ),
                    PropertyLabel(
                        Text(props.zLabel).Value("Z"),
                        FloatField(props.zField)
                            .OnChanged(x => props.value.value = new Vector3(props.value.value.x, props.value.value.y, x))
                    )
                );

            control.AddBinding(
                BindLayout(control.props.layout, control.gameObject.GetComponent<HorizontalLayoutGroup>()),
                control.props.value.Subscribe(x =>
                {
                    control.props.xField.value.value = x.currentValue.x;
                    control.props.yField.value.value = x.currentValue.y;
                    control.props.zField.value.value = x.currentValue.z;
                })
            );

            return control;
        }

        public class TabProps
        {
            public ValueObservable<string> name { get; } = new ValueObservable<string>();
            public ImageProps icon { get; } = DefaultImageProps();
            public ImageProps selectedIcon { get; } = DefaultImageProps();
            public ValueObservable<IControl> content { get; } = new ValueObservable<IControl>();
        }

        public class TabbedMenuProps
        {
            public ValueObservable<int> selectedTab { get; } = new ValueObservable<int>();
            public ListObservable<TabProps> tabs { get; } = new ListObservable<TabProps>();
            public TextStyleProps defaultLabelStyle { get; } = new TextStyleProps();
            public TextStyleProps selectedLabelStyle { get; } = new TextStyleProps();
            public ImageStyleProps background { get; } = new ImageStyleProps();
            public ImageStyleProps selectedBackground { get; } = new ImageStyleProps();
        }

        public static Control<TabbedMenuProps> TabbedMenu(TabbedMenuProps props = default)
        {
            props = props ?? new TabbedMenuProps();
            var control = Control("Tabbed Menu", props, typeof(VerticalLayoutGroup));
            var layout = control.gameObject.GetComponent<VerticalLayoutGroup>();
            layout.childControlHeight = true;
            layout.childControlWidth = true;

            control.Children(
                HorizontalLayout().Style(x =>
                {
                    x.childControlHeight.value = true;
                    x.childControlWidth.value = true;
                    x.childForceExpandWidth.value = true;
                }).Children(props.tabs.CreateDynamic(tabProps =>
                {
                    var index = props.tabs.IndexOfDynamic(tabProps);

                    var selected = Observables.Combine(
                        index,
                        props.selectedTab,
                        (index, selected) => index == selected
                    );

                    return Button()
                        .Background(selected.SelectDynamic(x => x ? props.background : props.selectedBackground))
                        .WithMetadata(index)
                        .Children(
                            Image().Style(selected.SelectDynamic(x => x ? tabProps.icon : tabProps.selectedIcon)),
                            Text().Style(selected.SelectDynamic(x => x ? props.defaultLabelStyle : props.selectedLabelStyle)).Value(tabProps.name)
                        );

                }).OrderByDynamic(x => x.metadata))
            );
        }
    }
}