using UnityEngine;

using System;
using UnityEngine.UI;
using TMPro;
using UnityEngine.EventSystems;

namespace Outernet.MapRegistrationTool
{
    public class HierarchyListElement : MonoBehaviour,
        IBeginDragHandler,
        IEndDragHandler,
        IPointerClickHandler,
        IPointerEnterHandler,
        IPointerExitHandler
    {
        public Toggle foldout;
        public TextMeshProUGUI label;
        public RectTransform contentParent;
        public RectTransform indentObject;

        public event Action<bool> onIsOpenChanged;
        public event Action onClick;
        public event Action onBeginDrag;
        public event Action onEndDrag;
        public event Action onPointerEnter;
        public event Action onPointerExit;

        private void Awake()
        {
            foldout.onValueChanged.AddListener(x =>
            {
                contentParent.gameObject.SetActive(x);
                onIsOpenChanged?.Invoke(x);
            });
        }

        void IBeginDragHandler.OnBeginDrag(PointerEventData eventData)
        {
            onBeginDrag?.Invoke();
        }

        void IEndDragHandler.OnEndDrag(PointerEventData eventData)
        {
            onEndDrag?.Invoke();
        }

        void IPointerClickHandler.OnPointerClick(PointerEventData eventData)
        {
            onClick?.Invoke();
        }

        void IPointerEnterHandler.OnPointerEnter(PointerEventData eventData)
        {
            onPointerEnter?.Invoke();
        }

        void IPointerExitHandler.OnPointerExit(PointerEventData eventData)
        {
            onPointerExit?.Invoke();
        }
    }
}