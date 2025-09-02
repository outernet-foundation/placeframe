using System;
using System.Linq;
using ObserveThing;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

using ImageType = UnityEngine.UI.Image.Type;
using TMP_ContentType = TMPro.TMP_InputField.ContentType;
using TMP_LineType = TMPro.TMP_InputField.LineType;
using ScrollRectMovementType = UnityEngine.UI.ScrollRect.MovementType;
using ScrollbarDirection = UnityEngine.UI.Scrollbar.Direction;
using ScrollRectScrollbarVisibility = UnityEngine.UI.ScrollRect.ScrollbarVisibility;

namespace Nessle
{
    public static class UIBuilder
    {
        public static Action<TextProps> DefaultTextStyle;
        public static Action<ImageProps> DefaultImageStyle;
        public static Action<ButtonProps> DefaultButtonStyle;
        public static Action<InputFieldProps> DefaultInputFieldStyle;
        public static Action<ScrollbarProps> DefaultScrollbarStyle;
        public static Action<ScrollRectProps> DefaultScrollRectStyle;
        public static Action<DropdownProps> DefaultDropdownStyle;

        public static TextProps DefaultTextProps()
        {
            var props = new TextProps();
            DefaultTextStyle?.Invoke(props);
            return props;
        }

        public static ImageProps DefaultImageProps()
        {
            var props = new ImageProps();
            DefaultImageStyle?.Invoke(props);
            return props;
        }

        public static ButtonProps DefaultButtonProps()
        {
            var props = new ButtonProps();
            DefaultButtonStyle?.Invoke(props);
            return props;
        }

        public static InputFieldProps DefaultInputFieldProps()
        {
            var props = new InputFieldProps();
            DefaultInputFieldStyle?.Invoke(props);
            return props;
        }

        public static ScrollbarProps DefaultScrollbarProps()
        {
            var props = new ScrollbarProps();
            DefaultScrollbarStyle?.Invoke(props);
            return props;
        }

        public static ScrollRectProps DefaultScrollRectProps()
        {
            var props = new ScrollRectProps();
            DefaultScrollRectStyle?.Invoke(props);
            return props;
        }

        public static DropdownProps DefaultDropdownProps()
        {
            var props = new DropdownProps();

            props.captionText.margin.value = new Vector4(12, 0, 0, 0);
            props.captionText.alignment.value = TextAlignmentOptions.CaplineLeft;

            props.arrow.style.preserveAspect.value = true;
            props.arrow.sprite.value = UIResources.ArrowDown;

            props.itemText.margin.value = new Vector4(12, 0, 0, 0);
            props.itemText.alignment.value = TextAlignmentOptions.CaplineLeft;

            props.itemCheckmark.style.preserveAspect.value = true;
            props.itemCheckmark.sprite.value = UIResources.Checkmark;

            DefaultDropdownStyle?.Invoke(props);
            return props;
        }

        public static Control Control(string name, params Type[] components)
            => new Control(name, components);

        public static Control<T> Control<T>(T props, params Type[] components)
            => new Control<T>(props, "Control", components);

        public static Control<T> Control<T>(string name, T props, params Type[] components)
            => new Control<T>(props, name, components);

        public static Control<T> Control<T>(T props, RectTransform control)
            => new Control<T>(props, control.gameObject);

        public static Control<T> HorizontalControl<T>(string name, Func<T, LayoutProps> selectLayoutProps, params Type[] components)
            where T : new()
        {
            var props = new T();
            return HorizontalControl(name, props, selectLayoutProps(props), components);
        }

        public static Control<T> HorizontalControl<T>(string name, T props, LayoutProps layoutProps, params Type[] components)
        {
            var control = new Control<T>(props, name, components);
            var layout = control.gameObject.AddComponent<HorizontalLayoutGroup>();
            control.AddBinding(BindLayout(layoutProps, layout));
            return control;
        }

        public static Control<T> VerticalControl<T>(string name, Func<T, LayoutProps> selectLayoutProps, params Type[] components)
            where T : new()
        {
            var props = new T();
            return VerticalControl(name, props, selectLayoutProps(props), components);
        }

        public static Control<T> VerticalControl<T>(string name, T props, LayoutProps layoutProps, params Type[] components)
        {
            var control = new Control<T>(props, name, components);
            var layout = control.gameObject.AddComponent<VerticalLayoutGroup>();
            control.AddBinding(BindLayout(layoutProps, layout));
            return control;
        }

        public static Control<T> Style<T>(this Control<T> control, Action<T> style)
        {
            style(control.props);
            return control;
        }

        public class TextProps : IDisposable
        {
            public ValueObservable<string> text { get; } = new ValueObservable<string>();
            public TextStyleProps style { get; } = new TextStyleProps();

            public void Dispose()
            {
                text.Dispose();
                style.Dispose();
            }
        }

        public class TextStyleProps : IDisposable
        {
            public ValueObservable<float> fontSize { get; } = new ValueObservable<float>();
            public ValueObservable<Color> color { get; } = new ValueObservable<Color>();
            public ValueObservable<TextAlignmentOptions> alignment { get; } = new ValueObservable<TextAlignmentOptions>();
            public ValueObservable<TMP_FontAsset> font { get; } = new ValueObservable<TMP_FontAsset>();
            public ValueObservable<FontStyles> fontStyle { get; } = new ValueObservable<FontStyles>();
            public ValueObservable<Vector4> margin { get; } = new ValueObservable<Vector4>();
            public ValueObservable<TextWrappingModes> wrappingMode { get; } = new ValueObservable<TextWrappingModes>();
            public ValueObservable<TextOverflowModes> overflowMode { get; } = new ValueObservable<TextOverflowModes>();
            public ValueObservable<FontWeight> fontWeight { get; } = new ValueObservable<FontWeight>();

            public void Dispose()
            {
                fontSize.Dispose();
                color.Dispose();
                alignment.Dispose();
                font.Dispose();
                fontStyle.Dispose();
                margin.Dispose();
                wrappingMode.Dispose();
                overflowMode.Dispose();
                fontWeight.Dispose();
            }
        }

        public static Control<TextProps> Text(TextProps props = default)
            => Text(props ?? DefaultTextProps(), out var _);

        private static Control<TextProps> Text(out TextMeshProUGUI textComponent)
            => Text(new TextProps(), out textComponent);

        private static Control<TextProps> Text(TextProps props, out TextMeshProUGUI textComponent)
        {
            props = props ?? DefaultTextProps();
            var control = new Control<TextProps>(props, "Text", typeof(TextMeshProUGUI));
            var text = control.gameObject.GetComponent<TextMeshProUGUI>();

            control.AddBinding(
                props.text.Subscribe(x => text.text = x.currentValue),
                props.style.fontSize.Subscribe(x => text.fontSize = x.currentValue),
                props.style.color.Subscribe(x => text.color = x.currentValue),
                props.style.alignment.Subscribe(x => text.alignment = x.currentValue),
                props.style.font.Subscribe(x => text.font = x.currentValue),
                props.style.fontStyle.Subscribe(x => text.fontStyle = x.currentValue),
                props.style.margin.Subscribe(x => text.margin = x.currentValue),
                props.style.wrappingMode.Subscribe(x => text.textWrappingMode = x.currentValue),
                props.style.overflowMode.Subscribe(x => text.overflowMode = x.currentValue),
                props.style.fontWeight.Subscribe(x => text.fontWeight = x.currentValue)
            );

            textComponent = text;

            return control;
        }

        public class ImageProps : IDisposable
        {
            public ValueObservable<Sprite> sprite { get; } = new ValueObservable<Sprite>();
            public ImageStyleProps style { get; } = new ImageStyleProps();

            public void Dispose()
            {
                sprite.Dispose();
                style.Dispose();
            }
        }

        public class ImageStyleProps : IDisposable
        {
            public ValueObservable<Color> color { get; } = new ValueObservable<Color>(Color.white);
            public ValueObservable<float> pixelsPerUnitMultiplier { get; } = new ValueObservable<float>();
            public ValueObservable<bool> preserveAspect { get; } = new ValueObservable<bool>();
            public ValueObservable<ImageType> imageType { get; } = new ValueObservable<ImageType>();

            public void Dispose()
            {
                color.Dispose();
                pixelsPerUnitMultiplier.Dispose();
                preserveAspect.Dispose();
                imageType.Dispose();
            }
        }

        public static Control<ImageProps> Image(ImageProps props = default)
            => Image(props ?? DefaultImageProps(), out var _);

        private static Control<ImageProps> Image(ImageProps props, out Image imageComponent)
        {
            props = props ?? DefaultImageProps();
            var control = new Control<ImageProps>(props, "Image", typeof(Image));
            var image = control.gameObject.GetComponent<Image>();

            control.AddBinding(
                props.sprite.Subscribe(x => image.sprite = x.currentValue),
                props.style.color.Subscribe(x => image.color = x.currentValue),
                props.style.pixelsPerUnitMultiplier.Subscribe(x => image.pixelsPerUnitMultiplier = x.currentValue),
                props.style.preserveAspect.Subscribe(x => image.preserveAspect = x.currentValue),
                props.style.imageType.Subscribe(x => image.type = x.currentValue)
            );

            imageComponent = image;

            return control;
        }

        public class ButtonProps : IDisposable
        {
            public event Action onClick;
            public ValueObservable<bool> selected { get; } = new ValueObservable<bool>();
            public ValueObservable<bool> interactable { get; } = new ValueObservable<bool>(true);
            public ValueObservable<RectOffset> padding { get; } = new ValueObservable<RectOffset>(new RectOffset());
            public ValueObservable<float> spacing { get; } = new ValueObservable<float>(10);
            public ImageProps background { get; } = DefaultImageProps();

            public void Dispose()
            {
                interactable.Dispose();
                background.Dispose();
            }

            public void InvokeOnClick()
            {
                onClick?.Invoke();
            }
        }

        public static Control<ButtonProps> Button(ButtonProps props = default)
        {
            props = props ?? DefaultButtonProps();
            var control = new Control<ButtonProps>(props, "Button", typeof(Button), typeof(HorizontalLayoutGroup));
            var button = control.gameObject.GetComponent<Button>();
            var layout = control.gameObject.GetComponent<HorizontalLayoutGroup>();

            control.Children(Image(props.background, out var background).Name("Background").IgnoreLayout(true).FillParent());

            layout.childControlWidth = true;
            layout.childControlHeight = true;
            layout.childForceExpandWidth = false;
            layout.childForceExpandHeight = false;
            layout.childAlignment = TextAnchor.MiddleCenter;

            button.targetGraphic = background;

            button.onClick.AddListener(props.InvokeOnClick);

            control.AddBinding(
                props.interactable.Subscribe(x => button.interactable = x.currentValue),
                props.padding.Subscribe(x => layout.padding = x.currentValue),
                props.spacing.Subscribe(x => layout.spacing = x.currentValue)
            );

            return control;
        }

        public class LayoutProps : IDisposable
        {
            public ValueObservable<RectOffset> padding { get; } = new ValueObservable<RectOffset>(new RectOffset());
            public ValueObservable<float> spacing { get; } = new ValueObservable<float>();
            public ValueObservable<TextAnchor> childAlignment { get; } = new ValueObservable<TextAnchor>();
            public ValueObservable<bool> reverseArrangement { get; } = new ValueObservable<bool>();
            public ValueObservable<bool> childForceExpandHeight { get; } = new ValueObservable<bool>();
            public ValueObservable<bool> childForceExpandWidth { get; } = new ValueObservable<bool>();
            public ValueObservable<bool> childControlWidth { get; } = new ValueObservable<bool>();
            public ValueObservable<bool> childControlHeight { get; } = new ValueObservable<bool>();
            public ValueObservable<bool> childScaleWidth { get; } = new ValueObservable<bool>();
            public ValueObservable<bool> childScaleHeight { get; } = new ValueObservable<bool>();

            public void Dispose()
            {
                padding.Dispose();
                spacing.Dispose();
                childAlignment.Dispose();
                reverseArrangement.Dispose();
                childForceExpandHeight.Dispose();
                childForceExpandWidth.Dispose();
                childControlWidth.Dispose();
                childControlHeight.Dispose();
                childScaleWidth.Dispose();
                childScaleHeight.Dispose();
            }
        }

        public static Control<LayoutProps> HorizontalLayout(LayoutProps props = default)
        {
            props = props ?? new LayoutProps();
            var control = new Control<LayoutProps>(props, "HorizontalLayout", typeof(HorizontalLayoutGroup));
            var layout = control.gameObject.GetComponent<HorizontalLayoutGroup>();
            control.AddBinding(BindLayout(props, layout));
            return control;
        }

        public static Control<LayoutProps> VerticalLayout(LayoutProps props = default)
        {
            props = props ?? new LayoutProps();
            var control = new Control<LayoutProps>(props, "VerticalLayout", typeof(VerticalLayoutGroup));
            var layout = control.gameObject.GetComponent<VerticalLayoutGroup>();
            control.AddBinding(BindLayout(props, layout));
            return control;
        }

        public static IDisposable BindLayout(LayoutProps props, HorizontalOrVerticalLayoutGroup layout)
        {
            return new ComposedDisposable(
                props.padding.Subscribe(x => layout.padding = x.currentValue),
                props.spacing.Subscribe(x => layout.spacing = x.currentValue),
                props.childAlignment.Subscribe(x => layout.childAlignment = x.currentValue),
                props.reverseArrangement.Subscribe(x => layout.reverseArrangement = x.currentValue),
                props.childForceExpandHeight.Subscribe(x => layout.childForceExpandHeight = x.currentValue),
                props.childForceExpandWidth.Subscribe(x => layout.childForceExpandWidth = x.currentValue),
                props.childControlWidth.Subscribe(x => layout.childControlWidth = x.currentValue),
                props.childControlHeight.Subscribe(x => layout.childControlHeight = x.currentValue),
                props.childScaleWidth.Subscribe(x => layout.childScaleWidth = x.currentValue),
                props.childScaleHeight.Subscribe(x => layout.childScaleHeight = x.currentValue)
            );
        }

        public class InputFieldProps : IDisposable
        {
            public event Action<string> onEndEdit;

            public ValueObservable<bool> interactable { get; } = new ValueObservable<bool>(true);
            public ValueObservable<TMP_ContentType> contentType { get; } = new ValueObservable<TMP_ContentType>();
            public ValueObservable<bool> readOnly { get; } = new ValueObservable<bool>();
            public ValueObservable<TMP_LineType> lineType { get; } = new ValueObservable<TMP_LineType>();
            public ValueObservable<int> characterLimit { get; } = new ValueObservable<int>();
            public TextProps inputText { get; } = DefaultTextProps();
            public TextProps placeholder { get; } = DefaultTextProps();
            public ImageProps background { get; } = DefaultImageProps();

            public void Dispose()
            {
                contentType.Dispose();
                readOnly.Dispose();
                lineType.Dispose();
                characterLimit.Dispose();
                interactable.Dispose();
                inputText.Dispose();
                placeholder.Dispose();
                background.Dispose();
            }

            public void RaiseEndEdit()
            {
                onEndEdit?.Invoke(inputText.text.value);
            }
        }

        public static Control<InputFieldProps> InputField(InputFieldProps props = default)
            => InputField(props ?? DefaultInputFieldProps(), out var _);

        private static Control<InputFieldProps> InputField(InputFieldProps props, out TMP_InputField inputFieldComponent)
        {
            props = props ?? DefaultInputFieldProps();
            var control = new Control<InputFieldProps>(props, "InputField", typeof(TMP_InputField));
            var inputField = control.gameObject.GetComponent<TMP_InputField>();

            IControl viewport;

            control.Children(
                Image(props.background, out var background).Name("Background").FillParent(),
                viewport = Control("Viewport", typeof(RectMask2D)).FillParent().Children(
                    Text(props.inputText, out var inputText).Name("InputText").FillParent(),
                    Text(props.placeholder, out var placeholder).Name("Placeholder").FillParent()
                )
            );

            inputField.targetGraphic = background;
            inputField.textViewport = viewport.transform;
            inputField.textComponent = inputText;
            inputField.placeholder = placeholder;

            inputField.enabled = false;
            inputField.enabled = true;

            inputField.onEndEdit.AddListener(x =>
            {
                props.inputText.text.value = x;
                props.RaiseEndEdit();
            });

            control.AddBinding(
                props.inputText.text.Subscribe(x => inputField.text = x.currentValue),
                props.contentType.Subscribe(x => inputField.contentType = x.currentValue),
                props.readOnly.Subscribe(x => inputField.readOnly = x.currentValue),
                props.lineType.Subscribe(x => inputField.lineType = x.currentValue),
                props.characterLimit.Subscribe(x => inputField.characterLimit = x.currentValue),
                props.interactable.Subscribe(x => inputField.interactable = x.currentValue)
            );

            inputFieldComponent = inputField;

            return control;
        }

        public static Control Space()
            => new Control("Space");

        public class ScrollbarProps : IDisposable
        {
            public ValueObservable<bool> selected { get; } = new ValueObservable<bool>();
            public ValueObservable<bool> interactable { get; } = new ValueObservable<bool>();
            public ValueObservable<float> value { get; } = new ValueObservable<float>();
            public ValueObservable<ScrollbarDirection> direction { get; } = new ValueObservable<ScrollbarDirection>();
            public ValueObservable<float> size { get; } = new ValueObservable<float>();
            public ValueObservable<int> numberOfSteps { get; } = new ValueObservable<int>();
            public ImageProps handle { get; } = DefaultImageProps();
            public ImageProps background { get; } = DefaultImageProps();

            public void Dispose()
            {
                value.Dispose();
                direction.Dispose();
                size.Dispose();
                numberOfSteps.Dispose();
                handle.Dispose();
                background.Dispose();
            }
        }

        public static Control<ScrollbarProps> Scrollbar(ScrollbarProps props = default)
            => Scrollbar(props ?? DefaultScrollbarProps(), out var _);

        public static Control<ScrollbarProps> Scrollbar(ScrollbarProps props, out Scrollbar scrollbarComponent)
        {
            props = props ?? DefaultScrollbarProps();
            var control = new Control<ScrollbarProps>(props, "Scrollbar", typeof(Scrollbar));
            var scrollbar = control.gameObject.GetComponent<Scrollbar>();

            control.Children(
                Image(props.background, out var background)
                    .FillParent()
                    .Children(
                        Image(props.handle, out var handle)
                            .FillParent()
                    )
            );

            scrollbar.handleRect = handle.rectTransform;
            scrollbar.targetGraphic = handle;
            scrollbar.onValueChanged.AddListener(x => props.value.value = x);

            control.AddBinding(
                props.value.Subscribe(x => scrollbar.value = x.currentValue),
                props.direction.Subscribe(x => scrollbar.direction = x.currentValue),
                props.size.Subscribe(x => scrollbar.size = x.currentValue),
                props.numberOfSteps.Subscribe(x => scrollbar.numberOfSteps = x.currentValue)
            );

            scrollbarComponent = scrollbar;

            return control;
        }

        public class ScrollRectProps : IDisposable
        {
            public ValueObservable<Vector2> value { get; } = new ValueObservable<Vector2>(new Vector2(0, 1));
            public ValueObservable<bool> horizontal { get; } = new ValueObservable<bool>(true);
            public ValueObservable<bool> vertical { get; } = new ValueObservable<bool>(true);
            public ValueObservable<ScrollRectMovementType> movementType { get; } = new ValueObservable<ScrollRectMovementType>(ScrollRectMovementType.Elastic);
            public ValueObservable<bool> inertia { get; } = new ValueObservable<bool>(true);
            public ValueObservable<float> decelerationRate { get; } = new ValueObservable<float>(1);
            public ValueObservable<float> scrollSensitivity { get; } = new ValueObservable<float>(1);
            public ValueObservable<ScrollRectScrollbarVisibility> horizontalScrollbarVisibility { get; } = new ValueObservable<ScrollRectScrollbarVisibility>(ScrollRectScrollbarVisibility.AutoHideAndExpandViewport);
            public ValueObservable<ScrollRectScrollbarVisibility> verticalScrollbarVisibility { get; } = new ValueObservable<ScrollRectScrollbarVisibility>(ScrollRectScrollbarVisibility.AutoHideAndExpandViewport);
            public ValueObservable<float> horizontalScrollbarSpacing { get; } = new ValueObservable<float>(3);
            public ValueObservable<float> verticalScrollbarSpacing { get; } = new ValueObservable<float>(3);
            public ImageProps background { get; } = DefaultImageProps();
            public ScrollbarProps verticalScrollbar { get; } = DefaultScrollbarProps();
            public ScrollbarProps horizontalScrollbar { get; } = DefaultScrollbarProps();

            public ScrollRectProps()
            {
                verticalScrollbar.direction.value = ScrollbarDirection.BottomToTop;
                horizontalScrollbar.direction.value = ScrollbarDirection.LeftToRight;
            }

            public void Dispose()
            {
                value.Dispose();
                horizontal.Dispose();
                vertical.Dispose();
                movementType.Dispose();
                inertia.Dispose();
                decelerationRate.Dispose();
                scrollSensitivity.Dispose();
                horizontalScrollbarVisibility.Dispose();
                verticalScrollbarVisibility.Dispose();
                horizontalScrollbarSpacing.Dispose();
                verticalScrollbarSpacing.Dispose();
                background.Dispose();
                verticalScrollbar.Dispose();
                horizontalScrollbar.Dispose();
            }
        }

        public static Control<ScrollRectProps> ScrollRect(ScrollRectProps props = default)
            => ScrollRect(props ?? DefaultScrollRectProps(), out var _);

        private static Control<ScrollRectProps> ScrollRect(ScrollRectProps props, out ScrollRect scrollRectComponent)
        {
            var control = new Control<ScrollRectProps>(props, "ScrollRect", typeof(ScrollRect));
            var scrollRect = control.gameObject.GetComponent<ScrollRect>();

            IControl viewport = default;
            IControl content = default;

            control.Children(
                Image(props.background).Name("Background").FillParent(),
                viewport = new Control("Viewport", typeof(RectMask2D))
                    .SetPivot(new Vector2(0, 1f))
                    .FillParent()
                    .Children(
                        content = new Control("Content", typeof(ContentSizeFitter), typeof(VerticalLayoutGroup))
                            .SetPivot(new Vector2(0, 1))
                            .AnchorToTop()
                    ),
                Scrollbar(props.horizontalScrollbar, out var horizontalScrollbar)
                    .SetPivot(Vector2.zero)
                    .AnchorMin(Vector2.zero)
                    .AnchorMax(Vector2.right)
                    .OffsetMin(Vector2.zero)
                    .OffsetMax(new Vector2(5f, 10f)),
                Scrollbar(props.verticalScrollbar, out var verticalScrollbar)
                    .SetPivot(Vector2.one)
                    .AnchorMin(Vector2.right)
                    .AnchorMax(Vector2.one)
                    .OffsetMin(new Vector2(-10f, -5f))
                    .OffsetMax(Vector2.zero)
            );

            var contentSizeFitter = content.gameObject.GetComponent<ContentSizeFitter>();
            var contentLayout = content.gameObject.GetComponent<VerticalLayoutGroup>();

            contentLayout.childControlWidth = true;
            contentLayout.childControlHeight = true;
            contentLayout.childForceExpandWidth = false;
            contentLayout.childForceExpandHeight = false;

            scrollRect.viewport = viewport.transform;
            scrollRect.horizontalScrollbar = horizontalScrollbar;
            scrollRect.verticalScrollbar = verticalScrollbar;
            scrollRect.content = content.transform;
            scrollRect.onValueChanged.AddListener(x => props.value.value = x);

            control.childParentOverride = (RectTransform)scrollRect.content.transform;
            control.AddBinding(
                props.value.Subscribe(x => scrollRect.normalizedPosition = x.currentValue),
                props.movementType.Subscribe(x => scrollRect.movementType = x.currentValue),
                props.inertia.Subscribe(x => scrollRect.inertia = x.currentValue),
                props.decelerationRate.Subscribe(x => scrollRect.decelerationRate = x.currentValue),
                props.scrollSensitivity.Subscribe(x => scrollRect.scrollSensitivity = x.currentValue),
                props.horizontalScrollbarVisibility.Subscribe(x => scrollRect.horizontalScrollbarVisibility = x.currentValue),
                props.verticalScrollbarVisibility.Subscribe(x => scrollRect.verticalScrollbarVisibility = x.currentValue),
                props.horizontalScrollbarSpacing.Subscribe(x => scrollRect.horizontalScrollbarSpacing = x.currentValue),
                props.verticalScrollbarSpacing.Subscribe(x => scrollRect.verticalScrollbarSpacing = x.currentValue),
                props.horizontal.Subscribe(x =>
                {
                    if (x.currentValue)
                    {
                        scrollRect.horizontal = true;
                        contentSizeFitter.horizontalFit = ContentSizeFitter.FitMode.PreferredSize;
                    }
                    else
                    {
                        scrollRect.horizontal = false;
                        contentSizeFitter.horizontalFit = ContentSizeFitter.FitMode.Unconstrained;
                        content.transform.FillParentWidth();
                    }
                }),
                props.vertical.Subscribe(x =>
                {
                    if (x.currentValue)
                    {
                        scrollRect.vertical = true;
                        contentSizeFitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;
                    }
                    else
                    {
                        scrollRect.vertical = false;
                        contentSizeFitter.verticalFit = ContentSizeFitter.FitMode.Unconstrained;
                        content.transform.FillParentHeight();
                    }
                })
            );

            scrollRectComponent = scrollRect;

            return control;
        }

        public class DropdownProps : IDisposable
        {
            public ValueObservable<bool> selected { get; } = new ValueObservable<bool>();
            public ValueObservable<bool> interactable { get; } = new ValueObservable<bool>(true);
            public ValueObservable<int> value { get; } = new ValueObservable<int>();
            public ValueObservable<bool> allowMultiselect { get; } = new ValueObservable<bool>();
            public ListObservable<string> options { get; } = new ListObservable<string>();

            public ImageProps background { get; } = DefaultImageProps();
            public TextStyleProps captionText { get; }
            public ImageProps arrow { get; } = DefaultImageProps();
            public ScrollRectProps template { get; } = DefaultScrollRectProps();
            public ImageProps itemBackground { get; } = DefaultImageProps();
            public TextStyleProps itemText { get; }
            public ImageProps itemCheckmark { get; } = DefaultImageProps();

            public void Dispose()
            {
                selected.Dispose();
                interactable.Dispose();
                value.Dispose();
                allowMultiselect.Dispose();
                options.Dispose();
                background.Dispose();
                captionText.Dispose();
                arrow.Dispose();
                template.Dispose();
                itemBackground.Dispose();
                itemText.Dispose();
                itemCheckmark.Dispose();
            }
        }

        public static Control<DropdownProps> Dropdown(DropdownProps props = default)
        {
            props = props ?? DefaultDropdownProps();
            var control = new Control<DropdownProps>(props, "Dropdown", typeof(TMP_Dropdown));
            var dropdown = control.gameObject.GetComponent<TMP_Dropdown>();

            IControl content;
            IControl itemToggle;

            control.Children(
                Image(props.background, out var background).Name("Background").FillParent(),
                Text(out var captionText).Name("CaptionText").Style(props.captionText).FillParent(),
                Image(props.arrow, out var arrow).Name("Arrow").AnchorToRight().SizeDelta(new Vector2(10, 10)).AnchoredPosition(new Vector2(-15f, -1.2f)),
                ScrollRect(props.template, out var template).SizeDelta(new Vector2(0, 150)).SetPivot(new Vector2(0, 1)).FillParentWidth().AnchorToBottom().Children(
                    content = VerticalLayout().Name("Content")
                        .FitContentVertical(ContentSizeFitter.FitMode.PreferredSize)
                        .SetPivot(new Vector2(0.5f, 1f))
                        .AnchorToTop()
                        .FillParentWidth()
                        .SizeDelta(new Vector2(0, 150f))
                        .Style(x =>
                        {
                            x.childControlWidth.value = true;
                            x.childControlHeight.value = true;
                        }),
                    itemToggle = Control("Item Toggle", typeof(Toggle)).PreferredHeight(30).Children(
                        Image(props.itemBackground, out var itemBackground)
                            .Name("Item Background")
                            .FillParent(),
                        Text(out var itemText)
                            .Name("Item Text")
                            .Style(props.itemText)
                            .FillParent(),
                        Image(props.itemCheckmark, out var itemCheckmark)
                            .Name("Item Checkmark")
                            .SetPivot(new Vector2(1f, 0.5f))
                            .SizeDelta(new Vector2(15, 15))
                            .AnchorToRight()
                            .AnchoredPosition(new Vector3(-10, 0, 0))
                    )
                )
            );

            var itemToggleComponent = itemToggle.gameObject.GetComponent<Toggle>();
            itemToggleComponent.graphic = itemCheckmark;
            itemToggleComponent.targetGraphic = itemBackground;

            dropdown.targetGraphic = background;
            dropdown.template = (RectTransform)template.transform;
            dropdown.captionText = captionText;
            dropdown.itemText = itemText;
            dropdown.onValueChanged.AddListener(x => props.value.value = x);

            template.gameObject.SetActive(false);

            control.AddBinding(
                props.value.Subscribe(x => dropdown.value = x.currentValue),
                props.options.Subscribe(_ => dropdown.options = props.options.Select(x => new TMP_Dropdown.OptionData() { text = x }).ToList()),
                props.interactable.Subscribe(x => dropdown.interactable = x.currentValue)
            );

            return control;
        }
    }
}
