
using System;
using UnityEngine;
using R3;

namespace Outernet.Client
{
    public class ResizeHandle : Handle
    {
        private Transform attachTransform;
        private Vector3 originalAttachPosition;
        private Vector3 originalChromePosition;
        private Vector2 originalDimensions;
        private IDisposable subscriptions;

        protected override void Awake()
        {
            base.Awake();

            subscriptions = Disposable.Combine(
                interactable.firstSelectEntered.AsObservable().Subscribe(beginSelectEvent =>
                {
                    attachTransform = beginSelectEvent.interactorObject.GetAttachTransform(interactable);
                    originalAttachPosition = attachTransform.position;
                    originalChromePosition = chrome.transform.parent.position;
                    originalDimensions = chrome.dimensions;

                    chrome.onResizeStarted.Invoke();
                }),

                interactable.lastSelectExited.AsObservable().Subscribe(_ =>
                {
                    chrome.onResizeEnded.Invoke();
                })
            );
        }

        private void OnDestroy()
        {
            subscriptions.Dispose();
        }

        private void Update()
        {
            if (!interactable.isSelected || !chrome.allowResize) return;

            // Calculate the normalized position of the attach transform relative to the chrome
            Vector2 attachTransformDeltaRelativeToChrome = chrome.transform.parent.InverseTransformVector(attachTransform.position - originalAttachPosition);
            attachTransformDeltaRelativeToChrome.x = normalizedPosition.x == 0 ? 0 : attachTransformDeltaRelativeToChrome.x;
            attachTransformDeltaRelativeToChrome.y = normalizedPosition.y == 0 ? 0 : attachTransformDeltaRelativeToChrome.y;

            // Calculate the new dimensions of the chrome, constrained by the minimum dimensions
            var newDimensions = originalDimensions + Vector2.Scale(attachTransformDeltaRelativeToChrome, normalizedPosition * 2);
            var constrainedNewDimensions = Vector2.Max(newDimensions, chrome.minimumDimensions);

            // Adjust the attach transform delta to account for the constrained new dimensions
            attachTransformDeltaRelativeToChrome += Vector2.Scale(constrainedNewDimensions - newDimensions, normalizedPosition * 2);

            // Update the chrome's position and dimensions
            chrome.transform.parent.position = originalChromePosition + chrome.transform.parent.TransformVector(attachTransformDeltaRelativeToChrome / 2);
            chrome.dimensions = constrainedNewDimensions;
        }
    }
}