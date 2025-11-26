using UnityEngine;
using UnityEngine.EventSystems;

namespace Outernet.MapRegistrationTool
{
    public class SelectionTracker : MonoBehaviour, IPointerUpHandler, IPointerDownHandler
    {
        public static SelectionTracker Selected { get; private set; }
        public static int pointerId;

        public Transform snapTarget;

        public void OnPointerDown(PointerEventData eventData)
        {
            pointerId = eventData.pointerId;
            Selected = this;
        }

        public void OnPointerUp(PointerEventData eventData)
        {
            if (Selected != this) throw new System.Exception("Invalid state");

            Selected = null;
        }
    }
}