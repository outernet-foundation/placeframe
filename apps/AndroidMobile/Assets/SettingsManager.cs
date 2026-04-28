using System;
using System.Collections.Generic;
using System.IO;
using FofX.Stateful;
using SimpleJSON;
using UnityEngine;

namespace Placeframe.Client
{
    public class SettingsManager : MonoBehaviour
    {
        private bool _initializing;
        private string settingsPath => $"{Application.persistentDataPath}/settings.json";

        private void Awake()
        {
            Debug.Log(settingsPath);

            if (!File.Exists(settingsPath))
            {
                App.ExecuteTransaction(appState =>
                {
                    var x = appState.settings;
                    x.domain.value = null;
                    x.username.value = "user";
                    x.password.value = "password";
                });
            }
            else
            {
                App.ExecuteTransaction(appState =>
                {
                    var json = JSONNode.Parse(File.ReadAllText(settingsPath));
                    appState.settings.FromJSON(json);
                });
            }

            _initializing = true;

            App.state.settings.SubscribeOperationsRecursive(_ =>
            {
                if (_initializing)
                    return;

                File.WriteAllText(settingsPath, App.state.settings.ToJSON(_ => true).ToString());
            });

            _initializing = false;
        }
    }
}