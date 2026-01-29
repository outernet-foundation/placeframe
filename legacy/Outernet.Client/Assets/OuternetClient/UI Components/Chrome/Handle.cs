
using System;
using UnityEngine;
using UnityEngine.XR.Interaction.Toolkit.Interactables;
using R3;

namespace Outernet.Client
{
    [RequireComponent(typeof(HandleGeometry))]
    public abstract class Handle : MonoBehaviour
    {
        public Chrome chrome;

        public XRBaseInteractable interactable => GetComponent<XRBaseInteractable>();

        public Vector2 normalizedPosition;
        public Vector3 offset;

        private IDisposable subscriptions;

        protected virtual void Awake()
        {
            subscriptions = chrome.dimensionsSubject.Subscribe(value =>
            {
                transform.position = chrome.transform.parent.TransformPoint(
                    Vector3.Scale(value, normalizedPosition) +
                    Vector3.Scale(offset, chrome.transform.localScale));
            });
        }

        private void OnDestroy()
        {
            subscriptions.Dispose();
        }
    }
}