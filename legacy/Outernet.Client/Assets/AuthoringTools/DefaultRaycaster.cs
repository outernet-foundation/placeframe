using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Outernet.Client.AuthoringTools
{
    [RequireComponent(typeof(Camera))]
    public class DefaultRaycaster : BaseRaycaster
    {
        public override Camera eventCamera => _eventCamera;

        public GameObject defaultObject;
        private Camera _eventCamera;

        protected override void Awake()
        {
            _eventCamera = GetComponent<Camera>();
            base.Awake();
        }

        public override void Raycast(PointerEventData eventData, List<RaycastResult> resultAppendList)
        {
            resultAppendList.Add(new RaycastResult()
            {
                gameObject = defaultObject,
                module = this,
                distance = float.MaxValue,
                screenPosition = eventData.position,
                index = resultAppendList.Count
            });
        }
    }
}