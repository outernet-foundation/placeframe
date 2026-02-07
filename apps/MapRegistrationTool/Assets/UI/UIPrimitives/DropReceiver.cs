using System;

using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Placeframe.MapRegistrationTool
{
    public class DropReceiver : ViewBase, IDropHandler
    {
        public Func<GameObject, bool> filter;
        public Action<GameObject> onDrop;

        private void Awake()
        {
            if (GetComponent<Graphic>() == null)
                gameObject.AddComponent<NonDrawingGraphic>();
        }

        public void OnDrop(PointerEventData eventData)
        {
            onDrop(eventData.pointerDrag);
        }
    }
}