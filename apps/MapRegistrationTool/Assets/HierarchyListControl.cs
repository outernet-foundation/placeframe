using Nessle;
using UnityEngine;

using ObserveThing;

using static Nessle.UIBuilder;
using static Nessle.Props;
using static Outernet.MapRegistrationTool.UIElements;

using System.Collections.Generic;

using System;
using System.Linq;
using UnityEngine.EventSystems;

namespace Outernet.MapRegistrationTool
{
    public struct HierarchyElementProps
    {
        public object key;
        public IValueObservable<string> label;
        public IValueObservable<bool> open;
        public IValueObservable<bool> selected;
        public IValueObservable<object> parent;

        public Action<string> onLabelChanged;
        public Action<bool> onOpenChanged;
        public Action<bool> onSelectedChanged;
        public Action<object> onParentChanged;
    }

    public struct HierarchyListProps
    {
        public ICollectionObservable<HierarchyElementProps> elements;
        public IValueObservable<float> indentSize;
    }

    public delegate void ParentChangedDelegate(object target, object parent);

    public class HierarchyListControl : Nessle.Control<HierarchyListProps>, IPointerEnterHandler, IPointerExitHandler
    {
        private HashSet<ElementData> _selectedElements = new HashSet<ElementData>();
        private DictionaryObservable<object, ElementData> _elementByValue = new DictionaryObservable<object, ElementData>();
        private Dictionary<ElementData, object> _valueByElement = new Dictionary<ElementData, object>();

        private bool _reparentInProgress = false;
        private ElementData _dropTarget = null;
        private bool _dropIsTargetingList = false;
        private ElementData _mostRecentSelection = null;

        public HierarchyListElement elementPrefab;

        private class ElementData
        {
            public HierarchyElementProps props;
            public HierarchyListElement view;
            public IDisposable disposable;
        }

        protected override void SetupInternal()
        {
            AddBinding(
                props.elements
                    .OrderByDynamic(x => x.key)
                    .SelectDynamic(elementProps =>
                    {
                        var element = new ElementData();
                        element.props = elementProps;
                        element.view = Instantiate(elementPrefab, transform);
                        element.disposable = new ComposedDisposable(
                            element.props.label?.Subscribe(x => element.view.label.text = x.currentValue),
                            element.props.open?.Subscribe(x => element.view.foldout.isOn = x.currentValue),
                            element.props.parent == null ? null : _elementByValue.TrackDynamic(element.props.parent).Subscribe(x =>
                            {
                                element.view.transform.SetParent(x.currentValue.keyPresent ?
                                    x.currentValue.value.view.contentParent : transform);
                            })
                        );

                        element.view.onBeginDrag += () => _reparentInProgress = true;

                        element.view.onEndDrag += () =>
                        {
                            if (_reparentInProgress && _dropTarget != null)
                                HandleDrop(_dropIsTargetingList, _dropTarget, _selectedElements.ToArray());

                            _dropIsTargetingList = false;
                            _reparentInProgress = false;
                            _dropTarget = null;
                        };

                        element.view.onPointerEnter += () =>
                        {
                            if (_reparentInProgress)
                                _dropTarget = element;
                        };

                        element.view.onPointerExit += () =>
                        {
                            if (_dropTarget == element.props.key)
                                _dropTarget = null;
                        };

                        element.view.onClick += () =>
                        {
                            if (Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift))
                            {
                                if (_selectedElements.Contains(element))
                                {
                                    if (_mostRecentSelection != null)
                                    {
                                        SelectBetween(_mostRecentSelection, element);
                                    }
                                    else
                                    {
                                        Select(element);
                                    }
                                }
                                else
                                {
                                    Deselect(element);
                                }
                            }
                            else if (Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl))
                            {
                                SelectAdditive(element);
                            }
                            else
                            {
                                Select(element);
                            }
                        };

                        element.view.onIsOpenChanged += x => element.props.onOpenChanged?.Invoke(x);

                        return element;

                    }).Subscribe(x =>
                    {
                        if (x.operationType == OpType.Add)
                        {
                            _elementByValue.Add(x.element.props.key, x.element);
                            _valueByElement.Add(x.element, x.element.props.key);
                        }
                        else if (x.operationType == OpType.Remove)
                        {
                            x.element.disposable.Dispose();
                            _elementByValue.Remove(x.element.props.key);
                            _elementByValue.Remove(x.element);
                        }
                    })
            );
        }

        private void Select(ElementData element)
        {
            foreach (var toDeselect in _selectedElements.ToArray())
            {
                _selectedElements.Remove(toDeselect);
                toDeselect.props.onSelectedChanged?.Invoke(false);
            }

            _mostRecentSelection = element;
            _selectedElements.Add(element);
            element.props.onSelectedChanged?.Invoke(true);
        }

        private void SelectAdditive(ElementData element)
        {
            _mostRecentSelection = element;
            _selectedElements.Add(element);
            element.props.onSelectedChanged?.Invoke(true);
        }

        private void SelectBetween(ElementData element1, ElementData element2)
        {

        }

        private void Deselect(ElementData element)
        {
            _mostRecentSelection = null;
            _selectedElements.Remove(element);
            element.props.onSelectedChanged?.Invoke(false);
        }

        private void HandleDrop(bool dropIsTargetingList, ElementData dropTarget, ElementData[] selectedElements)
        {
            if (dropIsTargetingList)
            {
                foreach (var element in selectedElements)
                {
                    element.view.transform.SetParent(transform);
                    element.props.onParentChanged?.Invoke(null);
                }
            }

            dropTarget.view.foldout.isOn = true;
            foreach (var element in selectedElements)
            {
                element.view.transform.SetParent(dropTarget.view.contentParent);
                element.props.onParentChanged?.Invoke(dropTarget);
            }
        }

        public void OnPointerEnter(PointerEventData eventData)
        {
            if (!_reparentInProgress)
                return;

            _dropTarget = null;
            _dropIsTargetingList = true;
        }

        public void OnPointerExit(PointerEventData eventData)
        {
            if (!_reparentInProgress)
                return;

            _dropIsTargetingList = false;
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