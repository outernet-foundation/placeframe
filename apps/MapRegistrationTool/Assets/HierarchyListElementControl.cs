using Nessle;
using UnityEngine;

using ObserveThing;

using static Nessle.UIBuilder;
using static Nessle.Props;

using System;
using UnityEngine.UI;
using TMPro;
using UnityEngine.EventSystems;
using System.Collections.Generic;

namespace Outernet.MapRegistrationTool
{
    public struct HierarchyListElementProps
    {
        public object key;
        public IControl hierarchyListControl;

        public IValueObservable<bool> dragInProgress;
        public IListObservable<IControl> selectedElements;

        public ElementProps element;
        public LayoutProps layout;

        public IValueObservable<string> label;
        public IValueObservable<bool> selected;
        public IValueObservable<bool> open;
        public IValueObservable<float> indentSize;

        public Action<string> onLabelChanged;
        public Action<bool> onSelectedChanged;
        public Action<bool> onOpenChanged;
        public Action onDragStarted;
        public Action onDragEnded;

        public IListObservable<IControl> children;
    }

    public interface IHierarchyListElement : IDisposable
    {
        IHierarchyListElement parent { get; }
        List<IHierarchyListElement> children { get; }
        bool isOpen { get; }

        void HandleDrop(IHierarchyListElement[] elements);
        void Setup(HierarchyListElementProps props);
    }

    public class HierarchyListElementControl : Nessle.Control<HierarchyListElementProps>,
        IPointerEnterHandler,
        IPointerExitHandler,
        IBeginDragHandler,
        IPointerDownHandler,
        IPointerUpHandler,
        IHierarchyListElement
    {
        public GameObject foldoutRegion;
        public Toggle foldout;
        public TextMeshProUGUI label;
        public RectTransform contentParent;
        public RectTransform indentObject;

        private bool _dragging;

        protected override void SetupInternal()
        {
            // contentParent.onChildrenChanged.AddListener(() =>
            // {
            //     foldout.gameObject.SetActive(contentParent.childCount > 0);
            //     contentParent.gameObject.SetActive(foldout.isOn && contentParent.childCount > 0);
            // });

            foldout.onValueChanged.AddListener(x => contentParent.gameObject.SetActive(x && transform.childCount > 0));

            var indentLayoutElement = indentObject.gameObject.GetOrAddComponent<LayoutElement>();

            AddBinding(
                props.element.Subscribe(this),
                props.layout.Subscribe(this),
                props.indentSize?.Subscribe(x =>
                {
                    indentLayoutElement.minWidth = x.currentValue;
                    indentLayoutElement.preferredWidth = x.currentValue;
                }),
                props.label?.Subscribe(x => label.text = x.currentValue),
                props.children?.SubscribeAsChildren(contentParent)
            );
        }

        void IPointerEnterHandler.OnPointerEnter(PointerEventData eventData)
        {

        }

        void IPointerExitHandler.OnPointerExit(PointerEventData eventData)
        {

        }

        void IPointerDownHandler.OnPointerDown(PointerEventData eventData)
        {
            // no-op, IPointerDownHandler must be implemented in order to receive IPointerUpHandler callbacks
        }

        void IPointerUpHandler.OnPointerUp(PointerEventData eventData)
        {
            if (_dragging)
                props.onDropped?.Invoke();

            _dragging = false;
        }
    }
}