package io.placeframe.android;

import android.util.Log;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

// Tails the device logcat in a background thread and pushes each parsed line
// to a listener. Without android.permission.READ_LOGS the kernel only exposes
// lines from this process; with the permission, framework tags such as
// UsbHostManager / UsbDeviceManager become visible. The permission is
// signature|privileged|development, so it cannot be granted at install time
// but can be granted at runtime via:
//   adb shell pm grant <package> android.permission.READ_LOGS
public final class LogcatReader {
    public interface LineListener {
        void onLine(String level, String tag, int pid, String message);
    }

    private static final String LOG_TAG = "PlaceframeLogcat";
    private static final Object lock = new Object();
    private static Thread thread;
    private static Process process;

    private LogcatReader() {}

    public static void start(LineListener listener, String[] tagFilters) {
        synchronized (lock) {
            if (thread != null) return;
            String[] command = buildCommand(tagFilters);
            try {
                process = new ProcessBuilder(command).redirectErrorStream(true).start();
            } catch (IOException e) {
                Log.e(LOG_TAG, "logcat spawn failed", e);
                return;
            }
            Process held = process;
            thread = new Thread(() -> readLoop(held, listener), "placeframe-logcat-reader");
            thread.setDaemon(true);
            thread.start();
        }
    }

    public static void stop() {
        synchronized (lock) {
            if (process != null) process.destroy();
            process = null;
            if (thread != null) thread.interrupt();
            thread = null;
        }
    }

    private static String[] buildCommand(String[] tagFilters) {
        String[] base = {"logcat", "-v", "threadtime", "-T", "1", "-b", "all"};
        String[] command = new String[base.length + tagFilters.length];
        System.arraycopy(base, 0, command, 0, base.length);
        System.arraycopy(tagFilters, 0, command, base.length, tagFilters.length);
        return command;
    }

    private static void readLoop(Process process, LineListener listener) {
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while (!Thread.currentThread().isInterrupted() && (line = reader.readLine()) != null) {
                Parsed parsed = parse(line);
                if (parsed == null) continue;
                try {
                    listener.onLine(parsed.level, parsed.tag, parsed.pid, parsed.message);
                } catch (Throwable t) {
                    Log.e(LOG_TAG, "listener threw", t);
                }
            }
        } catch (IOException e) {
            Log.e(LOG_TAG, "logcat stream closed", e);
        }
    }

    // threadtime layout: "MM-DD HH:MM:SS.sss  PID  TID L TAG: message".
    // Hand-scan rather than split because the gap between date and PID is two
    // spaces and PID itself is right-aligned with variable padding.
    private static Parsed parse(String line) {
        if (line.startsWith("---")) return null;
        if (line.length() < 33) return null;
        int cursor = skipSpaces(line, 18);
        int pidEnd = cursor;
        while (pidEnd < line.length() && Character.isDigit(line.charAt(pidEnd))) pidEnd++;
        if (pidEnd == cursor) return null;
        int pid;
        try {
            pid = Integer.parseInt(line.substring(cursor, pidEnd));
        } catch (NumberFormatException e) {
            return null;
        }
        cursor = skipSpaces(line, pidEnd);
        while (cursor < line.length() && Character.isDigit(line.charAt(cursor))) cursor++;
        cursor = skipSpaces(line, cursor);
        if (cursor >= line.length()) return null;
        String level = String.valueOf(line.charAt(cursor));
        cursor = skipSpaces(line, cursor + 1);
        int tagEnd = line.indexOf(':', cursor);
        if (tagEnd < 0) return null;
        String tag = line.substring(cursor, tagEnd).trim();
        int messageStart = tagEnd + 1;
        if (messageStart < line.length() && line.charAt(messageStart) == ' ') messageStart++;
        return new Parsed(level, tag, pid, line.substring(messageStart));
    }

    private static int skipSpaces(String line, int cursor) {
        while (cursor < line.length() && line.charAt(cursor) == ' ') cursor++;
        return cursor;
    }

    private static final class Parsed {
        final String level;
        final String tag;
        final int pid;
        final String message;

        Parsed(String level, String tag, int pid, String message) {
            this.level = level;
            this.tag = tag;
            this.pid = pid;
            this.message = message;
        }
    }
}
