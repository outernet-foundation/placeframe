using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using Cysharp.Net.Http;
using Newtonsoft.Json.Linq;
using Serilog;
using Serilog.Configuration;
using Serilog.Events;
using Serilog.Formatting;
using Serilog.Sinks.Grafana.Loki;
using Serilog.Sinks.Grafana.Loki.HttpClients;
using UnityEngine.Networking;

namespace Outernet.MapRegistrationTool
{
    static public class UnityMainThreadDispatcher
    {
        private static readonly ConcurrentQueue<Action> _executionQueue = new ConcurrentQueue<Action>();

        // Enqueue a task to run on the main thread
        static public void Enqueue(Action action)
        {
            if (action == null) throw new ArgumentNullException(nameof(action));
            _executionQueue.Enqueue(action);
        }

        // Enqueue an async task to run on the main thread
        static public Task Enqueue(Func<Task> task)
        {
            var tcs = new TaskCompletionSource<bool>();
            Enqueue(async () =>
            {
                try
                {
                    await task();
                    tcs.SetResult(true);
                }
                catch (Exception ex)
                {
                    tcs.SetException(ex);
                }
            });
            return tcs.Task;
        }

        // Call this from Unity's Update() method to process all enqueued actions
        static public void Flush()
        {
            while (_executionQueue.TryDequeue(out var action))
            {
                action?.Invoke();
            }
        }
    }

    static class LokiLoggerConfiguration
    {
        static string lokiUserId = "961726";
        static string lokiAccessToken = "glc_eyJvIjoiMTE4OTQ0OSIsIm4iOiJzdGFjay0xMDAzOTQ2LWludGVncmF0aW9uLXBsZXJpb24tbG9raS1hY2Nlc3MtdG9rZW4iLCJrIjoiMmxvQklxNHE5OTJYM2NnZTg2Q2s1NExJIiwibSI6eyJyIjoicHJvZC11cy1lYXN0LTAifX0=";

        public static LoggerConfiguration Loki(this LoggerSinkConfiguration loggerConfiguration)
        {
            return loggerConfiguration.GrafanaLoki(
                "https://logs-prod-006.grafana.net",
                httpClient: new BearerTokenAuthenticatedHttpClient($"{lokiUserId}:{lokiAccessToken}"),
                labels: new List<LokiLabel> {
                    new LokiLabel() { Key = "app", Value = "outernet-client" },
                    new LokiLabel() {
                        Key = "platform",
#if UNITY_EDITOR
                        Value = "editor"
#elif MAGIC_LEAP
                        Value = "magic-leap"
#elif OUTERNET_ANDROID_MOBILE
                        Value = "android-mobile"
#else
                        Value = "unknown"
#endif
                    }
                },
                textFormatter: new LokiJsonTextFormatter());
        }

        class BearerTokenAuthenticatedHttpClient : BaseLokiHttpClient
        {
            public BearerTokenAuthenticatedHttpClient(string bearerToken)
            {
                HttpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", bearerToken);
            }

            public override async Task<HttpResponseMessage> PostAsync(string requestUri, Stream contentStream)
            {
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
                        _ => 5  // Uncategorized properties will have an order between "message" and "stackTrace"
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