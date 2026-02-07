using UnityEngine;
using UnityEngine.EventSystems;

namespace Placeframe.MapRegistrationTool
{
    [RequireComponent(typeof(RectTransform))]
    public class ResizablePanel : MonoBehaviour, IBeginDragHandler, IEndDragHandler, IDragHandler
    {
        [System.Serializable]
        public struct Handle
        {
            public RectTransform transform;
            public Vector2 scaleAxes;
        }

        public Handle[] handles;
        private Handle _currentHandle;
        private RectTransform _rectTransform;
        private Vector3 _anchorPos;
        private bool _resizing;

        private void Awake()
        {
            _rectTransform = (RectTransform)transform;
        }

        public void OnBeginDrag(PointerEventData eventData)
        {
            if (TryGetHandle(eventData.rawPointerPress, out _currentHandle))
            {
                _resizing = true;
                _anchorPos = _rectTransform.TransformPoint(
                    _rectTransform.rect.center +
                    Vector2.Scale(_rectTransform.rect.size, _currentHandle.scaleAxes * -0.5f)
                );
            }
        }

        public void OnDrag(PointerEventData eventData)
        {
            if (!_resizing)
                return;

            var delta = Vector2.Scale(eventData.delta, _currentHandle.scaleAxes);
            var sizeDelta = (Vector2)transform.parent.InverseTransformVector(delta);

            _rectTransform.SetSizeWithCurrentAnchors(RectTransform.Axis.Horizontal, _rectTransform.rect.width + sizeDelta.x);
            _rectTransform.SetSizeWithCurrentAnchors(RectTransform.Axis.Vertical, _rectTransform.rect.height + sizeDelta.y);

            var relAnchorPos = _rectTransform.TransformPoint(
                _rectTransform.rect.center +
                Vector2.Scale(_rectTransform.rect.size, _currentHandle.scaleAxes * -0.5f)
            );

            _rectTransform.position += _anchorPos - relAnchorPos;
        }

        public void OnEndDrag(PointerEventData eventData)
        {
            _currentHandle = default;
            _resizing = false;
        }

        private bool TryGetHandle(GameObject pressReceiver, out Handle handle)
        {
            Transform currUpstream = pressReceiver.transform;
            while (currUpstream != null)
            {
                if (currUpstream is RectTransform currUpstreamRect)
                {
                    foreach (var handleToCheck in handles)
                    {
                        if (handleToCheck.transform == currUpstreamRect)
                        {
                            handle = handleToCheck;
                            return true;
                        }
                    }
                }

                currUpstream = currUpstream.parent;
                continue;
            }

            handle = default;
            return false;
        }
    }
}