#if UNITY_EDITOR && !AUTHORING_TOOLS_ENABLED
using UnityEngine;
using UnityEngine.InputSystem;

namespace Outernet.Client
{
    class Platform : MonoBehaviour
    {
        private const float lookMultiplier = 25;
        private const float moveMultiplier = 2f;
        private const float shiftMultiplier = 5f;

        private InputAction moveAction;
        private InputAction lookAction;
        private InputAction rightClickAction;
        private InputAction shiftAction;
        private InputAction verticalAction;

        private void Start()
        {
            Camera.main.clearFlags = CameraClearFlags.Skybox;

            if (Camera.main.TryGetComponent(out UnityEngine.InputSystem.XR.TrackedPoseDriver poseDriver))
                poseDriver.enabled = false;

            Instantiate(Resources.Load("MouseInteractor"));

            moveAction = new InputAction(type: InputActionType.Value, binding: "<Keyboard>/w");
            moveAction.AddCompositeBinding("Dpad")
                .With("Up", "<Keyboard>/w")
                .With("Down", "<Keyboard>/s")
                .With("Left", "<Keyboard>/a")
                .With("Right", "<Keyboard>/d");
            moveAction.Enable();

            verticalAction = new InputAction(type: InputActionType.Value);
            verticalAction.AddCompositeBinding("Axis")
                .With("Positive", "<Keyboard>/q")
                .With("Negative", "<Keyboard>/e");
            verticalAction.Enable();

            lookAction = new InputAction(type: InputActionType.Value, binding: "<Mouse>/delta");
            lookAction.Enable();

            rightClickAction = new InputAction(type: InputActionType.Button, binding: "<Mouse>/rightButton");
            rightClickAction.Enable();

            shiftAction = new InputAction(type: InputActionType.Button, binding: "<Keyboard>/shift");
            shiftAction.Enable();
        }

        void Update()
        {
            var frameLookMultiplier = lookMultiplier * Time.deltaTime;
            var frameMoveMultiplier = moveMultiplier * Time.deltaTime * (shiftAction.ReadValue<float>() > 0 ? shiftMultiplier : 1f);
            var lookDelta = lookAction.ReadValue<Vector2>();
            var moveDelta2D = moveAction.ReadValue<Vector2>();
            var moveDelta = Camera.main.transform.TransformDirection(new Vector3(moveDelta2D.x, 0, moveDelta2D.y));
            var verticalDelta = Vector3.up * verticalAction.ReadValue<float>();

            if (rightClickAction.ReadValue<float>() > 0)
            {
                Camera.main.transform.rotation = Quaternion.Euler(
                    Camera.main.transform.eulerAngles.x - (lookDelta.y * frameLookMultiplier),
                    Camera.main.transform.eulerAngles.y + (lookDelta.x * frameLookMultiplier),
                    0
                );
            }

            Camera.main.transform.position += frameMoveMultiplier * (moveDelta + verticalDelta);
        }
    }
}
#endif
