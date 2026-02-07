using System;
using System.IO;
using FofX.Stateful;
using SimpleJSON;
using UnityEngine;

namespace Placeframe.Client
{
    public class SettingsManager : MonoBehaviour
    {
        private string settingsPath => $"{Application.persistentDataPath}/settings.json";

        private void Awake()
        {
            Debug.Log(settingsPath);

            if (!File.Exists(settingsPath))
            {
                App.state.settings.ExecuteAction(x =>
                {
                    x.domain.value = null;
                    x.username.value = "user";
                    x.password.value = "password";
                });
            }
            else
            {
                App.state.settings.ExecuteAction(
                    JSONNode.Parse(File.ReadAllText(settingsPath)),
                    (json, settings) => settings.FromJSON(json)
                );
            }

            App.RegisterObserver(HandleSettingsChanged, App.state.settings);
        }

        private void HandleSettingsChanged(NodeChangeEventArgs args)
        {
            if (args.initialize)
                return;

            File.WriteAllText(settingsPath, App.state.settings.ToJSON(_ => true).ToString());
        }
    }
}