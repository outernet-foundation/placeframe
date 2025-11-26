using System;
using System.Linq;
using Newtonsoft.Json.Linq;
using Serilog.Events;

namespace Outernet.MapRegistrationTool
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
                var stackTrace = (value as SequenceValue).Elements
                    .Select(frame =>
                    {
                        var frameProperty = frame as DictionaryValue;
                        var frameString = (frameProperty.Elements[Enricher.methodSignatureKey] as ScalarValue).Value;

                        if (frameProperty.Elements.TryGetValue(Enricher.fileNameKey, out var fileNameProperty))
                        {
                            var fileName = (fileNameProperty as ScalarValue).Value;
                            var lineNumber = (frameProperty.Elements[Enricher.lineNumberKey] as ScalarValue).Value;

                            if (addHyperlinks)
                            {
                                frameString += $" (at <a href=\"{fileName}\" line=\"{lineNumber}\">{fileName}:{lineNumber}</a>)";
                            }
                            else
                            {
                                frameString += $" (at {fileName}:{lineNumber})";
                            }
                        }

                        return frameString;
                    });

                return JToken.FromObject(stackTrace);
            }

            if (key == "httpResponse" || key == "json")
            {
                // this json already, so just parse and return
                return JToken.Parse((value as ScalarValue).Value.ToString());
            }

            return JToken.FromObject(value switch
            {
                ScalarValue scalarValue => scalarValue.Value,

                StructureValue structureValue => structureValue.Properties
                    .ToDictionary(property => property.Name, property => FromSerilogProperty(property.Name, property.Value, addHyperlinks)),

                DictionaryValue dictionaryValue => dictionaryValue.Elements
                    .ToDictionary(kvp => kvp.Key.Value.ToString(), kvp => FromSerilogProperty(kvp.Key.Value.ToString(), kvp.Value, addHyperlinks)),

                SequenceValue sequenceValue => sequenceValue.Elements
                    .Select(element => FromSerilogProperty(null, element, addHyperlinks)),

                _ => throw new NotSupportedException($"Unsupported property value type: {value.GetType()}")
            });
        }
    }
}