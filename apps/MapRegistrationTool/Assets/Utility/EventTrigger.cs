using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.EventSystems;

namespace Placeframe.MapRegistrationTool
{
    public class EventTrigger : MonoBehaviour
    {
        private static Dictionary<EventTriggerType, Type> _componentTypes = new Dictionary<EventTriggerType, Type>()
        {
            {EventTriggerType.PointerEnter, typeof(PointerEnterHandler) },
            {EventTriggerType.PointerExit, typeof(PointerExitHandler) },
            {EventTriggerType.PointerDown, typeof(PointerDownHandler) },
            {EventTriggerType.PointerUp, typeof(PointerUpHandler) },
            {EventTriggerType.PointerClick, typeof(PointerClickHandler) },
            {EventTriggerType.Drop, typeof(DropHandler) },
            {EventTriggerType.Scroll, typeof(ScrollHandler) },
            {EventTriggerType.UpdateSelected, typeof(UpdateSelectedHandler) },
            {EventTriggerType.Select, typeof(SelectHandler) },
            {EventTriggerType.Deselect, typeof(DeselectHandler) },
            {EventTriggerType.Move, typeof(MoveHandler) },
            {EventTriggerType.Submit, typeof(SubmitHandler) },
            {EventTriggerType.Cancel, typeof(CancelHandler) }
        };

        private EventHandlerBase GetEventHandler(EventTriggerType type)
        {
            return (EventHandlerBase)gameObject.GetOrAddComponent(_componentTypes[type]);
        }

        public void AddListener(EventTriggerType type, UnityAction<BaseEventData> listener)
        {
            switch (type)
            {
                case EventTriggerType.InitializePotentialDrag:
                    gameObject.GetOrAddComponent<DragHandler>().onInitializePotentialDrag.AddListener(listener);
                    break;
                case EventTriggerType.BeginDrag:
                    gameObject.GetOrAddComponent<DragHandler>().onBeginDrag.AddListener(listener);
                    break;
                case EventTriggerType.Drag:
                    gameObject.GetOrAddComponent<DragHandler>().onDrag.AddListener(listener);
                    break;
                case EventTriggerType.EndDrag:
                    gameObject.GetOrAddComponent<DragHandler>().onEndDrag.AddListener(listener);
                    break;
                default:
                    GetEventHandler(type).onEvent.AddListener(listener);
                    break;
            }
        }

        public void RemoveListener(EventTriggerType type, UnityAction<BaseEventData> listener)
        {
            switch (type)
            {
                case EventTriggerType.InitializePotentialDrag:
                    gameObject.GetOrAddComponent<DragHandler>().onInitializePotentialDrag.RemoveListener(listener);
                    break;
                case EventTriggerType.BeginDrag:
                    gameObject.GetOrAddComponent<DragHandler>().onBeginDrag.RemoveListener(listener);
                    break;
                case EventTriggerType.Drag:
                    gameObject.GetOrAddComponent<DragHandler>().onDrag.RemoveListener(listener);
                    break;
                case EventTriggerType.EndDrag:
                    gameObject.GetOrAddComponent<DragHandler>().onEndDrag.RemoveListener(listener);
                    break;
                default:
                    GetEventHandler(type).onEvent.RemoveListener(listener);
                    break;
            }
        }

        private class EventHandlerBase : MonoBehaviour
        {
            public UnityEvent<BaseEventData> onEvent = new UnityEvent<BaseEventData>();
        }

        private class PointerEnterHandler : EventHandlerBase, IPointerEnterHandler
        {
            public void OnPointerEnter(PointerEventData eventData)
                => onEvent.Invoke(eventData);
        }

        private class PointerExitHandler : EventHandlerBase, IPointerExitHandler
        {
            public void OnPointerExit(PointerEventData eventData)
                => onEvent.Invoke(eventData);
        }

        private class PointerDownHandler : EventHandlerBase, IPointerDownHandler
        {
            public void OnPointerDown(PointerEventData eventData)
                => onEvent.Invoke(eventData);
        }

        private class PointerUpHandler : EventHandlerBase, IPointerUpHandler
        {
            public void OnPointerUp(PointerEventData eventData)
                => onEvent.Invoke(eventData);
        }

        private class PointerClickHandler : EventHandlerBase, IPointerClickHandler
        {
            public void OnPointerClick(PointerEventData eventData)
                => onEvent.Invoke(eventData);
        }

        public class DragHandler : MonoBehaviour, IInitializePotentialDragHandler, IBeginDragHandler, IDragHandler, IEndDragHandler
        {
            public UnityEvent<BaseEventData> onInitializePotentialDrag = new UnityEvent<BaseEventData>();
            public UnityEvent<BaseEventData> onBeginDrag = new UnityEvent<BaseEventData>();
            public UnityEvent<BaseEventData> onDrag = new UnityEvent<BaseEventData>();
            public UnityEvent<BaseEventData> onEndDrag = new UnityEvent<BaseEventData>();

            void IInitializePotentialDragHandler.OnInitializePotentialDrag(PointerEventData eventData)
                => onInitializePotentialDrag.Invoke(eventData);

            void IBeginDragHandler.OnBeginDrag(PointerEventData eventData)
                => onBeginDrag.Invoke(eventData);

            void IDragHandler.OnDrag(PointerEventData eventData)
                => onDrag.Invoke(eventData);

            void IEndDragHandler.OnEndDrag(PointerEventData eventData)
                => onEndDrag.Invoke(eventData);
        }

        private class DropHandler : EventHandlerBase, IDropHandler
        {
            public void OnDrop(PointerEventData eventData)
                => onEvent.Invoke(eventData);
        }

        private class ScrollHandler : EventHandlerBase, IScrollHandler
        {
            public void OnScroll(PointerEventData eventData)
                => onEvent.Invoke(eventData);
        }

        private class UpdateSelectedHandler : EventHandlerBase, IUpdateSelectedHandler
        {
            public void OnUpdateSelected(BaseEventData eventData)
                => onEvent.Invoke(eventData);
        }

        private class SelectHandler : EventHandlerBase, ISelectHandler
        {
            public void OnSelect(BaseEventData eventData)
                => onEvent.Invoke(eventData);
        }

        private class DeselectHandler : EventHandlerBase, IDeselectHandler
        {
            public void OnDeselect(BaseEventData eventData)
                => onEvent.Invoke(eventData);
        }

        private class MoveHandler : EventHandlerBase, IMoveHandler
        {
            public void OnMove(AxisEventData eventData)
                => onEvent.Invoke(eventData);
        }

        private class SubmitHandler : EventHandlerBase, ISubmitHandler
        {
            public void OnSubmit(BaseEventData eventData)
                => onEvent.Invoke(eventData);
        }

        private class CancelHandler : EventHandlerBase, ICancelHandler
        {
            public void OnCancel(BaseEventData eventData)
                => onEvent.Invoke(eventData);
        }
    }
}