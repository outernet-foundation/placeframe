using System;
using Microsoft.Extensions.Logging;

namespace Outernet.Logging
{
    public static class Log<TLogGroup> where TLogGroup : struct, Enum
    {
        public static LogLevel logLevel = LogLevel.Info;
        public static LogLevel stackTraceLevel = LogLevel.Warn;
        public static TLogGroup enabledLogGroups;

        internal static Action<LogLevel, TLogGroup, Exception, string, object[]> LogHandler
            = (level, group, exception, template, values) => Logger<TLogGroup>.Serilog(level, group, exception, template, values);

        static Log()
        {
            // Default to all bits set (all groups enabled)
            enabledLogGroups = (TLogGroup)(object)~0;
        }

        private static void LogBase(LogLevel level, TLogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            if (level < logLevel || !enabledLogGroups.HasFlag(group)) return;

            LogHandler(level, group, exception, messageTemplate, propertyValues);
        }

        public static void DoLog(LogLevel level, TLogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(level, group, exception, messageTemplate, propertyValues);
        }

        public static void DoLog(LogLevel level, TLogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(level, group, null, messageTemplate, propertyValues);
        }

        public static void DoLog(LogLevel level, string messageTemplate, params object[] propertyValues)
        {
            LogBase(level, default, null, messageTemplate, propertyValues);
        }

        public static void DoLog(LogLevel level, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(level, default, exception, messageTemplate, propertyValues);
        }

        public static void DoLog(LogLevel level, TLogGroup group, Exception exception)
        {
            if (level < logLevel || !enabledLogGroups.HasFlag(group)) return;

            LogBase(level, group, exception, null, null);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Trace(TLogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Trace, group, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Trace(TLogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Trace, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Trace(string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Trace, default, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Trace(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Trace, default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Debug(TLogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Debug, group, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Debug(TLogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Debug, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Debug(string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Debug, default, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Debug(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Debug, default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Info(TLogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Info, group, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Info(TLogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Info, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Info(string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Info, default, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Info(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Info, default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(TLogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Warn, group, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(TLogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Warn, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(TLogGroup group, string messageTemplate, Exception exception, params object[] propertyValues)
        {
            LogBase(LogLevel.Warn, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Warn, default, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Warn, default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(string messageTemplate, Exception exception, params object[] propertyValues)
        {
            LogBase(LogLevel.Warn, default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(TLogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, group, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(TLogGroup group, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, group, null, null, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(TLogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(TLogGroup group, string messageTemplate, Exception exception, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, default, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Error(string messageTemplate, Exception exception, params object[] propertyValues)
        {
            LogBase(LogLevel.Error, default, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Fatal(TLogGroup group, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Fatal, group, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Fatal(TLogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Fatal, group, exception, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Fatal(string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Fatal, default, null, messageTemplate, propertyValues);
        }

        [InnerFramesHiddenFromStackTrace]
        public static void Fatal(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            LogBase(LogLevel.Fatal, default, exception, messageTemplate, propertyValues);
        }

        public class LoggerFactory : ILoggerFactory
        {
            public class Logger : ILogger
            {
                private TLogGroup logGroup;

                public Logger(TLogGroup logGroup) => this.logGroup = logGroup;

                public IDisposable BeginScope<TState>(TState state) => null;

                public bool IsEnabled(Microsoft.Extensions.Logging.LogLevel logLevel) =>
                    MapLogLevel(logLevel) >= Outernet.Logging.Log<TLogGroup>.logLevel && Outernet.Logging.Log<TLogGroup>.enabledLogGroups.HasFlag(logGroup);

                public void Log<TState>(
                    Microsoft.Extensions.Logging.LogLevel logLevel,
                    EventId eventId,
                    TState state,
                    Exception exception,
                    Func<TState, Exception, string> formatter)
                {
                    Outernet.Logging.Log<TLogGroup>.LogBase(MapLogLevel(logLevel), logGroup, exception, formatter(state, exception));
                }

                private static Logging.LogLevel MapLogLevel(Microsoft.Extensions.Logging.LogLevel logLevel)
                {
                    switch (logLevel)
                    {
                        case Microsoft.Extensions.Logging.LogLevel.Trace:
                            return Logging.LogLevel.Trace;
                        case Microsoft.Extensions.Logging.LogLevel.Debug:
                            return Logging.LogLevel.Debug;
                        case Microsoft.Extensions.Logging.LogLevel.Information:
                            return Logging.LogLevel.Info;
                        case Microsoft.Extensions.Logging.LogLevel.Warning:
                            return Logging.LogLevel.Warn;
                        case Microsoft.Extensions.Logging.LogLevel.Error:
                            return Logging.LogLevel.Error;
                        case Microsoft.Extensions.Logging.LogLevel.Critical:
                            return Logging.LogLevel.Fatal;
                        default:
                            return Logging.LogLevel.None;
                    }
                }
            }

            private TLogGroup logGroup;

            public LoggerFactory(TLogGroup logGroup) => this.logGroup = logGroup;
            public ILogger CreateLogger(string _) => new Logger(logGroup);
            public void AddProvider(ILoggerProvider provider) { }
            public void Dispose() { }
        }
    }
}
