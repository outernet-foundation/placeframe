using System.IO;
using FofX.Stateful;
using UnityEngine;
using SimpleJSON;

namespace Outernet.Client.AuthoringTools
{
    public class SettingsManager : MonoBehaviour
    {
        private static readonly string USER_SETTINGS = "settings.json";
        private static string USER_SETTINGS_PATH => $"{Application.persistentDataPath}/{USER_SETTINGS}";

        private void Awake()
        {
            App.RegisterObserver(HandleSettingsLoadedChanged, App.state.authoringTools.settings.loaded);
            App.RegisterObserver(HandleSettingsChanged, App.state.authoringTools.settings, App.state.settings.visibleLayers);
            App.RegisterObserver(HandleLocationChanged, App.state.authoringTools.location);

            if (File.Exists(USER_SETTINGS_PATH))
            {
                var settingsJSON = JSONNode.Parse(File.ReadAllText(USER_SETTINGS_PATH));
                settingsJSON = SettingsUpgrader.UpgradeIfNecessary(settingsJSON);

                App.ExecuteActionOrDelay(new LoadSettingsAction(settingsJSON["data"]));
            }
            else
            {
                App.ExecuteActionOrDelay(
                    new SetupDefaultSettingsAction()
                );
            }
        }

        private void HandleLocationChanged(NodeChangeEventArgs args)
        {
            if (!App.state.authoringTools.settings.loaded.value ||
                !App.state.authoringTools.location.value.HasValue)
            {
                return;
            }

            App.ExecuteActionOrDelay(
                new SetLastLocationAction(App.state.authoringTools.location.value)
            );
        }

        private void HandleSettingsLoadedChanged(NodeChangeEventArgs args)
        {
            if (App.state.authoringTools.settings.loaded.value &&
                App.state.authoringTools.settings.restoreLocationAutomatically.value)
            {
                App.ExecuteActionOrDelay(new SetLocationAction(App.state.authoringTools.settings.lastLocation.value));
            }
        }

        private void HandleSettingsChanged(NodeChangeEventArgs args)
        {
            if (!App.state.authoringTools.settings.loaded.value)
                return;

            File.WriteAllText(
                USER_SETTINGS_PATH,
                SettingsUpgrader.FormatSettings(
                    App.state.authoringTools.settings,
                    App.state.settings.visibleLayers
                ).ToString()
            );
        }
    }
}