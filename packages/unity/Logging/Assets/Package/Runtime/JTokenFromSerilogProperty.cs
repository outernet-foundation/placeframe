using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Serilog.Events;

namespace Outernet.Logging
{
    public static class Json
    {
        public static JToken FromSerilogProperty(string key, LogEventPropertyValue value, bool addHyperlinks)
        {
            if (key == "message")
            {
                var message = (value as ScalarValue).Value as string;

                var messageLines = message.Split(new[] { '\n' }, StringSplitOptions.None);

                if (messageLines.Length > 1)
                {
                    return JToken.FromObject(messageLines.Select(line => line.Trim()));
                }

                return JToken.FromObject(message);
            }

            if (key == "stackTrace")
            {
                return JToken.FromObject((value as SequenceValue).Elements.Select(frame => FrameToString(frame as DictionaryValue, addHyperlinks)));
            }

            return value switch
            {
                ScalarValue { Value: null } => JValue.CreateNull(),

                ScalarValue scalarValue => JToken.FromObject(scalarValue.Value),

                StructureValue structureValue => JToken.FromObject(
                    structureValue.Properties.ToDictionary(
                        property => property.Name,
                        property => FromSerilogProperty(property.Name, property.Value, addHyperlinks)
                    )
                ),

                DictionaryValue dictionaryValue => JToken.FromObject(
                    dictionaryValue.Elements.ToDictionary(
                        kvp => kvp.Key.Value.ToString(),
                        kvp => FromSerilogProperty(kvp.Key.Value.ToString(), kvp.Value, addHyperlinks)
                    )
                ),

                SequenceValue sequenceValue => JToken.FromObject(sequenceValue.Elements.Select(element => FromSerilogProperty(null, element, addHyperlinks))),

                _ => throw new NotSupportedException($"Unsupported property value type: {value.GetType()}"),
            };
        }

        // Flatten a Serilog property into Loki structured metadata (string->string).
        // Scalars land verbatim; nested structures/dicts expand to dotted keys; sequences
        // serialize to a compact-JSON string. The exception object and stack traces get
        // OTel-semconv key names. Loki sanitizes '.' to '_' on ingest, so dotted keys here
        // become e.g. exception_type, exception_message, exception_stacktrace.
        public static void FlattenSerilogProperty(string key, LogEventPropertyValue value, IDictionary<string, string> sink)
        {
            if (key == "exception" && value is DictionaryValue exceptionValue)
            {
                FlattenException("exception", exceptionValue, sink);
                return;
            }

            if (key == "stackTrace" && value is SequenceValue stackTraceValue)
            {
                sink["code.stacktrace"] = RenderFrames(stackTraceValue);
                return;
            }

            switch (value)
            {
                case ScalarValue { Value: null }:
                    return;

                case ScalarValue scalarValue:
                    sink[key] = Convert.ToString(scalarValue.Value, CultureInfo.InvariantCulture);
                    return;

                case StructureValue structureValue:
                    foreach (var property in structureValue.Properties)
                        FlattenSerilogProperty($"{key}.{property.Name}", property.Value, sink);
                    return;

                case DictionaryValue dictionaryValue:
                    foreach (var element in dictionaryValue.Elements)
                        FlattenSerilogProperty($"{key}.{element.Key.Value}", element.Value, sink);
                    return;

                case SequenceValue sequenceValue:
                    sink[key] = FromSerilogProperty(key, sequenceValue, false).ToString(Formatting.None);
                    return;
            }
        }

        private static void FlattenException(string prefix, DictionaryValue exception, IDictionary<string, string> sink)
        {
            foreach (var element in exception.Elements)
            {
                switch (element.Key.Value as string)
                {
                    case "type":
                        AddScalar($"{prefix}.type", element.Value, sink);
                        break;

                    case "message":
                        AddScalar($"{prefix}.message", element.Value, sink);
                        break;

                    case "stackTrace" when element.Value is SequenceValue frames:
                        sink[$"{prefix}.stacktrace"] = RenderFrames(frames);
                        break;

                    case "javaStackTrace":
                        AddScalar($"{prefix}.javastacktrace", element.Value, sink);
                        break;

                    case "innerException" when element.Value is DictionaryValue inner:
                        FlattenException($"{prefix}.inner", inner, sink);
                        break;

                    case "innerExceptions":
                        sink[$"{prefix}.inner"] = FromSerilogProperty("innerExceptions", element.Value, false).ToString(Formatting.None);
                        break;
                }
            }
        }

        private static void AddScalar(string key, LogEventPropertyValue value, IDictionary<string, string> sink)
        {
            if (value is ScalarValue { Value: not null } scalarValue)
                sink[key] = Convert.ToString(scalarValue.Value, CultureInfo.InvariantCulture);
        }

        private static string RenderFrames(SequenceValue stackTrace)
        {
            return string.Join("\n", stackTrace.Elements.Select(frame => FrameToString(frame as DictionaryValue, false)));
        }

        private static string FrameToString(DictionaryValue frame, bool addHyperlinks)
        {
            var frameString = (frame.Elements[EnricherKeys.MethodSignatureKey] as ScalarValue).Value as string;

            if (frame.Elements.TryGetValue(EnricherKeys.FileNameKey, out var fileNameProperty))
            {
                var fileName = (fileNameProperty as ScalarValue).Value;
                var lineNumber = (frame.Elements[EnricherKeys.LineNumberKey] as ScalarValue).Value;

                frameString += addHyperlinks
                    ? $" (at <a href=\"{fileName}\" line=\"{lineNumber}\">{fileName}:{lineNumber}</a>)"
                    : $" (at {fileName}:{lineNumber})";
            }

            return frameString;
        }
    }
}
