using System;
using System.Collections.Generic;
using System.Linq;

using Unity.Mathematics;

using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

using FofX.Stateful;

using TMPro;
using Placeframe.Core;

namespace Placeframe.MapRegistrationTool
{
    public enum LabelType
    {
        None,
        Tight,
        Standard,
        Adaptive,
        Foldout,
        Header,
        Default
    }

    public class UpdateInputImmediatelyAttribute : Attribute { }
    public class HideInInspectorUIAttribute : Attribute { }
    public class ReadonlyInUIAttribute : Attribute { }

    public class InspectorTypeAttribute : Attribute
    {
        public Type type;
        public LabelType labelType;

        public InspectorTypeAttribute(Type type, LabelType labelType = LabelType.Foldout)
        {
            this.type = type;
            this.labelType = labelType;
        }
    }

    public static class UIBuilderExtensions
    {
        public static ComponentView<T> Padding<T>(this ComponentView<T> view, RectOffset padding)
            where T : LayoutGroup
        {
            view.component.padding = padding;
            return view;
        }

        public static ComponentView<T> Alignment<T>(this ComponentView<T> view, TextAnchor childAlignment)
            where T : LayoutGroup
        {
            view.component.childAlignment = childAlignment;
            return view;
        }

        public static ComponentView<T> Spacing<T>(this ComponentView<T> view, float spacing)
            where T : HorizontalOrVerticalLayoutGroup
        {
            view.component.spacing = spacing;
            return view;
        }

        public static ComponentView<T> ReverseArrangement<T>(this ComponentView<T> view, bool reverseArrangement)
            where T : HorizontalOrVerticalLayoutGroup
        {
            view.component.reverseArrangement = reverseArrangement;
            return view;
        }

        public static ComponentView<T> ControlChildSize<T>(this ComponentView<T> view, bool? controlWidth = default, bool? controlHeight = default)
            where T : HorizontalOrVerticalLayoutGroup
        {
            view.component.childControlWidth = controlWidth ?? view.component.childControlWidth;
            view.component.childControlHeight = controlHeight ?? view.component.childControlHeight;
            return view;
        }

        public static ComponentView<T> UseChildScale<T>(this ComponentView<T> view, bool? useWidth = default, bool? useHeight = default)
            where T : HorizontalOrVerticalLayoutGroup
        {
            view.component.childScaleWidth = useWidth ?? view.component.childScaleWidth;
            view.component.childScaleHeight = useHeight ?? view.component.childScaleHeight;
            return view;
        }

        public static ComponentView<T> ForceChildExpand<T>(this ComponentView<T> view, bool? forceExpandWidth = default, bool? forceExpandHeight = default)
            where T : HorizontalOrVerticalLayoutGroup
        {
            view.component.childForceExpandWidth = forceExpandWidth ?? view.component.childForceExpandWidth;
            view.component.childForceExpandHeight = forceExpandHeight ?? view.component.childForceExpandHeight;
            return view;
        }

        public static ComponentView<T> Color<T>(this ComponentView<T> view, Color color)
            where T : TMP_Text
        {
            view.component.color = color;
            return view;
        }

        public static ComponentView<T> WithChildren<T>(this ComponentView<T> view, params Component[] children)
            => view.WithChildren((IEnumerable<Component>)children);

        public static ComponentView<T> WithChildren<T>(this ComponentView<T> view, IEnumerable<Component> children)
        {
            if (children == null)
                return view;

            foreach (var child in children)
                child.transform.SetParent(view.transform, false);

            return view;
        }

        public static ComponentView<ScrollRect> WithChildren(this ComponentView<ScrollRect> view, params Component[] children)
            => view.WithChildren((IEnumerable<Component>)children);

        public static ComponentView<ScrollRect> WithChildren(this ComponentView<ScrollRect> view, IEnumerable<Component> children)
        {
            if (children == null)
                return view;

            foreach (var child in children)
                child.transform.SetParent(view.component.content, false);

            return view;
        }

        public static T WithBinding<T>(this T view, Func<T, IDisposable> bind)
            where T : ViewBase
        {
            view.AddBinding(bind(view));
            return view;
        }
    }

    public static partial class UIBuilder
    {
        private delegate ValueControl ValueControlConstructorDelegate(string label, LabelType labelType, bool interactable, params Attribute[] attributes);
        private static Dictionary<Type, ValueControlConstructorDelegate> _valueControlConstructors = new Dictionary<Type, ValueControlConstructorDelegate>()
        {
            { typeof(bool), BoolControl },
            { typeof(string), StringControl },
            { typeof(int), IntControl },
            { typeof(float), FloatControl },
            { typeof(double), DoubleControl },
            { typeof(double2), Double2Control },
            { typeof(double3), Double3Control },
            { typeof(Vector2), Vector2Control },
            { typeof(Vector3), Vector3Control },
            { typeof(Vector4), Vector4Control },
            { typeof(Quaternion), QuaternionControl },
            { typeof(Bounds), BoundsControl }
        };

        private static ComponentView<TComponent> AsView<TComponent, TView>(this TComponent component)
            where TComponent : Component
            where TView : ComponentView<TComponent>
        {
            var view = component.gameObject.AddComponent<TView>();
            view.component = component;
            return view;
        }

        public static Control NodeInspector(string label, IObservableNode node, LabelType labelType = LabelType.Default, bool interactable = true)
        {
            if (node.HasAttribute<HideInInspectorUIAttribute>())
            {
                var control = DefaultObservableNodeInspector(label, node, labelType, interactable);
                var element = control.gameObject.AddComponent<LayoutElement>();
                element.ignoreLayout = true;
                element.gameObject.SetActive(false);
                return control;
            }
            else if (node.TryGetAttribute(out InspectorTypeAttribute attribute))
            {
                return CustomObservableNodeInspector(label, node, attribute.type, labelType == LabelType.Default ? attribute.labelType : labelType, interactable);
            }
            else if (node is ObservableObject obj)
            {
                return ObservableObjectInspector(label, obj, labelType, interactable);
            }
            else if (node is IObservableDictionary dict)
            {
                return ObservableDictionaryInspector(label, dict, labelType, interactable);
            }
            else if (node is IObservableList list)
            {
                return ObservableListInspector(label, list, labelType, interactable);
            }
            else if (node is IObservableSet set)
            {
                return ObservableSetInspector(label, set, labelType, interactable);
            }
            else if (node is IObservablePrimitiveMap map)
            {
                return ObservablePrimitiveMapInspector(label, map, labelType, interactable);
            }
            else if (node is IObservablePrimitiveArray array)
            {
                return ObservablePrimitiveArrayInspector(label, array, labelType, interactable);
            }
            else if (node is IObservablePrimitive primitive)
            {
                return ObservablePrimitiveInspector(label, primitive, labelType, interactable);
            }
            else
            {
                return DefaultObservableNodeInspector(label, node, labelType, interactable);
            }
        }

        public static ObservableNodeInspector<ObservableObject> ObservableObjectInspector(string label, ObservableObject target, LabelType labelType = LabelType.Default, bool interactable = true)
        {
            var layout = VerticalLayout();
            var instance = HandleLabel(label, labelType, LabelType.Foldout, layout).gameObject.AddComponent<ObservableObjectInspector>();
            instance.gameObject.name = target.nodePath;
            instance.rect = (RectTransform)layout.transform;
            instance.Setup(target.nodePath, interactable);

            return instance;
        }

        public static ObservableNodeInspector<IObservableDictionary> ObservableDictionaryInspector(string label, IObservableDictionary target, LabelType labelType = LabelType.Default, bool interactable = true)
        {
            var layout = VerticalLayout();
            var instance = HandleLabel(label, labelType, LabelType.Foldout, layout).gameObject.AddComponent<ObservableDictionaryInspector>();
            instance.gameObject.name = target.nodePath;
            instance.rect = (RectTransform)layout.transform;
            instance.Setup(target.nodePath, interactable);

            return instance;
        }

        public static ObservableNodeInspector<IObservableList> ObservableListInspector(string label, IObservableList target, LabelType labelType = LabelType.Default, bool interactable = true)
        {
            var layout = VerticalLayout();
            var instance = HandleLabel(label, labelType, LabelType.Foldout, layout).gameObject.AddComponent<ObservableListInspector>();
            instance.gameObject.name = target.nodePath;
            instance.rect = (RectTransform)layout.transform;
            instance.Setup(target.nodePath, interactable);

            return instance;
        }

        public static ObservableNodeInspector<IObservableSet> ObservableSetInspector(string label, IObservableSet target, LabelType labelType = LabelType.Default, bool interactable = true)
        {
            var layout = VerticalLayout();
            var instance = HandleLabel(label, labelType, LabelType.Foldout, layout).gameObject.AddComponent<ObservableSetInspector>();
            instance.gameObject.name = target.nodePath;
            instance.rect = (RectTransform)layout.transform;
            instance.Setup(target.nodePath, interactable);

            return instance;
        }

        public static ObservableNodeInspector<IObservableNode> DefaultObservableNodeInspector(string label, IObservableNode target, LabelType labelType = LabelType.Default, bool interactable = true)
        {
            var layout = VerticalLayout();
            var instance = HandleLabel(label, labelType, LabelType.Foldout, layout).gameObject.AddComponent<DefaultObservableNodeInspector>();
            instance.gameObject.name = target.nodePath;
            instance.rect = (RectTransform)layout.transform;
            instance.Setup(target.nodePath, interactable);

            return instance;
        }

        public static ObservableNodeInspector<IObservablePrimitiveMap> ObservablePrimitiveMapInspector(string label, IObservablePrimitiveMap target, LabelType labelType = LabelType.Default, bool interactable = true)
        {
            var layout = VerticalLayout();
            var instance = HandleLabel(label, labelType, LabelType.Foldout, layout).gameObject.AddComponent<ObservablePrimitiveMapInspector>();
            instance.gameObject.name = target.nodePath;
            instance.rect = (RectTransform)layout.transform;
            instance.Setup(target.nodePath, interactable);

            return instance;
        }

        public static ObservableNodeInspector<IObservablePrimitiveArray> ObservablePrimitiveArrayInspector(string label, IObservablePrimitiveArray target, LabelType labelType = LabelType.Default, bool interactable = true)
        {
            var layout = VerticalLayout();
            var instance = HandleLabel(label, labelType, LabelType.Foldout, layout).gameObject.AddComponent<ObservablePrimitiveArrayInspector>();
            instance.gameObject.name = target.nodePath;
            instance.rect = (RectTransform)layout.transform;
            instance.Setup(target.nodePath, interactable);

            return instance;
        }

        public static ObservableNodeInspector<IObservablePrimitive> ObservablePrimitiveInspector(string label, IObservablePrimitive target, LabelType labelType = LabelType.Default, bool interactable = true)
        {
            var layout = VerticalLayout();
            layout.component.childForceExpandWidth = false;
            var instance = HandleLabel(label, labelType, LabelType.Adaptive, layout).gameObject.AddComponent<ObservablePrimitiveInspector>();
            instance.gameObject.name = target.nodePath;
            instance.rect = (RectTransform)layout.transform;
            instance.Setup(target.nodePath, interactable);

            return instance;
        }

        public static CustomObservableNodeInspector CustomObservableNodeInspector(string label, IObservableNode target, Type inspectorType, LabelType labelType = LabelType.Default, bool interactable = true)
        {
            var layout = VerticalLayout();
            var instance = (CustomObservableNodeInspector)HandleLabel(label, labelType, LabelType.Foldout, layout).gameObject.AddComponent(inspectorType);
            instance.gameObject.name = target.nodePath;
            instance.rect = (RectTransform)layout.transform;
            instance.Setup(target.nodePath, interactable);

            return instance;
        }

        public static ValueControl ValueControl(Type type, string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            foreach (var attribute in attributes)
            {
                if (_valueControlConstructors.TryGetValue(attribute.GetType(), out var overrideConstructor))
                    return overrideConstructor(label, labelType, interactable, attributes);
            }

            if (_valueControlConstructors.TryGetValue(type, out var defaultConstructor))
                return defaultConstructor(label, labelType, interactable, attributes);

            if (type.IsEnum)
                return EnumControl(type, label, labelType, interactable);

            return DefaultControl(label, labelType, interactable);
        }

        public static ValueControl<object> EnumControl(Type enumType, string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var names = new List<string>(Enum.GetNames(enumType));
            var dropdown = Dropdown(names);
            var control = HandleLabel(label, labelType, LabelType.Adaptive, dropdown).gameObject.AddComponent<ObjectValueControl>();

            dropdown.component.interactable = interactable;
            dropdown.component.onValueChanged.AddListener(x => control.value = Enum.Parse(enumType, names[x]));

            control.onValueChanged += () => dropdown.component.value = names.IndexOf(Enum.GetName(enumType, control.value));

            return control;
        }

        public static ValueControl<object> DefaultControl(string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var text = Text("null");
            var control = HandleLabel(label, labelType, LabelType.Adaptive, text).gameObject.AddComponent<ObjectValueControl>();
            control.onValueChanged += () => text.component.text = control.value?.ToString() ?? "null";
            return control;
        }

        public static ValueControl<bool> BoolControl(string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var toggle = Toggle();
            toggle.component.interactable = interactable;
            var control = HandleLabel(label, labelType, LabelType.Adaptive, toggle).gameObject.AddComponent<BoolValueControl>();
            toggle.component.onValueChanged.AddListener(x => control.value = x);
            control.onValueChanged += () => toggle.component.isOn = control.value;
            return control;
        }

        public static ValueControl<string> StringControl(string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var inputField = InputField();
            inputField.component.interactable = interactable;
            var control = HandleLabel(label, labelType, LabelType.Adaptive, inputField).gameObject.AddComponent<StringValueControl>();
            control.onValueChanged += () => inputField.component.text = control.value;

            UnityEvent<string> inputUpdateEvent = attributes.Any(x => x is UpdateInputImmediatelyAttribute) ?
                inputField.component.onValueChanged : inputField.component.onEndEdit;

            inputUpdateEvent.AddListener(x => control.value = x);

            return control;
        }

        public static ValueControl<float> FloatControl(string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var inputField = InputField("0", TMP_InputField.ContentType.DecimalNumber);
            inputField.component.interactable = interactable;
            var control = HandleLabel(label, labelType, LabelType.Adaptive, inputField).gameObject.AddComponent<FloatValueControl>();

            bool pushingChanges = false;
            control.onValueChanged += () =>
            {
                pushingChanges = true;
                inputField.component.text = Mathf.Abs(control.value) > Mathf.Epsilon ? Math.Round(control.value, 7).ToString() : "0";
                pushingChanges = false;
            };

            UnityEvent<string> inputUpdateEvent = attributes.Any(x => x is UpdateInputImmediatelyAttribute) ?
                inputField.component.onValueChanged : inputField.component.onEndEdit;

            inputUpdateEvent.AddListener(x =>
            {
                if (pushingChanges)
                    return;

                control.value = float.TryParse(x, out var result) ? result : default;
            });

            return control;
        }


        public static ValueControl<double> DoubleControl(string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var inputField = InputField("0", TMP_InputField.ContentType.DecimalNumber);
            inputField.component.interactable = interactable;
            var control = HandleLabel(label, labelType, LabelType.Adaptive, inputField).gameObject.AddComponent<DoubleValueControl>();
            control.onValueChanged += () => inputField.component.text = Math.Round(control.value, 7).ToString();

            UnityEvent<string> inputUpdateEvent = attributes.Any(x => x is UpdateInputImmediatelyAttribute) ?
                inputField.component.onValueChanged : inputField.component.onEndEdit;

            inputUpdateEvent.AddListener(x => control.value = double.TryParse(x, out var result) ? result : default);

            return control;
        }

        public static ValueControl<int> IntControl(string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var inputField = InputField("0", TMP_InputField.ContentType.IntegerNumber);
            inputField.component.interactable = interactable;
            var control = HandleLabel(label, labelType, LabelType.Adaptive, inputField).gameObject.AddComponent<IntValueControl>();
            control.onValueChanged += () => inputField.component.text = control.value.ToString();

            UnityEvent<string> inputUpdateEvent = attributes.Any(x => x is UpdateInputImmediatelyAttribute) ?
                inputField.component.onValueChanged : inputField.component.onEndEdit;

            inputUpdateEvent.AddListener(x => control.value = int.TryParse(x, out var result) ? result : default);

            return control;
        }

        public static ValueControl<Vector2> Vector2Control(string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var xControl = FloatControl("x", LabelType.Tight, interactable: interactable);
            var yControl = FloatControl("y", LabelType.Tight, interactable: interactable);

            var control = HandleLabel(
                label,
                labelType,
                LabelType.Adaptive,
                HorizontalLayout(xControl, yControl)
            ).gameObject.AddComponent<Vector2ValueControl>();

            bool pushingChanges = false;

            Action handleChildChanged = () =>
            {
                if (pushingChanges)
                    return;

                control.value = new Vector2(
                    xControl.value,
                    yControl.value
                );
            };

            xControl.onValueChanged += handleChildChanged;
            yControl.onValueChanged += handleChildChanged;

            control.onValueChanged += () =>
            {
                pushingChanges = true;
                xControl.value = control.value.x;
                yControl.value = control.value.y;
                pushingChanges = false;
            };

            return control;
        }

        public static ValueControl<Vector3> Vector3Control(string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var xControl = FloatControl("x", LabelType.Tight, interactable: interactable);
            var yControl = FloatControl("y", LabelType.Tight, interactable: interactable);
            var zControl = FloatControl("z", LabelType.Tight, interactable: interactable);

            var control = HandleLabel(
                label,
                labelType,
                LabelType.Adaptive,
                HorizontalLayout(xControl, yControl, zControl)
            ).gameObject.AddComponent<Vector3ValueControl>();

            bool pushingChanges = false;

            Action handleChildChanged = () =>
            {
                if (pushingChanges)
                    return;

                control.value = new Vector3(
                    xControl.value,
                    yControl.value,
                    zControl.value
                );
            };

            xControl.onValueChanged += handleChildChanged;
            yControl.onValueChanged += handleChildChanged;
            zControl.onValueChanged += handleChildChanged;

            control.onValueChanged += () =>
            {
                pushingChanges = true;
                xControl.value = control.value.x;
                yControl.value = control.value.y;
                zControl.value = control.value.z;
                pushingChanges = false;
            };

            return control;
        }

        public static ValueControl<Vector4> Vector4Control(string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var xControl = FloatControl("x", LabelType.Tight, interactable: interactable);
            var yControl = FloatControl("y", LabelType.Tight, interactable: interactable);
            var zControl = FloatControl("z", LabelType.Tight, interactable: interactable);
            var wControl = FloatControl("w", LabelType.Tight, interactable: interactable);

            var control = HandleLabel(
                label,
                labelType,
                LabelType.Adaptive,
                HorizontalLayout(xControl, yControl, zControl, wControl)
            ).gameObject.AddComponent<Vector4ValueControl>();

            bool pushingChanges = false;

            Action handleChildChanged = () =>
            {
                if (pushingChanges)
                    return;

                control.value = new Vector4(
                    xControl.value,
                    yControl.value,
                    zControl.value,
                    wControl.value
                );
            };

            xControl.onValueChanged += handleChildChanged;
            yControl.onValueChanged += handleChildChanged;
            zControl.onValueChanged += handleChildChanged;
            wControl.onValueChanged += handleChildChanged;

            control.onValueChanged += () =>
            {
                pushingChanges = true;
                xControl.value = control.value.x;
                yControl.value = control.value.y;
                zControl.value = control.value.z;
                wControl.value = control.value.w;
                pushingChanges = false;
            };

            return control;
        }

        public static ValueControl<double2> Double2Control(string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var xControl = DoubleControl("x", LabelType.Tight, interactable: interactable);
            var yControl = DoubleControl("y", LabelType.Tight, interactable: interactable);

            var control = HandleLabel(
                label,
                labelType,
                LabelType.Adaptive,
                VerticalLayout(xControl, yControl)
            ).gameObject.AddComponent<Double2ValueControl>();

            bool pushingChanges = false;

            Action handleChildChanged = () =>
            {
                if (pushingChanges)
                    return;

                control.value = new double2(
                    xControl.value,
                    yControl.value
                );
            };

            xControl.onValueChanged += handleChildChanged;
            yControl.onValueChanged += handleChildChanged;

            control.onValueChanged += () =>
            {
                pushingChanges = true;
                xControl.value = control.value.x;
                yControl.value = control.value.y;
                pushingChanges = false;
            };

            return control;
        }

        public static ValueControl<double3> Double3Control(
            string label = null,
            LabelType labelType = LabelType.None,
            bool interactable = true,
            params Attribute[] attributes)
        {
            var xControl = DoubleControl("x", LabelType.Tight, interactable: interactable);
            var yControl = DoubleControl("y", LabelType.Tight, interactable: interactable);
            var zControl = DoubleControl("z", LabelType.Tight, interactable: interactable);

            var control = HandleLabel(
                label,
                labelType,
                LabelType.Adaptive,
                VerticalLayout(xControl, yControl, zControl)
            ).gameObject.AddComponent<Double3ValueControl>();

            bool pushingChanges = false;

            Action handleChildChanged = () =>
            {
                if (pushingChanges)
                    return;

                control.value = new double3(
                    xControl.value,
                    yControl.value,
                    zControl.value
                );
            };

            xControl.onValueChanged += handleChildChanged;
            yControl.onValueChanged += handleChildChanged;
            zControl.onValueChanged += handleChildChanged;

            control.onValueChanged += () =>
            {
                pushingChanges = true;
                xControl.value = control.value.x;
                yControl.value = control.value.y;
                zControl.value = control.value.z;
                pushingChanges = false;
            };

            return control;
        }

        public static ValueControl<CartographicCoordinates> CartographicCoordinatesControl(
            string label = null,
            LabelType labelType = LabelType.None,
            bool interactable = true,
            params Attribute[] attributes)
        {
            var latitude = DoubleControl("latitude", LabelType.Tight, interactable: interactable);
            var longitude = DoubleControl("longitude", LabelType.Tight, interactable: interactable);
            var height = DoubleControl("height", LabelType.Tight, interactable: interactable);

            var control = HandleLabel(
                label,
                labelType,
                LabelType.Adaptive,
                VerticalLayout(latitude, longitude, height)
            ).gameObject.AddComponent<CartographicValueControl>();

            bool pushingChanges = false;

            Action handleChildChanged = () =>
            {
                if (pushingChanges)
                    return;

                control.value = CartographicCoordinates.FromLatitudeLongitudeHeight(
                    latitude.value,
                    longitude.value,
                    height.value
                );
            };

            latitude.onValueChanged += handleChildChanged;
            longitude.onValueChanged += handleChildChanged;
            height.onValueChanged += handleChildChanged;

            control.onValueChanged += () =>
            {
                pushingChanges = true;
                latitude.value = control.value.Latitude;
                longitude.value = control.value.Longitude;
                height.value = control.value.Height;
                pushingChanges = false;
            };

            return control;
        }

        public static ValueControl<Quaternion> QuaternionControl(string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var xControl = FloatControl("x", LabelType.Tight, interactable: interactable);
            var yControl = FloatControl("y", LabelType.Tight, interactable: interactable);
            var zControl = FloatControl("z", LabelType.Tight, interactable: interactable);

            var control = HandleLabel(
                label,
                labelType,
                LabelType.Adaptive,
                HorizontalLayout(xControl, yControl, zControl)
            ).gameObject.AddComponent<QuaternionValueControl>();

            bool pushingChanges = false;

            Action handleChildChanged = () =>
            {
                if (pushingChanges)
                    return;

                control.value = Quaternion.Euler(xControl.value, yControl.value, zControl.value);
            };

            xControl.onValueChanged += handleChildChanged;
            yControl.onValueChanged += handleChildChanged;
            zControl.onValueChanged += handleChildChanged;

            control.onValueChanged += () =>
            {
                pushingChanges = true;
                xControl.value = control.value.eulerAngles.x;
                yControl.value = control.value.eulerAngles.y;
                zControl.value = control.value.eulerAngles.z;
                pushingChanges = false;
            };

            return control;
        }

        public static ValueControl<Bounds> BoundsControl(string label = null, LabelType labelType = LabelType.None, bool interactable = true, params Attribute[] attributes)
        {
            var centerControl = Vector3Control("Center", LabelType.Adaptive, interactable: interactable);
            var sizeControl = Vector3Control("Size", LabelType.Adaptive, interactable: interactable);

            var control = HandleLabel(
                label,
                labelType,
                LabelType.Adaptive,
                VerticalLayout(centerControl, sizeControl)
            ).gameObject.AddComponent<BoundsValueControl>();

            bool pushingChanges = false;

            Action handleChildChanged = () =>
            {
                if (pushingChanges)
                    return;

                control.value = new Bounds(centerControl.value, sizeControl.value);
            };

            centerControl.onValueChanged += handleChildChanged;
            sizeControl.onValueChanged += handleChildChanged;

            control.onValueChanged += () =>
            {
                pushingChanges = true;
                centerControl.value = control.value.center;
                sizeControl.value = control.value.size;
                pushingChanges = false;
            };

            return control;
        }

        public static ComponentView<TextMeshProUGUI> Text(ObservablePrimitive<string> bindTo, VerticalAlignmentOptions verticalAlignment = VerticalAlignmentOptions.Top, HorizontalAlignmentOptions horizontalAlignment = HorizontalAlignmentOptions.Left)
        {
            var text = Text(bindTo.value, verticalAlignment, horizontalAlignment);
            text.AddBinding(text.component.BindText(bindTo));
            return text;
        }

        public static EditableLabel EditableLabel(ObservablePrimitive<string> bindTo)
        {
            var editableLabel = EditableLabel(bindTo.value);
            bool applyingFromState = false;
            editableLabel.AddBinding(
                bindTo.OnChange(
                    value =>
                    {
                        applyingFromState = true;
                        editableLabel.text = bindTo.value;
                        applyingFromState = false;
                    }
                ),
                editableLabel.onValueChanged.OnRaised(
                    x =>
                    {
                        if (applyingFromState)
                            return;

                        bindTo.ExecuteSetOrDelay(editableLabel.text);
                    }
                )
            );

            return editableLabel;
        }

        public static EditableLabel EditableLabel(string text)
        {
            var editableLabel = UnityEngine.Object.Instantiate(Prefabs.EditableLabel);
            editableLabel.text = text;
            return editableLabel;
        }

        public static ComponentView<LayoutElement> FlexibleSpace(bool flexibleWidth = false, bool flexibleHeight = false)
        {
            var space = new GameObject("FlexibleSpace", typeof(RectTransform), typeof(LayoutElement));
            var layoutElement = space.GetComponent<LayoutElement>();
            layoutElement.flexibleWidth = flexibleWidth ? 1 : 0;
            layoutElement.flexibleHeight = flexibleHeight ? 1 : 0;
            return layoutElement.AsView<LayoutElement, LayoutElementView>();
        }

        public static ComponentView<TextMeshProUGUI> Text(string text = null, VerticalAlignmentOptions verticalAlignment = VerticalAlignmentOptions.Top, HorizontalAlignmentOptions horizontalAlignment = HorizontalAlignmentOptions.Left)
        {
            var result = UnityEngine.Object.Instantiate(Prefabs.Text);
            result.text = text;
            result.verticalAlignment = verticalAlignment;
            result.horizontalAlignment = horizontalAlignment;
            var view = result.AsView<TextMeshProUGUI, TextView>();
            view.AddBinding(view.gameObject.DestroyOnRelease());
            return view;
        }

        public static LabelButton Button(string label = null, UnityAction onClick = null, bool interactable = true)
        {
            var result = UnityEngine.Object.Instantiate(Prefabs.Button);
            result.label.text = label;
            result.button.interactable = interactable;
            result.AddBinding(result.gameObject.DestroyOnRelease());

            if (onClick != null)
                result.button.onClick.AddListener(onClick);

            return result;
        }

        public static ComponentView<VerticalLayoutGroup> Window(params Component[] elements)
        {
            var window = UnityEngine.Object.Instantiate(Prefabs.Window);

            var layoutElement = window.gameObject.AddComponent<LayoutElement>();
            layoutElement.minWidth = 300;

            var contentSizeFitter = window.gameObject.AddComponent<ContentSizeFitter>();
            contentSizeFitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;
            contentSizeFitter.horizontalFit = ContentSizeFitter.FitMode.PreferredSize;

            var verticalLayout = window.gameObject.AddComponent<VerticalLayoutGroup>();
            verticalLayout.padding = new RectOffset(20, 20, 20, 20);
            verticalLayout.spacing = 20f;

            foreach (var element in elements)
                element.transform.SetParent(window.transform, false);

            var view = verticalLayout.AsView<VerticalLayoutGroup, VerticalLayoutGroupView>();
            view.AddBinding(view.gameObject.DestroyOnRelease());

            return view;
        }

        public static ListElementContainer ListElement(params Component[] elements)
            => ListElement(true, content: VerticalLayout(elements).transform);

        public static ListElementContainer ListElement(bool interactable = true, params Component[] elements)
            => ListElement(interactable, content: VerticalLayout(elements).transform);

        public static ListElementContainer ListElement(bool interactable = true, Action onRemoved = null, params Component[] content)
        {
            var listElement = UnityEngine.Object.Instantiate(Prefabs.ListElement);
            listElement.removeButton.interactable = interactable;
            listElement.removeButton.onClick.AddListener(() =>
            {
                UnityEngine.Object.Destroy(listElement.gameObject);
                onRemoved?.Invoke();
            });

            foreach (var element in content)
                element.transform.SetParent(listElement.content, false);

            listElement.AddBinding(listElement.gameObject.DestroyOnRelease());

            return listElement;
        }

        public static ComponentView<TMP_InputField> FloatField(ObservablePrimitive<float> bindTo)
        {
            var inputField = InputField("0", TMP_InputField.ContentType.DecimalNumber);
            inputField.AddBinding(inputField.component.BindInput(bindTo));
            return inputField;
        }

        public static ComponentView<TMP_InputField> IntField(ObservablePrimitive<int> bindTo)
        {
            var inputField = InputField("0", TMP_InputField.ContentType.IntegerNumber);
            inputField.AddBinding(inputField.component.BindInput(bindTo));
            return inputField;
        }

        public static ComponentView<TMP_InputField> InputField(ObservablePrimitive<string> bindTo, TMP_InputField.ContentType contentType = TMP_InputField.ContentType.Standard)
        {
            var inputField = InputField(bindTo.value, contentType);
            inputField.AddBinding(inputField.component.BindInput(bindTo));
            return inputField;
        }

        public static ComponentView<TMP_InputField> InputField(string text = null, TMP_InputField.ContentType contentType = TMP_InputField.ContentType.Standard)
        {
            var inputField = UnityEngine.Object.Instantiate(Prefabs.InputField);
            inputField.text = text;
            inputField.contentType = contentType;
            var view = inputField.AsView<TMP_InputField, InputFieldView>();
            view.AddBinding(view.gameObject.DestroyOnRelease());
            return view;
        }

        public static ComponentView<TMP_InputField> InputRegion(ObservablePrimitive<string> bindTo, TMP_InputField.ContentType contentType = TMP_InputField.ContentType.Standard)
        {
            var inputRegion = InputRegion(bindTo.value, contentType);
            inputRegion.AddBinding(inputRegion.component.BindInput(bindTo));
            return inputRegion;
        }

        public static ComponentView<TMP_InputField> InputRegion(string text = null, TMP_InputField.ContentType contentType = TMP_InputField.ContentType.Standard)
        {
            var inputRegion = UnityEngine.Object.Instantiate(Prefabs.InputRegion);
            inputRegion.text = text;
            inputRegion.contentType = contentType;
            var view = inputRegion.AsView<TMP_InputField, InputFieldView>();
            view.AddBinding(view.gameObject.DestroyOnRelease());
            return view;
        }

        public static ComponentView<Toggle> Toggle(ObservablePrimitive<bool> value)
        {
            var toggle = Toggle();
            bool settingFromState = false;

            toggle.AddBinding(
                value.OnChange(x =>
                {
                    settingFromState = true;
                    toggle.component.isOn = x;
                    settingFromState = false;
                }),
                toggle.component.onValueChanged.OnRaised(isOn =>
                {
                    if (settingFromState)
                        return;

                    value.ExecuteSet(isOn);
                })
            );

            return toggle;
        }

        public static ComponentView<Toggle> Toggle()
        {
            var view = UnityEngine.Object.Instantiate(Prefabs.Toggle).AsView<Toggle, ToggleView>();
            view.AddBinding(view.gameObject.DestroyOnRelease());
            return view;
        }

        public static ComponentView<TMP_Dropdown> Dropdown(IEnumerable<string> options)
            => Dropdown(options.Select(x => new TMP_Dropdown.OptionData(x)).ToList());

        public static ComponentView<TMP_Dropdown> Dropdown(List<TMP_Dropdown.OptionData> options)
        {
            var dropdown = Dropdown();
            dropdown.component.options = options;
            return dropdown;
        }

        public static ComponentView<TMP_Dropdown> Dropdown()
        {
            var dropdown = UnityEngine.Object.Instantiate(Prefabs.Dropdown);
            var view = dropdown.AsView<TMP_Dropdown, DropdownView>();
            view.AddBinding(view.gameObject.DestroyOnRelease());
            return view;
        }

        public static Foldout Foldout(ObservablePrimitive<string> label = null, params Component[] content)
            => SetupPropertyLabel(label, Prefabs.Foldout, content);

        public static Foldout Foldout(string label = null, params Component[] content)
            => SetupPropertyLabel(label, Prefabs.Foldout, content);

        public static PropertyLabel Header(ObservablePrimitive<string> label = null, params Component[] content)
            => SetupPropertyLabel(label, Prefabs.Header, content);

        public static PropertyLabel Header(string label = null, params Component[] content)
            => SetupPropertyLabel(label, Prefabs.Header, content);

        public static PropertyLabel TightPropertyLabel(ObservablePrimitive<string> label, params Component[] content)
            => SetupPropertyLabel(label, Prefabs.TightPropertyLabel, content);

        public static PropertyLabel TightPropertyLabel(string label, params Component[] content)
            => SetupPropertyLabel(label, Prefabs.TightPropertyLabel, content);

        public static PropertyLabel PropertyLabel(ObservablePrimitive<string> label, params Component[] content)
            => SetupPropertyLabel(label, Prefabs.AdaptivePropertyLabel, content);

        public static PropertyLabel PropertyLabel(string label, params Component[] content)
            => SetupPropertyLabel(label, Prefabs.AdaptivePropertyLabel, content);

        public static AdaptivePropertyLabel AdaptivePropertyLabel(ObservablePrimitive<string> label, params Component[] content)
            => SetupPropertyLabel(label, Prefabs.AdaptivePropertyLabel, content);

        public static AdaptivePropertyLabel AdaptivePropertyLabel(string label, params Component[] content)
            => SetupPropertyLabel(label, Prefabs.AdaptivePropertyLabel, content);

        public static T SetupPropertyLabel<T>(ObservablePrimitive<string> label, T prefab, params Component[] content)
            where T : PropertyLabel
        {
            var propLabel = SetupPropertyLabel(label.value, prefab, content);
            propLabel.AddBinding(propLabel.label.BindText(label));
            return propLabel;
        }

        private static T SetupPropertyLabel<T>(string label, T prefab, params Component[] content)
            where T : PropertyLabel
        {
            var propertyLabel = UnityEngine.Object.Instantiate(prefab);

            foreach (var element in content)
                element.transform.SetParent(propertyLabel.content, false);

            propertyLabel.label.text = label;
            propertyLabel.AddBinding(propertyLabel.gameObject.DestroyOnRelease());

            return propertyLabel;
        }

        public static ComponentView<HorizontalLayoutGroup> HorizontalLayout(params Component[] elements)
            => HorizontalLayout((IEnumerable<Component>)elements);

        public static ComponentView<HorizontalLayoutGroup> HorizontalLayout(IEnumerable<Component> elements)
        {
            var layout = UnityEngine.Object.Instantiate(Prefabs.HorizontalLayout);
            var view = layout.AsView<HorizontalLayoutGroup, HorizontalLayoutGroupView>();
            view.AddBinding(view.gameObject.DestroyOnRelease());

            if (view != null)
                view.WithChildren(elements);

            return view;
        }

        public static ComponentView<VerticalLayoutGroup> VerticalLayout(params Component[] elements)
            => VerticalLayout((IEnumerable<Component>)elements);

        public static ComponentView<VerticalLayoutGroup> VerticalLayout(IEnumerable<Component> elements)
        {
            var layout = UnityEngine.Object.Instantiate(Prefabs.VerticalLayout);
            var view = layout.AsView<VerticalLayoutGroup, VerticalLayoutGroupView>();
            view.AddBinding(view.gameObject.DestroyOnRelease());

            if (view != null)
                view.WithChildren(elements);

            return view;
        }

        public static ComponentView<ScrollRect> ScrollRect(params Component[] elements)
            => ScrollRect((IEnumerable<Component>)elements);

        public static ComponentView<ScrollRect> ScrollRect(IEnumerable<Component> elements)
        {
            var scrollRect = UnityEngine.Object.Instantiate(Prefabs.ScrollRect);
            var view = scrollRect.AsView<ScrollRect, ScrollRectView>();
            view.AddBinding(view.gameObject.DestroyOnRelease());

            if (view != null)
                view.WithChildren(elements);

            return view;
        }

        public static T WithDropReceiver<T>(this T view, Func<GameObject, bool> filter = null, Action<GameObject> onDrop = null)
            where T : Component
        {
            var dropReceiver = view.gameObject.AddComponent<DropReceiver>();
            dropReceiver.filter = filter;
            dropReceiver.onDrop = onDrop;

            return view;
        }

        public static T WithLayoutProperties<T>(this T view, bool? ignoreLayout = default, float? minWidth = default, float? minHeight = default, float? preferredWidth = default, float? preferredHeight = default, bool? flexibleWidth = default, bool? flexibleHeight = default, int? layoutPriority = 1)
            where T : Component
        {
            var layoutElement = view.gameObject.GetOrAddComponent<LayoutElement>();
            layoutElement.ignoreLayout = ignoreLayout ?? layoutElement.ignoreLayout;
            layoutElement.minWidth = minWidth ?? layoutElement.minWidth;
            layoutElement.minHeight = minHeight ?? layoutElement.minHeight;
            layoutElement.preferredWidth = preferredWidth ?? layoutElement.preferredWidth;
            layoutElement.preferredHeight = preferredHeight ?? layoutElement.preferredHeight;
            layoutElement.flexibleWidth = flexibleWidth == null ? layoutElement.flexibleWidth : flexibleWidth.Value ? 1 : 0;
            layoutElement.flexibleHeight = flexibleHeight == null ? layoutElement.flexibleHeight : flexibleHeight.Value ? 1 : 0;
            layoutElement.layoutPriority = layoutPriority ?? layoutElement.layoutPriority;
            return view;
        }

        private static Transform HandleLabel(string label, LabelType labelType, LabelType defaultLabelType, params Component[] content)
        {
            if (labelType == LabelType.Default)
                labelType = defaultLabelType == LabelType.Default ? LabelType.None : defaultLabelType;

            switch (labelType)
            {
                case LabelType.None:
                    return (content.Length == 1) ? content[0].transform : VerticalLayout(content).transform;
                case LabelType.Tight:
                    return TightPropertyLabel(label, content).transform;
                case LabelType.Standard:
                    return PropertyLabel(label, content).transform;
                case LabelType.Adaptive:
                    return AdaptivePropertyLabel(label, content).transform;
                case LabelType.Foldout:
                    return Foldout(label, content).transform;
                case LabelType.Header:
                    return Header(label, content).transform;
                default:
                    throw new Exception($"Unhandled label type {defaultLabelType}");
            }
        }

        private class ObjectValueControl : ValueControl<object> { }
        private class StringValueControl : ValueControl<string> { }
        private class BoolValueControl : ValueControl<bool> { }
        private class FloatValueControl : ValueControl<float> { }
        private class DoubleValueControl : ValueControl<double> { }
        private class IntValueControl : ValueControl<int> { }
        private class Vector2ValueControl : ValueControl<Vector2> { }
        private class Vector3ValueControl : ValueControl<Vector3> { }
        private class Vector4ValueControl : ValueControl<Vector4> { }
        private class QuaternionValueControl : ValueControl<Quaternion> { }
        private class Double2ValueControl : ValueControl<double2> { }
        private class Double3ValueControl : ValueControl<double3> { }
        private class CartographicValueControl : ValueControl<CartographicCoordinates> { }
        private class BoundsValueControl : ValueControl<Bounds> { }
        private class HorizontalLayoutGroupView : ComponentView<HorizontalLayoutGroup> { }
        private class VerticalLayoutGroupView : ComponentView<VerticalLayoutGroup> { }
        private class ScrollRectView : ComponentView<ScrollRect> { }
        private class TextView : ComponentView<TextMeshProUGUI> { }
        private class ToggleView : ComponentView<Toggle> { }
        private class LayoutElementView : ComponentView<LayoutElement> { }
        private class InputFieldView : ComponentView<TMP_InputField>
        {
            private void OnTransformParentChanged()
            {
                //Do this to re-evaluate instance variables that are set only OnEnable in TMP_InputField
                component.enabled = false;
                component.enabled = true;
            }
        }

        private class DropdownView : ComponentView<TMP_Dropdown> { }
    }

    public class ComponentView<T> : ViewBase
    {
        public T component;
    }
}