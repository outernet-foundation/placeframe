using System;
using Cysharp.Threading.Tasks;
using FofX;
using ObserveThing;
using Outernet.Logging;
using Placeframe.Core;

namespace Plerion.MakeItSing
{
    public class App : AppBase<AppState>
    {
        public static bool AppInitialized { get; private set; }

        private InRoomManager _inRoomManager;
        private IDisposable _subscription;

        protected override void Awake()
        {
            base.Awake();
            AppInitialized = true;

            _subscription = new ComposedDisposable(
                App.state.loggedIn
                    .ObservableSkipWhile(() => !App.state.loggedIn.value)
                    .Subscribe(
                        onNext: loggedIn =>
                        {
                            if (loggedIn)
                            {
                                VisualPositioningSystem.StartLocalizing(1f);
                            }
                            else
                            {
                                VisualPositioningSystem.StopLocalizing();
                            }
                        }
                    ),
                App.state.roomConnection.connected.Subscribe(
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
                App.state.loginStatus.Subscribe(
                    onNext: status =>
                    {
                        if (status == LoginStatus.LoginRequested)
                            Tasks.Login().Forget();
                    }
                ),
                App.state.inRoomAndSynchronized.Subscribe(
                    onNext: inRoomAndSynchronized => App.state.systemUIOpen.value = !inRoomAndSynchronized
                ),
                App.state.config.logGroups.Subscribe(x => Log<LogGroup>.enabledLogGroups = x),
                App.state.config.logLevel.Subscribe(x => Log<LogGroup>.logLevel = x),
                App.state.config.stackTraceLevel.Subscribe(x => Log<LogGroup>.stackTraceLevel = x)
            );
        }

        private void OnDestroy()
        {
            AppInitialized = false;
            _subscription.Dispose();
        }

        protected override void InitializeState(AppState state)
        {
            state.Initialize(Settings.DefaultObservationContext, new GroupLogger() { group = LogGroup.Stateful }, "root");
        }

        public class GroupLogger : ILogger
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