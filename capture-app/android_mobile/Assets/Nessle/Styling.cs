using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using ObserveThing;
using TMPro;
using UnityEngine;
using TMP_LineType = TMPro.TMP_InputField.LineType;
using TMP_ContentType = TMPro.TMP_InputField.ContentType;
using TMP_FontStyles = TMPro.FontStyles;
using ScrollRectScrollbarVisibility = UnityEngine.UI.ScrollRect.ScrollbarVisibility;
using ScrollRectMovementType = UnityEngine.UI.ScrollRect.MovementType;

namespace Nessle
{
    public interface IStyleProperty
    {
        string identifier { get; }
        Type type { get; }

        IStyleProperty Clone();
    }

    public class StyleProperty<T> : IStyleProperty
    {
        public string identifier { get; }
        public IValueObservable<T> defaultValue { get; }
        public Type type => typeof(T);

        public StyleProperty(string identifier)
            : this(identifier, new ValueObservable<T>()) { }

        public StyleProperty(string identifier, T defaultValue)
            : this(identifier, new ValueObservable<T>(defaultValue)) { }

        public StyleProperty(string identifier, IValueObservable<T> defaultValue)
        {
            this.identifier = identifier;
            this.defaultValue = defaultValue;
        }

        public IStyleProperty Clone()
            => new StyleProperty<T>(identifier, defaultValue);
    }

    public static class StyleProperties
    {
        public static StyleProperty<float> FontSize { get; } = new StyleProperty<float>(nameof(FontSize), 16f);
        public static StyleProperty<TMP_FontStyles> FontStyle { get; } = new StyleProperty<TMP_FontStyles>(nameof(FontStyle), TMP_FontStyles.Normal);
        public static StyleProperty<Color> Color { get; } = new StyleProperty<Color>(nameof(Color), UnityEngine.Color.white);
        public static StyleProperty<TextAlignmentOptions> Alignment { get; } = new StyleProperty<TextAlignmentOptions>(nameof(Alignment));
        public static StyleProperty<TMP_FontAsset> Font { get; } = new StyleProperty<TMP_FontAsset>(nameof(Font));
        public static StyleProperty<Vector4> Margin { get; } = new StyleProperty<Vector4>(nameof(Margin));
        public static StyleProperty<TextWrappingModes> WrappingMode { get; } = new StyleProperty<TextWrappingModes>(nameof(WrappingMode));
        public static StyleProperty<TextOverflowModes> OverflowMode { get; } = new StyleProperty<TextOverflowModes>(nameof(OverflowMode));
        public static StyleProperty<FontWeight> FontWeight { get; } = new StyleProperty<FontWeight>(nameof(FontWeight));

        public static StyleProperty<float> PlaceholderFontSize { get; } = new StyleProperty<float>(nameof(PlaceholderFontSize), 16f);
        public static StyleProperty<TMP_FontStyles> PlaceholderFontStyle { get; } = new StyleProperty<TMP_FontStyles>(nameof(PlaceholderFontStyle), TMP_FontStyles.Normal);
        public static StyleProperty<Color> PlaceholderColor { get; } = new StyleProperty<Color>(nameof(PlaceholderColor), UnityEngine.Color.white);
        public static StyleProperty<TextAlignmentOptions> PlaceholderAlignment { get; } = new StyleProperty<TextAlignmentOptions>(nameof(PlaceholderAlignment));
        public static StyleProperty<TMP_FontAsset> PlaceholderFont { get; } = new StyleProperty<TMP_FontAsset>(nameof(PlaceholderFont));
        public static StyleProperty<Vector4> PlaceholderMargin { get; } = new StyleProperty<Vector4>(nameof(PlaceholderMargin));
        public static StyleProperty<TextWrappingModes> PlaceholderWrappingMode { get; } = new StyleProperty<TextWrappingModes>(nameof(PlaceholderWrappingMode));
        public static StyleProperty<TextOverflowModes> PlaceholderOverflowMode { get; } = new StyleProperty<TextOverflowModes>(nameof(PlaceholderOverflowMode));
        public static StyleProperty<FontWeight> PlaceholderFontWeight { get; } = new StyleProperty<FontWeight>(nameof(PlaceholderFontWeight));

        public static StyleProperty<float> ScrollbarSize { get; } = new StyleProperty<float>(nameof(ScrollbarSize));
        public static StyleProperty<int> ScrollbarNumberOfSteps { get; } = new StyleProperty<int>(nameof(ScrollbarNumberOfSteps), 0);
        public static StyleProperty<Sprite> ScrollbarHandleSprite { get; } = new StyleProperty<Sprite>(nameof(ScrollbarHandleSprite));
        public static StyleProperty<Color> ScrollbarHandleColor { get; } = new StyleProperty<Color>(nameof(ScrollbarHandleSprite));
        public static StyleProperty<Sprite> ScrollbarBackgroundSprite { get; } = new StyleProperty<Sprite>(nameof(ScrollbarBackgroundSprite));
        public static StyleProperty<Color> ScrollbarBackgroundColor { get; } = new StyleProperty<Color>(nameof(ScrollbarBackgroundSprite));


        public static StyleProperty<ScrollRectMovementType> MovementType { get; } = new StyleProperty<ScrollRectMovementType>(nameof(MovementType));
        public static StyleProperty<bool> Inertia { get; } = new StyleProperty<bool>(nameof(Inertia));
        public static StyleProperty<float> DecelerationRate { get; } = new StyleProperty<float>(nameof(DecelerationRate));
        public static StyleProperty<float> ScrollSensitivity { get; } = new StyleProperty<float>(nameof(ScrollSensitivity));
        public static StyleProperty<ScrollRectScrollbarVisibility> ScrollbarVisibility { get; } = new StyleProperty<ScrollRectScrollbarVisibility>(nameof(ScrollbarVisibility));
        public static StyleProperty<float> ScrollbarSpacing { get; } = new StyleProperty<float>(nameof(ScrollbarSpacing));


        public static StyleProperty<Color> OutlineColor { get; } = new StyleProperty<Color>(nameof(OutlineColor), UnityEngine.Color.grey);
        public static StyleProperty<Color> BackgroundColor { get; } = new StyleProperty<Color>(nameof(BackgroundColor), UnityEngine.Color.grey);
        public static StyleProperty<Sprite> BackgroundSprite { get; } = new StyleProperty<Sprite>(nameof(BackgroundSprite));
        public static StyleProperty<AnimationCurve> Transition { get; } = new StyleProperty<AnimationCurve>(nameof(Transition), AnimationCurve.EaseInOut(0, 0, 1, 1));
        public static StyleProperty<bool> Interactable { get; } = new StyleProperty<bool>(nameof(Interactable), true);
        public static StyleProperty<RectOffset> Padding { get; } = new StyleProperty<RectOffset>(nameof(Padding));
        public static StyleProperty<float> Spacing { get; } = new StyleProperty<float>(nameof(Spacing), 10f);
        public static StyleProperty<bool> ReverseArrangement { get; } = new StyleProperty<bool>(nameof(ReverseArrangement), false);
        public static StyleProperty<TextAnchor> ChildAlignment { get; } = new StyleProperty<TextAnchor>(nameof(ChildAlignment), TextAnchor.UpperLeft);
        public static StyleProperty<bool> ControlChildWidth { get; } = new StyleProperty<bool>(nameof(ControlChildWidth), false);
        public static StyleProperty<bool> ControlChildHeight { get; } = new StyleProperty<bool>(nameof(ControlChildHeight), false);
        public static StyleProperty<bool> ForceChildExpandWidth { get; } = new StyleProperty<bool>(nameof(ForceChildExpandWidth), false);
        public static StyleProperty<bool> ForceChildExpandHeight { get; } = new StyleProperty<bool>(nameof(ForceChildExpandHeight), false);
        public static StyleProperty<bool> ScaleChildWidth { get; } = new StyleProperty<bool>(nameof(ScaleChildWidth), false);
        public static StyleProperty<bool> ScaleChildHeight { get; } = new StyleProperty<bool>(nameof(ScaleChildHeight), false);
        public static StyleProperty<float> PixelsPerUnitMultiplier { get; } = new StyleProperty<float>(nameof(PixelsPerUnitMultiplier));
        public static StyleProperty<bool> PreserveAspect { get; } = new StyleProperty<bool>(nameof(PreserveAspect));
        public static StyleProperty<UnityEngine.UI.Image.Type> ImageType { get; } = new StyleProperty<UnityEngine.UI.Image.Type>(nameof(ImageType));
        public static StyleProperty<TMP_LineType> LineType { get; } = new StyleProperty<TMP_LineType>(nameof(LineType), TMP_LineType.SingleLine);
        public static StyleProperty<bool> ReadOnly { get; } = new StyleProperty<bool>(nameof(ReadOnly), false);
        public static StyleProperty<int> CharacterLimit { get; } = new StyleProperty<int>(nameof(CharacterLimit), 0);
        public static StyleProperty<TMP_ContentType> ContentType { get; } = new StyleProperty<TMP_ContentType>(nameof(ContentType), TMP_ContentType.Standard);
    }

    public interface IStyleEntry
    {
        IStyleProperty property { get; }
        string state { get; }

        IStyleEntry Clone();
    }

    public class StyleEntry<T> : IStyleEntry
    {
        public string state { get; private set; }
        public StyleProperty<T> property { get; private set; }
        public IValueObservable<T> value { get; private set; }

        IStyleProperty IStyleEntry.property => property;

        public StyleEntry(StyleProperty<T> property, T value)
            : this(null, property, new ValueObservable<T>(value)) { }

        public StyleEntry(string state, StyleProperty<T> property, T value)
            : this(state, property, new ValueObservable<T>(value)) { }

        public StyleEntry(StyleProperty<T> property, IValueObservable<T> value)
            : this(null, property, value) { }

        public StyleEntry(string state, StyleProperty<T> property, IValueObservable<T> value)
        {
            this.property = property;
            this.state = state;
            this.value = value;
        }

        public IStyleEntry Clone()
            => new StyleEntry<T>(state, property, value);
    }

    public class Style : IEnumerable<IStyleEntry>
    {
        private Dictionary<IStyleProperty, IStyleEntry> _defaultPropertyLookup = new Dictionary<IStyleProperty, IStyleEntry>();
        private Dictionary<string, Dictionary<IStyleProperty, IStyleEntry>> _statedPropertyLookup = new Dictionary<string, Dictionary<IStyleProperty, IStyleEntry>>();

        public bool TryGetPropertyValue<T>(StyleProperty<T> property, out IValueObservable<T> value)
            => TryGetPropertyValue(property, null, out value);

        public bool TryGetPropertyValue<T>(StyleProperty<T> property, string state, out IValueObservable<T> value)
        {
            if (state != null &&
                _statedPropertyLookup.TryGetValue(state, out var statedLookup) &&
                statedLookup.TryGetValue(property, out var statedEntry))
            {
                value = ((StyleEntry<T>)statedEntry).value;
                return true;
            }

            if (_defaultPropertyLookup.TryGetValue(property, out var entry))
            {
                value = ((StyleEntry<T>)entry).value;
                return true;
            }

            value = default;
            return false;
        }

        public void Add<T>(StyleProperty<T> property, T value)
            => Add(new StyleEntry<T>(property, value));

        public void Add<T>(string state, StyleProperty<T> property, T value)
            => Add(new StyleEntry<T>(state, property, value));

        public void Add<T>(StyleProperty<T> property, IValueObservable<T> value)
            => Add(new StyleEntry<T>(property, value));

        public void Add<T>(string state, StyleProperty<T> property, IValueObservable<T> value)
            => Add(new StyleEntry<T>(state, property, value));

        public void Add(IStyleEntry entry)
        {
            Dictionary<IStyleProperty, IStyleEntry> propertyLookup;

            if (entry.state == null)
            {
                propertyLookup = _defaultPropertyLookup;
            }
            else if (!_statedPropertyLookup.TryGetValue(entry.state, out propertyLookup))
            {
                propertyLookup = new Dictionary<IStyleProperty, IStyleEntry>();
                _statedPropertyLookup.Add(entry.state, propertyLookup);
            }

            propertyLookup[entry.property] = entry;
        }

        public IEnumerator<IStyleEntry> GetEnumerator()
        {
            foreach (var entry in _defaultPropertyLookup.Values.Concat(_statedPropertyLookup.Values.SelectMany(x => x.Values)))
                yield return entry;
        }

        IEnumerator IEnumerable.GetEnumerator()
        {
            return GetEnumerator();
        }
    }
}