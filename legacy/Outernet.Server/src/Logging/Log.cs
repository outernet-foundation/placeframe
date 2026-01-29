using Microsoft.Extensions.Logging;

namespace Outernet.Server
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
        Rest = 1 << 2,
    }

    public static class Log
    {
        public static LogLevel logLevel = LogLevel.None;
        public static LogLevel stackTraceLevel = LogLevel.None;
        public static LogGroup enabledLogGroups = LogGroup.None;

        private static void LogBase(LogLevel level, LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            if (level < logLevel || (group & enabledLogGroups) == 0) return;

            Logger.Serilog(level, group, exception, messageTemplate, propertyValues);
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
                    MapLogLevel(logLevel) >= Server.Log.logLevel && (logGroup & enabledLogGroups) != 0;

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