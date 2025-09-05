using System;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Nessle
{

    public class PointerDownHandler : UIEventReceiver<PointerEventData>, IPointerDownHandler
    {
        public void OnPointerDown(PointerEventData eventData)
            => RaiseOnReceivedEvent(eventData);
    }

    public class PointerUpHandler : UIEventReceiver<PointerEventData>, IPointerUpHandler
    {
        public void OnPointerUp(PointerEventData eventData)
            => RaiseOnReceivedEvent(eventData);
    }

    public class PointerClickHandler : UIEventReceiver<PointerEventData>, IPointerClickHandler
    {
        public void OnPointerClick(PointerEventData eventData)
            => RaiseOnReceivedEvent(eventData);
    }

    public class PointerEnterHandler : UIEventReceiver<PointerEventData>, IPointerEnterHandler
    {
        public void OnPointerEnter(PointerEventData eventData)
            => RaiseOnReceivedEvent(eventData);
    }

    public class PointerExitHandler : UIEventReceiver<PointerEventData>, IPointerExitHandler
    {
        public void OnPointerExit(PointerEventData eventData)
            => RaiseOnReceivedEvent(eventData);
    }

    public class DragHandler : UIEventReceiver<PointerEventData>, IDragHandler
    {
        public void OnDrag(PointerEventData eventData)
            => RaiseOnReceivedEvent(eventData);
    }

    public class BeginDragHandler : UIEventReceiver<PointerEventData>, IBeginDragHandler
    {
        public void OnBeginDrag(PointerEventData eventData)
            => RaiseOnReceivedEvent(eventData);
    }

    public class EndDragHandler : UIEventReceiver<PointerEventData>, IEndDragHandler
    {
        public void OnEndDrag(PointerEventData eventData)
            => RaiseOnReceivedEvent(eventData);
    }

    public class SelectHandler : UIEventReceiver<BaseEventData>, ISelectHandler
    {
        public void OnSelect(BaseEventData eventData)
            => RaiseOnReceivedEvent(eventData);
    }

    public class DeselectHandler : UIEventReceiver<BaseEventData>, IDeselectHandler
    {
        public void OnDeselect(BaseEventData eventData)
            => RaiseOnReceivedEvent(eventData);
    }

    public class RectTransformChangedHandler : UIEventReceiver<Rect>
    {
        private RectTransform _rectTransform;

        protected override void Awake()
            => _rectTransform = GetComponent<RectTransform>();

        protected override void OnRectTransformDimensionsChange()
        {
            if (_rectTransform == null)
                _rectTransform = GetComponent<RectTransform>();

            RaiseOnReceivedEvent(_rectTransform.rect);
        }
    }

    public class UIEventReceiver<T> : UIBehaviour
    {
        public event Action<T> onReceivedEvent;

        protected void RaiseOnReceivedEvent(T eventData)
        {
            onReceivedEvent?.Invoke(eventData);
        }
    }
}