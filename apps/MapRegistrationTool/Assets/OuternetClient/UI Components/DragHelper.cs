using UnityEngine;
using UnityEngine.EventSystems;

namespace Outernet.MapRegistrationTool
{
    public class DragHelper : MonoBehaviour, IBeginDragHandler
    {
        public event System.Action onDragStarted;

        public void OnBeginDrag(PointerEventData eventData)
        {
            if (eventData.button != PointerEventData.InputButton.Left)
                return;

            onDragStarted?.Invoke();
        }
    }
}