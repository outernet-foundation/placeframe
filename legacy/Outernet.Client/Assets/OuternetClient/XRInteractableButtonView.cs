using UnityEngine;
using UnityEngine.Events;
using UnityEngine.XR.Interaction.Toolkit;
using UnityEngine.XR.Interaction.Toolkit.Interactables;

namespace Outernet.Client
{
    [RequireComponent(typeof(XRBaseInteractable))]
    public class XRInteractableButtonView : MonoBehaviour
    {
        public Animator animator;
        public string hoverPropertyName = "hover";
        public string pressPropertyName = "press";
        public UnityEvent onClick;
        private XRBaseInteractable _interactable;

        private void Awake()
        {
            _interactable = GetComponent<XRBaseInteractable>();
            _interactable.firstHoverEntered.AddListener(HandleFirstHoverEntered);
            _interactable.lastHoverExited.AddListener(HandleLastHoverExited);
            _interactable.selectEntered.AddListener(HandleSelectEntered);
            _interactable.selectExited.AddListener(HandleSelectExited);
        }

        private void HandleFirstHoverEntered(HoverEnterEventArgs arg0)
        {
            animator.SetBool(hoverPropertyName, true);
        }

        private void HandleLastHoverExited(HoverExitEventArgs arg0)
        {
            animator.SetBool(hoverPropertyName, false);
        }

        private void HandleSelectEntered(SelectEnterEventArgs arg0)
        {
            if (_interactable.isSelected)
                animator.SetBool(pressPropertyName, true);
        }

        private void HandleSelectExited(SelectExitEventArgs arg0)
        {
            if (!arg0.isCanceled)
                onClick.Invoke();

            if (!_interactable.isSelected)
                animator.SetBool(pressPropertyName, false);
        }
    }
}