using System;

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
    Stateful = 1 << 13,
}

public static class Log
{
    public static LogLevel Level { get; set; } = LogLevel.Info;

    public static void Trace(LogGroup group, string message)
    {
        if (Level <= LogLevel.Trace)
            UnityEngine.Debug.Log($"[{group}] {message}");
    }

    public static void Debug(LogGroup group, string message)
    {
        if (Level <= LogLevel.Debug)
            UnityEngine.Debug.Log($"[{group}] {message}");
    }

    public static void Info(LogGroup group, string message)
    {
        if (Level <= LogLevel.Info)
            UnityEngine.Debug.Log($"[{group}] {message}");
    }

    public static void Info(LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
    {
        if (Level <= LogLevel.Info)
        {
            UnityEngine.Debug.Log($"[{group}] {messageTemplate} {propertyValues}\nException: {exception}");
        }
    }

    public static void Warn(LogGroup group, string message)
    {
        if (Level <= LogLevel.Warn)
            UnityEngine.Debug.LogWarning($"[{group}] {message}");
    }

    public static void Error(LogGroup group, string message)
    {
        if (Level <= LogLevel.Error)
            UnityEngine.Debug.LogError($"[{group}] {message}");
    }

    public static void Exception(Exception exception)
    {
        if (Level <= LogLevel.Error)
        {
            UnityEngine.Debug.LogException(exception);
        }
    }

    public static void Fatal(LogGroup group, string message)
    {
        if (Level <= LogLevel.Fatal)
            UnityEngine.Debug.LogError($"[{group}] {message}");
    }
}
