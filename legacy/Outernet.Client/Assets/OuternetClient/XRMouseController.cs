using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.XR;
using UnityEngine.XR.Interaction.Toolkit;

namespace Outernet.Client
{
    public class XRMouseController : XRBaseController
    {
        private Camera _mainCamera;

        // Input Actions for the new input system
        private InputAction mousePositionAction;
        private InputAction mouseButtonAction;

        protected override void Awake()
        {
            base.Awake();
            _mainCamera = Camera.main;

            // Define input actions
            mousePositionAction = new InputAction("MousePosition", binding: "<Mouse>/position");
            mouseButtonAction = new InputAction("Fire", binding: "<Mouse>/leftButton");

            // Enable input actions
            mousePositionAction.Enable();
            mouseButtonAction.Enable();
        }

        protected override void UpdateTrackingInput(XRControllerState controllerState)
        {
            base.UpdateTrackingInput(controllerState);
            if (controllerState == null)
                return;

            controllerState.isTracked = true;
            controllerState.inputTrackingState = InputTrackingState.Position | InputTrackingState.Rotation;

            // Get the current mouse position using the new input system
            Vector2 mousePosition = mousePositionAction.ReadValue<Vector2>();

            // Convert screen point to ray
            var screenRay = _mainCamera.ScreenPointToRay(mousePosition);

            // Update controller state with position and rotation based on the ray
            controllerState.position = screenRay.origin;
            controllerState.rotation = Quaternion.LookRotation(screenRay.direction, Vector3.up);
        }

        protected override void UpdateInput(XRControllerState controllerState)
        {
            base.UpdateInput(controllerState);
            if (controllerState == null)
                return;

            controllerState.ResetFrameDependentStates();

            // Get the current state of the left mouse button
            bool pressed = mouseButtonAction.ReadValue<float>() > 0;

            // Update controllerState with select, activate, UIPress values
            controllerState.selectInteractionState.SetFrameState(pressed);
            controllerState.uiPressInteractionState.SetFrameState(pressed);
        }

        protected void OnDestroy()
        {
            // Disable input actions to prevent memory leaks
            mousePositionAction.Disable();
            mouseButtonAction.Disable();
        }
    }
}
