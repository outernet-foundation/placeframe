using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

using UnityEngine;
using UnityEngine.Networking;

using Cysharp.Threading.Tasks;

using FofX;

namespace Outernet.MapRegistrationTool
{
    public class ContentManager : MonoBehaviour
    {
        private interface IContentLoader : IDisposable
        {
            public string address { get; }
        }

        private class ContentLoader<T> : IContentLoader
        {
            public string address { get; private set; }

            public int liveHandleCount => _liveHandles.Count;
            public IEnumerable<IContentHandle<T>> liveHandles => _liveHandles;

            public event Action<ContentLoader<T>> onAllHandlesReleased;

            private Action<T> _offloadContent;
            private TaskHandle<T> _taskHandle;
            private HashSet<IContentHandle<T>> _liveHandles = new HashSet<IContentHandle<T>>();

            public ContentLoader(string address, Func<string, CancellationToken, UniTask<T>> taskGenerator, Action<T> offloadContent = null)
            {
                this.address = address;
                _offloadContent = offloadContent;
                _taskHandle = TaskHandle<T>.Execute(token => taskGenerator(address, token));
            }

            private async UniTask ResolveHandle(ContentHandle<T> handle)
            {
                T result;

                try
                {
                    result = await _taskHandle.completionTask;
                }
                catch (Exception exc)
                {
                    await UniTask.SwitchToMainThread();

                    if (handle.done)
                        return;

                    if (exc is TaskCanceledException)
                    {
                        handle.TrySetCanceled();
                        return;
                    }

                    handle.TrySetException(exc);
                    return;
                }

                await UniTask.SwitchToMainThread();

                if (handle.done)
                    return;

                handle.TrySetResult(result);
            }

            public ContentHandle<T> GetHandle()
            {
                var handle = new ContentHandle<T>(address, x =>
                {
                    _liveHandles.Remove(x);

                    if (_liveHandles.Count == 0)
                        onAllHandlesReleased?.Invoke(this);
                });

                _liveHandles.Add(handle);
                ResolveHandle(handle).Forget();

                return handle;
            }

            public void Dispose()
            {
                if (_taskHandle.succeeded)
                    _offloadContent?.Invoke(_taskHandle.completionTask.GetAwaiter().GetResult());

                if (!_taskHandle.complete)
                    _taskHandle.Cancel();
            }
        }

        private class ContentHandle<T> : IContentHandle<T>
        {
            public string address { get; private set; }
            public T result { get; private set; }
            public Exception exception { get; private set; }

            public bool complete { get; private set; }
            public bool faulted { get; private set; }
            public bool canceled { get; private set; }
            public bool done => complete || faulted || canceled;

            private Action<ContentHandle<T>> _onRelease;
            private bool _disposed;

            private List<Action<T>> _onCompleteHandlers = new List<Action<T>>();
            private List<Action> _onCancelHandlers = new List<Action>();
            private List<Action<Exception>> _onExceptionHandlers = new List<Action<Exception>>();
            private List<Action> _onDoneHandlers = new List<Action>();

            public ContentHandle(string address, Action<ContentHandle<T>> onRelease)
            {
                this.address = address;
                _onRelease = onRelease;
            }

            public void TrySetResult(T result)
            {
                if (done)
                    return;

                this.result = result;
                complete = true;

                foreach (var handler in _onCompleteHandlers)
                {
                    try
                    {
                        handler.Invoke(result);
                    }
                    catch (Exception exc)
                    {
                        Log.Error("Encountered an error while notifying ContentHandle.OnComplete: {address}", exc, address);
                    }
                }

                NotifyDoneHandlers();
            }

            public void TrySetCanceled()
            {
                if (done)
                    return;

                canceled = true;

                foreach (var handler in _onCancelHandlers)
                {
                    try
                    {
                        handler.Invoke();
                    }
                    catch (Exception exc)
                    {
                        Log.Error("Encountered an error while notifying ContentHandle.OnCancel: {address}", exc, address);
                    }
                }

                NotifyDoneHandlers();
            }

            public void TrySetException(Exception exception)
            {
                if (done)
                    return;

                this.exception = exception;
                faulted = true;

                foreach (var handler in _onExceptionHandlers)
                {
                    try
                    {
                        handler.Invoke(exception);
                    }
                    catch (Exception exc)
                    {
                        Log.Error("Encountered an error while notifying ContentHandle.OnException: {address}", exc, address);
                    }
                }

                NotifyDoneHandlers();
            }

            private void NotifyDoneHandlers()
            {
                foreach (var handler in _onDoneHandlers)
                {
                    try
                    {
                        handler.Invoke();
                    }
                    catch (Exception exc)
                    {
                        Log.Error("Encountered an error while notifying ContentHandle.OnDone: {address}", exc, address);
                    }
                }
            }

            public IContentHandle<T> OnComplete(Action<T> onComplete)
            {
                if (complete)
                {
                    onComplete.Invoke(result);
                    return this;
                }

                _onCompleteHandlers.Add(onComplete);
                return this;
            }

            public IContentHandle<T> OnCancel(Action onCancel)
            {
                if (canceled)
                {
                    onCancel.Invoke();
                    return this;
                }

                _onCancelHandlers.Add(onCancel);
                return this;
            }

            public IContentHandle<T> OnException(Action<Exception> onException)
            {
                if (faulted)
                {
                    onException.Invoke(exception);
                    return this;
                }

                _onExceptionHandlers.Add(onException);
                return this;
            }

            public IContentHandle<T> OnDone(Action onDone)
            {
                if (done)
                {
                    onDone.Invoke();
                    return this;
                }

                _onDoneHandlers.Add(onDone);
                return this;
            }

            public void Dispose()
            {
                if (_disposed)
                    return;

                if (!done)
                    TrySetCanceled();

                _disposed = true;
                _onRelease?.Invoke(this);
            }
        }

        private static Dictionary<string, IContentLoader> _contentLoaders =
            new Dictionary<string, IContentLoader>();

        private static async UniTask<T> LoadWebRequest<T>(UnityWebRequest request, Func<UnityWebRequest, T> parseResponse, CancellationToken token = default)
        {
            try
            {
                Log.Trace(LogGroup.ContentManagement, "Loading from web or local file system. Address: {address}", request.url);
                await request.SendWebRequest().WithCancellation(token);

                Log.Trace(LogGroup.ContentManagement, "Load complete, starting parse. Address: {address}", request.url);
                T result = parseResponse(request);

                Log.Trace(LogGroup.ContentManagement, "Parse complete. Address: {address}", request.url);
                return result;
            }
            catch (Exception exc)
            {
                throw new Exception($"Encountered an error while loading.\nAddress: {request.url}\nDownload Handler Error: {request.downloadHandler.error}", exc);
            }
            finally
            {
                request.Dispose();
            }
        }

        private static UniTask<T> LoadResource<T>(string address, CancellationToken token = default) where T : UnityEngine.Object
        {
            Log.Trace(LogGroup.ContentManagement, "Loading from resources. Address: {address}", address);
            return Resources.LoadAsync<T>(address)
                .WithCancellation(token)
                .ContinueWith(x => (T)x);
        }

        private static void HandleContentLoaderDereferenced(IContentLoader loader)
        {
            Log.Trace(LogGroup.ContentManagement, "Offloading dereferenced loader. Address: {address}", loader.address);
            _contentLoaders.Remove(loader.address);
            loader.Dispose();
        }

        public static IContentHandle<Texture2D> LoadTexture(string address)
        {
            if (_contentLoaders.TryGetValue(address, out var pendingLoader))
            {
                Log.Trace(LogGroup.ContentManagement, "Using existing loader. Address: {address}", address);
                return ((ContentLoader<Texture2D>)pendingLoader).GetHandle();
            }

            Log.Trace(LogGroup.ContentManagement, "Setting up new loader. Address: {address}", address);
            ContentLoader<Texture2D> loader = default;

            if (address.StartsWith("resources:///"))
            {
                loader = new ContentLoader<Texture2D>(
                    address.Substring(13),
                    LoadResource<Texture2D>
                );
            }
            else
            {
                loader = new ContentLoader<Texture2D>(
                    address,
                    (address, token) => LoadWebRequest(
                        UnityWebRequestTexture.GetTexture(address),
                        DownloadHandlerTexture.GetContent,
                        token
                    ),
                    Destroy
                );
            }

            _contentLoaders.Add(address, loader);

            loader.onAllHandlesReleased += HandleContentLoaderDereferenced;

            return loader.GetHandle();
        }

        public static IContentHandle<AudioClip> LoadAudio(string address, AudioType audioType)
        {
            if (_contentLoaders.TryGetValue(address, out var pendingLoader))
            {
                Log.Trace(LogGroup.ContentManagement, "Using existing loader. Address: {address}", address);
                return ((ContentLoader<AudioClip>)pendingLoader).GetHandle();
            }

            Log.Trace(LogGroup.ContentManagement, "Setting up new loader. Address: {address}", address);
            ContentLoader<AudioClip> loader = default;

            if (address.StartsWith("resources:///"))
            {
                loader = new ContentLoader<AudioClip>(
                    address.Substring(13),
                    LoadResource<AudioClip>
                );
            }
            else
            {
                loader = new ContentLoader<AudioClip>(
                    address,
                    (address, token) => LoadWebRequest(
                        UnityWebRequestMultimedia.GetAudioClip(address, audioType),
                        DownloadHandlerAudioClip.GetContent,
                        token
                    ),
                    Destroy
                );
            }

            _contentLoaders.Add(address, loader);

            loader.onAllHandlesReleased += HandleContentLoaderDereferenced;

            return loader.GetHandle();
        }
    }

    public interface IContentHandle<T> : IDisposable
    {
        T result { get; }
        Exception exception { get; }

        bool complete { get; }
        bool faulted { get; }
        bool canceled { get; }
        bool done { get; }

        IContentHandle<T> OnComplete(Action<T> onComplete);
        IContentHandle<T> OnCancel(Action onCancel);
        IContentHandle<T> OnException(Action<Exception> onException);
        IContentHandle<T> OnDone(Action onDone);
    }
}