using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using R3;
using Serilog;
using UnityEngine;

namespace Outernet.Logging
{
    public static class Logger<TLogGroup> where TLogGroup : struct, Enum
    {
        public static Serilog.Core.Logger logger { get; private set; }
        public static ILogHandler defaultUnityLogHandler;
        [ThreadStatic] internal static bool emittingToUnity;

        private static string _deviceName;
        public static string DeviceName => _deviceName;

        private static IDisposable subscriptions;
        private static IReadOnlyList<string> benignErrorSubstrings = Array.Empty<string>();

        public static void Initialize(IEnumerable<string> suppressErrors = null)
        {
            benignErrorSubstrings = suppressErrors != null ? new List<string>(suppressErrors) : Array.Empty<string>();
            _deviceName = SystemInfo.deviceName;

            logger = new LoggerConfiguration()
                .MinimumLevel.Verbose()
                .Enrich.With<Enricher<TLogGroup>>()
                .WriteTo.Unity<TLogGroup>()
                .CreateLogger();

            defaultUnityLogHandler = Debug.unityLogger.logHandler;
            Debug.unityLogger.logHandler = new SerilogLogHandler();

            global::Serilog.Debugging.SelfLog.Enable(
                error =>
                {
                    defaultUnityLogHandler.LogFormat(LogType.Error, null, error);
                });

            Application.SetStackTraceLogType(LogType.Log, StackTraceLogType.None);
            Application.SetStackTraceLogType(LogType.Warning, StackTraceLogType.None);
            Application.SetStackTraceLogType(LogType.Error, StackTraceLogType.None);
            Application.SetStackTraceLogType(LogType.Exception, StackTraceLogType.None);
            Application.SetStackTraceLogType(LogType.Assert, StackTraceLogType.None);

            subscriptions = Disposable.Combine(
                Observable
                    .FromEvent<Application.LogCallback, (string condition, string stackTrace, LogType type)>(
                        handler => (condition, stackTrace, type) => handler((condition, stackTrace, type)),
                        handler => Application.logMessageReceived += handler,
                        handler => Application.logMessageReceived -= handler)
                    .Subscribe(tuple => UnityLogMessageReceived(tuple.condition, tuple.stackTrace, tuple.type)),

                Observable
                    .FromEvent<Exception>(
                        handler => UniTaskScheduler.UnobservedTaskException += handler,
                        handler => UniTaskScheduler.UnobservedTaskException -= handler)
                    .Subscribe(exception => Log<TLogGroup>.Error(exception, "UniTaskScheduler UnobservedTaskException")),

                Observable
                    .FromEventHandler<UnobservedTaskExceptionEventArgs>(
                        handler => TaskScheduler.UnobservedTaskException += handler,
                        handler => TaskScheduler.UnobservedTaskException -= handler)
                    .Subscribe(args => Log<TLogGroup>.Error(args.e.Exception, "TaskScheduler UnobservedTaskException: sender {0}", args.sender))
            );

            ObservableSystem.RegisterUnhandledExceptionHandler(exception => Log<TLogGroup>.Error(exception, "R3 subscription unhandled exception"));
        }

        public static void EnableLoki(string domain, Func<UniTask<string>> tokenProvider, IEnumerable<(string key, string value)> labels)
        {
            var previous = logger;
            logger = new LoggerConfiguration()
                .MinimumLevel.Verbose()
                .Enrich.With<Enricher<TLogGroup>>()
                .WriteTo.Unity<TLogGroup>()
                .WriteTo.Loki(domain, tokenProvider, labels)
                .CreateLogger();
            previous.Dispose();
        }

        public static void Terminate()
        {
            subscriptions.Dispose();
            logger.Dispose();
        }

        public static void Serilog(LogLevel level, TLogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
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

        static LogType SuppressBenignErrors(LogType type, string message)
        {
            if ((type == LogType.Exception || type == LogType.Error) && benignErrorSubstrings.Count > 0)
            {
                for (int i = 0; i < benignErrorSubstrings.Count; i++)
                {
                    if (message.Contains(benignErrorSubstrings[i]))
                        return LogType.Log;
                }
            }
            return type;
        }

        [InnerFramesHiddenFromStackTrace]
        static void UnityLogMessageReceived(string condition, string _, LogType type)
        {
            if (emittingToUnity) return;

            type = SuppressBenignErrors(type, condition);

            switch (type)
            {
                case LogType.Assert:
                    Log<TLogGroup>.Fatal(condition);
                    break;
                case LogType.Error:
                    Log<TLogGroup>.Error(condition);
                    break;
                case LogType.Warning:
                case LogType.Log:
                    Log<TLogGroup>.Warn(condition);
                    break;
            }
        }

        class SerilogLogHandler : ILogHandler
        {
            [InnerFramesHiddenFromStackTrace]
            public void LogFormat(LogType logType, UnityEngine.Object context, string format, params object[] args)
            {
                string message = string.Format(format, args);
                logType = SuppressBenignErrors(logType, message);

                switch (logType)
                {
                    case LogType.Assert:
                        Log<TLogGroup>.Fatal(message);
                        break;
                    case LogType.Error:
                        Log<TLogGroup>.Error(message);
                        break;
                    case LogType.Warning:
                        Log<TLogGroup>.Warn(message);
                        break;
                    case LogType.Log:
                        Log<TLogGroup>.Info(message);
                        break;
                }
            }

            [InnerFramesHiddenFromStackTrace]
            public void LogException(Exception exception, UnityEngine.Object context)
            {
                Log<TLogGroup>.Error(exception, "Unity exception");
            }
        }
    }
}
