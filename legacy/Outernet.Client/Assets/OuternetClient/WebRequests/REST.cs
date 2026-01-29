using System;
using System.Collections.Generic;
using System.Text;
using Cysharp.Threading.Tasks;
using Newtonsoft.Json;
using UnityEngine.Networking;

namespace Outernet.Client
{
    public static class RestClient
    {
        private const int MaxRetries = 10;
        private const float BackoffFactor = 1.5f;
        private const int InitialDelay = 50; // milliseconds

        private static readonly Queue<UniTask> pendingRequests = new Queue<UniTask>();
        private static bool isProcessingRequests = false;

        public static async UniTask<T> Get<T>(string url, Dictionary<string, string> headers = null) =>
            await EnqueueRequest<T>(url, () => AddHeaders(UnityWebRequest.Get(url), headers));

        public static async UniTask<ResponseType> Post<ContentType, ResponseType>(string url, ContentType content, Dictionary<string, string> headers = null)
        {
            string jsonData = JsonConvert.SerializeObject(content);
            return await EnqueueRequest<ResponseType>(url, () => AddHeaders(UnityWebRequest.Post(url, jsonData, "application/json"), headers));
        }

        public static async UniTask<ResponseType> Patch<ContentType, ResponseType>(string url, ContentType content, Dictionary<string, string> headers = null)
        {
            return await EnqueueRequest<ResponseType>(url, () =>
            {
                UnityWebRequest webRequest = new UnityWebRequest(url, "PATCH");
                webRequest.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(content)));
                webRequest.downloadHandler = new DownloadHandlerBuffer();
                webRequest.SetRequestHeader("Content-Type", "application/json");
                return AddHeaders(webRequest, headers);
            });
        }

        public static async UniTask<string> Post<ContentType>(string url, ContentType content, Dictionary<string, string> headers = null) =>
            await Post<ContentType, string>(url, content, headers);

        public static async UniTask<string> Patch<ContentType>(string url, ContentType content, Dictionary<string, string> headers = null) =>
            await Patch<ContentType, string>(url, content, headers);

        public static async UniTask Delete(string url, Dictionary<string, string> headers = null) =>
            await EnqueueRequest(url, () => AddHeaders(UnityWebRequest.Delete(url), headers));

        private static UnityWebRequest AddHeaders(UnityWebRequest webRequest, Dictionary<string, string> headers)
        {
            if (headers != null)
            {
                foreach (var header in headers)
                {
                    webRequest.SetRequestHeader(header.Key, header.Value);
                }
            }

            return webRequest;
        }

        private static UniTask<T> EnqueueRequest<T>(string url, Func<UnityWebRequest> requestFactory)
        {
            var taskCompletionSource = new UniTaskCompletionSource<T>();

            EnqueueRequestTask(ExecuteRequest(url, requestFactory, taskCompletionSource)).Forget();

            return taskCompletionSource.Task;
        }

        private static UniTask EnqueueRequest(string url, Func<UnityWebRequest> requestFactory)
        {
            var taskCompletionSource = new UniTaskCompletionSource();

            EnqueueRequestTask(ExecuteRequest(url, requestFactory, taskCompletionSource)).Forget();

            return taskCompletionSource.Task;
        }

        private static async UniTask EnqueueRequestTask(UniTask requestTask)
        {
            lock (pendingRequests)
            {
                pendingRequests.Enqueue(requestTask);
            }

            if (isProcessingRequests) return;

            isProcessingRequests = true;
            while (true)
            {
                UniTask? request = null;

                lock (pendingRequests)
                {
                    if (pendingRequests.Count == 0)
                    {
                        isProcessingRequests = false;
                        break;
                    }

                    request = pendingRequests.Dequeue();
                }

                await request.Value;
            }
        }

        private static async UniTask ExecuteRequest(
            string url,
            Func<UnityWebRequest> requestFactory,
            UniTaskCompletionSource taskCompletionSource)
        {
            try
            {
                await SendRequestWithRetries(requestFactory);
                taskCompletionSource.TrySetResult();
            }
            catch (Exception exception)
            {
                Log.Error(LogGroup.Rest, exception, "Unexpected exception in RestClient.ExecuteRequest for url: {requestUrl}", url);
                taskCompletionSource.TrySetException(exception);
            }
        }

        private static async UniTask ExecuteRequest<T>(
            string url,
            Func<UnityWebRequest> requestFactory,
            UniTaskCompletionSource<T> taskCompletionSource)
        {
            try
            {
                var webRequest = await SendRequestWithRetries(requestFactory);

                if (typeof(T) == typeof(string))
                {
                    taskCompletionSource.TrySetResult((T)(object)webRequest.downloadHandler.text);
                    return;
                }

                if (typeof(T) == typeof(byte[]))
                {
                    taskCompletionSource.TrySetResult((T)(object)webRequest.downloadHandler.data);
                    return;
                }

                try
                {
                    var text = webRequest.downloadHandler.text;
                    // JsonConvert is slow :(
                    var result = await UniTask.RunOnThreadPool(() => JsonConvert.DeserializeObject<T>(text));
                    taskCompletionSource.TrySetResult(result);
                    return;
                }
                catch (Exception exception)
                {
                    taskCompletionSource.TrySetException(new ResponseDeserializationException(webRequest.url, webRequest.downloadHandler.text, exception));
                    return;
                }
            }
            catch (Exception exception)
            {
                Log.Error(LogGroup.Rest, exception, "Unexpected exception in RestClient.ExecuteRequest for url: {requestUrl}", url);
                taskCompletionSource.TrySetException(exception);
            }
        }

        private static async UniTask<UnityWebRequest> SendRequestWithRetries(Func<UnityWebRequest> requestFactory)
        {
            int retries = 0;
            int delay = InitialDelay;

            while (true)
            {
                var webRequest = requestFactory();
                try
                {
                    await webRequest.SendWebRequest();

                    if (webRequest.result == UnityWebRequest.Result.Success)
                        return webRequest;

                    var exception = new WebRequestException(
                        webRequest.result,
                        webRequest.error,
                        webRequest.responseCode,
                        webRequest.downloadHandler.text
                    );

                    webRequest.Dispose();

                    if (exception.UnityWebRequestResult == UnityWebRequest.Result.ProtocolError)
                        throw exception;

                    if (retries >= MaxRetries)
                        throw exception;

                    Log.Info(LogGroup.Rest, exception, "Retrying request ({retries}/{maxRetries}): {requestUrl}", retries, MaxRetries, webRequest.url);
                    await UniTask.Delay(delay);

                    delay = (int)(delay * BackoffFactor);
                    retries++;
                }
                catch (Exception exc)
                {
                    webRequest.Dispose();
                    throw exc;
                }
            }
        }
    }
}