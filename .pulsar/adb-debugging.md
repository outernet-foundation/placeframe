# ADB Device Debugging Workflow

How to get device logs from a phone or Magic Leap 2 into the Claude Code container for diagnosis.

## Setup

The device must be connected to the host via ADB. Logs are written to a file in the repo, which is mounted into the container.

## Per-diagnosis cycle

On the host:

```bash
# 1. Kill any previous logcat (if running)
kill %1

# 2. Clear device buffer and start fresh capture
adb logcat -c
> ./adb.log
adb logcat > ./adb.log &

# 3. Launch the app on the device, reproduce the issue

# 4. Stop capture
kill %1
```

Inside the container, Claude reads `adb.log` and greps for:
- `E Unity` — Unity errors and exceptions
- The app's package name (e.g. `com.outernet.captureapp`) — app-specific logs
- `CRASH`, `DEBUG`, `AndroidRuntime` — native crashes and unhandled exceptions
- `ActivityManager` — app lifecycle events

## Notes

- Use unfiltered logcat (no tag filters) for first-pass diagnosis — Unity crashes often surface in system-level tags, not just `Unity`.
- `adb.log` is gitignored. Don't commit it.
- `adb logcat -c` can be slow; skip it if it hangs — a few seconds of pre-launch noise is fine to filter past.
