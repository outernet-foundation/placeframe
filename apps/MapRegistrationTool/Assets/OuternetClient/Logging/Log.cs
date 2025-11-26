using System;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;

namespace Outernet.MapRegistrationTool
{
    public enum LogLevel
    {
        Trace,
        Debug,
        Info,
        Warn,
        Error,
        Fatal,
        None,
    }

    [Flags]
    public enum LogGroup
    {
        None = 0,
        Default = 1 << 0,
        UncaughtException = 1 << 1,
        LoggingTests = 1 << 2,
        Grpc = 1 << 3,
        SyncedStateClient = 1 << 4,
        MagicLeapCamera = 1 << 5,
        Immersal = 1 << 6,
        Rest = 1 << 7,
        Localizer = 1 << 8,
        PlaneDetector = 1 << 9,
        Permissions = 1 << 10,
        BugReports = 1 << 11,
        ContentManagement = 1 << 12,
        Stateful = 1 << 13
    }

    public static class Log
    {
        public static readonly Dictionary<string, string> ColorPalette = new Dictionary<string, string>
        {
            { "Default", "#4E79A7" }, // Blue
            { "UncaughtException", "#E15759" }, // Red
            { "LoggingTests", "#59A14F" }, // Green
            { "Grpc", "#F28E2B" }, // Orange
            { "SyncedStateClient", "#B07AA1" }, // Purple
            // { "MagicLeapCamera", "" }, This can't show up in editor logs, so no reason to use up a color for it
            { "Immersal", "#9C755F" }, // Brown
            { "Rest", "#76B7B2" }, // Cyan
            { "Localizer", "#EDC948" }, // Yellow
            // { "PlaneDetector", "" }, This can't show up in editor logs, so no reason to use up a color for it
            { "Permissions", "#FF9DA7" }, // Pink
        };

        public static LogLevel logLevel = LogLevel.None;
        public static LogLevel stackTraceLevel = LogLevel.None;
        public static LogGroup enabledLogGroups = LogGroup.None;

        // Overridable action to show a toast message; unit tests can override this to mock behavior
        internal static Action<LogLevel, LogGroup, Exception, string, object[]> LogHandler
            = (level, group, exception, template, values) => Logger.Serilog(level, group, exception, template, values);

        private static void LogBase(LogLevel level, LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            if (level < logLevel || (group & enabledLogGroups) == 0) return;

            LogHandler(level, group, exception, messageTemplate, propertyValues);
        }

        public static void DoLog(LogLevel level, LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(level, group, exception, messageTemplate, propertyValues);
        }

        public static void DoLog(LogLevel level, LogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(level, group, null, messageTemplate, propertyValues);
        }

        public static void DoLog(LogLevel level, string messageTemplate, params object[] propertyValues)
        {
            LogBase(level, LogGroup.Default, null, messageTemplate, propertyValues);
        }

        public static void DoLog(LogLevel level, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(level, LogGroup.Default, exception, messageTemplate, propertyValues);
        }

        public static void DoLog(LogLevel level, LogGroup group, Exception exception)
        {
            if (level < logLevel || (group & enabledLogGroups) == 0) return;

            LogBase(level, group, exception, null, null);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Trace(LogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Trace, group, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Trace(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Trace, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Trace(string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Trace, LogGroup.Default, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Trace(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Trace, LogGroup.Default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Debug(LogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Debug, group, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Debug(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Debug, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Debug(string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Debug, LogGroup.Default, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Debug(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Debug, LogGroup.Default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Info(LogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Info, group, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Info(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Info, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Info(string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Info, LogGroup.Default, null, messageTemplate, propertyValues);
        }


        [InnerFramesHiddenFromStackTrace]
        public static void Info(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Info, LogGroup.Default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(LogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Warn, group, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Warn, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(LogGroup group, string messageTemplate, Exception exception, params object[] propertyValues)
        {
            LogBase(LogLevel.Warn, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Warn, LogGroup.Default, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Warn, LogGroup.Default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(string messageTemplate, Exception exception, params object[] propertyValues)
        {
            LogBase(LogLevel.Warn, LogGroup.Default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(LogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, group, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(LogGroup group, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, group, null, null, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(LogGroup group, string messageTemplate, Exception exception, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, LogGroup.Default, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, LogGroup.Default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(string messageTemplate, Exception exception, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, LogGroup.Default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Fatal(LogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Fatal, group, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Fatal(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Fatal, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Fatal(string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Fatal, LogGroup.Default, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Fatal(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Fatal, LogGroup.Default, exception, messageTemplate, propertyValues);
        }

        public class LoggerFactory : ILoggerFactory
        {
            public class Logger : ILogger
            {
                private LogGroup logGroup;

                public Logger(LogGroup logGroup) => this.logGroup = logGroup;

                public IDisposable BeginScope<TState>(TState state) => null;

                public bool IsEnabled(Microsoft.Extensions.Logging.LogLevel logLevel) =>
                    MapLogLevel(logLevel) >= MapRegistrationTool.Log.logLevel && (logGroup & enabledLogGroups) != 0;

                public void Log<TState>(
                    Microsoft.Extensions.Logging.LogLevel logLevel,
                    EventId eventId,
                    TState state,
                    Exception exception,
                    Func<TState, Exception, string> formatter)
                {
                    LogBase(MapLogLevel(logLevel), logGroup, exception, formatter(state, exception));
                }

                private static LogLevel MapLogLevel(Microsoft.Extensions.Logging.LogLevel logLevel)
                {
                    switch (logLevel)
                    {
                        case Microsoft.Extensions.Logging.LogLevel.Trace:
                            return LogLevel.Trace;
                        case Microsoft.Extensions.Logging.LogLevel.Debug:
                            return LogLevel.Debug;
                        case Microsoft.Extensions.Logging.LogLevel.Information:
                            return LogLevel.Info;
                        case Microsoft.Extensions.Logging.LogLevel.Warning:
                            return LogLevel.Warn;
                        case Microsoft.Extensions.Logging.LogLevel.Error:
                            return LogLevel.Error;
                        case Microsoft.Extensions.Logging.LogLevel.Critical:
                            return LogLevel.Fatal;
                        default:
                            return LogLevel.None;
                    }
                }
            }

            private LogGroup logGroup;

            public LoggerFactory(LogGroup logGroup) => this.logGroup = logGroup;
            public ILogger CreateLogger(string _) => new Logger(logGroup);
            public void AddProvider(ILoggerProvider provider) { }
            public void Dispose() { }
        }
    }
}