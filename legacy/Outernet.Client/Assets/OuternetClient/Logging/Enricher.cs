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

namespace Outernet.Client
{
    public class Enricher : ILogEventEnricher
    {
        public static ScalarValue methodSignatureKey = new ScalarValue("methodSignature");
        public static ScalarValue fileNameKey = new ScalarValue("fileName");
        public static ScalarValue lineNumberKey = new ScalarValue("lineNumber");

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
            // If the log event has an exception, enrich with exception details
            if (logEvent.Exception != null)
            {
                logEvent.AddPropertyIfAbsent(new LogEventProperty("exception", SerilogException(logEvent.Exception)));

                // If the log event is an uncaught exception, we have no more information to add
                // logEvent.Properties.TryGetValue("logGroup", out var logGroup);
                // if ((string)((ScalarValue)logGroup).Value == "UncaughtException") return;
            }

            logEvent.AddPropertyIfAbsent(new LogEventProperty("messageTemplate", new ScalarValue(logEvent.MessageTemplate.Text)));
            logEvent.AddPropertyIfAbsent(new LogEventProperty("message", new ScalarValue(logEvent.MessageTemplate.Render(logEvent.Properties))));
            logEvent.AddPropertyIfAbsent(new LogEventProperty("deviceName", new ScalarValue(Logger.DeviceName)));

            var room = ConnectionManager.RoomConnectionRequested.Value;
            if (room != null)
            {
                logEvent.AddOrUpdateProperty(propertyFactory.CreateProperty("room", room));
            }

            var propertyTokens = logEvent.MessageTemplate.Tokens
                .OfType<PropertyToken>()
                .Where(token => token.Format != null);

            // If the message template contained formatting tokens, enrich with the rendered properties
            if (propertyTokens.Any())
            {
                logEvent.AddPropertyIfAbsent(new LogEventProperty("properties", new SequenceValue(propertyTokens.Select(token =>
                {
                    using var stringWriter = new System.IO.StringWriter();
                    token.Render(logEvent.Properties, stringWriter);
                    return new ScalarValue(stringWriter.ToString());
                }))));
            }

            // If the log level is greater than or equal to the configured stack trace level, enrich with the stack trace
            if (logLevelMap[logEvent.Level] >= Log.stackTraceLevel)
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

            if (exception is WebRequestException)
            {
                properties.Add(new ScalarValue("httpStatusCode"), new ScalarValue((exception as WebRequestException).StatusCode));
                properties.Add(new ScalarValue("httpResponse"), new ScalarValue((exception as WebRequestException).Response));
            }

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

            if (exception is ResponseDeserializationException)
            {
                properties.Add(new ScalarValue("json"), new ScalarValue((exception as ResponseDeserializationException).Json));
            }

            return new DictionaryValue(properties);
        }

        SequenceValue SerilogStackTrace(Exception exception = null)
        {
            var stackTrace = exception != null
                ? new StackTrace(exception, true)
                : new StackTrace(true);

            var frames = stackTrace.GetFrames().AsEnumerable();
            // var lastHiddenFrame = frames
            //     .Select((value, index) => new { value, index })
            //     .LastOrDefault(frame =>
            //         frame.value.GetMethod() != null &&
            //         frame.value.GetMethod().GetCustomAttributes(typeof(InnerFramesHiddenFromStackTraceAttribute), false).Length > 0);

            // if (lastHiddenFrame != null)
            // {
            //     frames = frames.Skip(lastHiddenFrame.index + 1);
            // }

            return new SequenceValue(frames.Select(frame =>
            {
                var method = frame.GetMethod();

                // If we couldn't determine the method name, enrich with a method signature of "<unknown method>"
                if (method == null)
                {
                    return new DictionaryValue(new Dictionary<ScalarValue, LogEventPropertyValue>
                    {
                        { methodSignatureKey, new ScalarValue("<unknown method>") }
                    });
                }

                var methodParameters = method.GetParameters();
                var methodSignature = BuildMethodName(method);
                methodSignature += methodParameters.Length == 0 ? "()" : $"({string.Join(", ", methodParameters.Select(parameter => parameter.ParameterType.Name))})";

                // Enrich with the method signature
                var properties = new Dictionary<ScalarValue, LogEventPropertyValue>
                {
                    { methodSignatureKey, new ScalarValue(methodSignature) }
                };

                // Enrich with the file name and line number, if available
                var fileName = frame.GetFileName();
                if (fileName != null && fileName != string.Empty)
                {
                    fileName = Path.GetFullPath(fileName);
                    if (fileName.StartsWith(unityProjectRoot))
                    {
                        fileName = fileName.Substring(unityProjectRoot.Length + 1);
                    }

                    properties.Add(fileNameKey, new ScalarValue(fileName));
                    properties.Add(lineNumberKey, new ScalarValue(frame.GetFileLineNumber()));
                }

                return new DictionaryValue(properties);
            }));
        }

        private static string BuildMethodName(MethodBase method)
        {
            if (method == null) return null;

            var methodName = method.Name;
            var type = method.DeclaringType;

            // If this is a generic method, append the generic arguments to the method name
            if (method.IsGenericMethod)
            {
                methodName += $"<{string.Join(", ", method.GetGenericArguments().Select(arg => arg.Name))}>";
            }

            if (type != null)
            {
                var typeName = type.Name;

                // If this is a lambda method, use a less cryptic name
                if (typeName.StartsWith("<>c"))
                {
                    var match = anonymousFunctionRegex.Match(methodName);
                    var enclosingMethodName = match.Groups["method"].Value;
                    var lambdaIndex = match.Groups["index"].Value;
                    return $"{BuildTypeName(type.DeclaringType)}.{enclosingMethodName}+[Anonymous_{lambdaIndex}]";
                }

                // If this is an async state machine method, use a less cryptic name
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

            // If this is a generic type, append the generic arguments to the type name
            // if (type.IsGenericType)
            // {
            //     // Remove the backtick and the number of generic arguments from the type name
            //     typeName = typeName.Substring(0, typeName.IndexOf('`'));

            //     var genericArgs = type.GetGenericArguments()
            //         .Select(arg =>
            //         {
            //             // If this generic argument is an async state machine, use a less cryptic name
            //             if (arg.Name.Contains("d__"))
            //             {
            //                 var match = asyncStateMachineRegex.Match(arg.Name);
            //                 var methodName = match.Groups["method"].Value;
            //                 return $"{methodName}+[AsyncStateMachine]";
            //             }
            //             return arg.Name;
            //         });

            //     typeName += $"<{string.Join(", ", genericArgs)}>";
            // }

            // If this is a nested type, prepend the declaring type name
            if (type.IsNested)
            {
                return $"{BuildTypeName(type.DeclaringType)}+{typeName}";
            }

            // If this type is in a namespace, prepend the namespace
            if (type.Namespace != null)
            {
                return $"{type.Namespace}.{typeName}";
            }

            return typeName;
        }
    }
}

