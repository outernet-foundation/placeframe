using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Outernet.Client.AuthoringTools
{
    public class NonDraggingScrollRect : ScrollRect
    {
        public override void OnDrag(PointerEventData eventData) { }
        public override void OnBeginDrag(PointerEventData eventData) { }
        public override void OnEndDrag(PointerEventData eventData) { }
        public override void OnInitializePotentialDrag(PointerEventData eventData) { }
    }
}
