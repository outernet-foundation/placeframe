using System;
using System.Linq;
using Cysharp.Threading.Tasks;
using FofX;
using FofX.Stateful;
using ObserveThing;
using Outernet.Logging;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class App : AppBase<AppState>
    {
        public static bool AppInitialized { get; private set; }

        private InRoomManager _inRoomManager;
        private IDisposable _subscriptions;

        protected override void Awake()
        {
            base.Awake();
            AppInitialized = true;

            _subscriptions = new ComposedDisposable(
                Observables.ObservableCombineValues(
                    App.state.inRoom,
                    App.state.offlineMode,
                    (inRoom, offlineMode) => inRoom && offlineMode
                ).Subscribe(setupRoomInOfflineMode =>
                {
                    if (setupRoomInOfflineMode)
                    {
                        App.ExecuteTransaction(state =>
                        {
                            state.masterClientID.value = 1;
                            state.playerID.value = 1;
                        });
                    }
                }),
                StateObservables.SubscribeOperations( // Do this here because PhotonConnectionManager doesn't exist if we're in offline mode
                    onOperation: ops =>
                    {
                        if (App.state.inRoomAndSynchronized.value && !App.state.scene.players.ContainsKey(App.state.playerID.value))
                            App.ExecuteTransaction(new AddLocalPlayerDataAction());
                    },
                    App.state.inRoomAndSynchronized,
                    App.state.scene.players
                ),
                App.state.inRoom.Subscribe(
                    onNext: inRoom =>
                    {
                        if (inRoom)
                        {
                            _inRoomManager = gameObject.AddComponent<InRoomManager>();
                        }
                        else if (_inRoomManager != null)
                        {
                            Destroy(_inRoomManager);
                            _inRoomManager = null;
                        }
                    }
                ),
                Observables.ObservableCombineValues(
                    App.state.loginStatus,
                    App.state.offlineMode,
                    (status, offlineMode) => status == LoginStatus.LoginRequested && !offlineMode
                ).Subscribe(shouldLogIn =>
                {
                    if (shouldLogIn)
                        Tasks.Login().Forget();
                }),
                App.state.config.logGroups.Subscribe(x => Log<LogGroup>.enabledLogGroups = x),
                App.state.config.logLevel.Subscribe(x => Log<LogGroup>.logLevel = x),
                App.state.config.stackTraceLevel.Subscribe(x => Log<LogGroup>.stackTraceLevel = x)
            );
        }

        private void OnDestroy()
        {
            AppInitialized = false;
            _subscriptions.Dispose();
        }

        protected override void InitializeState(AppState state)
        {
            state.Initialize(Settings.DefaultObservationContext, new GroupLogger() { group = LogGroup.Stateful }, "root");
        }

        public class GroupLogger : FofX.ILogger
        {
            public LogGroup group;

            private Outernet.Logging.LogLevel ToOuternetLogLevel(FofX.LogLevel logLevel)
            {
                switch (logLevel)
                {
                    case FofX.LogLevel.Trace:
                        return Outernet.Logging.LogLevel.Trace;
                    case FofX.LogLevel.Debug:
                        return Outernet.Logging.LogLevel.Debug;
                    case FofX.LogLevel.Info:
                        return Outernet.Logging.LogLevel.Info;
                    case FofX.LogLevel.Warn:
                        return Outernet.Logging.LogLevel.Warn;
                    case FofX.LogLevel.Error:
                        return Outernet.Logging.LogLevel.Error;
                    case FofX.LogLevel.Fatal:
                        return Outernet.Logging.LogLevel.Fatal;
                    case FofX.LogLevel.None:
                        return Outernet.Logging.LogLevel.None;
                    default:
                        throw new Exception($"Unhandled log level {logLevel}");
                }
            }

            public bool LevelEnabled(FofX.LogLevel logLevel)
                => Log<LogGroup>.LogEnabled(ToOuternetLogLevel(logLevel), group);

            public void Generic(FofX.LogLevel logLevel, string message, Exception exception)
            {
                switch (logLevel)
                {
                    case FofX.LogLevel.Trace:
                        Trace(message);
                        break;
                    case FofX.LogLevel.Debug:
                        Debug(message);
                        break;
                    case FofX.LogLevel.Info:
                        Info(message);
                        break;
                    case FofX.LogLevel.Warn:
                        Warning(message);
                        break;
                    case FofX.LogLevel.Error:
                        Error(message, exception);
                        break;
                    case FofX.LogLevel.Fatal:
                        Fatal(message);
                        break;
                }
            }

            public void Debug(string message)
                => Log<LogGroup>.Debug(group, message);

            public void Error(string message)
                => Log<LogGroup>.Error(group, message);

            public void Error(Exception exception)
                => Log<LogGroup>.Error(group, exception);

            public void Error(string message, Exception exception)
                => Log<LogGroup>.Error(group, message, exception);

            public void Fatal(string message)
                => Log<LogGroup>.Fatal(group, message);

            public void Info(string message)
                => Log<LogGroup>.Info(group, message);

            public void Trace(string message)
                => Log<LogGroup>.Trace(group, message);

            public void Warning(string message)
                => Log<LogGroup>.Warn(group, message);
        }
    }
}