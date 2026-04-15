using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.RegularExpressions;
using Serilog.Core;
using Serilog.Events;
using Serilog.Parsing;
using UnityEngine;

namespace Outernet.Logging
{
    public class Enricher<TLogGroup> : ILogEventEnricher where TLogGroup : struct, Enum
    {
        private static Regex anonymousFunctionRegex = new Regex(@"\<(?<method>\w+)\>b__\d+_(?<index>\d+)");
        private static Regex asyncStateMachineRegex = new Regex(@"\<(?<method>\w+)\>d__\d+");

        private static readonly string unityProjectRoot = Path.GetFullPath(Application.dataPath + "/..");

        static readonly Dictionary<LogEventLevel, LogLevel> logLevelMap = new Dictionary<LogEventLevel, LogLevel>
        {
            { LogEventLevel.Verbose, LogLevel.Trace },
            { LogEventLevel.Debug, LogLevel.Debug },
            { LogEventLevel.Information, LogLevel.Info },
            { LogEventLevel.Warning, LogLevel.Warn },
            { LogEventLevel.Error, LogLevel.Error },
            { LogEventLevel.Fatal, LogLevel.Fatal }
        };

        public void Enrich(LogEvent logEvent, ILogEventPropertyFactory propertyFactory)
        {
            if (logEvent.Exception != null)
            {
                logEvent.AddPropertyIfAbsent(new LogEventProperty("exception", SerilogException(logEvent.Exception)));
            }

            logEvent.AddPropertyIfAbsent(new LogEventProperty("messageTemplate", new ScalarValue(logEvent.MessageTemplate.Text)));
            logEvent.AddPropertyIfAbsent(new LogEventProperty("message", new ScalarValue(logEvent.MessageTemplate.Render(logEvent.Properties))));
            logEvent.AddPropertyIfAbsent(new LogEventProperty("deviceName", new ScalarValue(Logger<TLogGroup>.DeviceName)));

            var propertyTokens = logEvent.MessageTemplate.Tokens
                .OfType<PropertyToken>()
                .Where(token => token.Format != null);

            if (propertyTokens.Any())
            {
                logEvent.AddPropertyIfAbsent(new LogEventProperty("properties", new SequenceValue(propertyTokens.Select(token =>
                {
                    using var stringWriter = new System.IO.StringWriter();
                    token.Render(logEvent.Properties, stringWriter);
                    return new ScalarValue(stringWriter.ToString());
                }))));
            }

            if (logLevelMap[logEvent.Level] >= Log<TLogGroup>.stackTraceLevel)
            {
                logEvent.AddPropertyIfAbsent(new LogEventProperty("stackTrace", SerilogStackTrace()));
            }
        }

        DictionaryValue SerilogException(Exception exception)
        {
            var properties = new Dictionary<ScalarValue, LogEventPropertyValue>
            {
                { new ScalarValue("type"), new ScalarValue(exception.GetType().FullName) },
                { new ScalarValue("message"), new ScalarValue(exception.Message) }
            };

            if (exception.StackTrace != null)
            {
                properties.Add(new ScalarValue("stackTrace"), SerilogStackTrace(exception));
            }

            if (exception is AggregateException aggregateException)
            {
                properties.Add(new ScalarValue("innerExceptions"), new SequenceValue(aggregateException.InnerExceptions.Select(SerilogException)));
            }
            else if (exception.InnerException != null)
            {
                properties.Add(new ScalarValue("innerException"), SerilogException(exception.InnerException));
            }

            return new DictionaryValue(properties);
        }

        SequenceValue SerilogStackTrace(Exception exception = null)
        {
            var stackTrace = exception != null
                ? new StackTrace(exception, true)
                : new StackTrace(true);

            var frames = (stackTrace.GetFrames() ?? Array.Empty<StackFrame>()).AsEnumerable();

            return new SequenceValue(frames.Select(frame =>
            {
                var method = frame.GetMethod();

                if (method == null)
                {
                    return new DictionaryValue(new Dictionary<ScalarValue, LogEventPropertyValue>
                    {
                        { EnricherKeys.MethodSignatureKey, new ScalarValue("<unknown method>") }
                    });
                }

                var methodParameters = method.GetParameters();
                var methodSignature = BuildMethodName(method);
                methodSignature += methodParameters.Length == 0 ? "()" : $"({string.Join(", ", methodParameters.Select(parameter => parameter.ParameterType.Name))})";

                var properties = new Dictionary<ScalarValue, LogEventPropertyValue>
                {
                    { EnricherKeys.MethodSignatureKey, new ScalarValue(methodSignature) }
                };

                var fileName = frame.GetFileName();

                if (fileName != null && fileName != string.Empty)
                {
                    fileName = Path.GetFullPath(fileName);
                    if (fileName.StartsWith(unityProjectRoot))
                    {
                        fileName = fileName.Substring(unityProjectRoot.Length + 1);
                    }

                    properties.Add(EnricherKeys.FileNameKey, new ScalarValue(fileName));
                    properties.Add(EnricherKeys.LineNumberKey, new ScalarValue(frame.GetFileLineNumber()));
                }

                return new DictionaryValue(properties);
            }));
        }

        private static string BuildMethodName(MethodBase method)
        {
            if (method == null) return null;

            var methodName = method.Name;
            var type = method.DeclaringType;

            if (method.IsGenericMethod)
            {
                var genericArgs = method.GetGenericArguments();
                methodName += $"<{string.Join(", ", genericArgs.Select(arg => arg.Name))}>";
            }

            if (type != null)
            {
                var typeName = type.Name;

                if (typeName.StartsWith("<>c"))
                {
                    var match = anonymousFunctionRegex.Match(methodName);
                    var enclosingMethodName = match.Groups["method"].Value;
                    var lambdaIndex = match.Groups["index"].Value;
                    return $"{BuildTypeName(type.DeclaringType)}.{enclosingMethodName}+[Anonymous_{lambdaIndex}]";
                }

                if (typeName.Contains("d__"))
                {
                    var match = asyncStateMachineRegex.Match(typeName);
                    var originalMethodName = match.Groups["method"].Value;
                    return $"{BuildTypeName(type.DeclaringType)}.{originalMethodName}+[AsyncStateMachine].{methodName}";
                }

                return $"{BuildTypeName(type)}.{methodName}";
            }

            return methodName;
        }

        private static string BuildTypeName(Type type)
        {
            string typeName = type.Name;

            if (type.IsNested)
            {
                return $"{BuildTypeName(type.DeclaringType)}+{typeName}";
            }

            if (type.Namespace != null)
            {
                return $"{type.Namespace}.{typeName}";
            }

            return typeName;
        }
    }

    public static class EnricherKeys
    {
        public static readonly ScalarValue MethodSignatureKey = new ScalarValue("methodSignature");
        public static readonly ScalarValue FileNameKey = new ScalarValue("fileName");
        public static readonly ScalarValue LineNumberKey = new ScalarValue("lineNumber");
    }
}
