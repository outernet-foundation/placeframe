using System;
using System.Linq;
using ObserveThing;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

using TMP_ContentType = TMPro.TMP_InputField.ContentType;
using TMP_LineType = TMPro.TMP_InputField.LineType;
using ScrollbarDirection = UnityEngine.UI.Scrollbar.Direction;
using SliderDirection = UnityEngine.UI.Slider.Direction;

namespace Nessle
{
    public static class UIBuilder
    {
        public static Control Control(string identifier, params Type[] components)
            => new Control(identifier, components);

        public static Control<T> Control<T>(string identifier, T props, params Type[] components)
            => new Control<T>(identifier, props, components);

        public class TextProps : IDisposable
        {
            public ValueObservable<string> text { get; } = new ValueObservable<string>();

            public void Dispose()
            {
                text.Dispose();
            }
        }

        public static Control<TextProps> Text(string identifier = "text", TextProps props = default, TextMeshProUGUI prefab = default, Action<Control<TextProps>> setup = default)
        {
            var text = UnityEngine.Object.Instantiate(prefab == null ? UIResources.Text : prefab);
            var control = new Control<TextProps>(identifier, props ?? new TextProps(), text.gameObject);

            control.AddBinding(
                control.props.text.Subscribe(x => text.text = x.currentValue)
            );

            setup?.Invoke(control);

            return control;
        }

        public class ImageProps : IDisposable
        {
            public ValueObservable<Sprite> sprite { get; } = new ValueObservable<Sprite>();
            public ValueObservable<Color> color { get; } = new ValueObservable<Color>();

            public void Dispose()
            {
                sprite.Dispose();
                color.Dispose();
            }
        }

        public static Control<ImageProps> Image(string identifier = "image", ImageProps props = default, Image prefab = default)
        {
            var image = prefab == null ? new GameObject(identifier, typeof(Image)).GetComponent<Image>() : UnityEngine.Object.Instantiate(prefab);
            var control = new Control<ImageProps>(identifier, props ?? new ImageProps(), image.gameObject);

            control.AddBinding(
                control.props.sprite.Subscribe(x => image.sprite = x.currentValue),
                control.props.color.Subscribe(x => image.color = x.currentValue)
            );

            return control;
        }

        public class ButtonProps : IDisposable
        {
            public ValueObservable<Action> onClick { get; } = new ValueObservable<Action>();
            public ValueObservable<bool> interactable { get; } = new ValueObservable<bool>(true);

            public void Dispose()
            {
                onClick.Dispose();
                interactable.Dispose();
            }
        }

        public static Control<ButtonProps> Button(string identifier = "button", ButtonProps props = default, Button prefab = default, Action<IControl<ButtonProps>> setup = default)
        {
            var button = UnityEngine.Object.Instantiate(prefab == null ? UIResources.Button : prefab);
            var control = new Control<ButtonProps>(identifier, props ?? new ButtonProps(), button.gameObject);

            button.onClick.AddListener(() => control.props.onClick.value?.Invoke());

            control.AddBinding(control.props.interactable.Subscribe(x => button.interactable = x.currentValue));

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

        public static Control<LayoutProps> HorizontalLayout(string identifier = "horizontalLayout.layout", LayoutProps props = default, HorizontalLayoutGroup prefab = default)
        {
            var layout = UnityEngine.Object.Instantiate(prefab == null ? UIResources.HorizontalLayout : prefab);
            var control = new Control<LayoutProps>(identifier, props ?? new LayoutProps(), layout.gameObject);

            control.AddBinding(
                control.props.padding.Subscribe(x => layout.padding = x.currentValue),
                control.props.spacing.Subscribe(x => layout.spacing = x.currentValue),
                control.props.childAlignment.Subscribe(x => layout.childAlignment = x.currentValue),
                control.props.reverseArrangement.Subscribe(x => layout.reverseArrangement = x.currentValue),
                control.props.childForceExpandHeight.Subscribe(x => layout.childForceExpandHeight = x.currentValue),
                control.props.childForceExpandWidth.Subscribe(x => layout.childForceExpandWidth = x.currentValue),
                control.props.childControlWidth.Subscribe(x => layout.childControlWidth = x.currentValue),
                control.props.childControlHeight.Subscribe(x => layout.childControlHeight = x.currentValue),
                control.props.childScaleWidth.Subscribe(x => layout.childScaleWidth = x.currentValue),
                control.props.childScaleHeight.Subscribe(x => layout.childScaleHeight = x.currentValue)
            );

            return control;
        }

        public static Control<LayoutProps> VerticalLayout(string identifier = "verticalLayout.layout", LayoutProps props = default, VerticalLayoutGroup prefab = default)
        {
            var layout = UnityEngine.Object.Instantiate(prefab == null ? UIResources.VerticalLayout : prefab);
            var control = new Control<LayoutProps>(identifier, props ?? new LayoutProps(), layout.gameObject);

            control.AddBinding(
                control.props.padding.Subscribe(x => layout.padding = x.currentValue),
                control.props.spacing.Subscribe(x => layout.spacing = x.currentValue),
                control.props.childAlignment.Subscribe(x => layout.childAlignment = x.currentValue),
                control.props.reverseArrangement.Subscribe(x => layout.reverseArrangement = x.currentValue),
                control.props.childForceExpandHeight.Subscribe(x => layout.childForceExpandHeight = x.currentValue),
                control.props.childForceExpandWidth.Subscribe(x => layout.childForceExpandWidth = x.currentValue),
                control.props.childControlWidth.Subscribe(x => layout.childControlWidth = x.currentValue),
                control.props.childControlHeight.Subscribe(x => layout.childControlHeight = x.currentValue),
                control.props.childScaleWidth.Subscribe(x => layout.childScaleWidth = x.currentValue),
                control.props.childScaleHeight.Subscribe(x => layout.childScaleHeight = x.currentValue)
            );

            return control;
        }

        public class InputFieldProps : IDisposable
        {
            public ValueObservable<string> inputText { get; } = new ValueObservable<string>();
            public ValueObservable<string> placeholderText { get; } = new ValueObservable<string>();
            public ValueObservable<TMP_ContentType> contentType { get; } = new ValueObservable<TMP_ContentType>();
            public ValueObservable<bool> readOnly { get; } = new ValueObservable<bool>();
            public ValueObservable<TMP_LineType> lineType { get; } = new ValueObservable<TMP_LineType>();
            public ValueObservable<int> characterLimit { get; } = new ValueObservable<int>();
            public ValueObservable<bool> interactable { get; } = new ValueObservable<bool>(true);
            public ValueObservable<Action<string>> onEndEdit { get; } = new ValueObservable<Action<string>>();

            public void Dispose()
            {
                inputText.Dispose();
                placeholderText.Dispose();
                contentType.Dispose();
                readOnly.Dispose();
                lineType.Dispose();
                characterLimit.Dispose();
                interactable.Dispose();
                onEndEdit.Dispose();
            }
        }

        public static Control<InputFieldProps> InputField(string identifier = "inputField", InputFieldProps props = default, TMP_InputField prefab = default)
        {
            var inputField = UnityEngine.Object.Instantiate(prefab == null ? UIResources.InputField : prefab);
            var control = new Control<InputFieldProps>(identifier, props ?? new InputFieldProps(), inputField.gameObject);

            inputField.enabled = false;
            inputField.enabled = true;

            inputField.onValueChanged.AddListener(x => control.props.inputText.From(x));
            inputField.onEndEdit.AddListener(x => control.props.onEndEdit.value?.Invoke(x));

            control.AddBinding(
                control.props.inputText.Subscribe(x => inputField.text = x.currentValue),
                control.props.placeholderText.Subscribe(x =>
                {
                    if (inputField.placeholder is TextMeshProUGUI placeholder)
                        placeholder.text = x.currentValue;
                }),
                control.props.contentType.Subscribe(x => inputField.contentType = x.currentValue),
                control.props.readOnly.Subscribe(x => inputField.readOnly = x.currentValue),
                control.props.lineType.Subscribe(x => inputField.lineType = x.currentValue),
                control.props.characterLimit.Subscribe(x => inputField.characterLimit = x.currentValue),
                control.props.interactable.Subscribe(x => inputField.interactable = x.currentValue)
            );

            return control;
        }

        public class FloatFieldProps : IDisposable
        {
            public ValueObservable<float> value { get; } = new ValueObservable<float>();
            public ValueObservable<string> placeholderText { get; } = new ValueObservable<string>();
            public ValueObservable<bool> readOnly { get; } = new ValueObservable<bool>();
            public ValueObservable<bool> interactable { get; } = new ValueObservable<bool>(true);

            public void Dispose()
            {
                value.Dispose();
                placeholderText.Dispose();
                readOnly.Dispose();
                interactable.Dispose();
            }
        }

        public static Control<FloatFieldProps> FloatField(string identifier = "floatField", FloatFieldProps props = default, TMP_InputField prefab = default)
        {
            var inputField = UnityEngine.Object.Instantiate(prefab == null ? UIResources.InputField : prefab);
            var control = new Control<FloatFieldProps>(identifier, props ?? new FloatFieldProps(), inputField.gameObject);

            inputField.enabled = false;
            inputField.enabled = true;

            inputField.onEndEdit.AddListener(x => control.props.value.From(float.TryParse(x, out var value) ? value : 0));

            control.AddBinding(
                control.props.value.Subscribe(x => inputField.text = x.currentValue.ToString()),
                control.props.placeholderText.Subscribe(x =>
                {
                    if (inputField.placeholder is TextMeshProUGUI placeholder)
                        placeholder.text = x.currentValue;
                }),
                control.props.readOnly.Subscribe(x => inputField.readOnly = x.currentValue),
                control.props.interactable.Subscribe(x => inputField.interactable = x.currentValue)
            );

            return control;
        }

        public class IntFieldProps : IDisposable
        {
            public ValueObservable<int> value { get; } = new ValueObservable<int>();
            public ValueObservable<string> placeholderText { get; } = new ValueObservable<string>();
            public ValueObservable<bool> readOnly { get; } = new ValueObservable<bool>();
            public ValueObservable<bool> interactable { get; } = new ValueObservable<bool>(true);

            public void Dispose()
            {
                value.Dispose();
                placeholderText.Dispose();
                readOnly.Dispose();
                interactable.Dispose();
            }
        }

        public static Control<IntFieldProps> IntField(string identifier = "intField", IntFieldProps props = default, TMP_InputField prefab = default)
        {
            var inputField = UnityEngine.Object.Instantiate(prefab == null ? UIResources.InputField : prefab);
            var control = new Control<IntFieldProps>(identifier, props ?? new IntFieldProps(), inputField.gameObject);

            inputField.enabled = false;
            inputField.enabled = true;

            inputField.onEndEdit.AddListener(x => control.props.value.From(int.TryParse(x, out var value) ? value : 0));

            control.AddBinding(
                control.props.value.Subscribe(x => inputField.text = x.currentValue.ToString()),
                control.props.placeholderText.Subscribe(x =>
                {
                    if (inputField.placeholder is TextMeshProUGUI placeholder)
                        placeholder.text = x.currentValue;
                }),
                control.props.readOnly.Subscribe(x => inputField.readOnly = x.currentValue),
                control.props.interactable.Subscribe(x => inputField.interactable = x.currentValue)
            );

            return control;
        }

        public static Control Space(string identifier = "space")
            => new Control(identifier);

        public class ScrollbarProps : IDisposable
        {
            public ValueObservable<float> value { get; } = new ValueObservable<float>();
            public ValueObservable<ScrollbarDirection> direction { get; } = new ValueObservable<ScrollbarDirection>();
            public ValueObservable<float> size { get; } = new ValueObservable<float>();
            public ValueObservable<bool> interactable { get; } = new ValueObservable<bool>(true);

            public void Dispose()
            {
                value.Dispose();
                direction.Dispose();
                size.Dispose();
                interactable.Dispose();
            }
        }

        public static Control<ScrollbarProps> Scrollbar(string identifier = "scrollbar", ScrollbarProps props = default, Scrollbar prefab = default)
        {
            var scrollbar = UnityEngine.Object.Instantiate(prefab == null ? UIResources.Scrollbar : prefab);
            var control = new Control<ScrollbarProps>(identifier, props ?? new ScrollbarProps(), scrollbar.gameObject);

            scrollbar.onValueChanged.AddListener(x => control.props.value.From(x));

            control.AddBinding(
                control.props.value.Subscribe(x => scrollbar.value = x.currentValue),
                control.props.direction.Subscribe(x => scrollbar.direction = x.currentValue),
                control.props.size.Subscribe(x => scrollbar.size = x.currentValue),
                control.props.interactable.Subscribe(x => scrollbar.interactable = x.currentValue)
            );

            return control;
        }

        public class ScrollRectProps : IDisposable
        {
            public ValueObservable<Vector2> value { get; } = new ValueObservable<Vector2>(new Vector2(0, 1));
            public ValueObservable<bool> horizontal { get; } = new ValueObservable<bool>(true);
            public ValueObservable<bool> vertical { get; } = new ValueObservable<bool>(true);
            public ValueObservable<IControl> content { get; } = new ValueObservable<IControl>();

            public void Dispose()
            {
                value.Dispose();
                horizontal.Dispose();
                vertical.Dispose();
                content.Dispose();
            }
        }

        public static IControl<ScrollRectProps> ScrollRect(Action<IControl<ScrollRectProps>> setup)
            => ScrollRect(props: default, setup: setup);

        public static Control<ScrollRectProps> ScrollRect(string identifier = "scrollRect", ScrollRectProps props = default, ScrollRect prefab = default, Action<IControl<ScrollRectProps>> setup = default)
        {
            var scrollRect = UnityEngine.Object.Instantiate(prefab == null ? UIResources.ScrollRect : prefab);
            var control = new Control<ScrollRectProps>(identifier, props ?? new ScrollRectProps(), scrollRect.gameObject);

            scrollRect.onValueChanged.AddListener(x => control.props.value.From(x));

            control.AddBinding(
                control.props.value.Subscribe(x => scrollRect.normalizedPosition = x.currentValue),
                control.props.horizontal.Subscribe(x => scrollRect.horizontal = x.currentValue),
                control.props.vertical.Subscribe(x => scrollRect.vertical = x.currentValue),
                control.props.content.Subscribe(x =>
                {
                    x.currentValue.SetParent(control);
                    x.currentValue.transform.SetParent(scrollRect.viewport, false);
                    scrollRect.content = x.currentValue.transform;
                    x.currentValue.SetPivot(new Vector2(0, 1));
                    x.currentValue.AnchorToTop();
                })
            );

            return control;
        }

        public class DropdownProps : IDisposable
        {
            public ValueObservable<int> value { get; } = new ValueObservable<int>();
            public ValueObservable<bool> allowMultiselect { get; } = new ValueObservable<bool>();
            public ListObservable<string> options { get; } = new ListObservable<string>();
            public ValueObservable<bool> interactable { get; } = new ValueObservable<bool>(true);

            public void Dispose()
            {
                value.Dispose();
                allowMultiselect.Dispose();
                options.Dispose();
                interactable.Dispose();
            }
        }

        public static Control<DropdownProps> Dropdown(string identifier = "dropdown", DropdownProps props = default, TMP_Dropdown prefab = default)
        {
            var dropdown = UnityEngine.Object.Instantiate(prefab == null ? UIResources.Dropdown : prefab);
            var control = new Control<DropdownProps>(identifier, props ?? new DropdownProps(), dropdown.gameObject);

            control.AddBinding(
                control.props.value.Subscribe(x => dropdown.value = x.currentValue),
                control.props.allowMultiselect.Subscribe(x => dropdown.MultiSelect = x.currentValue),
                control.props.options.Subscribe(_ => dropdown.options = control.props.options.Select(x => new TMP_Dropdown.OptionData() { text = x }).ToList()),
                control.props.interactable.Subscribe(x => dropdown.interactable = x.currentValue)
            );

            return control;
        }

        public class ToggleProps : IDisposable
        {
            public ValueObservable<bool> isOn { get; } = new ValueObservable<bool>();

            public void Dispose()
            {
                isOn.Dispose();
            }
        }

        public static Control<ToggleProps> Toggle(string identifier = "toggle", ToggleProps props = default, Toggle prefab = default)
        {
            var toggle = UnityEngine.Object.Instantiate(prefab == null ? UIResources.Toggle : prefab);
            var control = new Control<ToggleProps>(identifier, props ?? new ToggleProps(), toggle.gameObject);

            toggle.onValueChanged.AddListener(x => control.props.isOn.From(x));

            control.AddBinding(control.props.isOn.Subscribe(x => toggle.isOn = x.currentValue));

            return control;
        }

        public class SliderProps : IDisposable
        {
            public ValueObservable<float> value { get; } = new ValueObservable<float>();
            public ValueObservable<float> minValue { get; } = new ValueObservable<float>();
            public ValueObservable<float> maxValue { get; } = new ValueObservable<float>();
            public ValueObservable<bool> wholeNumbers { get; } = new ValueObservable<bool>();
            public ValueObservable<SliderDirection> direction { get; } = new ValueObservable<SliderDirection>();

            public void Dispose()
            {
                value.Dispose();
                minValue.Dispose();
                maxValue.Dispose();
                wholeNumbers.Dispose();
                direction.Dispose();
            }
        }

        public static Control<SliderProps> Slider(string identifier = "slider", SliderProps props = default, Slider prefab = default)
        {
            var slider = UnityEngine.Object.Instantiate(prefab == null ? UIResources.Slider : prefab);
            var control = new Control<SliderProps>(identifier, props ?? new SliderProps(), slider.gameObject);

            slider.onValueChanged.AddListener(x => control.props.value.From(x));

            control.AddBinding(
                control.props.value.Subscribe(x => slider.value = x.currentValue),
                control.props.minValue.Subscribe(x => slider.minValue = x.currentValue),
                control.props.maxValue.Subscribe(x => slider.maxValue = x.currentValue),
                control.props.wholeNumbers.Subscribe(x => slider.wholeNumbers = x.currentValue),
                control.props.direction.Subscribe(x => slider.direction = x.currentValue)
            );

            return control;
        }
    }
}
