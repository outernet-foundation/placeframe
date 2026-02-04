using System;

namespace Placeframe.MapRegistrationTool
{
    public class ChannelLogger : FofX.ILogger
    {
        public LogGroup logGroup;

        public bool LevelEnabled(FofX.LogLevel logLevel)
            => Log.logLevel <= ToClientLogLevel(logLevel);

        public bool LevelEnabled(LogLevel logLevel)
            => Log.logLevel <= logLevel;

        private LogLevel ToClientLogLevel(FofX.LogLevel logLevel)
            => (LogLevel)(int)logLevel;

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
                case FofX.LogLevel.Fatal:
                    Error(message, exception);
                    break;
            }
        }

        public void Debug(string message)
            => Log.Debug(logGroup, message);

        public void Error(string message)
            => Log.Error(logGroup, message);

        public void Error(Exception exception)
            => Log.Error(logGroup, exception, null);

        public void Error(string message, Exception exception)
            => Log.Error(logGroup, exception, message);

        public void Info(string message)
            => Log.Info(logGroup, message);

        public void Trace(string message)
            => Log.Trace(logGroup, message);

        public void Warning(string message)
            => Log.Warn(logGroup, message);
    }
}