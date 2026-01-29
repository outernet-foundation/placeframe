using System;
using System.Collections.Generic;

namespace Outernet.Shared
{
    public abstract class SyncedStateSystem
    {
        private Queue<(Action action, string caller, string filePath, int lineNumber)> actionQueue = new Queue<(Action, string, string, int)>();

        protected abstract void HandleException(Exception exception);

        public abstract Guid? ClientID { get; set; }
        public abstract uint Tick { get; protected set; }
        public abstract bool Deserializing { get; protected set; }

        public void EnqueueAction(
            Action action,
            string caller,
            string filePath,
            int lineNumber)
        {
            if (ClientID == null) throw new InvalidOperationException("Cannot enqueue actions when not connected");

            actionQueue.Enqueue((action, caller, filePath, lineNumber));
        }

        public void DrainActionQueue()
        {
            while (actionQueue.Count > 0)
            {
                var action = actionQueue.Dequeue();

                try
                {
                    action.action();
                }
                catch (Exception e)
                {
                    HandleException(
                        new Exception($"Action queued in {action.caller} at {action.filePath}:{action.lineNumber} threw an exception", e)
                    );
                }
            }
        }
    }
}