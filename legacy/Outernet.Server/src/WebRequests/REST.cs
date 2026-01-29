using System.Net;
using System.Text;
using Newtonsoft.Json;

namespace Outernet.Server
{
    public static class RestClient
    {
        private const int MaxRetries = 10;
        private const double BackoffFactor = 1.5;
        private const int InitialDelay = 50; // milliseconds

        private static readonly HttpClient httpClient = new HttpClient();

        private static readonly Queue<Task> pendingRequests = new Queue<Task>();
        private static bool isProcessingRequests = false;

        public static async Task<ResponseType> Post<ContentType, ResponseType>(
            string url,
            ContentType content,
            Dictionary<string, string>? headers = null)
        {
            string jsonData = JsonConvert.SerializeObject(content);
            return await EnqueueRequest<ResponseType>(() =>
            {
                var request = new HttpRequestMessage(HttpMethod.Post, url)
                {
                    Content = new StringContent(jsonData, Encoding.UTF8, "application/json")
                };
                AddHeaders(request, headers);
                return request;
            });
        }

        private static void AddHeaders(HttpRequestMessage request, Dictionary<string, string>? headers)
        {
            if (headers != null)
            {
                foreach (var header in headers)
                {
                    request.Headers.TryAddWithoutValidation(header.Key, header.Value);
                }
            }
        }

        private static async Task<T> EnqueueRequest<T>(Func<HttpRequestMessage> requestFactory)
        {
            var taskCompletionSource = new TaskCompletionSource<T>();

            var _ = EnqueueRequestTask(ExecuteRequest(requestFactory, taskCompletionSource));

            return await taskCompletionSource.Task;
        }

        private static async Task EnqueueRequestTask(Task requestTask)
        {
            lock (pendingRequests)
            {
                pendingRequests.Enqueue(requestTask);
            }

            if (isProcessingRequests) return;

            isProcessingRequests = true;
            while (true)
            {
                Task? request = null;

                lock (pendingRequests)
                {
                    if (pendingRequests.Count == 0)
                    {
                        isProcessingRequests = false;
                        break;
                    }

                    request = pendingRequests.Dequeue();
                }

                await request;
            }
        }

        private static async Task ExecuteRequest<T>(
            Func<HttpRequestMessage> requestFactory,
            TaskCompletionSource<T> taskCompletionSource)
        {
            int retries = 0;
            int delay = InitialDelay;

            while (true)
            {
                using (var request = requestFactory())
                {
                    string requestUrl = request.RequestUri != null ? request.RequestUri.ToString() : "null";
                    try
                    {
                        HttpResponseMessage response = await httpClient.SendAsync(request).ConfigureAwait(false);

                        if (!response.IsSuccessStatusCode)
                        {
                            var responseText = await response.Content.ReadAsStringAsync();

                            var exception = new WebRequestException(
                                $"Request failed with status code {(int)response.StatusCode}: {response.ReasonPhrase}",
                                response.StatusCode,
                                responseText);

                            // Was it a protocol error?
                            if (response.StatusCode != HttpStatusCode.RequestTimeout &&
                                response.StatusCode != HttpStatusCode.ServiceUnavailable &&
                                response.StatusCode != HttpStatusCode.GatewayTimeout)
                            {
                                Log.Error(LogGroup.Rest, exception, "Request failed: {requestUrl}", requestUrl);
                                taskCompletionSource.TrySetException(exception);
                                break;
                            }

                            if (retries < MaxRetries)
                            {
                                Log.Info(LogGroup.Rest, exception, "Retrying request ({retries}/{maxRetries}): {requestUrl}", retries, MaxRetries, requestUrl);
                                await Task.Delay(delay);

                                delay = (int)(delay * BackoffFactor);
                                retries++;

                                continue;
                            }

                            Log.Warn(LogGroup.Rest, exception, "Request timed out: {requestUrl}", requestUrl);
                            taskCompletionSource.TrySetException(exception);
                            break;
                        }

                        if (typeof(T) == typeof(byte[]))
                        {
                            byte[] data = await response.Content.ReadAsByteArrayAsync();
                            taskCompletionSource.TrySetResult((T)(object)data);
                            break;
                        }

                        string text = await response.Content.ReadAsStringAsync();

                        if (typeof(T) == typeof(string))
                        {
                            taskCompletionSource.TrySetResult((T)(object)text);
                            break;
                        }

                        try
                        {
                            // JsonConvert is slow :(
                            var result = await Task.Run(() => JsonConvert.DeserializeObject<T>(text));
                            taskCompletionSource.TrySetResult(result);
                            break;
                        }
                        catch (Exception exception)
                        {
                            taskCompletionSource.TrySetException(new ResponseDeserializationException(requestUrl, text, exception));
                            break;
                        }
                    }
                    catch (Exception exception)
                    {
                        Log.Error(LogGroup.Rest, exception, "Unexpected exception RestClient.ExecuteRequest");
                        taskCompletionSource.TrySetException(exception);
                        break;
                    }
                }
            }
        }
    }
}