using UnityEngine;
using R3;
using Outernet.Shared;
using System;

namespace Outernet.Client
{
    [RequireComponent(typeof(SyncedAnchor))]
    public class RemoteUser : MonoBehaviour
    {
        private Indicator indicator;
        private SettingsPanel settingsPanel;
        private UserRecord userRecord;
        private IDisposable subscriptions;

        public void Initialize(Guid id)
        {
            userRecord = App.State_Old.users.Get(id);

            GetComponent<SyncedAnchor>().Initialize(userRecord.geoPose);

            indicator = PrefabSystem.Create(PrefabSystem.indicatorView);
            indicator.transform.parent = transform;
            indicator.Initialize(true);

            subscriptions = userRecord.settingsMenuOpen
                .SkipWhile(open => open.Value == SettingsMenuState.ClosedLeftPalm)
                // For reasons I don't understand, this DelayFrame is required to prevent bugs if the local
                // client joins when this remote client already has the settings menu open.
                .DelayFrame(1)
                .Subscribe(open =>
                {
                    if (open.Value == SettingsMenuState.OpenLeftPalm ||
                        open.Value == SettingsMenuState.OpenRightPalm)
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
                });
        }

        public void Terminate()
        {
            indicator.Terminate();
            PrefabSystem.Destroy(indicator);

            if (settingsPanel != null)
            {
                settingsPanel.Close(true);
            }

            subscriptions.Dispose();
        }
    }
}