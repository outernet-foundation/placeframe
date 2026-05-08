using System.IO;
using UnityEngine;
using SimpleJSON;
using FofX.Stateful;
using System;
using System.Linq;
using ObserveThing;
using System.Collections.Generic;

namespace Plerion.MakeItSing
{
    public class SettingsManager : MonoBehaviour
    {
        private string settingsPath => $"{Application.persistentDataPath}/settings.json";
        private IDisposable _subscription;

        private void Awake()
        {
            if (!File.Exists(settingsPath))
            {
                App.ExecuteTransaction(x =>
                {
                    x.userSettings.domain.value = null;
                    x.userSettings.username.value = "user";
                    x.userSettings.password.value = "password";
                });
            }
            else
            {
                App.state.userSettings.FromJSON(JSONNode.Parse(File.ReadAllText(settingsPath)));
            }

            _subscription = new ComposedDisposable(
                App.state.userSettings.SubscribeOperationsRecursive(HandleSettingsChanged),
                App.state.inRoom.Subscribe(HandleInRoomChanged)
            );
        }

        private void OnDestroy()
        {
            _subscription.Dispose();
        }

        private void HandleInRoomChanged(bool inRoom)
        {
            if (!inRoom)
                return;

            var roomID = App.state.roomID.value;
            var now = DateTime.UtcNow;

            App.ExecuteTransaction(x => App.state.userSettings.recentRooms.GetOrAdd(roomID).value = now);
        }


        private void HandleSettingsChanged(IReadOnlyList<IStateOperation> ops)
        {
            File.WriteAllText(settingsPath, App.state.userSettings.ToJSON(_ => true).ToString());
        }
    }
}