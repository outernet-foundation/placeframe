#if !UNITY_EDITOR && UNITY_ANDROID
using System;
using UnityEngine;

namespace Placeframe.Client
{
    // Bridges Android logcat into the existing Serilog -> Loki path so phone-side
    // diagnosis of USB / accessory events does not require an adb cable. The
    // androidlib's logcat process needs android.permission.READ_LOGS to see
    // tags from other processes (system_server's UsbHostManager etc.); without
    // it, the reader still runs but only surfaces this app's own lines.
    public static class LogcatRelay
    {
        // Tag whitelist. Scoped to USB / accessory framework tags because raw
        // logcat is too chatty to ship to Loki wholesale. The trailing *:S
        // silences every other tag at the logcat process boundary so unwanted
        // lines never cross the JNI boundary.
        private static readonly string[] TagFilters =
        {
            "UsbHostManager:V",
            "UsbDeviceManager:V",
            "UsbService:V",
            "UsbAccessory:V",
            "UsbHostController:V",
            "UsbPortManager:V",
            "UsbDescriptorParser:V",
            // OkHttp HTTP/2 frame trace, emitted by AoaAccessoryClient's static
            // initializer when it pipes okhttp3.internal.http2.Http2's JUL
            // logger to logcat under this tag.
            "OkHttpH2:V",
            "*:S",
        };

        private static AndroidJavaClass _readerCls;
        private static LineListenerProxy _proxy;

        public static void Start()
        {
            if (_proxy != null) return;
            try
            {
                _readerCls = new AndroidJavaClass("io.placeframe.android.LogcatReader");
                _proxy = new LineListenerProxy();
                _readerCls.CallStatic("start", _proxy, TagFilters);
            }
            catch (Exception exception)
            {
                Log.Error(LogGroup.Android, exception, "logcat relay start failed");
                _readerCls?.Dispose();
                _readerCls = null;
                _proxy = null;
            }
        }

        public static void Stop()
        {
            if (_readerCls == null) return;
            try
            {
                _readerCls.CallStatic("stop");
            }
            catch (Exception exception)
            {
                Log.Error(LogGroup.Android, exception, "logcat relay stop failed");
            }
            _readerCls.Dispose();
            _readerCls = null;
            _proxy = null;
        }

        // AndroidJavaProxy dispatches from the Java background reader thread.
        // Serilog and the LokiSink are thread-safe so no main-thread hop here.
        private sealed class LineListenerProxy : AndroidJavaProxy
        {
            public LineListenerProxy() : base("io.placeframe.android.LogcatReader$LineListener") {}

            public void onLine(string level, string tag, int pid, string message)
            {
                if (level == "E" || level == "F" || level == "A")
                    Log.Error(
                        LogGroup.Android,
                        "logcat tag={Tag} level={Level} pid={Pid} {Message}",
                        tag, level, pid, message
                    );
                else
                    Log.Info(
                        LogGroup.Android,
                        "logcat tag={Tag} level={Level} pid={Pid} {Message}",
                        tag, level, pid, message
                    );
            }
        }
    }
}
#endif
