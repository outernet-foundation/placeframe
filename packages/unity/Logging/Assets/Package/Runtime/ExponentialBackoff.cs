using System;

namespace Outernet.Logging
{
    // Schedules sleep durations for a retry loop. Three transitions:
    //   OnSuccess — work completed, no sleep, backoff resets to initial.
    //   OnIdle    — no work to do, brief idle sleep, backoff resets.
    //   OnFailure — work failed, sleep current backoff, then double up to max.
    // Caller reads SleepDuration before its next attempt.
    internal sealed class ExponentialBackoff
    {
        private readonly TimeSpan _initial;
        private readonly TimeSpan _idleSleep;
        private readonly TimeSpan _max;
        private TimeSpan _backoff;

        public TimeSpan SleepDuration { get; private set; }

        public ExponentialBackoff(TimeSpan initial, TimeSpan idleSleep, TimeSpan max)
        {
            _initial = initial;
            _idleSleep = idleSleep;
            _max = max;
            _backoff = initial;
            SleepDuration = TimeSpan.Zero;
        }

        public void OnSuccess()
        {
            SleepDuration = TimeSpan.Zero;
            _backoff = _initial;
        }

        public void OnIdle()
        {
            SleepDuration = _idleSleep;
            _backoff = _initial;
        }

        public void OnFailure()
        {
            SleepDuration = _backoff;
            _backoff = NextBackoff();
        }

        private TimeSpan NextBackoff() => TimeSpan.FromSeconds(Math.Min(_backoff.TotalSeconds * 2, _max.TotalSeconds));
    }
}
