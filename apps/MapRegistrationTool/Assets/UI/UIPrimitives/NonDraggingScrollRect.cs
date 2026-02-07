using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Placeframe.MapRegistrationTool
{
    public class NonDraggingScrollRect : ScrollRect
    {
        public override void OnDrag(PointerEventData eventData) { }
        public override void OnBeginDrag(PointerEventData eventData) { }
        public override void OnEndDrag(PointerEventData eventData) { }
        public override void OnInitializePotentialDrag(PointerEventData eventData) { }
    }
}
