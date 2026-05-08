using UnityEngine;
using ObserveThing;
using System;

namespace Plerion.MakeItSing
{
    public class NotificationManager : MonoBehaviour
    {
        private bool _init;
        private IDisposable _subscriptions;

        private void Awake()
        {
            _subscriptions = new ComposedDisposable(

                App.state.nameServerConnection.status.Subscribe(
                    onNext: x =>
                    {
                        if (!_init)
                            return;

                        App.ExecuteTransaction(state =>
                        {
                            var notification = state.notifications.Add();
                            notification.message.value = GetConnectionMessage("server", x, state.nameServerConnection.error.value);
                            notification.generatedTime.value = Time.time;
                            notification.displayDuration.value = 5f;

                            if (x == ConnectionStatus.Error)
                            {
                                notification.logLevel.value = Outernet.Logging.LogLevel.Error;
                            }
                            else if (x == ConnectionStatus.Connected || x == ConnectionStatus.Disconnected)
                            {
                                notification.logLevel.value = Outernet.Logging.LogLevel.Info;
                            }
                            else
                            {
                                notification.logLevel.value = Outernet.Logging.LogLevel.Debug;
                            }
                        });
                    }
                ),

                App.state.roomConnection.status.Subscribe(
                    onNext: x =>
                    {
                        if (!_init)
                            return;

                        App.ExecuteTransaction(state =>
                        {
                            var notification = state.notifications.Add();
                            notification.message.value = GetConnectionMessage("room", x, state.roomConnection.error.value);
                            notification.generatedTime.value = Time.time;
                            notification.displayDuration.value = 5f;

                            if (x == ConnectionStatus.Error)
                            {
                                notification.logLevel.value = Outernet.Logging.LogLevel.Error;
                            }
                            else if (x == ConnectionStatus.Connected || x == ConnectionStatus.Disconnected)
                            {
                                notification.logLevel.value = Outernet.Logging.LogLevel.Info;
                            }
                            else
                            {
                                notification.logLevel.value = Outernet.Logging.LogLevel.Debug;
                            }
                        });
                    }
                )

            );

            _init = true;
        }

        private void OnDestroy()
        {
            _subscriptions.Dispose();
        }

        private string GetConnectionMessage(string connectionName, ConnectionStatus status, string error)
        {
            switch (status)
            {
                case ConnectionStatus.Connected:
                    return $"Connected to {connectionName}";

                case ConnectionStatus.Connecting:
                    return $"Connecting to {connectionName}";

                case ConnectionStatus.Disconnected:
                    return $"Disconnected from {connectionName}";

                case ConnectionStatus.Disconnecting:
                    return $"Disconnecting from {connectionName}";

                case ConnectionStatus.Error:
                    return $"Connection to {connectionName} encountered an error: {error}";

                default:
                    throw new System.Exception($"Unhandled connection status {status}");
            }
        }

        private void LateUpdate()
        {
            for (int i = 0; i < App.state.notifications.Count; i++)
            {
                var notification = App.state.notifications[i];

                if (notification.displayDuration.value == -1)
                    continue;

                if (Time.time - notification.generatedTime.value >= notification.displayDuration.value)
                {
                    App.state.notifications.RemoveAt(i);
                    i--;
                }
            }
        }
    }
}