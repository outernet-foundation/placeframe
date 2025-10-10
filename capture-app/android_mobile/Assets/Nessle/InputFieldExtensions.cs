using System;
using ObserveThing;
using TMP_ContentType = TMPro.TMP_InputField.ContentType;
using TMP_LineType = TMPro.TMP_InputField.LineType;
using FofX.Stateful;
using static Nessle.UIBuilder;

namespace Nessle
{
    public static class InputFieldExtensions
    {
        public static T Text<T>(this T control, string text)
            where T : IControl<InputFieldProps>
        {
            control.props.inputText.value = text;
            return control;
        }

        public static T Text<T>(this T control, IValueObservable<string> text)
            where T : IControl<InputFieldProps>
        {
            control.props.inputText.From(text);
            return control;
        }

        public static T OnChange<T>(this T control, Action<string> onChange)
            where T : IControl<InputFieldProps>
        {
            control.AddBinding(control.props.inputText.Subscribe(x => onChange(x.currentValue)));
            return control;
        }

        public static T ContentType<T>(this T control, TMP_ContentType contentType)
            where T : IControl<InputFieldProps>
        {
            control.props.contentType.value = contentType;
            return control;
        }

        public static T ContentType<T>(this T control, IValueObservable<TMP_ContentType> contentType)
            where T : IControl<InputFieldProps>
        {
            control.props.contentType.From(contentType);
            return control;
        }

        public static T ReadOnly<T>(this T control, bool readOnly)
            where T : IControl<InputFieldProps>
        {
            control.props.readOnly.value = readOnly;
            return control;
        }

        public static T ReadOnly<T>(this T control, IValueObservable<bool> readOnly)
            where T : IControl<InputFieldProps>
        {
            control.props.readOnly.From(readOnly);
            return control;
        }

        public static T Interactable<T>(this T control, bool interactable)
            where T : IControl<InputFieldProps>
        {
            control.props.interactable.value = interactable;
            return control;
        }

        public static T Interactable<T>(this T control, IValueObservable<bool> interactable)
            where T : IControl<InputFieldProps>
        {
            control.props.interactable.From(interactable);
            return control;
        }

        public static T OnEndEdit<T>(this T control, Action<string> onEndEdit)
            where T : IControl<InputFieldProps>
        {
            control.props.onEndEdit.value = onEndEdit;
            return control;
        }

        public static T OnEndEdit<T>(this T control, IValueObservable<Action<string>> onEndEdit)
            where T : IControl<InputFieldProps>
        {
            control.props.onEndEdit.From(onEndEdit);
            return control;
        }

        public static T PlaceholderText<T>(this T control, string placeholderText)
            where T : IControl<InputFieldProps>
        {
            control.props.placeholderText.value = placeholderText;
            return control;
        }

        public static T PlaceholderText<T>(this T control, IValueObservable<string> placeholderText)
            where T : IControl<InputFieldProps>
        {
            control.props.placeholderText.From(placeholderText);
            return control;
        }

        public static T LineType<T>(this T control, TMP_LineType lineType)
            where T : IControl<InputFieldProps>
        {
            control.props.lineType.value = lineType;
            return control;
        }

        public static T LineType<T>(this T control, IValueObservable<TMP_LineType> lineType)
            where T : IControl<InputFieldProps>
        {
            control.props.lineType.From(lineType);
            return control;
        }

        public static T CharacterLimit<T>(this T control, int characterLimit)
            where T : IControl<InputFieldProps>
        {
            control.props.characterLimit.value = characterLimit;
            return control;
        }

        public static T CharacterLimit<T>(this T control, IValueObservable<int> characterLimit)
            where T : IControl<InputFieldProps>
        {
            control.props.characterLimit.From(characterLimit);
            return control;
        }

        public static T BindValue<T>(this T control, ObservablePrimitive<string> bindTo)
            where T : IControl<InputFieldProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.inputText.value = x.currentValue),
                control.props.inputText.Subscribe(x => bindTo.ExecuteSetOrDelay(x.currentValue))
            );

            return control;
        }

        public static TControl BindValue<TControl, TValue>(this TControl control, ObservablePrimitive<TValue> bindTo, Func<string, TValue> toState, Func<TValue, string> toControl)
            where TControl : IControl<InputFieldProps>
        {
            control.AddBinding(
                bindTo.Subscribe(x => control.props.inputText.value = toControl(x.currentValue)),
                control.props.inputText.Subscribe(x => bindTo.ExecuteSetOrDelay(toState(x.currentValue)))
            );

            return control;
        }
    }
}
