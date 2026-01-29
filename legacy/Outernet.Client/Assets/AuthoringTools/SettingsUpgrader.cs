using System;
using FofX.Stateful;
using SimpleJSON;

namespace Outernet.Client.AuthoringTools
{
    public static class SettingsUpgrader
    {
        public delegate JSONNode UpgradeDelegate(JSONNode settings);

        public static int CurrentSettingsVersion => _upgraders.Length;

        private static UpgradeDelegate[] _upgraders = new UpgradeDelegate[]
        {
            ToVersion1
        };

        public static JSONNode UpgradeIfNecessary(JSONNode settings)
        {
            if (!settings.HasKey("version"))
            {
                var oldSettings = settings;
                settings = new JSONObject();
                settings["version"] = 0;
                settings["data"] = oldSettings;
            }

            var version = settings["version"].AsInt;
            var data = settings["data"];

            for (int i = version; i < _upgraders.Length; i++)
                data = _upgraders[i].Invoke(data);

            settings["version"] = _upgraders.Length;
            settings["data"] = data;

            return settings;
        }

        private static JSONNode ToVersion1(JSONNode data)
        {
            JSONObject newData = new JSONObject();
            JSONArray visibleLayers = new JSONArray();
            visibleLayers[0] = Guid.Empty.ToString();
            newData["authoringToolsSettings"] = data;
            newData["visibleLayers"] = visibleLayers;
            return newData;
        }

        public static JSONNode FormatSettings(UserSettings authoringToolsSettings, ObservableSet<Guid> visibleLayers)
        {
            JSONObject settings = new JSONObject();
            JSONObject data = new JSONObject();
            settings["version"] = 1;
            settings["data"] = data;

            data["authoringToolsSettings"] = authoringToolsSettings.ToJSON(x =>
                !x.isDefault &&
                !x.isDerived &&
                x != App.state.authoringTools.settings.loaded
            );

            data["visibleLayers"] = visibleLayers.ToJSON(x => true);

            return settings;
        }
    }
}