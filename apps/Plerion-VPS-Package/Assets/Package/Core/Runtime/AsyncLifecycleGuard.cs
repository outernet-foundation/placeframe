using System;
using System.Threading;
using Cysharp.Threading.Tasks;

namespace Plerion.Core
{
    public class AsyncLifecycleGuard
    {
        public enum LifecycleState
        {
            Idle,
            Starting,
            Running,
            Stopping,
        }

        private readonly SemaphoreSlim _executionLock = new SemaphoreSlim(1, 1);
        private CancellationTokenSource _sessionCts;

        public LifecycleState State { get; private set; } = LifecycleState.Idle;
        public CancellationToken Token => _sessionCts?.Token ?? CancellationToken.None;

        public async UniTask StartAsync(
            Func<CancellationToken, UniTask> onStart,
            CancellationToken externalToken = default
        ) =>
            await StartAsync<bool>(
                async token =>
                {
                    await onStart(token);
                    return true;
                },
                externalToken
            );

        public async UniTask<T> StartAsync<T>(
            Func<CancellationToken, UniTask<T>> onStart,
            CancellationToken externalToken = default
        )
        {
            // If currently stopping, wait for it to finish
            while (State == LifecycleState.Stopping)
            {
                await UniTask.WaitUntil(() => State == LifecycleState.Idle, cancellationToken: externalToken);
            }

            // We must be Idle to start
            if (State != LifecycleState.Idle)
                throw new InvalidOperationException($"Cannot Start while in state {State}");

            State = LifecycleState.Starting;
            _sessionCts = CancellationTokenSource.CreateLinkedTokenSource(externalToken);

            // Acquire lock to guarantee any previous Stop() has fully completed cleanup
            await _executionLock.WaitAsync();

            try
            {
                // Check if Stop() was called while we were waiting for the lock
                if (_sessionCts.Token.IsCancellationRequested)
                    _sessionCts.Token.ThrowIfCancellationRequested();

                var result = await onStart(_sessionCts.Token);

                // If StopAsync() was called while onStart was running, the state will now be Stopping;
                // We cannot return success here because the system is shutting down, so treat this as a cancellation
                if (State != LifecycleState.Starting)
                    throw new OperationCanceledException(_sessionCts.Token);

                State = LifecycleState.Running;
                return result;
            }
            catch
            {
                // Only reset state if we still own it (Starting);
                // If state is Stopping, StopAsync() took ownership and will handle cleanup
                if (State == LifecycleState.Starting)
                {
                    State = LifecycleState.Idle;
                    _sessionCts?.Dispose();
                    _sessionCts = null;
                }
                throw;
            }
            finally
            {
                _executionLock.Release();
            }
        }

        public async UniTask StopAsync(Func<UniTask> onStop)
        {
            if (State != LifecycleState.Running && State != LifecycleState.Starting)
                throw new InvalidOperationException($"Cannot Stop while in state {State}");

            State = LifecycleState.Stopping;

            // Signal the active session to cancel; this forces StartAsync to abort any
            // awaiting tasks and release the execution lock immediately
            _sessionCts?.Cancel();

            // Wait for Start() to catch cancellation, cleanup, and release the lock
            await _executionLock.WaitAsync();

            try
            {
                await onStop();
            }
            finally
            {
                _sessionCts?.Dispose();
                _sessionCts = null;
                State = LifecycleState.Idle;
                _executionLock.Release();
            }
        }
    }
}
