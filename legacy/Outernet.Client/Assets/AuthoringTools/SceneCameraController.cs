using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;

namespace Outernet.Client.AuthoringTools
{
    public class SceneCameraController : MonoBehaviour, IScrollHandler, IPointerClickHandler, IPointerDownHandler, IPointerUpHandler, IDragHandler
    {
        private static readonly float MIN_CAMERA_SPEED = 0.1f;
        private static readonly float MAX_CAMERA_SPEED = 200;
        private static readonly float CAMERA_ACCELERATION = 2f;

        private float _yRotation;
        private float _xRotation;
        private float _focusDistance = 3f;

        private bool _hasRightMouseDown = false;
        private float _currentSpeed = 0.1f;

        private Camera _camera;

        private void Awake()
        {
            _camera = Camera.main;

            SystemMenu.AddMenuItem(
                "Edit/Focus",
                onSelect: () =>
                {
                    _focusDistance = 3f;
                    Utility.CalcSelectedGroupTransform(out var position, out var _);
                    _camera.transform.position = position - (_camera.transform.forward * _focusDistance);
                },
                validate: () => App.state.authoringTools.selectedObjects.count > 0,
                commandKeys: new Key[] { Key.F }
            );
        }

        private void Update()
        {
            if (_hasRightMouseDown && !Utility.KeyboardIsFocused())
            {
                var direction = Vector3.zero;

                if (Keyboard.current.qKey.isPressed)
                    direction.y -= 1f;

                if (Keyboard.current.eKey.isPressed)
                    direction.y += 1f;

                if (Keyboard.current.aKey.isPressed)
                    direction.x -= 1f;

                if (Keyboard.current.dKey.isPressed)
                    direction.x += 1f;

                if (Keyboard.current.wKey.isPressed)
                    direction.z += 1f;

                if (Keyboard.current.sKey.isPressed)
                    direction.z -= 1f;

                if (direction == Vector3.zero)
                {
                    _currentSpeed = MIN_CAMERA_SPEED;
                    return;
                }

                float speed = Keyboard.current.shiftKey.isPressed ? _currentSpeed * 3f : _currentSpeed;
                _camera.transform.position += _camera.transform.rotation * direction.normalized * speed * Time.deltaTime;
                _currentSpeed = Mathf.Min(_currentSpeed + (CAMERA_ACCELERATION * Time.deltaTime), MAX_CAMERA_SPEED);
            }
        }

        public void OnScroll(PointerEventData eventData)
        {
            var prevFocusLocation = _camera.ViewportToWorldPoint(new Vector3(0.5f, 0.5f, _focusDistance));
            _focusDistance *= eventData.scrollDelta.y > 0 ? 0.975f : 1.025f;
            _camera.transform.position = prevFocusLocation - (_camera.transform.forward * _focusDistance);
        }

        public void OnPointerClick(PointerEventData eventData)
        {
            if (eventData.button == PointerEventData.InputButton.Left &&
                eventData.rawPointerPress == gameObject)
            {
                AuthoringToolsApp.SetSelectedObjects();
            }
        }

        public void OnPointerDown(PointerEventData eventData)
        {
            if (eventData.button == PointerEventData.InputButton.Right)
            {
                _currentSpeed = MIN_CAMERA_SPEED;
                _hasRightMouseDown = true;
            }
        }

        public void OnPointerUp(PointerEventData eventData)
        {
            if (eventData.button == PointerEventData.InputButton.Right)
                _hasRightMouseDown = false;
        }

        // pan : middle click / alt + ctrl + left click / option + command + left click
        // orbit: alt + left click / alt + left click / option + left click
        // zoom: scroll wheel / alt + right click / alt + right click / scroll / option + ctrl + left click

        private bool IsPan(PointerEventData eventData)
        {
            return eventData.button == PointerEventData.InputButton.Middle ||
#if UNITY_STANDALONE_OSX
                (eventData.button == PointerEventData.InputButton.Left && Keyboard.current.altKey.isPressed && (Keyboard.current.leftCommandKey.isPressed || Keyboard.current.rightCommandKey.isPressed));
#else
                (eventData.button == PointerEventData.InputButton.Left && Keyboard.current.altKey.isPressed && Keyboard.current.ctrlKey.isPressed);
#endif
        }

        // private bool IsOrbit(PointerEventData eventData)
        // {
        //     return eventData.button == PointerEventData.InputButton.Left && Keyboard.current.altKey.isPressed;
        // }

        // private bool IsZoom(PointerEventData eventData)
        // {
        //     return (eventData.button == PointerEventData.InputButton.Right && Keyboard.current.altKey.isPressed) ||
        //         (eventData.button == PointerEventData.InputButton.Left && Keyboard.current.altKey.isPressed && Keyboard.current.ctrlKey.isPressed);
        // }

        public void OnDrag(PointerEventData eventData)
        {
            if (eventData.button == PointerEventData.InputButton.Right)
            {
                _yRotation += eventData.delta.x / Screen.width * 90f;
                _xRotation = Mathf.Clamp(_xRotation + (-eventData.delta.y / Screen.height * 90f), -89f, 89f);
                _camera.transform.rotation = Quaternion.AngleAxis(_yRotation, Vector3.up) * Quaternion.AngleAxis(_xRotation, Vector3.right);
            }
            else if (IsPan(eventData))
            {
                var prevWorldPoint = _camera.ScreenToWorldPoint(new Vector3(eventData.position.x - eventData.delta.x, eventData.position.y - eventData.delta.y, _focusDistance));
                var curWorldPoint = _camera.ScreenToWorldPoint(new Vector3(eventData.position.x, eventData.position.y, _focusDistance));
                _camera.transform.position += prevWorldPoint - curWorldPoint;
            }
        }
    }
}