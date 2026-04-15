using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using Newtonsoft.Json.Linq;
using Serilog;
using Serilog.Configuration;
using Serilog.Events;
using Serilog.Formatting;
using Serilog.Sinks.Grafana.Loki;
using Serilog.Sinks.Grafana.Loki.HttpClients;

namespace Outernet.Logging
{
    static class LokiLoggerConfiguration
    {
        public static LoggerConfiguration Loki(
            this LoggerSinkConfiguration loggerConfiguration,
            string domain,
            Func<UniTask<string>> tokenProvider,
            IEnumerable<(string key, string value)> labels)
        {
            return loggerConfiguration.GrafanaLoki(
                $"https://{domain}",
                httpClient: new TokenAuthenticatedHttpClient(tokenProvider),
                labels: labels.Select(l => new LokiLabel() { Key = l.key, Value = l.value }).ToList(),
                textFormatter: new LokiJsonTextFormatter());
        }

        class TokenAuthenticatedHttpClient : BaseLokiHttpClient
        {
            private readonly Func<UniTask<string>> _tokenProvider;

            public TokenAuthenticatedHttpClient(Func<UniTask<string>> tokenProvider)
            {
                _tokenProvider = tokenProvider;
            }

            public override async Task<HttpResponseMessage> PostAsync(string requestUri, Stream contentStream)
            {
                var token = await _tokenProvider();
                HttpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

                using var content = new StreamContent(contentStream);
                content.Headers.Add("Content-Type", "application/json");

                return await HttpClient
                    .PostAsync(requestUri, content)
                    .ConfigureAwait(false);
            }
        }

        public class LokiJsonTextFormatter : ITextFormatter
        {
            public void Format(LogEvent logEvent, TextWriter output)
            {
                if (logEvent == null) throw new ArgumentNullException(nameof(logEvent));
                if (output == null) throw new ArgumentNullException(nameof(output));

                var jsonObject = logEvent.Properties
                    .OrderBy(property => property.Key switch
                    {
                        "level" => 1,
                        "logGroup" => 2,
                        "messageTemplate" => 3,
                        "message" => 4,
                        "stackTrace" => 6,
                        "exception" => 7,
                        _ => 5
                    })
                    .ToDictionary(
                        property => property.Key,
                        property => Json.FromSerilogProperty(property.Key, property.Value, false)
                    );

                output.Write(JToken.FromObject(jsonObject));
            }
        }
    }
}
