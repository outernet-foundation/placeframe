using UnityEngine;
using Outernet.Shared;
using UnityEngine.InputSystem;
using UnityEngine.XR.Interaction.Toolkit.Interactors;
using UnityEngine.XR;
using System;

namespace Outernet.Client
{
    [Flags]
    enum TrackingStates
    {
        None,
        Position = 1 << 0,
        Rotation = 1 << 1,
    }

    public class Controller : MonoBehaviour
    {
        public InputActionProperty menuInput;
        public InputActionProperty trackingStateInput;
        public NearFarInteractor nearFarInteractor;

        private void Start()
        {
            menuInput.action.Enable();
            menuInput.action.performed += ToggleSettingsMenu;

            trackingStateInput.action.Enable();
            trackingStateInput.action.performed += context =>
                nearFarInteractor.gameObject.SetActive(context.ReadValue<int>() != 0);
            trackingStateInput.action.canceled += context =>
                nearFarInteractor.gameObject.SetActive(false);
        }

        private void ToggleSettingsMenu(InputAction.CallbackContext _)
        {
            if (LocalUser.SettingsOpen())
            {
                LocalUser.ChangeSettingsMenuState(SettingsMenuState.ClosedRightPalm);
            }
            else
            {
                LocalUser.ChangeSettingsMenuState(SettingsMenuState.OpenRightPalm);
            }
        }

        private void Update()
        {
            var localPalmPosition = Camera.main.transform.InverseTransformPoint(transform.position);
            var localPalmRotation = Quaternion.Inverse(Camera.main.transform.rotation) * transform.rotation;

            if (App.ClientID != null && App.State_Old.users.ContainsKey(App.ClientID.Value))
            {
                var localUser = App.State_Old.users.Get(App.ClientID.Value);

                localUser.rightPalmLocalPosition.EnqueueSet(localPalmPosition);
                localUser.rightPalmLocalRotation.EnqueueSet(localPalmRotation);
            }
        }
    }
}