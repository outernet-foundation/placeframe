using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using Serilog;
using Serilog.Configuration;
using Serilog.Core;
using Serilog.Events;
using UnityEngine;

namespace Outernet.MapRegistrationTool
{
    static class UnityLoggerConfiguration
    {
        public static LoggerConfiguration Unity(this LoggerSinkConfiguration loggerConfiguration)
        {
            return loggerConfiguration.Sink(new UnityDebugSink());
        }

        class UnityDebugSink : ILogEventSink
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

            string SerializeJToken(JToken jToken)
            {
                // jToken may have strings fields, which may already have escaped characters, and I see no way to prevent JsonConvert from escaping backslashes again, so we have to unescape them here
                return jToken.ToString().Replace("\\\\", "\\").Replace("\\\"", "\"");
            }

            public void Emit(LogEvent logEvent)
            {
                string message;

                string logGroup = (string)(logEvent.Properties.GetValueOrDefault("logGroup") as ScalarValue).Value;
                string prelude = Log.ColorPalette.ContainsKey(logGroup) ?
                    $"<color={Log.ColorPalette[logGroup]}>[{logGroup}]</color>" :
                    $"[{logGroup}]";

                if (logEvent.Properties.TryGetValue("message", out var messageProperty))
                {
                    message = $"{prelude} {(string)(messageProperty as ScalarValue).Value}";

                    if (logEvent.Properties.TryGetValue("stackTrace", out var stackTrace))
                    {
                        message += $"\n{string.Join("\n", Json.FromSerilogProperty("stackTrace", stackTrace, true) as JArray)}";
                    }

                    if (logEvent.Properties.TryGetValue("exception", out var exception))
                    {
                        message += $"\n\nException: {SerializeJToken(Json.FromSerilogProperty("exception", exception, true))}";
                    }
                }
                else
                {
                    // If the log event doesn't have a message property, this is an uncaught exception log and the only property is the 
                    // exception, which we format a bit differently for easier readability in the Unity console

                    logEvent.Properties.TryGetValue("exception", out var exception);
                    var exceptionJson = Json.FromSerilogProperty("exception", exception, true) as JObject;

                    message = $"{prelude} {exceptionJson["type"]}";
                    message += $"\n{string.Join("\n", exceptionJson["stackTrace"] as JArray)}";

                    if (exceptionJson.Count > 0)
                    {
                        message += $"\n\nException: {SerializeJToken(exceptionJson)}";
                    }
                }

                // Escape curly braces so defaultLogHandler.LogFormat doesn't interpret them as format specifiers
                message = message
                    .Replace("{", "{{")
                    .Replace("}", "}}");

                Logger.defaultUnityLogHandler.LogFormat(logLevelMap[logEvent.Level], null, message);
            }
        }
    }
}