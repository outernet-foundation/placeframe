#if UNITY_EDITOR
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using Cysharp.Threading.Tasks;

namespace Outernet.Client.Location
{
    // Adapted from: https://gist.github.com/lmcarreiro/cb67f6695b1ed78a9ce281bdcb51b4bc
    public class WifiScanner
    {
        public async UniTask<List<WifiAccessPoint>> ScanAsync()
        {
            var accessPoints = await GetSignalOfNetworksAsync();
            return accessPoints.ToList();
        }

        private static async UniTask<List<WifiAccessPoint>> GetSignalOfNetworksAsync()
        {
            await UniTask.SwitchToThreadPool();

            string result = await ExecuteProcessAsync(@"C:\Windows\System32\netsh.exe", "wlan show networks mode=bssid");

            var wifiAccessPoints = Regex
                .Split(result, @"[^B]SSID \d+")
                .Skip(1)
                .SelectMany(GetAccessPointFromNetwork)
                .ToList();

            await UniTask.SwitchToMainThread();

            Log.Info(LogGroup.Localizer, "Found {Count} nearby WiFi access points: {AccessPoints}",
                wifiAccessPoints.Count, string.Join(", ", wifiAccessPoints.Select(ap => ap.macAddress)));

            return wifiAccessPoints;
        }

        private static List<WifiAccessPoint> GetAccessPointFromNetwork(string network)
        {
            string withoutLineBreaks = Regex.Replace(network, @"[\r\n]+", " ").Trim();

            return Regex
                .Split(withoutLineBreaks, @"\s{4}BSSID \d+")
                .Skip(1)
                .Select(GetAccessPoint)
                .ToList();
        }

        private static WifiAccessPoint GetAccessPoint(string ap)
        {
            string withoutLineBreaks = Regex.Replace(ap, @"[\r\n]+", " ").Trim();
            string bssid = Regex.Replace(withoutLineBreaks, @"^:\s+([a-fA-F0-9]{2}(:[a-fA-F0-9]{2}){5}).*$", "$1").Trim();
            int signalStrength = int.Parse(Regex.Replace(withoutLineBreaks, @"^.*Signal\s+:\s+(\d+)%.*$", "$1").Trim());

            // https://stackoverflow.com/questions/56793886/get-wifi-access-apoint-signal-strength-in-windows#comment100158319_56797714
            signalStrength = (signalStrength / 2) - 100;

            return new WifiAccessPoint
            {
                macAddress = bssid,
                signalStrength = signalStrength,
            };
        }


        private static async UniTask<string> ExecuteProcessAsync(string cmd, string args = null)
        {
            var process = new Process()
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = cmd,
                    Arguments = args,
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    StandardOutputEncoding = Encoding.UTF8,
                }
            };

            process.Start();

            string result = await process.StandardOutput.ReadToEndAsync();

            process.WaitForExit();

            return result;
        }
    }
}
#endif
