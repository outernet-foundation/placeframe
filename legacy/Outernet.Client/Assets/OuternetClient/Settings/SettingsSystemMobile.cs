using System;
using R3;
using UnityEngine;
using UnityEngine.UI;

namespace Outernet.Client
{
    public class SettingsSystemMobile : MonoBehaviour
    {
        public Toggle settingsMenuToggle;
        private Stub settingsMenu;
        private IDisposable subscriptions;

        void Start()
        {
            subscriptions = settingsMenuToggle.onValueChanged.AsObservable().Subscribe(value =>
            {
                if (!value)
                {
                    settingsMenu.GetComponentInChildren<SettingsMenu>().Terminate();
                    PrefabSystem.Destroy(settingsMenu);
                }

                if (value)
                {
                    settingsMenu = PrefabSystem.Create(PrefabSystem.systemUIViewMobile);
                    settingsMenu.transform.SetParent(transform, false);
                    settingsMenu.GetComponentInChildren<SettingsMenu>().Initialize();
                }
            });
        }

        void OnDestroy()
        {
            subscriptions.Dispose();
        }

        void Update()
        {
            if (GetComponentInChildren<SettingsMenu>() == null) return;

            GetComponentInChildren<SettingsMenu>().RealUpdate();
        }
    }
}
