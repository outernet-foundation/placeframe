using System;

using UnityEngine;

namespace Plerion
{
    public enum LogGroup
    {
        VisualPositioningSystem,
        CameraLocalization,
        Rest,
        Permissions,
        MagicLeapCamera,
        MapVisualization,
        Immersal
    }

    public static class Log
    {
        public static void Debug(LogGroup logGroup, string message)
        {
            LogInternal("Debug", logGroup.ToString(), Color.cyan, message, null, UnityEngine.Debug.Log);
        }

        public static void Warn(LogGroup logGroup, string message)
        {
            LogInternal("Warn", logGroup.ToString(), Color.yellow, message, null, UnityEngine.Debug.LogWarning);
        }

        public static void Error(LogGroup logGroup, string message, Exception exception)
        {
            LogInternal("Error", logGroup.ToString(), Color.red, message, exception, UnityEngine.Debug.LogError);
        }

        public static void Error(LogGroup logGroup, Exception exception)
        {
            LogInternal("Error", logGroup.ToString(), Color.red, null, exception, UnityEngine.Debug.LogError);
        }

        public static void Error(LogGroup logGroup, string message)
        {
            LogInternal("Error", logGroup.ToString(), Color.red, message, null, UnityEngine.Debug.LogError);
        }

        public static void Info(LogGroup logGroup, string message)
        {
            LogInternal("Info", logGroup.ToString(), Color.green, message, null, UnityEngine.Debug.Log);
        }

        public static void Trace(LogGroup logGroup, string message)
        {
            LogInternal("Trace", logGroup.ToString(), Color.white, message, null, UnityEngine.Debug.Log);
        }

        private static void LogInternal(string logLevel, string tag, Color color, string message, Exception exception, Action<string> logMethod)
        {
            if (message != null && exception != null)
            {
                logMethod($"<color=#{ColorUtility.ToHtmlStringRGB(color)}>[{logLevel}] [{tag}]</color> {message}\nException: {exception}");
            }
            else if (message != null)
            {
                logMethod($"<color=#{ColorUtility.ToHtmlStringRGB(color)}>[{logLevel}] [{tag}]</color> {message}");
            }
            else if (exception != null)
            {
                logMethod($"<color=#{ColorUtility.ToHtmlStringRGB(color)}>[{logLevel}] [{tag}]</color> {exception}");
            }
        }
    }
}