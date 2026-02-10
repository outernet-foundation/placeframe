using System.IO;
using UnityEngine;
using SimpleJSON;
using FofX.Stateful;

namespace Plerion.MakeItSing
{
    public class SettingsManager : MonoBehaviour
    {
        private string settingsPath => $"{Application.persistentDataPath}/settings.json";

        private void Awake()
        {
            Debug.Log(settingsPath);

            if (!File.Exists(settingsPath))
            {
                App.state.userSettings.ExecuteAction(x =>
                {
                    x.domain.value = null;
                    x.username.value = "user";
                    x.password.value = "password";
                });
            }
            else
            {
                App.state.userSettings.ExecuteAction(
                    JSONNode.Parse(File.ReadAllText(settingsPath)),
                    (json, settings) => settings.FromJSON(json)
                );
            }

            App.RegisterObserver(HandleSettingsChanged, App.state.userSettings);
        }

        private void HandleSettingsChanged(NodeChangeEventArgs args)
        {
            if (args.initialize)
                return;

            File.WriteAllText(settingsPath, App.state.userSettings.ToJSON(_ => true).ToString());
        }
    }
}