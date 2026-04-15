using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using Outernet.Logging;

namespace Outernet.Client
{
    [Flags]
    public enum LogGroup
    {
        None = 0,
        [LogGroupColor("#4E79A7")] Default = 1 << 0,
        [LogGroupColor("#E15759")] UncaughtException = 1 << 1,
        [LogGroupColor("#59A14F")] LoggingTests = 1 << 2,
        [LogGroupColor("#F28E2B")] Grpc = 1 << 3,
        [LogGroupColor("#B07AA1")] SyncedStateClient = 1 << 4,
        MagicLeapCamera = 1 << 5,
        [LogGroupColor("#9C755F")] Immersal = 1 << 6,
        [LogGroupColor("#76B7B2")] Rest = 1 << 7,
        [LogGroupColor("#EDC948")] Localizer = 1 << 8,
        PlaneDetector = 1 << 9,
        [LogGroupColor("#FF9DA7")] Permissions = 1 << 10,
        BugReports = 1 << 11,
        ContentManagement = 1 << 12,
        Stateful = 1 << 13
    }

    public static class Log
    {
        public static LogLevel logLevel { get => Log<LogGroup>.logLevel; set => Log<LogGroup>.logLevel = value; }
        public static LogLevel stackTraceLevel { get => Log<LogGroup>.stackTraceLevel; set => Log<LogGroup>.stackTraceLevel = value; }
        public static LogGroup enabledLogGroups { get => Log<LogGroup>.enabledLogGroups; set => Log<LogGroup>.enabledLogGroups = value; }

        public static void DoLog(LogLevel level, LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.DoLog(level, group, exception, messageTemplate, propertyValues);
        public static void DoLog(LogLevel level, LogGroup group, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.DoLog(level, group, messageTemplate, propertyValues);
        public static void DoLog(LogLevel level, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.DoLog(level, messageTemplate, propertyValues);
        public static void DoLog(LogLevel level, Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.DoLog(level, exception, messageTemplate, propertyValues);
        public static void DoLog(LogLevel level, LogGroup group, Exception exception)
            => Log<LogGroup>.DoLog(level, group, exception);

        [InnerFramesHiddenFromStackTrace]
        public static void Trace(LogGroup group, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Trace(group, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Trace(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Trace(group, exception, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Trace(string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Trace(messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Trace(Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Trace(exception, messageTemplate, propertyValues);

        [InnerFramesHiddenFromStackTrace]
        public static void Debug(LogGroup group, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Debug(group, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Debug(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Debug(group, exception, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Debug(string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Debug(messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Debug(Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Debug(exception, messageTemplate, propertyValues);

        [InnerFramesHiddenFromStackTrace]
        public static void Info(LogGroup group, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Info(group, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Info(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Info(group, exception, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Info(string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Info(messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Info(Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Info(exception, messageTemplate, propertyValues);

        [InnerFramesHiddenFromStackTrace]
        public static void Warn(LogGroup group, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Warn(group, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Warn(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Warn(group, exception, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Warn(LogGroup group, string messageTemplate, Exception exception, params object[] propertyValues)
            => Log<LogGroup>.Warn(group, messageTemplate, exception, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Warn(string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Warn(messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Warn(Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Warn(exception, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Warn(string messageTemplate, Exception exception, params object[] propertyValues)
            => Log<LogGroup>.Warn(messageTemplate, exception, propertyValues);

        [InnerFramesHiddenFromStackTrace]
        public static void Error(LogGroup group, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Error(group, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Error(LogGroup group, params object[] propertyValues)
            => Log<LogGroup>.Error(group, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Error(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Error(group, exception, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Error(LogGroup group, string messageTemplate, Exception exception, params object[] propertyValues)
            => Log<LogGroup>.Error(group, messageTemplate, exception, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Error(string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Error(messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Error(Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Error(exception, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Error(string messageTemplate, Exception exception, params object[] propertyValues)
            => Log<LogGroup>.Error(messageTemplate, exception, propertyValues);

        [InnerFramesHiddenFromStackTrace]
        public static void Fatal(LogGroup group, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Fatal(group, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Fatal(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Fatal(group, exception, messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Fatal(string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Fatal(messageTemplate, propertyValues);
        [InnerFramesHiddenFromStackTrace]
        public static void Fatal(Exception exception, string messageTemplate, params object[] propertyValues)
            => Log<LogGroup>.Fatal(exception, messageTemplate, propertyValues);

        public class LoggerFactory : Log<LogGroup>.LoggerFactory
        {
            public LoggerFactory(LogGroup logGroup) : base(logGroup) { }
        }
    }

    public static class Logger
    {
        public static void Initialize(IEnumerable<string> suppressErrors = null)
            => Logger<LogGroup>.Initialize(suppressErrors);

        public static void EnableLoki(string domain, Func<UniTask<string>> tokenProvider, IEnumerable<(string key, string value)> labels)
            => Logger<LogGroup>.EnableLoki(domain, tokenProvider, labels);

        public static void Terminate()
            => Logger<LogGroup>.Terminate();
    }
}
