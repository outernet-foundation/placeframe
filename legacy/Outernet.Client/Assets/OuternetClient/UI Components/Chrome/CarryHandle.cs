
using System;
using UnityEngine;
using R3;

namespace Outernet.Client
{
    [RequireComponent(typeof(LineHandleGeometry))]
    public class CarryHandle : Handle
    {
        private Transform attachTransform;
        private Vector3 attachPositionRelative;
        private IDisposable subscriptions;

        protected override void Awake()
        {
            if (!Application.isPlaying) return;

            base.Awake();

            subscriptions = Disposable.Combine(
                interactable.firstSelectEntered.AsObservable().Subscribe(beginSelectEvent =>
                {
                    attachTransform = beginSelectEvent.interactorObject.GetAttachTransform(interactable);
                    attachPositionRelative = attachTransform.InverseTransformPoint(chrome.transform.parent.position);
                    chrome.onCarryStarted.Invoke();
                }),

                interactable.lastSelectExited.AsObservable().Subscribe(_ =>
                {
                    chrome.onCarryEnded.Invoke();
                })
            );
        }

        private void OnDestroy()
        {
            if (!Application.isPlaying) return;

            subscriptions.Dispose();
        }

        private void Update()
        {
            if (!interactable.isSelected || !chrome.allowCarry) return;

            chrome.transform.parent.SetPositionAndRotation(
                attachTransform.TransformPoint(attachPositionRelative),
                Quaternion.LookRotation(Camera.main.transform.position - transform.parent.position) *
                Quaternion.Euler(0, 180, 0) *
                Quaternion.Euler(20, 0, 0));
        }
    }
}