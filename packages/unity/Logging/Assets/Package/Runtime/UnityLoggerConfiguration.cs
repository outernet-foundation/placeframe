using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Newtonsoft.Json.Linq;
using Serilog;
using Serilog.Configuration;
using Serilog.Core;
using Serilog.Events;
using UnityEngine;

namespace Outernet.Logging
{
    static class UnityLoggerConfiguration
    {
        public static LoggerConfiguration Unity<TLogGroup>(this LoggerSinkConfiguration loggerConfiguration) where TLogGroup : struct, Enum
        {
            return loggerConfiguration.Sink(new UnityDebugSink<TLogGroup>());
        }

        class UnityDebugSink<TLogGroup> : ILogEventSink where TLogGroup : struct, Enum
        {
            static readonly Dictionary<LogEventLevel, LogType> logLevelMap = new Dictionary<LogEventLevel, LogType>
            {
                { LogEventLevel.Verbose, LogType.Log },
                { LogEventLevel.Debug, LogType.Log },
                { LogEventLevel.Information, LogType.Log },
                { LogEventLevel.Warning, LogType.Warning },
                { LogEventLevel.Error, LogType.Error },
                { LogEventLevel.Fatal, LogType.Error }
            };

            static readonly Dictionary<string, string> colorCache;

            static UnityDebugSink()
            {
                colorCache = new Dictionary<string, string>();
                foreach (var field in typeof(TLogGroup).GetFields(BindingFlags.Public | BindingFlags.Static))
                {
                    var attr = field.GetCustomAttribute<LogGroupColorAttribute>();
                    if (attr != null)
                    {
                        colorCache[field.Name] = attr.HexColor;
                    }
                }
            }

            public void Emit(LogEvent logEvent)
            {
                string logGroup = (string)(logEvent.Properties.GetValueOrDefault("logGroup") as ScalarValue).Value;
                string prelude = colorCache.TryGetValue(logGroup, out var color) ?
                    $"<color={color}>[{logGroup}]</color>" :
                    $"[{logGroup}]";

                string message;

                if (logEvent.Properties.TryGetValue("message", out var messageProperty))
                {
                    message = $"{prelude} {(string)(messageProperty as ScalarValue).Value}";
                }
                else
                {
                    message = prelude;
                }

                if (logEvent.Properties.TryGetValue("exception", out var exceptionProperty))
                {
                    message += FormatException(exceptionProperty as DictionaryValue);
                }

                if (logEvent.Properties.TryGetValue("stackTrace", out var stackTrace))
                {
                    message += $"\n{string.Join("\n", Json.FromSerilogProperty("stackTrace", stackTrace, true) as JArray)}";
                }

                // Escape curly braces so defaultLogHandler.LogFormat doesn't interpret them as format specifiers
                message = message
                    .Replace("{", "{{")
                    .Replace("}", "}}");

                Logger<TLogGroup>.emittingToUnity = true;
                try
                {
                    Logger<TLogGroup>.defaultUnityLogHandler.LogFormat(logLevelMap[logEvent.Level], null, message);
                }
                finally
                {
                    Logger<TLogGroup>.emittingToUnity = false;
                }
            }

            static string FormatException(DictionaryValue exceptionProperty)
            {
                var elements = exceptionProperty.Elements;

                var type = (elements[new ScalarValue("type")] as ScalarValue).Value;
                var exceptionMessage = (elements[new ScalarValue("message")] as ScalarValue).Value;

                var result = $"\n{type}: {exceptionMessage}";

                if (elements.TryGetValue(new ScalarValue("stackTrace"), out var stackTrace))
                {
                    result += $"\n{string.Join("\n", Json.FromSerilogProperty("stackTrace", stackTrace, true) as JArray)}";
                }

                if (elements.TryGetValue(new ScalarValue("javaStackTrace"), out var javaStackTrace))
                {
                    result += $"\n{(javaStackTrace as ScalarValue).Value}";
                }

                if (elements.TryGetValue(new ScalarValue("innerExceptions"), out var innerExceptions))
                {
                    foreach (var inner in (innerExceptions as SequenceValue).Elements)
                    {
                        result += "\n--- Inner Exception ---";
                        result += FormatException(inner as DictionaryValue);
                    }
                }
                else if (elements.TryGetValue(new ScalarValue("innerException"), out var innerException))
                {
                    result += "\n--- Inner Exception ---";
                    result += FormatException(innerException as DictionaryValue);
                }

                return result;
            }
        }
    }
}
