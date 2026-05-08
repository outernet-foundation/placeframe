using System;
using System.Collections.Generic;

using UnityEngine;
using UnityEngine.Events;
using UnityEngine.XR.Interaction.Toolkit.Samples.SpatialKeyboard;

using FofX.Stateful;

using Nessle;

using ObserveThing;

using static Nessle.UIBuilder;
using static Nessle.Props;

namespace Plerion.MakeItSing
{
    public static partial class UIElements
    {
        public static UIElementSet elements;

        public static LayoutProps FillParentProps(LayoutProps from = default)
        {
            from.anchorMin = from.anchorMin ?? Value(new Vector2(0, 0));
            from.anchorMax = from.anchorMax ?? Value(new Vector2(1, 1));
            from.offsetMin = from.offsetMin ?? Value(new Vector2(0, 0));
            from.offsetMax = from.offsetMax ?? Value(new Vector2(0, 0));

            return from;
        }

        public struct LabeledPropertyProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<string> label;
            public IValueObservable<float> labelWidth;
            public IValueObservable<IControl> content;
        }

        public static IControl LabeledProperty(LabeledPropertyProps props)
        {
            return HorizontalLayout(new()
            {
                element = props.element,
                layout = props.layout,
                childAlignment = Value(TextAnchor.MiddleLeft),
                spacing = Value(10f),
                childControlWidth = Value(true),
                childControlHeight = Value(true),
                children = List(
                    Value(Text(new()
                    {
                        value = props.label,
                        layout =
                        {
                            preferredWidth = props.labelWidth,
                            minWidth = props.labelWidth
                        }
                    })),
                    props.content
                )
            });
        }

        public struct TypedDropdownProps<T>
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<T> value;
            public IListObservable<T> options;
            public IValueObservable<bool> interactable;

            public TextStyleProps captionTextStyle;
            public TextStyleProps itemTextStyle;

            public UnityAction<T> onValueChanged;

            public Func<T, IValueObservable<string>> displayNameSelector;
        }

        public static IControl TypedDropdown<T>(TypedDropdownProps<T> props)
        {
            var value = default(T);
            var index = 0;
            var options = new List<T>();

            Action refreshValue = () =>
            {
                if (options.Count == 0)
                {
                    index = 0;

                    if (!Equals(value, default(T)))
                    {
                        value = default;
                        props.onValueChanged?.Invoke(value);
                    }

                    return;
                }

                if (index >= options.Count)
                    index = options.Count - 1;

                var newValue = options[index];
                if (!Equals(value, newValue))
                {
                    value = newValue;
                    props.onValueChanged?.Invoke(newValue);
                }
            };

            if (props.displayNameSelector == null)
                props.displayNameSelector = x => Value(x.ToString());

            return Dropdown(new()
            {
                element = props.element,
                layout = props.layout,
                interactable = props.interactable,
                captionTextStyle = props.captionTextStyle,
                itemTextStyle = props.itemTextStyle,
                onValueChanged = x =>
                {
                    index = x;
                    refreshValue();
                },
                value = props.value == null ? null : props.options?.ObservableIndexOf(props.value),
                options = props.options?
                    .ObservableForEach(
                        onAdd: (index, value) =>
                        {
                            options.Insert(index, value);
                            refreshValue();
                        },
                        onRemove: (index, value) =>
                        {
                            options.RemoveAt(index);
                            refreshValue();
                        }
                    )
                    .ObservableSelect(props.displayNameSelector)
            });
        }

        public static IControl ConnectingToRoomUI()
        {
            return null;
        }

        public static IControl TransformControl(TransformControlProps props)
        {
            var gameObject = new GameObject("TransformControl");
            var control = gameObject.AddComponent<TransformControl>();
            control.Setup(props);
            return control;
        }

        public struct PlatformInputFieldProps
        {
            public InputFieldProps inputField;

            // The below values are ignored if we're not on magic leap
            public IValueObservable<bool> useSceneKeyboard;
            public IValueObservable<XRKeyboard> keyboard;
            public IValueObservable<bool> updateOnKeyPress;
            public IValueObservable<bool> alwaysObserveKeyboard;
            public IValueObservable<bool> monitorInputFieldCharacterLimit;
            public IValueObservable<bool> clearTextOnSubmit;
            public IValueObservable<bool> clearTextOnOpen;
        }

        public static IControl PlatformInputField(PlatformInputFieldProps props)
        {
            var inputField = InputField(props.inputField);

#if PLERION_MAGIC_LEAP
            var keyboardDisplay = inputField.gameObject.AddComponent<XRKeyboardDisplay>();
            keyboardDisplay.inputField = inputField.gameObject.GetComponent<TMP_InputField>();

            inputField.AddBinding(
                props.useSceneKeyboard?.Subscribe(x => keyboardDisplay.useSceneKeyboard = x),
                props.keyboard?.Subscribe(x => keyboardDisplay.keyboard = x),
                props.updateOnKeyPress?.Subscribe(x => keyboardDisplay.updateOnKeyPress = x),
                props.alwaysObserveKeyboard?.Subscribe(x => keyboardDisplay.alwaysObserveKeyboard = x),
                props.monitorInputFieldCharacterLimit?.Subscribe(x => keyboardDisplay.monitorInputFieldCharacterLimit = x),
                props.clearTextOnSubmit?.Subscribe(x => keyboardDisplay.clearTextOnSubmit = x),
                props.clearTextOnOpen?.Subscribe(x => keyboardDisplay.clearTextOnOpen = x)
            );
#endif

            return inputField;
        }

        public struct AppStateLogProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<bool> filterToScene;
            public Action<bool> onFilterToSceneChanged;
        }

        public static IControl AppStateLog(AppStateLogProps props)
        {
            var filterToSceneInternal = new ObservableValue<bool>();

            props.element.bindings = props.element.bindings.With(
                props.filterToScene?.Subscribe(x => filterToSceneInternal.value = x),
                filterToSceneInternal.Subscribe(x => props.onFilterToSceneChanged?.Invoke(x))
            );

            return VerticalLayout(new()
            {
                element = props.element,
                layout = props.layout,
                children = List(
                    StateLog(new()
                    {
                        layout =
                        {
                            flexibleWidth = Value(1f),
                            flexibleHeight = Value(1f),
                        },
                        state = filterToSceneInternal.ObservableSelect(x => (IStateNode)(x ? App.state.scene : App.state))
                    }),
                    Button(new()
                    {
                        content = List(Text(new()
                        {
                            style = { horizontalAlignment = Value(TMPro.HorizontalAlignmentOptions.Center) },
                            value = filterToSceneInternal.ObservableSelect(x => x ? "Show Full State" : "Show Scene State"),
                            layout = { flexibleWidth = Value(1f) }
                        })),
                        onClick = () => filterToSceneInternal.value = !filterToSceneInternal.value
                    })
                )
            });
        }

        public struct StateLogProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<IStateNode> state;
        }

        public static IControl StateLog(StateLogProps props)
        {
            ObservableValue<string> output = new ObservableValue<string>();
            IStateNode targetState = null;
            IDisposable subscription = null;

            var binding = List(
                props.state?.Subscribe(x =>
                {
                    subscription?.Dispose();
                    subscription = null;

                    targetState = x;

                    if (x != null)
                    {
                        subscription = x.SubscribeOperationsRecursive(_ => output.value = targetState.ToJSON(_ => true).ToString(4));
                        // output.value = targetState.ToJSON(_ => true).ToString(4);
                    }
                    else
                    {
                        output.value = "null";
                    }
                }),
                new Disposable(() => subscription?.Dispose())
            );

            props.element.bindings = props.element.bindings == null ? binding : props.element.bindings.ObservableConcat(binding);

            return ScrollRect(new()
            {
                element = props.element,
                layout = props.layout,
                vertical = Value(true),
                horizontal = Value(true),
                movementType = Value(UnityEngine.UI.ScrollRect.MovementType.Clamped),
                content = Value(Text(new()
                {
                    layout = new()
                    {
                        pivot = Value(new Vector2(0, 1)),
                        anchorMin = Value(new Vector2(0, 1)),
                        anchorMax = Value(new Vector2(0, 1)),
                        fitContentHorizontal = Value(UnityEngine.UI.ContentSizeFitter.FitMode.PreferredSize),
                        fitContentVertical = Value(UnityEngine.UI.ContentSizeFitter.FitMode.PreferredSize)
                    },
                    value = output
                }))
            });
        }

        public struct VerticalScrollRectProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<float> value;
            public UnityAction<float> onValueChanged;
            public IValueObservable<RectOffset> padding;
            public IValueObservable<float> spacing;
            public IValueObservable<TextAnchor> childAlignment;
            public IValueObservable<bool> reverseArrangement;
            public IValueObservable<bool> childForceExpandHeight;
            public IValueObservable<bool> childForceExpandWidth;
            public IValueObservable<bool> childControlWidth;
            public IValueObservable<bool> childControlHeight;
            public IValueObservable<bool> childScaleWidth;
            public IValueObservable<bool> childScaleHeight;
            public IListObservable<IControl> children;
        }

        public static IControl VerticalScrollRect(VerticalScrollRectProps props)
        {
            props.spacing = props.spacing ?? Value(10f);
            props.childControlWidth = props.childControlWidth ?? Value(true);
            props.childControlHeight = props.childControlHeight ?? Value(true);

            return ScrollRect(new()
            {
                element = props.element,
                layout = props.layout,
                value = props.value?.ObservableSelect(x => new Vector2(0, x)),
                onValueChanged = props.onValueChanged == null ? null : x => props.onValueChanged(x.y),
                vertical = Value(true),
                horizontal = Value(false),
                content = Value(VerticalLayout(new()
                {
                    layout =
                    {
                        pivot = Value(new Vector2(0, 1)),
                        anchorMin = Value(new Vector2(0, 1)),
                        anchorMax = Value(new Vector2(1, 1)),
                        offsetMin = Value(new Vector2(0, 0)),
                        offsetMax = Value(new Vector2(0, 0)),
                        fitContentVertical = Value(UnityEngine.UI.ContentSizeFitter.FitMode.PreferredSize)
                    },
                    padding = props.padding,
                    spacing = props.spacing,
                    childAlignment = props.childAlignment,
                    reverseArrangement = props.reverseArrangement,
                    childForceExpandHeight = props.childForceExpandHeight,
                    childForceExpandWidth = props.childForceExpandWidth,
                    childControlWidth = props.childControlWidth,
                    childControlHeight = props.childControlHeight,
                    childScaleWidth = props.childScaleWidth,
                    childScaleHeight = props.childScaleHeight,
                    children = props.children
                }))
            });
        }

        /// <summary>
        /// Generates a list which animates adds and removes in a pleasing way. IMPORTANT: Use ObservableSelect instead of ObservableCreate for children! ObservableCreate disposes the child before it can animate out. 
        /// </summary>
        /// <param name="props"></param>
        /// <returns></returns>
        public static IControl AnimatedList(AnimatedListProps props)
        {
            var control = UnityEngine.Object.Instantiate(elements.animatedList);
            control.Setup(props);
            return control;
        }

        public struct NotificationProps
        {
            public ElementProps element;
            public IValueObservable<string> message;
            public TextStyleProps messageStyle;
            public IValueObservable<Sprite> background;
            public ImageStyleProps backgroundStyle;
            public Action onResolved;
        }

        public static IControl Notification(NotificationProps props)
        {
            return VerticalLayout(new()
            {
                padding = Value(new RectOffset(12, 12, 6, 6)),
                spacing = Value(5f),
                childAlignment = Value(TextAnchor.MiddleLeft),
                childControlWidth = Value(true),
                childControlHeight = Value(true),
                children = List(
                    RoundedRectElement(new()
                    {
                        layout = { ignoreLayout = Value(true) },
                        sprite = props.background,
                        style = props.backgroundStyle
                    }),
                    Text(new()
                    {
                        value = props.message,
                        style = props.messageStyle
                    })
                )
            });
        }

        public static IControl RoundedRectElement(ImageProps props = default)
        {
            props.style.color = props.style.color ?? Value(elements.elementColor);
            return RoundedRect(props);
        }

        public static IControl RoundedRectBackground(ImageProps props = default)
        {
            props.layout.ignoreLayout = props.layout.ignoreLayout ?? Value(true);
            props.style.color = props.style.color ?? Value(elements.backgroundColor);
            return RoundedRect(props);
        }

        public static IControl RoundedRect(ImageProps props = default)
        {
            props.layout.anchorMin = props.layout.anchorMin ?? Value(new Vector2(0, 0));
            props.layout.anchorMax = props.layout.anchorMax ?? Value(new Vector2(1, 1));
            props.layout.offsetMin = props.layout.offsetMin ?? Value(new Vector2(0, 0));
            props.layout.offsetMax = props.layout.offsetMax ?? Value(new Vector2(0, 0));
            props.sprite = props.sprite ?? Value(elements.background);
            props.style.pixelsPerUnitMultiplier = props.style.pixelsPerUnitMultiplier ?? Value(3.54f);
            props.style.imageType = props.style.imageType ?? Value(UnityEngine.UI.Image.Type.Sliced);
            props.style.fillCenter = props.style.fillCenter ?? Value(true);

            return Image(props);
        }

        public static IControl Tagalong(TagalongProps props = default)
        {
            var control = UnityEngine.Object.Instantiate(elements.tagalong);
            control.Setup(props);
            return control;
        }

        public static IControl RoundButton(PressableProps props = default)
        {
            props.background = props.background ?? Value(elements.circle);
            props.backgroundStyle.color = props.backgroundStyle.color ?? Value(elements.elementColor);

            props.layout.minHeight = props.layout.minHeight ?? Value(28f);
            props.layout.preferredHeight = props.layout.preferredHeight ?? Value(28f);
            props.layout.minWidth = props.layout.minWidth ?? Value(28f);
            props.layout.preferredWidth = props.layout.preferredWidth ?? Value(28f);

            return Pressable(props);
        }

        public static IControl Pressable(PressableProps props = default)
        {
            var control = UnityEngine.Object.Instantiate(elements.pressable);
            control.Setup(props);
            return control;
        }
    }
}