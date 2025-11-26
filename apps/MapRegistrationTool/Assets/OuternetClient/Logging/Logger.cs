using System;
using System.Linq;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using R3;
using Serilog;
using UnityEngine;

namespace Outernet.MapRegistrationTool
{
    static class Logger
    {
        public static Serilog.Core.Logger logger { get; private set; }
        public static ILogHandler defaultUnityLogHandler;

        private static string _deviceName;
        public static string DeviceName => _deviceName;

        private static IDisposable subscriptions;

        public static void Initialize()
        {
            _deviceName = SystemInfo.deviceName;

            logger = new LoggerConfiguration()
                .MinimumLevel.Verbose()
                .Enrich.With<Enricher>()
#if UNITY_EDITOR
                .WriteTo.Unity()
#endif
                .WriteTo.Loki()
                .CreateLogger();

            // Use a custom Unity log handler to pipe to Serilog any messages that are logged
            // directly using Unity's Debug class, such as by third-party code we don't control, or
            // by Unity itself when exceptions are thrown by Unity lifecycle methods
            defaultUnityLogHandler = Debug.unityLogger.logHandler;
            Debug.unityLogger.logHandler = new SerilogLogHandler();

            // If serilog itself throws an exception, log it using Unity's default log handler
            global::Serilog.Debugging.SelfLog.Enable(
                error =>
                {
                    defaultUnityLogHandler.LogFormat(LogType.Error, null, error);
                });

            // Disable Unity's stack trace generation, since we generate our own stack traces
            Application.SetStackTraceLogType(LogType.Log, StackTraceLogType.None);
            Application.SetStackTraceLogType(LogType.Warning, StackTraceLogType.None);
            // Application.SetStackTraceLogType(LogType.Error, StackTraceLogType.None);
            // Application.SetStackTraceLogType(LogType.Exception, StackTraceLogType.None);
            Application.SetStackTraceLogType(LogType.Assert, StackTraceLogType.None);

            subscriptions = Disposable.Combine(
                // Log logs that bypass Debug.unityLogger.logHandler
                Observable
                    .FromEvent<Application.LogCallback, (string condition, string stackTrace, LogType type)>(
                        handler => (condition, stackTrace, type) => handler((condition, stackTrace, type)),
                        handler => Application.logMessageReceived += handler,
                        handler => Application.logMessageReceived -= handler)
                    .Subscribe(tuple => UnityLogMessageReceived(tuple.condition, tuple.stackTrace, tuple.type)),

                // Log uncaught exceptions thrown by UniTasks
                Observable
                    .FromEvent<Exception>(
                        handler => UniTaskScheduler.UnobservedTaskException += handler,
                        handler => UniTaskScheduler.UnobservedTaskException -= handler)
                    .Subscribe(exception => Log.Error(LogGroup.UncaughtException, exception, "UniTaskScheduler UnobservedTaskException")),

                // Log uncaught exceptions thrown by Tasks
                Observable
                    .FromEventHandler<UnobservedTaskExceptionEventArgs>(
                        handler => TaskScheduler.UnobservedTaskException += handler,
                        handler => TaskScheduler.UnobservedTaskException -= handler)
                    .Subscribe(args => Log.Error(LogGroup.UncaughtException, args.e.Exception, "TaskScheduler UnobservedTaskException: sender {0}", args.sender))
            );

            // Log uncaught exceptions thrown by R3 subscriptions
            ObservableSystem.RegisterUnhandledExceptionHandler(exception => Log.Error(LogGroup.UncaughtException, exception, "R3 subscription unhandled exception"));
        }

        public static void Terminate()
        {
            subscriptions.Dispose();
            logger.Dispose();
        }

        public static void Serilog(LogLevel level, LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            messageTemplate ??= string.Empty;

            if (messageTemplate == string.Empty && exception != null)
            {
                messageTemplate = exception.Message;
            }

            var loggerWithContext = logger.ForContext("logGroup", group.ToString());

            switch (level)
            {
                case LogLevel.Trace:
                    loggerWithContext.Verbose(exception, messageTemplate, propertyValues);
                    break;
                case LogLevel.Debug:
                    loggerWithContext.Debug(exception, messageTemplate, propertyValues);
                    break;
                case LogLevel.Info:
                    loggerWithContext.Information(exception, messageTemplate, propertyValues);
                    break;
                case LogLevel.Warn:
                    loggerWithContext.Warning(exception, messageTemplate, propertyValues);
                    break;
                case LogLevel.Error:
                    loggerWithContext.Error(exception, messageTemplate, propertyValues);
                    break;
                case LogLevel.Fatal:
                    loggerWithContext.Fatal(exception, messageTemplate, propertyValues);
                    break;
            }
        }

        [InnerFramesHiddenFromStackTrace]
        static void UnityLogMessageReceived(string condition, string _, LogType type)
        {
#if UNITY_EDITOR
            // In player builds, because we use a custom log handler and don't forward logs to Unity's default log handler,
            // this callback will only ever be called when native code logs a message (example: assigning a Vector3 containing NaNs 
            // to a transform's position logs an error from native code, completely bypassing the managed log handler).

            // In the editor, we do forward logs back to Unity's default log handler so that we can see them in the editor console, 
            // so we need to check whether that is where this log message came from, and only if it isn't do we know it came from 
            // native code and should be forwarded to our logging system.

            // This does mean that logs from native code will result duplicate messages in the editor console, but I see no way to 
            // avoid that without suffering other, worse drawbacks.

            if (new System.Diagnostics.StackTrace(false)
                .GetFrames()
                .Any(frame =>
                    frame.GetMethod().DeclaringType == typeof(Log) &&
                    frame.GetMethod().Name == "LogBase"))
            {
                return;
            }
#endif

            switch (type)
            {
                case LogType.Assert:
                    Log.Fatal(condition);
                    break;
                case LogType.Error:
                    Log.Error(condition);
                    break;
                // Treat all native logs as possible bugs, since they might be (example: calling Quaternion.LookRotation with 
                // Vector3.zero is almost certainly a mistake, but results in native code logging a message of type LogType.Log)
                case LogType.Warning:
                case LogType.Log:
                    Log.Warn(condition);
                    break;
            }
        }

        class SerilogLogHandler : ILogHandler
        {
            [InnerFramesHiddenFromStackTrace]
            public void LogFormat(LogType logType, UnityEngine.Object context, string format, params object[] args)
            {
                string message = string.Format(format, args);

                if ((logType == LogType.Exception || logType == LogType.Error) &&
                    (message.Contains("Error: MLCamera.InternalGetFramePose failed to get camera frame pose. Reason: MLResult_PoseNotFound") ||
                    message.Contains("Error: MLCVCameraGetFramePose in the Magic Leap API failed. Reason: MLResult_PoseNotFound") ||
                    message.Contains("Error: XrBeginPlaneDetection in the Magic Leap API failed. Reason: SpaceNotLocatableEXT")))
                {
                    logType = LogType.Log;
                }

                switch (logType)
                {
                    case LogType.Assert:
                        Log.Fatal(message);
                        break;
                    case LogType.Error:
                        Log.Error(message);
                        break;
                    case LogType.Warning:
                        Log.Warn(message);
                        break;
                    case LogType.Log:
                        Log.Info(message);
                        break;
                }
            }

            [InnerFramesHiddenFromStackTrace]
            public void LogException(Exception exception, UnityEngine.Object context)
            {
                Log.Error(LogGroup.UncaughtException, exception, "Unity exception");
            }
        }
    }
}