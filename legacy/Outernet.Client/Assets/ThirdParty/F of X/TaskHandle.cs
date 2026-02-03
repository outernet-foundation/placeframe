using System;

using System.Threading;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;

namespace FofX
{
    public class TaskHandle
    {
        public static TaskHandle Complete = new TaskHandle(_ => UniTask.CompletedTask);

        public UniTask completionTask => _completionSource.Task;
        public UniTaskStatus status { get; private set; }

        public bool pending => status == UniTaskStatus.Pending;
        public bool succeeded => status == UniTaskStatus.Succeeded;
        public bool faulted => status == UniTaskStatus.Faulted;
        public bool canceled => status == UniTaskStatus.Canceled;
        public bool complete => succeeded || faulted || canceled;

        private Func<CancellationToken, UniTask> _getTask;
        private UniTaskCompletionSource _completionSource = new UniTaskCompletionSource();
        private CancellationTokenSource _tokenSource = new CancellationTokenSource();

        private TaskHandle(Func<CancellationToken, UniTask> getTask)
        {
            _getTask = getTask;
            Execute();
        }

        private async void Execute()
        {
            try
            {
                await _getTask(_tokenSource.Token);
                status = UniTaskStatus.Succeeded;
                _completionSource.TrySetResult();
            }
            catch (Exception exc)
            {
                if (exc is TaskCanceledException)
                {
                    status = UniTaskStatus.Canceled;
                    _completionSource.TrySetCanceled();
                }
                else
                {
                    status = UniTaskStatus.Faulted;
                    _completionSource.TrySetException(exc);
                    throw;
                }
            }
            finally
            {
                if (_tokenSource != null)
                {
                    _tokenSource.Dispose();
                    _tokenSource = null;
                }
            }
        }

        public void Cancel()
        {
            if (_tokenSource == null)
                return;

            var source = _tokenSource;
            _tokenSource = null;
            source.Cancel();
            source.Dispose();
        }

        public static TaskHandle Execute(Func<CancellationToken, UniTask> getTask)
        {
            var wrapper = new TaskHandle(getTask);
            return wrapper;
        }
    }

    public class TaskHandle<T>
    {
        public TaskHandle<T> Complete => Execute(_ => new UniTask<T>(default));
        public UniTask<T> completionTask => _completionSource.Task;
        public UniTaskStatus status { get; private set; }

        public bool pending => status == UniTaskStatus.Pending;
        public bool succeeded => status == UniTaskStatus.Succeeded;
        public bool faulted => status == UniTaskStatus.Faulted;
        public bool canceled => status == UniTaskStatus.Canceled;
        public bool complete => succeeded || faulted || canceled;

        private Func<CancellationToken, UniTask<T>> _getTask;
        private UniTaskCompletionSource<T> _completionSource = new UniTaskCompletionSource<T>();
        private CancellationTokenSource _tokenSource = new CancellationTokenSource();

        private TaskHandle(Func<CancellationToken, UniTask<T>> getTask)
        {
            _getTask = getTask;
            Execute();
        }

        private async void Execute()
        {
            try
            {
                var result = await _getTask(_tokenSource.Token);
                status = UniTaskStatus.Succeeded;
                _completionSource.TrySetResult(result);
            }
            catch (Exception exc)
            {
                if (exc is TaskCanceledException)
                {
                    status = UniTaskStatus.Canceled;
                    _completionSource.TrySetCanceled();
                }
                else
                {
                    status = UniTaskStatus.Faulted;
                    _completionSource.TrySetException(exc);
                }
            }
            finally
            {
                if (_tokenSource != null)
                {
                    _tokenSource.Dispose();
                    _tokenSource = null;
                }
            }
        }

        public void Cancel()
        {
            if (_tokenSource == null)
                return;

            var source = _tokenSource;
            _tokenSource = null;
            source.Cancel();
            source.Dispose();
        }

        public static TaskHandle<T> Execute(Func<CancellationToken, UniTask<T>> getTask)
        {
            var wrapper = new TaskHandle<T>(getTask);
            return wrapper;
        }
    }
}