using System;
using R3;
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.Interactables;

namespace Outernet.Client
{
    [RequireComponent(typeof(XRBaseInteractable))]
    abstract public class HandleGeometry : MonoBehaviour
    {
        public Chrome chrome;
        public GameObject modelGameObject;
        public bool hideWhenUnused = true;

        private XRBaseInteractable interactable => GetComponent<XRBaseInteractable>();
        private IDisposable subscriptions;

        protected void Awake()
        {
            subscriptions = Observable
                .Merge(
                    interactable.firstHoverEntered.AsObservable().Select(beginHover => Unit.Default),
                    interactable.lastHoverExited.AsObservable().Select(endHover => Unit.Default),
                    interactable.firstSelectEntered.AsObservable().Select(beginSelect => Unit.Default),
                    interactable.lastSelectExited.AsObservable().Select(endSelect => Unit.Default))
                .Subscribe(_ => UpdateVisibility());

            UpdateVisibility();
        }

        private void OnDestroy()
        {
            subscriptions.Dispose();
        }

        private void UpdateVisibility()
        {
            modelGameObject.SetActive(!hideWhenUnused || interactable.isSelected || interactable.isHovered);
        }
    }
}