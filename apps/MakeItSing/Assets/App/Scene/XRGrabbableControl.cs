using System;
using Nessle;
using ObserveThing;
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.Interactables;

namespace Plerion.MakeItSing
{
    public struct XRGrabbableProps
    {
        public IValueObservable<bool> allowGrab;
        public Action onGrabbed;
        public Action onReleased;
    }

    [RequireComponent(typeof(XRGrabInteractable))]
    public class XRGrabbableControl : Control<XRGrabbableProps>
    {
        private XRGrabInteractable _grabInteractable;

        private void Awake()
        {
            _grabInteractable = GetComponent<XRGrabInteractable>();
        }

        protected override void SetupInternal()
        {
            if (props.onGrabbed != null)
                _grabInteractable.firstSelectEntered.AddListener(_ => props.onGrabbed());

            if (props.onReleased != null)
                _grabInteractable.lastSelectExited.AddListener(_ => props.onReleased());

            AddBinding(
                props.allowGrab?.Subscribe(x => _grabInteractable.enabled = x)
            );
        }
    }
}