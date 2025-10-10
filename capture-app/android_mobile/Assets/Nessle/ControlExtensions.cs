using System;
using System.Collections.Generic;
using ObserveThing;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using FitMode = UnityEngine.UI.ContentSizeFitter.FitMode;

namespace Nessle
{
    public static class ControlExtensions
    {
        public static T Children<T>(this T control, params IControl[] children)
            where T : IControl => control.Children((IEnumerable<IControl>)children);

        public static T Children<T>(this T control, IEnumerable<IControl> children)
            where T : IControl
        {
            if (children == null)
                return control;

            foreach (var child in children)
                child.SetParent(control);

            return control;
        }

        public static TParent Children<TParent>(this TParent control, IListObservable<IControl> children)
            where TParent : IControl
        {
            control.AddBinding(children.Subscribe(
                args =>
                {
                    switch (args.operationType)
                    {
                        case OpType.Add:
                            args.element.SetParent(control);
                            args.element.SetSiblingIndex(args.index);
                            break;

                        case OpType.Remove:
                            args.element.SetParent(null);
                            break;
                    }
                }
            ));

            return control;
        }

        public static IControlWithMetadata<TProps, TData> WithMetadata<TProps, TData>(this IControl<TProps> control, TData data)
            => new UnityControlWithMetadata<TProps, TData>(control, data);

        public static T Active<T>(this T control, IValueObservable<bool> active)
            where T : IControl
        {
            control.AddBinding(active.Subscribe(x => control.gameObject.SetActive(x.currentValue)));
            return control;
        }

        public static T Selected<T>(this T control, IValueObservable<bool> selected)
            where T : IControl
        {
            control.AddBinding(selected.Subscribe(x =>
            {
                if (x.currentValue)
                {
                    EventSystem.current.SetSelectedGameObject(control.gameObject);
                }
                else if (!EventSystem.current.alreadySelecting &&
                    EventSystem.current.currentSelectedGameObject == control.gameObject)
                {
                    EventSystem.current.SetSelectedGameObject(null);
                }
            }));

            return control;
        }

        public static T Active<T>(this T control, bool active)
            where T : IControl
        {
            control.gameObject.SetActive(active);
            return control;
        }

        public static T FillParent<T>(this T control)
            where T : IControl
        {
            control.transform.anchorMin = new Vector2(0, 0);
            control.transform.anchorMax = new Vector2(1, 1);
            control.transform.offsetMin = new Vector2(0, 0);
            control.transform.offsetMax = new Vector2(0, 0);
            return control;
        }

        public static T FillParentWidth<T>(this T control)
            where T : IControl
        {
            control.transform.anchorMin = new Vector2(0, control.transform.anchorMin.y);
            control.transform.anchorMax = new Vector2(1, control.transform.anchorMax.y);
            control.transform.offsetMin = new Vector2(0, control.transform.offsetMin.y);
            control.transform.offsetMax = new Vector2(0, control.transform.offsetMax.y);
            return control;
        }

        public static T FillParentHeight<T>(this T control)
            where T : IControl
        {
            control.transform.anchorMin = new Vector2(control.transform.anchorMin.x, 0);
            control.transform.anchorMax = new Vector2(control.transform.anchorMax.x, 1);
            control.transform.offsetMin = new Vector2(control.transform.offsetMin.x, 0);
            control.transform.offsetMax = new Vector2(control.transform.offsetMax.x, 0);
            return control;
        }

        public static T AnchorToTop<T>(this T control)
            where T : IControl
        {
            control.transform.anchorMin = new Vector2(control.transform.anchorMin.x, 1);
            control.transform.anchorMax = new Vector2(control.transform.anchorMax.x, 1);
            return control;
        }

        public static T AnchorToBottom<T>(this T control)
            where T : IControl
        {
            control.transform.anchorMin = new Vector2(control.transform.anchorMin.x, 0);
            control.transform.anchorMax = new Vector2(control.transform.anchorMax.x, 0);
            return control;
        }

        public static T AnchorToLeft<T>(this T control)
            where T : IControl
        {
            control.transform.anchorMin = new Vector2(0, control.transform.anchorMin.y);
            control.transform.anchorMax = new Vector2(0, control.transform.anchorMax.y);
            return control;
        }

        public static T AnchorToRight<T>(this T control)
            where T : IControl
        {
            control.transform.anchorMin = new Vector2(1, control.transform.anchorMin.y);
            control.transform.anchorMax = new Vector2(1, control.transform.anchorMax.y);
            return control;
        }

        public static T AnchorToTopLeft<T>(this T control)
            where T : IControl
        {
            control.transform.anchorMin = new Vector2(0, 1);
            control.transform.anchorMax = new Vector2(0, 1);
            return control;
        }

        public static T AnchorToTopRight<T>(this T control)
            where T : IControl
        {
            control.transform.anchorMin = new Vector2(1, 1);
            control.transform.anchorMax = new Vector2(1, 1);
            return control;
        }

        public static T AnchorToBottomLeft<T>(this T control)
            where T : IControl
        {
            control.transform.anchorMin = new Vector2(0, 0);
            control.transform.anchorMax = new Vector2(0, 0);
            return control;
        }

        public static T AnchorToBottomRight<T>(this T control)
            where T : IControl
        {
            control.transform.anchorMin = new Vector2(1, 0);
            control.transform.anchorMax = new Vector2(1, 0);
            return control;
        }

        public static T SetPivot<T>(this T control, Vector2 pivot)
            where T : IControl
        {
            control.transform.pivot = pivot;
            return control;
        }

        public static T SetPivot<T>(this T control, IValueObservable<Vector2> pivot)
            where T : IControl
        {
            control.AddBinding(pivot.Subscribe(x => control.transform.pivot = x.currentValue));
            return control;
        }

        public static T LocalPosition<T>(this T control, Vector3 localPosition)
            where T : IControl
        {
            control.transform.localPosition = localPosition;
            return control;
        }

        public static T LocalPosition<T>(this T control, IValueObservable<Vector2> localPosition)
            where T : IControl
        {
            control.AddBinding(localPosition.Subscribe(x => control.transform.localPosition = x.currentValue));
            return control;
        }

        public static T Anchor<T>(this T control, Vector2 anchor)
            where T : IControl
        {
            control.AnchorMin(anchor);
            control.AnchorMax(anchor);
            return control;
        }

        public static T Anchor<T>(this T control, IValueObservable<Vector2> anchor)
            where T : IControl
        {
            control.AnchorMin(anchor);
            control.AnchorMax(anchor);
            return control;
        }

        public static T AnchorMin<T>(this T control, Vector2 anchorMin)
            where T : IControl
        {
            control.transform.anchorMin = anchorMin;
            return control;
        }

        public static T AnchorMin<T>(this T control, IValueObservable<Vector2> anchorMin)
            where T : IControl
        {
            control.AddBinding(anchorMin.Subscribe(x => control.transform.anchorMin = x.currentValue));
            return control;
        }

        public static T AnchorMax<T>(this T control, Vector2 anchorMax)
            where T : IControl
        {
            control.transform.anchorMax = anchorMax;
            return control;
        }

        public static T AnchorMax<T>(this T control, IValueObservable<Vector2> anchorMax)
            where T : IControl
        {
            control.AddBinding(anchorMax.Subscribe(x => control.transform.anchorMax = x.currentValue));
            return control;
        }

        public static T OffsetMin<T>(this T control, Vector2 offsetMin)
            where T : IControl
        {
            control.transform.offsetMin = offsetMin;
            return control;
        }

        public static T OffsetMin<T>(this T control, IValueObservable<Vector2> offsetMin)
            where T : IControl
        {
            control.AddBinding(offsetMin.Subscribe(x => control.transform.offsetMin = x.currentValue));
            return control;
        }

        public static T OffsetMax<T>(this T control, Vector2 offsetMax)
            where T : IControl
        {
            control.transform.offsetMax = offsetMax;
            return control;
        }

        public static T OffsetMax<T>(this T control, IValueObservable<Vector2> offsetMax)
            where T : IControl
        {
            control.AddBinding(offsetMax.Subscribe(x => control.transform.offsetMax = x.currentValue));
            return control;
        }

        public static T AnchoredPosition<T>(this T control, Vector2 anchoredPosition)
            where T : IControl
        {
            control.transform.anchoredPosition = anchoredPosition;
            return control;
        }

        public static T AnchoredPosition<T>(this T control, IValueObservable<Vector2> anchoredPosition)
            where T : IControl
        {
            control.AddBinding(anchoredPosition.Subscribe(x => control.transform.anchoredPosition = x.currentValue));
            return control;
        }

        public static T SizeDelta<T>(this T control, Vector2 sizeDelta)
            where T : IControl
        {
            control.transform.sizeDelta = sizeDelta;
            return control;
        }

        public static T SizeDelta<T>(this T control, IValueObservable<Vector2> sizeDelta)
            where T : IControl
        {
            control.AddBinding(sizeDelta.Subscribe(x => control.transform.sizeDelta = x.currentValue));
            return control;
        }

        public static T IgnoreLayout<T>(this T control, IValueObservable<bool> ignoreLayout)
            where T : IControl
        {
            control.AddBinding(ignoreLayout.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().ignoreLayout = x.currentValue));
            return control;
        }

        public static T IgnoreLayout<T>(this T control, bool ignoreLayout)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().ignoreLayout = ignoreLayout;
            return control;
        }

        public static T MinWidth<T>(this T control, IValueObservable<float> minWidth)
            where T : IControl
        {
            control.AddBinding(minWidth.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().minWidth = x.currentValue));
            return control;
        }

        public static T MinWidth<T>(this T control, float minWidth)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().minWidth = minWidth;
            return control;
        }

        public static T MinHeight<T>(this T control, IValueObservable<float> minHeight)
            where T : IControl
        {
            control.AddBinding(minHeight.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().minHeight = x.currentValue));
            return control;
        }

        public static T MinHeight<T>(this T control, float minHeight)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().minHeight = minHeight;
            return control;
        }

        public static T PreferredWidth<T>(this T control, IValueObservable<float> preferredWidth)
            where T : IControl
        {
            control.AddBinding(preferredWidth.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().preferredWidth = x.currentValue));
            return control;
        }

        public static T PreferredWidth<T>(this T control, float preferredWidth)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().preferredWidth = preferredWidth;
            return control;
        }

        public static T PreferredHeight<T>(this T control, IValueObservable<float> preferredHeight)
            where T : IControl
        {
            control.AddBinding(preferredHeight.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().preferredHeight = x.currentValue));
            return control;
        }

        public static T PreferredHeight<T>(this T control, float preferredHeight)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().preferredHeight = preferredHeight;
            return control;
        }

        public static T FlexibleWidth<T>(this T control, IValueObservable<bool> flexibleWidth)
            where T : IControl
        {
            control.AddBinding(flexibleWidth.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().flexibleWidth = x.currentValue ? 1 : -1));
            return control;
        }

        public static T FlexibleWidth<T>(this T control, bool flexibleWidth)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().flexibleWidth = flexibleWidth ? 1 : -1;
            return control;
        }

        public static T FlexibleHeight<T>(this T control, IValueObservable<bool> flexibleHeight)
            where T : IControl
        {
            control.AddBinding(flexibleHeight.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().flexibleHeight = x.currentValue ? 1 : -1));
            return control;
        }

        public static T FlexibleHeight<T>(this T control, bool flexibleHeight)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().flexibleHeight = flexibleHeight ? 1 : -1;
            return control;
        }

        public static T LayoutPriority<T>(this T control, IValueObservable<int> layoutPriority)
            where T : IControl
        {
            control.AddBinding(layoutPriority.Subscribe(x => control.gameObject.GetOrAddComponent<LayoutElement>().layoutPriority = x.currentValue));
            return control;
        }

        public static T LayoutPriority<T>(this T control, int layoutPriority)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<LayoutElement>().layoutPriority = layoutPriority;
            return control;
        }

        public static T FitContentVertical<T>(this T control, IValueObservable<FitMode> fitContentVertical)
            where T : IControl
        {
            control.AddBinding(fitContentVertical.Subscribe(x => control.gameObject.GetOrAddComponent<ContentSizeFitter>().verticalFit = x.currentValue));
            return control;
        }

        public static T FitContentVertical<T>(this T control, FitMode fitContentVertical)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<ContentSizeFitter>().verticalFit = fitContentVertical;
            return control;
        }

        public static T FitContentHorizontal<T>(this T control, IValueObservable<FitMode> fitContentHorizontal)
            where T : IControl
        {
            control.AddBinding(fitContentHorizontal.Subscribe(x => control.gameObject.GetOrAddComponent<ContentSizeFitter>().horizontalFit = x.currentValue));
            return control;
        }

        public static T FitContentHorizontal<T>(this T control, FitMode fitContentHorizontal)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<ContentSizeFitter>().horizontalFit = fitContentHorizontal;
            return control;
        }

        public static T SiblingIndex<T>(this T control, int index)
            where T : IControl
        {
            control.SetSiblingIndex(index);
            return control;
        }

        public static T OnHoverEntered<T>(this T control, Action<PointerEventData> onHoverEntered)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<PointerEnterHandler>().onReceivedEvent += onHoverEntered;
            return control;
        }

        public static T OnHoverExited<T>(this T control, Action<PointerEventData> onHoverExited)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<PointerExitHandler>().onReceivedEvent += onHoverExited;
            return control;
        }

        public static T OnPointerDown<T>(this T control, Action<PointerEventData> onPointerDown)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<PointerDownHandler>().onReceivedEvent += onPointerDown;
            return control;
        }

        public static T OnPointerUp<T>(this T control, Action<PointerEventData> onPointerUp)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<PointerUpHandler>().onReceivedEvent += onPointerUp;
            return control;
        }

        public static T OnPointerClick<T>(this T control, Action<PointerEventData> onPointerClick)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<PointerClickHandler>().onReceivedEvent += onPointerClick;
            return control;
        }

        public static T OnDragStarted<T>(this T control, Action<PointerEventData> onDragStarted)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<BeginDragHandler>().onReceivedEvent += onDragStarted;
            return control;
        }

        public static T OnDrag<T>(this T control, Action<PointerEventData> onDrag)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<DragHandler>().onReceivedEvent += onDrag;
            return control;
        }

        public static T OnDragEnded<T>(this T control, Action<PointerEventData> onDragEnded)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<EndDragHandler>().onReceivedEvent += onDragEnded;
            return control;
        }

        public static T OnSelect<T>(this T control, Action<BaseEventData> onSelect)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<SelectHandler>().onReceivedEvent += onSelect;
            return control;
        }

        public static T OnDeselect<T>(this T control, Action<BaseEventData> onDeselect)
            where T : IControl
        {
            control.gameObject.GetOrAddComponent<DeselectHandler>().onReceivedEvent += onDeselect;
            return control;
        }

        public static T Columns<T>(this T control, float spacing, params IControl[] controls)
            where T : IControl
        {
            control.Children(controls);
            float step = 1f / controls.Length;
            for (int i = 0; i < controls.Length; i++)
            {
                var child = controls[i];
                child.transform.anchorMin = new Vector2(step * i, 0);
                child.transform.anchorMax = new Vector2(step * (i + 1), 1);

                child.transform.offsetMin = new Vector2(Mathf.Lerp(0f, spacing, i * step), 0);
                child.transform.offsetMax = new Vector2(Mathf.Lerp(-spacing, 0f, (i + 1) * step), 0);
            }

            return control;
        }
    }
}
