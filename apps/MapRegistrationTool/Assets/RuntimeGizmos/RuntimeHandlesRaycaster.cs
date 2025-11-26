using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Outernet.MapRegistrationTool
{
    [RequireComponent(typeof(Camera))]
    public class RuntimeHandlesRaycaster : BaseRaycaster
    {
        private static List<IRuntimeHandle> _handles = new List<IRuntimeHandle>();
        public override Camera eventCamera => _eventCamera;

        private Camera _eventCamera;

        protected override void Awake()
        {
            _eventCamera = GetComponent<Camera>();
            base.Awake();
        }

        public override void Raycast(PointerEventData eventData, List<RaycastResult> resultAppendList)
        {
            IRuntimeHandle closestHandle = null;
            float closestDistance = float.MaxValue;

            var inputRay = _eventCamera.ScreenPointToRay(new Vector3(
                eventData.position.x,
                eventData.position.y,
                _eventCamera.nearClipPlane
            ));

            foreach (var handle in _handles)
            {
                if (handle.TryGetInputDistance(inputRay, out var dist))
                {
                    if (closestDistance > dist)
                    {
                        closestHandle = handle;
                        closestDistance = dist;
                    }
                }
            }

            if (closestHandle == null)
                return;

            resultAppendList.Add(new RaycastResult()
            {
                gameObject = closestHandle.gameObject,
                module = this,
                distance = closestDistance,
                worldPosition = inputRay.GetPoint(closestDistance),
                worldNormal = -inputRay.direction,
                screenPosition = eventData.position,
                index = resultAppendList.Count,
                sortingLayer = 0,
                sortingOrder = 0
            });
        }

        public static void RegisterHandle(IRuntimeHandle handle)
        {
            _handles.Add(handle);
        }

        public static void DeregisterHandle(IRuntimeHandle handle)
        {
            _handles.Remove(handle);
        }
    }
}