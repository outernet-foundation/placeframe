using System;
using FofX.Stateful;
using SimpleJSON;

namespace Placeframe.MapRegistrationTool
{
    public static class SettingsUpgrader
    {
        public delegate JSONNode UpgradeDelegate(JSONNode settings);

        public static int CurrentSettingsVersion => _upgraders.Length;

        private static UpgradeDelegate[] _upgraders = new UpgradeDelegate[0];

        public static JSONNode UpgradeIfNecessary(JSONNode settings)
        {
            var version = settings["version"].AsInt;
            var data = settings["data"];

            for (int i = version; i < _upgraders.Length; i++)
                data = _upgraders[i].Invoke(data);

            settings["version"] = _upgraders.Length;
            settings["data"] = data;

            return settings;
        }

        public static JSONNode FormatSettings(UserSettings settings)
        {
            JSONObject json = new JSONObject();

            json["version"] = 1;
            json["settings"] = settings.ToJSON(x =>
                !x.isDefault &&
                !x.isDerived &&
                x != App.state.settings.loaded
            );

            return json;
        }
    }
}