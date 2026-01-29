using System;
using Outernet.Client.Location;
using Outernet.Shared;
using Placeframe.Core;
using R3;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Outernet.Client
{
    [RequireComponent(typeof(SyncedAnchor))]
    public class LocalUser : MonoBehaviour
    {
        const float settingsPanelSpawnTilt = 30f;
        const float settingsPanelSpawnDistance = 1f;
        private static SettingsPanel settingsPanel;

        private UserRecord userRecord;
        private InputAction spaceAction;
        private IDisposable subscriptions;

        public void Initialize(Guid id)
        {
            userRecord = App.State_Old.users.Get(id);

            var syncedAnchor = GetComponent<SyncedAnchor>();
            syncedAnchor.Initialize(userRecord.geoPose);
            syncedAnchor.State = SyncedAnchor.SyncState.LocallyControlled;

            spaceAction = new InputAction(type: InputActionType.Button, binding: "<Keyboard>/space");
            spaceAction.Enable();

            var ecefTransform = VisualPositioningSystem.UnityWorldToEcef(transform.position, transform.rotation);
            userRecord.geoPose.ecefPosition.EnqueueSet(ecefTransform.position.ToDouble3());
            userRecord.geoPose.ecefRotation.EnqueueSet(ecefTransform.rotation);
            userRecord.hasGeoPose.EnqueueSet(true);

            subscriptions = Disposable.Combine(
                userRecord
                    .settingsMenuOpen.SkipWhile(open => open.Value == SettingsMenuState.ClosedLeftPalm)
                    .Subscribe(open =>
                    {
                        if (
                            open.Value == SettingsMenuState.OpenLeftPalm
                            || open.Value == SettingsMenuState.OpenRightPalm
                        )
                        {
                            settingsPanel = PrefabSystem.Create(PrefabSystem.systemUIView);
                            settingsPanel.chrome.dimensions = userRecord.settingsMenuDimensions.Value;
                            settingsPanel.Open(id, transform);
                        }
                        else
                        {
                            settingsPanel.Close();
                            settingsPanel = null;
                        }
                    })
            );
        }

        public void Terminate()
        {
            if (settingsPanel != null)
            {
                settingsPanel.Close(true);
                settingsPanel = null;
            }

            spaceAction.Disable();

            subscriptions.Dispose();
        }

        public void RealUpdate()
        {
            // TODO EP: Reference this staticly
            // MapManager.renderVisualizations = Settings.showPointCloud;

            Settings.menuOpen =
                userRecord.settingsMenuOpen.Value == SettingsMenuState.OpenLeftPalm
                || userRecord.settingsMenuOpen.Value == SettingsMenuState.OpenRightPalm;
            Settings.menuPanelDimensions = userRecord.settingsMenuDimensions.Value;
            Settings.localize = App.State_Old.settingsLocalize.Value;
            Settings.showPointCloud = App.State_Old.settingsShowPointCloud.Value;
            Settings.animateNodeIndicators = App.State_Old.settingsAnimateNodeIndicators.Value;
            Settings.animateUserIndicators = App.State_Old.settingsAnimateUserIndicators.Value;
            //Settings.numThreads.Value = userRecord.settingsNumThreads.Value;
            // Settings.solverType = userRecord.settingsSolverType.Value;
            // Settings.compression.Value = userRecord.settingsCompression.Value;
            // Settings.localizationReducer = App.State.settingsLocalizationReducer.Value;
            Settings.thresholding = App.State_Old.settingsEnableLocalizationThreshold.Value;
            Settings.fallbackToMostRecent = true; //App.State_Old.settingsFallbackToMostRecent.Value;
            // Settings.lightingCondition = userRecord.settingsLightingCondition.Value;
            Settings.positionThreshold = App.State_Old.settingsPositionThreshold.Value;
            Settings.rotationThreshold = App.State_Old.settingsRotationThreshold.Value;
            Settings.positionInlierThreshold = App.State_Old.settingsPositionInlierThreshold.Value;
            Settings.rotationInlierThreshold = App.State_Old.settingsRotationInlierThreshold.Value;
            Settings.discardBottomHalf = App.State_Old.settingsDiscardBottomHalf.Value;
            Settings.confidenceFactor = App.State_Old.settingsConfidenceFactor.Value;
            Settings.ransacHistorySize = App.State_Old.settingsRansacHistorySize.Value;
            Settings.favHistorySize = App.State_Old.settingsFavHistorySize.Value;
            Settings.favStandardDeviationsThreshold = App.State_Old.settingsFavThreshold.Value;
            Settings.useFloorPlaneDetection = App.State_Old.settingsUseFloorPlaneDetection.Value;

            transform.position = Camera.main.transform.position;
            transform.rotation = Camera.main.transform.rotation;

            if (spaceAction.triggered)
            {
                ChangeSettingsMenuState(
                    SettingsOpen() ? SettingsMenuState.ClosedLeftPalm : SettingsMenuState.OpenLeftPalm
                );
            }
        }

        public static void ChangeSettingsMenuState(SettingsMenuState settingsMenuState)
        {
            if (App.ClientID == null)
                return;

            var userRecord = App.State_Old.users.Get(App.ClientID.Value);

            if (
                settingsMenuState == SettingsMenuState.ClosedLeftPalm
                || settingsMenuState == SettingsMenuState.ClosedRightPalm
            )
            {
                userRecord.settingsMenuOpen.EnqueueSet(settingsMenuState);
                return;
            }

            var settingsPanelPosition =
                Camera.main.transform.position + (Camera.main.transform.forward * settingsPanelSpawnDistance);
            var settingsPanelRotation =
                Quaternion.LookRotation(Camera.main.transform.forward.Flatten(), Vector3.up)
                * Quaternion.Euler(settingsPanelSpawnTilt, 0, 0);

            var geoPose = VisualPositioningSystem.UnityWorldToEcef(settingsPanelPosition, settingsPanelRotation);

            userRecord.settingsMenuGeoPose.ecefPosition.EnqueueSet(geoPose.position.ToDouble3());
            userRecord.settingsMenuGeoPose.ecefRotation.EnqueueSet(geoPose.rotation);

            userRecord.settingsMenuDimensions.EnqueueSet(new Vector2 { x = 0.6f, y = 0.4f });

            userRecord.settingsMenuOpen.EnqueueSet(settingsMenuState);
        }

        public static bool SettingsOpen()
        {
            if (App.ClientID == null)
                return false;

            var userRecord = App.State_Old.users.Get(App.ClientID.Value);
            return userRecord.settingsMenuOpen.Value == SettingsMenuState.OpenLeftPalm
                || userRecord.settingsMenuOpen.Value == SettingsMenuState.OpenRightPalm;
        }
    }
}
