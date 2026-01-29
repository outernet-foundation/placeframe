using System;

namespace FofX
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

    public interface ILogger
    {
        bool LevelEnabled(LogLevel logLevel);
        void Generic(LogLevel logLevel, string message = default, Exception exception = default);
        void Trace(string message);
        void Debug(string message);
        void Info(string message);
        void Warning(string message);
        void Error(string message);
        void Error(Exception exception);
        void Error(string message, Exception exception);
    }
}
