using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.UI;

#if MAGIC_LEAP && !UNITY_EDITOR
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.UI;
#endif

namespace Outernet.Client
{
    // This class allows drag scrolling to continue even when the pointer is no longer over the scroll rect
    public class ContinuousScrollRect : ScrollRect
    {
        bool isDragging = false;
        BaseRaycaster raycaster;

#if MAGIC_LEAP && !UNITY_EDITOR
        TrackedDeviceModel trackedDeviceModel;
#endif

        public override void OnBeginDrag(PointerEventData eventData)
        {
            base.OnBeginDrag(eventData);

            isDragging = true;
            raycaster = eventData.pointerPressRaycast.module;

#if MAGIC_LEAP && !UNITY_EDITOR
            var inputModule = EventSystem.current.currentInputModule as XRUIInputModule;
            inputModule.GetTrackedDeviceModel(inputModule.GetInteractor(eventData.pointerId), out trackedDeviceModel);
#endif
        }

        public override void OnEndDrag(PointerEventData eventData)
        {
            base.OnEndDrag(eventData);
            isDragging = false;
        }

        // OnDrag is not called when the mouse is not over the scroll rect.
        public override void OnDrag(PointerEventData eventData) { }

        private void Update()
        {
            if (!isDragging) return;

#if MAGIC_LEAP && !UNITY_EDITOR
            if (!trackedDeviceModel.select)
#else
            if (Pointer.current == null || !Pointer.current.press.isPressed)
#endif
            {
                OnEndDrag(new PointerEventData(EventSystem.current)
                {
                    pointerPressRaycast = new RaycastResult() { module = raycaster }
                });
                return;
            }

#if MAGIC_LEAP && !UNITY_EDITOR
            if (trackedDeviceModel.raycastPoints.Count < 2) return;

            // Raycast from the tracked device to the plane defined by the scroll rect
            var ray = new Ray(trackedDeviceModel.raycastPoints[0], trackedDeviceModel.raycastPoints[1]);
            if (!new Plane(-transform.forward, transform.position).Raycast(ray, out var distance))
            {
                return;
            }

            // Convert the intersection point to screen space, as expected by OnDrag
            var position = raycaster.eventCamera.WorldToScreenPoint(ray.GetPoint(distance));
#else
            // We have an actual screen, so just use the current pointer position
            var position = Pointer.current.position.ReadValue();
#endif

            // Simulate a drag event
            base.OnDrag(new PointerEventData(EventSystem.current)
            {
                position = position,
                // OnDrag determines the camera to use for its calculations by getting it from the raycaster module, so we need to provide it
                pointerPressRaycast = new RaycastResult() { module = raycaster }
            });
        }
    }
}