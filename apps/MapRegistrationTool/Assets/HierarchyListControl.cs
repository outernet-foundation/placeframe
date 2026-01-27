using Nessle;
using UnityEngine;

using ObserveThing;

using static Nessle.UIBuilder;
using static Nessle.Props;
using static Outernet.MapRegistrationTool.UIElements;

using System.Collections.Generic;

using System;

namespace Outernet.MapRegistrationTool
{
    public struct HierarchyElementProps
    {
        public object key;
        public IValueObservable<string> label;
        public IValueObservable<bool> open;
        public IValueObservable<bool> selected;
        public IListObservable<HierarchyElementProps> children;

        public Action<string> onLabelChanged;
        public Action<bool> onOpenChanged;
        public Action<bool> onSelectedChanged;
    }

    public struct HierarchyListProps
    {
        public ICollectionObservable<HierarchyElementProps> elements;
        public IValueObservable<float> indentSize;
        public Action<object, object> onParentChanged;
    }

    public class HierarchyListControl : Nessle.Control<HierarchyListProps>
    {
        private DictionaryObservable<object, IControl> _valueToControl = new DictionaryObservable<object, IControl>();
        private Dictionary<IControl, object> _controlToValue = new Dictionary<IControl, object>();

        private object _dropTargetKey = null;
        private List<object> _selectedKeys = new List<object>();

        // private class ListElement
        // {
        //     public IControl control;
        //     public HierarchyElementProps<T> props;
        //     public ICollectionObservable<IDisposable> bindings;

        //     public ValueObservable<ListElement> parent = new ValueObservable<ListElement>();
        //     public ListObservable<ListElement> children = new ListObservable<ListElement>();

        //     public IValueObservable<int> indent;
        //     public Func<GameObject, bool> validatePotentialDrop;
        //     public Action<GameObject> onDropReceived;
        // }

        public IHierarchyListElement elementPrefab;

        protected override void SetupInternal()
        {
            AddBinding(
                props.elements
                    .OrderByDynamic(x => x.key)
                    .CreateDynamic(element =>
                    {
                        return (Nessle.Control<HierarchyListElementProps>)Control(
                            elementPrefab,
                            new()
                            {
                                key = element.key,
                                hierarchyListControl = this,
                                label = element.label,
                                indentSize = props.indentSize,
                                children = element.children.SelectDynamic(x => _valueToControl.TrackDynamic(x.key).SelectDynamic(x => x.keyPresent ? x.value : null)),
                                onPointerEntered = () => _dropTargetKey = element.key,
                                onPointerExited = () =>
                                {
                                    if (_dropTargetKey == element.key)
                                        _dropTargetKey = null;
                                },
                                onDragStarted = () => _dropTargetKey = null,
                                onDropped = () =>
                                {
                                    if (_dropTargetKey == null)
                                        return;

                                    foreach (var selected in _selectedKeys)
                                        props.onParentChanged?.Invoke(selected, _dropTargetKey);

                                    _dropTargetKey = null;
                                },
                                onLabelChanged = element.onLabelChanged,
                                onOpenChanged = element.onOpenChanged,
                                onSelectedChanged = x =>
                                {
                                    if (x)
                                    {
                                        _selectedKeys.Add(element.key);
                                    }
                                    else
                                    {
                                        _selectedKeys.Remove(element.key);
                                    }

                                    element.onSelectedChanged?.Invoke(x);
                                }
                            }
                        );
                    }).Subscribe(x =>
                    {
                        if (x.operationType == OpType.Add)
                        {
                            _controlToValue.Add(x.element, x.element.props.key);
                            _valueToControl.Add(x.element.props.key, x.element);
                        }
                        else if (x.operationType == OpType.Remove)
                        {
                            _controlToValue.Remove(x.element);
                            _valueToControl.Remove(x.element.props.key);
                        }
                    })
            );
        }

        // private IControl ElementControl(ListElement element)
        // {
        //     // Needed to set from the foldout toggle and read to the content active state
        //     ValueObservable<bool> isOpen = new ValueObservable<bool>();
        //     var internalBindings = List(
        //         element.props.open?.Subscribe(x => isOpen.value = x.currentValue),
        //         element.parent.Subscribe(x =>
        //         {
        //             if (x.previousValue != null)
        //                 x.previousValue.children.Remove(element);

        //             if (x.currentValue != null && !x.currentValue.children.Contains(element))
        //                 x.currentValue.children.Add(element);
        //         }),
        //         element.children.Subscribe(x => x.element.parent.value = element)
        //     );

        //     return Control(
        //         "Element",
        //         new()
        //         {
        //             element =
        //             {
        //                 bindings = element.bindings == null ?
        //                     internalBindings : element.bindings.ConcatDynamic(internalBindings)
        //             },
        //             children = List(
        //                 DropZone(new()
        //                 {
        //                     layout = FillParentProps(),
        //                     highlightStyle = { color = Value(Color.cyan) },
        //                     validateDrop = element.validatePotentialDrop,
        //                     onDropReceived = x => element.onDropReceived?.Invoke(x)
        //                 }),
        //                 HorizontalLayout(new()
        //                 {
        //                     childControlWidth = Value(true),
        //                     childControlHeight = Value(true),
        //                     childAlignment = Value(TextAnchor.MiddleLeft),
        //                     spacing = Value(5f),
        //                     padding = Observables.Combine(
        //                         props.indentSize,
        //                         element.parent.SelectDynamic(x => x == null ? Value(0) : x.indent.SelectDynamic(x => x + 1)),
        //                         (size, level) => new RectOffset(size * level, 0, 0, 0)
        //                     ),
        //                     children = List(
        //                         Control(
        //                             "ToggleZone",
        //                             new()
        //                             {
        //                                 layout =
        //                                 {
        //                                     minWidth = Value(30f),
        //                                     minHeight = Value(30f),
        //                                     preferredWidth = Value(30f),
        //                                     preferredHeight = Value(30f)
        //                                 },
        //                                 children = List(
        //                                     Toggle(new()
        //                                     {
        //                                         value = isOpen,
        //                                         element = { active = element.children.CountDynamic().SelectDynamic(x => x > 0) },
        //                                         onValueChanged = x =>
        //                                         {
        //                                             isOpen.value = x;
        //                                             element.props.onOpenChanged?.Invoke(x);
        //                                         }
        //                                     })
        //                                 )
        //                             }
        //                         ),
        //                         Text(new()
        //                         {
        //                             value = element.props.label,
        //                             style =
        //                             {
        //                                 textWrappingMode = Value(TMPro.TextWrappingModes.NoWrap),
        //                                 overflowMode = Value(TMPro.TextOverflowModes.Ellipsis)
        //                             }
        //                         }),
        //                         VerticalLayout(new()
        //                         {
        //                             element = { active = isOpen },
        //                             children = element.children.SelectDynamic(x => x.control)
        //                         })
        //                     )
        //                 })
        //             )
        //         }
        //     );
        // }
    }
}