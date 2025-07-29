using System;
using System.Collections.Generic;
using System.Threading;
using Cysharp.Threading.Tasks;

#if UNITY_ANDROID && !UNITY_EDITOR
using System.Text.RegularExpressions;
using UnityEngine;
using UnityEngine.Android;
#endif

public static class ZedCaptureController
{
    static string jetsonIP = null;
    static readonly int port = 8000;
    static readonly float timeoutSec = 10f; // Timeout for Jetson discovery

    [Serializable]
    struct StartCaptureRequest
    {
        public string capture_name;
        public float capture_interval;
    }

    public static void Initialize()
    {
#if UNITY_ANDROID && !UNITY_EDITOR
        // — Get Activity ------------------------------------------------------
        var unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer");
        var activity = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity");

        // — Show tether settings panel (no privileged APIs required) ----------
        try
        {
            const string ACTION_TETHER_SETTINGS = "android.settings.TETHER_SETTINGS";
            using var intent = new AndroidJavaObject("android.content.Intent", ACTION_TETHER_SETTINGS);
            intent.Call<AndroidJavaObject>("addFlags", 0x10000000); // FLAG_ACTIVITY_NEW_TASK
            activity.Call("startActivity", intent);
        }
        catch (Exception ex)
        {
            Debug.LogWarning("Could not open tether settings: " + ex.Message);
        }

        // 2) Poll neighbour tables for ncm0 / rndis0 / usb0 ---------------------
        var deadline = Time.realtimeSinceStartup + timeoutSec;
        string address = null;
        var ipv4Rx = new Regex(@"^(?:\d{1,3}\.){3}\d{1,3}$");

        while (Time.realtimeSinceStartup < deadline && address == null)
        {
            foreach (var iface in new[] { "ncm0", "rndis0", "usb0" })
            {
                string output = RunShell($"/system/bin/ip neigh show dev {iface}");
                if (!string.IsNullOrEmpty(output)) Debug.Log($"[neigh {iface}] {output}");

                foreach (string token in output.Split(new[] { ' ', '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries))
                {
                    if (ipv4Rx.IsMatch(token)) { address = token; break; }
                }
                if (address != null) break;
            }
            if (address == null) Thread.Sleep(500);
        }

        if (address == null)
        {
            Debug.LogError("Jetson IP not found – timeout");
            return;
        }

        jetsonIP = $"http://{address}:{port}";

        // ── local shell helper (inline for easier step‑through) ───────────────
        string RunShell(string cmd)
        {
            try
            {
                Debug.Log($"$ {cmd}");

                var runtime = new AndroidJavaClass("java.lang.Runtime")
                            .CallStatic<AndroidJavaObject>("getRuntime");

                // Launch through a shell so PATH expansion works.
                using var proc = runtime.Call<AndroidJavaObject>(
                    "exec",
                    new object[] { new[] { "sh", "-c", cmd } });

                int exitCode = proc.Call<int>("waitFor");

                using var isr = new AndroidJavaObject(
                    "java.io.InputStreamReader",
                    proc.Call<AndroidJavaObject>("getInputStream"));
                using var br  = new AndroidJavaObject("java.io.BufferedReader", isr);

                var sb = new System.Text.StringBuilder();
                string line;
                while ((line = br.Call<string>("readLine")) != null)
                    sb.AppendLine(line);

                Debug.Log($"[shell exit {exitCode}]\n{sb}");
                if (exitCode == 127)
                    Debug.LogWarning("⚠  exit-code 127 — binary not found. Prepend /system/bin/ or check PATH.");

                return sb.ToString();
            }
            catch (Exception ex)
            {
                Debug.LogWarning("RunShell() error: " + ex);
                return string.Empty;
            }
        }
#else
        // Editor / iOS fallback: assume default Jetson gadget address
        jetsonIP = "http://192.168.55.1";
#endif
    }


    public static async UniTask<IEnumerable<string>> GetCaptures()
    {
        // return await RestClient.Get<string[]>($"{jetsonIP}/captures");
        return new List<string>(); // Placeholder for actual implementation
    }

    public static async UniTask<byte[]> GetCapture(string captureName)
    {
        // return await RestClient.Get<byte[]>($"{jetsonIP}/capture/{captureName}");
        return new byte[0]; // Placeholder for actual implementation
    }

    public static async UniTask StartCapture(
        CancellationToken cancellationToken,
        float captureInterval = 10)
    {
        // await RestClient.Post(
        //     $"{jetsonIP}/start",
        //     new StartCaptureRequest
        //     {
        //         capture_name = DateTime.UtcNow.ToString("yyyy-MM-dd_HH-mm-ss"),
        //         capture_interval = captureInterval
        //     });
    }

    public static async UniTask StopCapture(
        CancellationToken cancellationToken)
    {
        // await RestClient.Post($"{jetsonIP}/stop", new { });
    }
}
