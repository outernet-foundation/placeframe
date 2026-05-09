using System;
using System.IO;
using FofX.Stateful;
using SimpleJSON;
using UnityEngine;

namespace Placeframe.Client
{
    public static class SettingsManager
    {
        private static bool _initializing;
        private static IDisposable _subscription;
        private static string settingsPath => $"{Application.persistentDataPath}/settings.json";

        public static void Initialize()
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

            _subscription = App.state.settings.SubscribeOperationsRecursive(_ =>
            {
                if (_initializing)
                    return;

                File.WriteAllText(settingsPath, App.state.settings.ToJSON(_ => true).ToString());
            });

            _initializing = false;
        }

        public static void Shutdown()
        {
            _subscription?.Dispose();
            _subscription = null;
        }
    }
}
