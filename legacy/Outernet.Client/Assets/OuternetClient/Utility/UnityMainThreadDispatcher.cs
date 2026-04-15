using System;
using System.Collections.Concurrent;
using System.Threading.Tasks;

namespace Outernet.Client
{
    public static class UnityMainThreadDispatcher
    {
        private static readonly ConcurrentQueue<Action> _executionQueue = new ConcurrentQueue<Action>();

        public static void Enqueue(Action action)
        {
            if (action == null) throw new ArgumentNullException(nameof(action));
            _executionQueue.Enqueue(action);
        }

        public static Task Enqueue(Func<Task> task)
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

        public static void Flush()
        {
            while (_executionQueue.TryDequeue(out var action))
            {
                action?.Invoke();
            }
        }
    }
}
