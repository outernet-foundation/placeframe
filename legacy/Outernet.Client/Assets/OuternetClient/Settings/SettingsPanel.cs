using UnityEngine;
using Outernet.Shared;
using Outernet.Client.Location;
using System;
using R3;
using Placeframe.Core;

namespace Outernet.Client
{
    [RequireComponent(typeof(SyncedAnchor))]
    public class SettingsPanel : MonoBehaviour
    {
        enum AnimationState
        {
            Opening,
            Open,
            Closing
        }

        private const float upwardOffset = 0.5f;
        private const float animationDuration = 0.5f;
        static readonly Vector3 vector3ZeroWidthHeight = new Vector3(0, 0, 0.25f);

        public Chrome chrome;
        public SettingsMenu settingsMenu;

        private Guid userID;
        private UserRecord userRecord;
        private SyncedAnchor syncedAnchor;
        private IDisposable subscriptions;
        private Transform parent;

        private AnimationState animationState;

        private Vector3 animationStartPosition;
        private Quaternion animationStartRotation;
        private Vector3 animationControlPoint;
        private float animationTime;

        public bool opening => animationState == AnimationState.Opening;

        bool rightPalm =>
            userRecord.settingsMenuOpen.Value == SettingsMenuState.OpenRightPalm ||
            userRecord.settingsMenuOpen.Value == SettingsMenuState.ClosedRightPalm;

        Vector3 palmLocalPosition => rightPalm ?
            userRecord.rightPalmLocalPosition.Value : userRecord.leftPalmLocalPosition.Value;
        Quaternion palmLocalRotation => rightPalm ?
            userRecord.rightPalmLocalRotation.Value : userRecord.leftPalmLocalRotation.Value;

        Quaternion settingsPanelLocalRotationWhenClosed => Quaternion.LookRotation(
            Vector3.down,
            palmLocalRotation * Vector3.forward
        );

        public void Open(Guid userID, Transform parent)
        {
            this.parent = parent;
            this.userID = userID;

            if (userID != App.ClientID)
            {
                chrome.allowCarry = false;
                chrome.allowResize = false;
            }

            userRecord = App.State_Old.users.Get(userID);

            syncedAnchor = GetComponent<SyncedAnchor>();
            syncedAnchor.Initialize(userRecord.settingsMenuGeoPose);
            settingsMenu.Initialize();

            subscriptions = userRecord.settingsMenuOpen
                .AsObservable()
                .SkipWhile(open => open.Value == SettingsMenuState.ClosedLeftPalm)
                .Subscribe(open =>
                {
                    if (open.Value == SettingsMenuState.ClosedLeftPalm)
                    {
                        Close();
                    }
                });

            transform.position = parent.TransformPoint(palmLocalPosition);
            transform.rotation = parent.rotation * settingsPanelLocalRotationWhenClosed;
            transform.localScale = vector3ZeroWidthHeight;

            animationStartPosition = transform.position;
            animationStartRotation = transform.rotation;
            animationControlPoint = animationStartPosition + Vector3.up * upwardOffset;
            animationTime = 0f;
            animationState = AnimationState.Opening;

            syncedAnchor.State = SyncedAnchor.SyncState.Animating;
        }

        public void Close(bool immediate = false)
        {
            if (immediate)
            {
                Terminate();
                return;
            }

            animationStartPosition = transform.position;
            animationStartRotation = transform.rotation;
            animationControlPoint = animationStartPosition + Vector3.up * upwardOffset;
            animationTime = 0f;
            animationState = AnimationState.Closing;

            syncedAnchor.State = SyncedAnchor.SyncState.Animating;
        }

        private void Terminate()
        {
            settingsMenu.Terminate();
            subscriptions.Dispose();

            PrefabSystem.Destroy(this);
        }

        private void FixedUpdate()
        {
            if (animationState == AnimationState.Opening)
            {
                animationTime += Time.fixedDeltaTime;
                float t = animationTime / animationDuration;

                var settingsMenuTransform = VisualPositioningSystem.EcefToUnityWorld(
                    new Unity.Mathematics.double3(
                        userRecord.settingsMenuGeoPose.ecefPosition.Value.x,
                        userRecord.settingsMenuGeoPose.ecefPosition.Value.y,
                        userRecord.settingsMenuGeoPose.ecefPosition.Value.z),
                    userRecord.settingsMenuGeoPose.ecefRotation.Value);

                transform.localScale = Vector3.Lerp(vector3ZeroWidthHeight, Vector3.one, t * t);
                transform.position = Vector3.Lerp(
                    Vector3.Lerp(animationStartPosition, animationControlPoint, t),
                    Vector3.Lerp(animationControlPoint, settingsMenuTransform.position, t),
                    t * t);
                transform.rotation = Quaternion.Slerp(
                    animationStartRotation,
                    settingsMenuTransform.rotation,
                    t);

                if (t >= 1f)
                {
                    animationState = AnimationState.Open;

                    syncedAnchor.State = userID == App.ClientID ?
                        SyncedAnchor.SyncState.LocallyControlled :
                        SyncedAnchor.SyncState.Synced;
                }
            }
            else if (animationState == AnimationState.Closing)
            {
                animationTime += Time.fixedDeltaTime;
                float t = animationTime / animationDuration;

                transform.localScale = Vector3.Lerp(Vector3.one, vector3ZeroWidthHeight, Mathf.Sqrt(t));
                transform.position = Vector3.Lerp(
                    Vector3.Lerp(animationStartPosition, animationControlPoint, t),
                    Vector3.Lerp(animationControlPoint, parent.TransformPoint(palmLocalPosition), t),
                    t);
                transform.rotation = Quaternion.Slerp(
                    animationStartRotation,
                    parent.rotation * settingsPanelLocalRotationWhenClosed,
                    Mathf.Sqrt(t));

                if (t >= 1f)
                {
                    Terminate();
                }
            }
        }

        private void Update()
        {
            settingsMenu.RealUpdate();

            if (userRecord.settingsMenuDimensions.Value == chrome.dimensions) return;

            if (userID == App.ClientID)
            {
                userRecord.settingsMenuDimensions.EnqueueSet(chrome.dimensions);
            }
            else
            {
                chrome.dimensions = Vector3.Lerp(chrome.dimensions, userRecord.settingsMenuDimensions.Value, 0.1f);
            }
        }
    }
}