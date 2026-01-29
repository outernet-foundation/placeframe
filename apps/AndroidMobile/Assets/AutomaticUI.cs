using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Nessle;
using ObserveThing;
using TMPro;
using UnityEngine;
using static Nessle.UIBuilder;

namespace Placeframe.Client
{
    public static partial class UIElements
    {
        public struct ObjectInspectorProps
        {
            public object target;
            public FoldoutProps foldout;
            public IValueObservable<bool> isReadonly;
        }

        public static IControl ObjectInspector(ObjectInspectorProps props = default)
        {
            props.foldout.childrenLayout.childControlHeight =
                props.foldout.childrenLayout.childControlHeight ?? Props.Value(true);
            props.foldout.childrenLayout.childControlWidth =
                props.foldout.childrenLayout.childControlWidth ?? Props.Value(true);
            props.foldout.childrenLayout.childForceExpandHeight =
                props.foldout.childrenLayout.childForceExpandHeight ?? Props.Value(false);
            props.foldout.childrenLayout.childForceExpandWidth =
                props.foldout.childrenLayout.childForceExpandWidth ?? Props.Value(false);
            props.foldout.childrenLayout.spacing = props.foldout.childrenLayout.spacing ?? Props.Value(10f);
            props.foldout.childrenLayout.padding =
                props.foldout.childrenLayout.padding ?? Props.Value(new RectOffset(50, 0, 0, 0));
            props.foldout.childrenLayout.children = Props.List(
                ObjectFieldInspectors(props.target, props.isReadonly.SelectDynamic(x => !x))
            );

            return Foldout(props.foldout);
        }

        public static IEnumerable<IControl> ObjectFieldInspectors(
            object target,
            IValueObservable<bool> interactable = default
        )
        {
            return target
                .GetType()
                .GetMembers(BindingFlags.DeclaredOnly | BindingFlags.Instance | BindingFlags.Public)
                .Where(x => x is FieldInfo || x is PropertyInfo)
                .Select(memberInfo =>
                {
                    string name = default;
                    Type type = default;
                    Func<object, object> getter = default;
                    Action<object, object> setter = default;

                    if (memberInfo is FieldInfo fieldInfo)
                    {
                        name = fieldInfo.Name;
                        type = fieldInfo.FieldType;
                        getter = fieldInfo.GetValue;
                        setter = fieldInfo.SetValue;
                    }
                    else
                    {
                        var propertyInfo = memberInfo as PropertyInfo;
                        name = propertyInfo.Name;
                        type = propertyInfo.PropertyType;
                        getter = propertyInfo.GetValue;
                        setter = propertyInfo.SetValue;
                    }

                    if (type.IsEnum || type.IsValueType || type == typeof(string))
                    {
                        return PrimitiveInspector(
                            Props.Value(name),
                            type,
                            Props.Value(getter(target)),
                            x => setter(target, x),
                            interactable
                        );
                    }
                    else
                    {
                        Log.Warn(LogGroup.Default, $"Unhandled field or property type {type.Name}");
                        return Text(
                            new TextProps()
                            {
                                value = Props.Value($"Unhandled Field: {name}"),
                                style = new TextStyleProps() { color = Props.Value(Color.yellow) },
                            }
                        );
                    }
                    //    else if (type.IsArray || type is IList)
                    //    {
                    //        var objList = getter(target);

                    //        if (objList == null)
                    //        {
                    //            objList = Activator.CreateInstance(type);
                    //            setter(target, objList);
                    //        }

                    //        return ListInspector(Props.Value(name), objList as IList);
                    //    }
                    //    else
                    //    {
                    //        var obj = getter(target);

                    //        if (obj == null)
                    //        {
                    //            obj = Activator.CreateInstance(type);
                    //            setter(target, obj);
                    //        }

                    //        return ObjectInspector(Props.Value(name), obj);
                    //    }
                });
        }

        // private static IControl ListInspector(IValueObservable<string> label, IList list)
        // {
        //     var elementType = list.GetType().GetElementType();
        //     IControl content = VerticalLayout(new LayoutProps()
        //     {
        //         spacing = Props.Value(10f),
        //         childControlHeight = Props.Value(true),
        //         childControlWidth = Props.Value(true),
        //         childForceExpandWidth = Props.Value(true)
        //     });

        //     Func<object, int, IControl> constructElementControl = (obj, index) =>
        //     {
        //         IControl subControl = default;
        //         IValueObservable<int> indexObs = content.children.FollowIndexDynamic(index);
        //         int currIndex = -1;

        //         if (elementType.IsArray || elementType is IList)
        //         {
        //             subControl = ListInspector(indexObs.SelectDynamic(x => x.ToString()), obj as IList);
        //         }
        //         else if (elementType.IsEnum || elementType.IsValueType || elementType == typeof(string))
        //         {
        //             var primControl = PrimitiveInspector(
        //                 indexObs.SelectDynamic(x => x.ToString()),
        //                 elementType,
        //                 Props.Value(obj),
        //                 x => list[currIndex] = x
        //             );

        //             subControl = primControl;
        //         }
        //         else
        //         {
        //             subControl = ObjectInspector(indexObs.SelectDynamic(x => x.ToString()), obj);
        //         }

        //         return HorizontalLayout(new LayoutProps()
        //         {
        //             childControlWidth = Props.Value(true),
        //             childControlHeight = Props.Value(true)
        //         })
        //         .Children(
        //             subControl,
        //             LabeledButton(new LabeledButtonProps()
        //             {
        //                 label = Props.Value("Remove"),
        //                 onClick = () =>
        //                 {
        //                     list.RemoveAt(currIndex);
        //                     var self = content.children[currIndex];
        //                     content.children.RemoveAt(currIndex);
        //                     self.Dispose();
        //                 }
        //             })
        //         );
        //     };

        //     for (int i = 0; i < list.Count; i++)
        //         content.children.Add(constructElementControl(list[i], i));

        //     return Foldout(new FoldoutProps()
        //     {
        //         label = new TextProps() { value = label },
        //         layout = new LayoutProps()
        //         {
        //             childControlHeight = Props.Value(true),
        //             childControlWidth = Props.Value(true),
        //             childForceExpandHeight = Props.Value(false),
        //             childForceExpandWidth = Props.Value(false),
        //             padding = Props.Value(new RectOffset(70, 0, 0, 0)),
        //             spacing = Props.Value(10f)
        //         }
        //     })
        //     .Children(
        //         content,
        //         LabeledButton(new LabeledButtonProps()
        //         {
        //             label = Props.Value("Add"),
        //             onClick = () =>
        //             {
        //                 var element = elementType.IsValueType ? Activator.CreateInstance(elementType) : null;
        //                 list.Add(element);
        //                 content.children.Add(constructElementControl(element, list.Count - 1));
        //             }
        //         })
        //     );
        // }

        public static IControl PrimitiveInspector(
            IValueObservable<string> label,
            Type type,
            IValueObservable<object> value,
            Action<object> onValueChanged,
            IValueObservable<bool> interactable = default
        )
        {
            var nullableUnderlyingType = Nullable.GetUnderlyingType(type);
            if (nullableUnderlyingType != null)
            {
                var initValue = value.Peek();
                var selectedValue = new ValueObservable<object>(
                    initValue ?? Activator.CreateInstance(nullableUnderlyingType)
                );
                var isNull = new ValueObservable<bool>(initValue == null);

                return HorizontalLayout(
                    new()
                    {
                        childControlWidth = Props.Value(true),
                        childControlHeight = Props.Value(true),
                        spacing = Props.Value(30f),
                        element = new()
                        {
                            bindings = Props.List(
                                value.Subscribe(x =>
                                {
                                    isNull.value = x.currentValue == null;

                                    if (x.currentValue != null)
                                        selectedValue.value = x.currentValue;
                                }),
                                Observables
                                    .Combine(selectedValue, isNull, (selected, isNull) => isNull ? null : selected)
                                    .Subscribe(x => onValueChanged?.Invoke(ConstructNullable(type, x.currentValue)))
                            ),
                        },
                        children = Props.List(
                            Toggle(
                                new()
                                {
                                    value = isNull.SelectDynamic(x => !x),
                                    onValueChanged = x => isNull.value = !x,
                                    interactable = interactable,
                                }
                            ),
                            VerticalLayout(
                                new()
                                {
                                    childControlWidth = Props.Value(true),
                                    childControlHeight = Props.Value(true),
                                    spacing = Props.Value(10f),
                                    children = Props.List(
                                        Text(
                                            new()
                                            {
                                                value = label,
                                                layout = new() { flexibleWidth = Props.Value(true) },
                                                style = new()
                                                {
                                                    verticalAlignment = Props.Value(VerticalAlignmentOptions.Capline),
                                                    overflowMode = Props.Value(TextOverflowModes.Ellipsis),
                                                    textWrappingMode = Props.Value(TextWrappingModes.NoWrap),
                                                },
                                            }
                                        ),
                                        PrimitiveControl(
                                            new()
                                            {
                                                type = nullableUnderlyingType,
                                                value = selectedValue,
                                                onValueChanged = x => selectedValue.value = x,
                                                interactable = interactable,
                                                layout = new() { flexibleWidth = Props.Value(true) },
                                            }
                                        )
                                    ),
                                }
                            )
                        ),
                    }
                );
            }

            return VerticalLayout(
                new()
                {
                    children = Props.List(
                        Text(
                            new()
                            {
                                value = label,
                                layout = new() { flexibleWidth = Props.Value(true) },
                                style = new()
                                {
                                    verticalAlignment = Props.Value(VerticalAlignmentOptions.Capline),
                                    overflowMode = Props.Value(TextOverflowModes.Ellipsis),
                                    textWrappingMode = Props.Value(TextWrappingModes.NoWrap),
                                },
                            }
                        ),
                        PrimitiveControl(
                            new()
                            {
                                type = nullableUnderlyingType,
                                value = value,
                                onValueChanged = onValueChanged,
                                interactable = interactable,
                                layout = new() { flexibleWidth = Props.Value(true) },
                            }
                        )
                    ),
                }
            );
        }

        private static object ConstructNullable(Type nullableType, object value)
        {
            return value == null
                ? Activator.CreateInstance(nullableType)
                : Activator.CreateInstance(nullableType, value);
        }

        public struct PrimitiveControlProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public Type type;
            public IValueObservable<object> value;
            public Action<object> onValueChanged;
            public IValueObservable<bool> interactable;
        }

        public static IControl PrimitiveControl(PrimitiveControlProps props)
        {
            if (props.type.IsEnum)
            {
                return Dropdown(
                    new DropdownProps()
                    {
                        element = props.element,
                        layout = props.layout,
                        options = Props.List(Enum.GetNames(props.type)),
                        value = props.value.SelectDynamic(x => x == null ? default : Convert.ToInt32(x)),
                        onValueChanged = x => props.onValueChanged?.Invoke(Enum.ToObject(props.type, x)),
                        interactable = props.interactable,
                    }
                );
            }
            else if (props.type == typeof(bool))
            {
                return Toggle(
                    new ToggleProps()
                    {
                        element = props.element,
                        layout = props.layout,
                        value = props.value.SelectDynamic(x => x == null ? default : (bool)x),
                        onValueChanged = x => props.onValueChanged?.Invoke(x),
                        interactable = props.interactable,
                    }
                );
            }
            else if (props.type == typeof(int))
            {
                return IntField(
                    new InputFieldProps<int>()
                    {
                        element = props.element,
                        layout = props.layout,
                        value = props.value.SelectDynamic(x => x == null ? default : (int)x),
                        onValueChanged = x => props.onValueChanged?.Invoke(x),
                        interactable = props.interactable,
                    }
                );
            }
            else if (props.type == typeof(float))
            {
                return FloatField(
                    new InputFieldProps<float>()
                    {
                        element = props.element,
                        layout = props.layout,
                        value = props.value.SelectDynamic(x => x == null ? default : (float)x),
                        onValueChanged = x => props.onValueChanged?.Invoke(x),
                        interactable = props.interactable,
                    }
                );
            }
            else if (props.type == typeof(double))
            {
                return DoubleField(
                    new InputFieldProps<double>()
                    {
                        element = props.element,
                        layout = props.layout,
                        value = props.value.SelectDynamic(x => x == null ? default : (double)x),
                        onValueChanged = x => props.onValueChanged?.Invoke(x),
                        interactable = props.interactable,
                    }
                );
            }
            else if (props.type == typeof(string))
            {
                return InputField(
                    new InputFieldProps()
                    {
                        element = props.element,
                        layout = props.layout,
                        value = props.value.SelectDynamic(x => x == null ? default : (string)x),
                        onValueChanged = x => props.onValueChanged?.Invoke(x),
                        interactable = props.interactable,
                    }
                );
            }
            else
            {
                Log.Warn(LogGroup.Default, $"Unhandled primitive type {props.type.Name}");
                return Text(
                    new TextProps()
                    {
                        element = props.element,
                        layout = props.layout,
                        value = props.value.SelectDynamic(x => x == null ? "NULL" : x.ToString()),
                        style = new TextStyleProps()
                        {
                            color = Props.Value(Color.yellow),
                            textWrappingMode = Props.Value(TextWrappingModes.NoWrap),
                            overflowMode = Props.Value(TextOverflowModes.Ellipsis),
                            verticalAlignment = Props.Value(VerticalAlignmentOptions.Capline),
                        },
                    }
                );
            }
        }
    }
}
