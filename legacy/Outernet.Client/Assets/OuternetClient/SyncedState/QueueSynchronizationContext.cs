using System;
using System.Collections.Generic;
using System.Threading;

namespace Outernet.Client
{
    public sealed class QueueSynchronizationContext : SynchronizationContext
    {
        private readonly Queue<(SendOrPostCallback, object)> queue = new();
        private bool draining;

        public override void Post(SendOrPostCallback callback, object state)
        {
            if (callback == null) throw new ArgumentNullException(nameof(callback));
            if (!callback.Method.IsStatic) throw new InvalidOperationException("Callback must be a static method");

            queue.Enqueue((callback, state));

            if (draining) return;

            Drain();
        }

        private void Drain()
        {
            draining = true;

            while (queue.Count != 0)
            {
                try
                {
                    var (callback, state) = queue.Dequeue();
                    callback(state);
                }
                catch (Exception exception)
                {
                    Log.Error(LogGroup.SyncedStateClient, exception);
                }
            }

            draining = false;
        }
    }
}