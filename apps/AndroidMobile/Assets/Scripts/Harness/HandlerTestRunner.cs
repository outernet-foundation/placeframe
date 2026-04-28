using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

namespace Placeframe.Client
{
    public class HandlerTestRunner : MonoBehaviour
    {
        private const int TransportCellular = 0;
        private const int TransportWifi = 1;
        private const int TransportEthernet = 3;
        private const int TestPort = 18099;

        private TcpListener listener;
        private CancellationTokenSource serverCts;
        private int selectedTransport;

        void Start()
        {
            selectedTransport = SelectTransport();
            Debug.Log($"HARNESS_TRANSPORT: {TransportName(selectedTransport)}={selectedTransport}");
            StartServer();
            _ = RunTests();
        }

        private static int SelectTransport()
        {
#if !UNITY_EDITOR && UNITY_ANDROID
            using var activity = new AndroidJavaClass("com.unity3d.player.UnityPlayer")
                .GetStatic<AndroidJavaObject>("currentActivity");
            using var cm = activity.Call<AndroidJavaObject>("getSystemService", "connectivity");
            var networks = cm.Call<AndroidJavaObject[]>("getAllNetworks");
            bool foundEthernet = false;
            bool foundWifi = false;
            foreach (var n in networks)
            {
                try
                {
                    using var caps = cm.Call<AndroidJavaObject>("getNetworkCapabilities", n);
                    if (caps == null) continue;
                    if (caps.Call<bool>("hasTransport", TransportEthernet)) foundEthernet = true;
                    else if (caps.Call<bool>("hasTransport", TransportWifi)) foundWifi = true;
                }
                finally
                {
                    n.Dispose();
                }
            }
            if (foundEthernet) return TransportEthernet;
            if (foundWifi) return TransportWifi;
            return TransportCellular;
#else
            return TransportCellular;
#endif
        }

        private static string TransportName(int t) => t switch
        {
            TransportEthernet => "ETHERNET",
            TransportWifi => "WIFI",
            TransportCellular => "CELLULAR",
            _ => "UNKNOWN",
        };

        void OnDestroy()
        {
            serverCts?.Cancel();
            listener?.Stop();
        }

        private void StartServer()
        {
            listener = new TcpListener(IPAddress.Loopback, TestPort);
            listener.Start();
            serverCts = new CancellationTokenSource();
            _ = Task.Run(() => ServerLoop(serverCts.Token));
        }

        private async Task ServerLoop(CancellationToken ct)
        {
            while (!ct.IsCancellationRequested)
            {
                TcpClient client;
                try { client = await listener.AcceptTcpClientAsync(); }
                catch { return; }
                _ = Task.Run(() => HandleClient(client));
            }
        }

        private async Task HandleClient(TcpClient client)
        {
            try
            {
                using (client)
                using (var stream = client.GetStream())
                {
                    var (requestLine, headers, reqBody) = await ReadRequest(stream);
                    if (requestLine == null) return;

                    string path = requestLine.Split(' ')[1];
                    string method = requestLine.Split(' ')[0];

                    if (path.StartsWith("/error"))
                    {
                        await WriteResponse(stream, 400, "bad request body");
                    }
                    else if (path.StartsWith("/big"))
                    {
                        int size = int.Parse(path.Split('=')[1]);
                        byte[] big = new byte[size];
                        for (int i = 0; i < size; i++) big[i] = (byte)(i & 0xff);
                        await WriteResponseRaw(stream, 200, "application/octet-stream", big);
                    }
                    else if (path.StartsWith("/slow"))
                    {
                        byte[] header = Encoding.ASCII.GetBytes(
                            "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 10\r\nConnection: close\r\n\r\n");
                        await stream.WriteAsync(header, 0, header.Length);
                        await stream.FlushAsync();
                        for (int i = 0; i < 10; i++)
                        {
                            byte[] one = new byte[] { (byte)'x' };
                            await stream.WriteAsync(one, 0, 1);
                            await stream.FlushAsync();
                            await Task.Delay(200);
                        }
                    }
                    else if (path.StartsWith("/echo-body"))
                    {
                        await WriteResponse(stream, 200, $"BODY={reqBody}");
                    }
                    else
                    {
                        await WriteResponse(stream, 200, $"ECHO {method} {path} BODY={reqBody}");
                    }
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"HARNESS server handler exception: {e.Message}");
            }
        }

        private static async Task<(string requestLine, System.Collections.Generic.Dictionary<string, string> headers, string body)> ReadRequest(NetworkStream stream)
        {
            var reader = new StreamReader(stream, Encoding.ASCII, false, 1024, leaveOpen: true);
            string requestLine = await reader.ReadLineAsync();
            if (string.IsNullOrEmpty(requestLine)) return (null, null, null);

            var headers = new System.Collections.Generic.Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            string line;
            while (!string.IsNullOrEmpty(line = await reader.ReadLineAsync()))
            {
                int colon = line.IndexOf(':');
                if (colon > 0) headers[line.Substring(0, colon).Trim()] = line.Substring(colon + 1).Trim();
            }

            string body = "";
            if (headers.TryGetValue("Content-Length", out string cl) && int.TryParse(cl, out int len) && len > 0)
            {
                char[] buf = new char[len];
                int total = 0;
                while (total < len)
                {
                    int n = await reader.ReadAsync(buf, total, len - total);
                    if (n <= 0) break;
                    total += n;
                }
                body = new string(buf, 0, total);
            }
            return (requestLine, headers, body);
        }

        private static async Task WriteResponse(NetworkStream stream, int status, string body)
        {
            byte[] bodyBytes = Encoding.UTF8.GetBytes(body);
            await WriteResponseRaw(stream, status, "text/plain", bodyBytes);
        }

        private static async Task WriteResponseRaw(NetworkStream stream, int status, string contentType, byte[] bodyBytes)
        {
            string statusText = status == 200 ? "OK" : status == 400 ? "Bad Request" : "Status";
            string header =
                $"HTTP/1.1 {status} {statusText}\r\n" +
                $"Content-Type: {contentType}\r\n" +
                $"Content-Length: {bodyBytes.Length}\r\n" +
                "Connection: close\r\n" +
                "\r\n";
            byte[] h = Encoding.ASCII.GetBytes(header);
            await stream.WriteAsync(h, 0, h.Length);
            await stream.WriteAsync(bodyBytes, 0, bodyBytes.Length);
            await stream.FlushAsync();
        }

        private async Task RunTests()
        {
            await Task.Delay(500);
            Debug.Log("HARNESS_BEGIN");

            await Scenario("GET_basic", async handler =>
            {
                using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(10) };
                var response = await client.GetAsync($"http://127.0.0.1:{TestPort}/ping");
                string body = await response.Content.ReadAsStringAsync();
                Expect(response.IsSuccessStatusCode, $"status {(int)response.StatusCode}");
                Expect(body.Contains("GET /ping"), $"unexpected body: {body}");
            });

            await Scenario("POST_body", async handler =>
            {
                using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(10) };
                var content = new StringContent("{\"hello\":\"world\"}", Encoding.UTF8, "application/json");
                var response = await client.PostAsync($"http://127.0.0.1:{TestPort}/echo-body", content);
                string body = await response.Content.ReadAsStringAsync();
                Expect(response.IsSuccessStatusCode, $"status {(int)response.StatusCode}");
                Expect(body.Contains("hello"), $"body missing payload: {body}");
            });

            await Scenario("DELETE_method", async handler =>
            {
                using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(10) };
                var response = await client.DeleteAsync($"http://127.0.0.1:{TestPort}/item/42");
                string body = await response.Content.ReadAsStringAsync();
                Expect(response.IsSuccessStatusCode, $"status {(int)response.StatusCode}");
                Expect(body.Contains("DELETE /item/42"), $"unexpected body: {body}");
            });

            await Scenario("large_streaming", async handler =>
            {
                const int size = 2 * 1024 * 1024;
                using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(30) };
                using var response = await client.GetAsync(
                    $"http://127.0.0.1:{TestPort}/big?size={size}",
                    HttpCompletionOption.ResponseHeadersRead);
                using var stream = await response.Content.ReadAsStreamAsync();
                byte[] buf = new byte[64 * 1024];
                int total = 0;
                int n;
                while ((n = await stream.ReadAsync(buf, 0, buf.Length)) > 0)
                {
                    for (int i = 0; i < n; i++) if (buf[i] != (byte)((total + i) & 0xff)) throw new Exception($"byte mismatch at {total + i}");
                    total += n;
                }
                Expect(total == size, $"got {total} bytes expected {size}");
            });

            await Scenario("error_4xx", async handler =>
            {
                using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(10) };
                var response = await client.GetAsync($"http://127.0.0.1:{TestPort}/error");
                string body = await response.Content.ReadAsStringAsync();
                Expect((int)response.StatusCode == 400, $"expected 400, got {(int)response.StatusCode}");
                Expect(body.Contains("bad request"), $"unexpected error body: {body}");
            });

            await Scenario("cancellation", async handler =>
            {
                using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(30) };
                using var cts = new CancellationTokenSource(TimeSpan.FromMilliseconds(400));
                try
                {
                    using var response = await client.GetAsync(
                        $"http://127.0.0.1:{TestPort}/slow",
                        HttpCompletionOption.ResponseHeadersRead,
                        cts.Token);
                    using var stream = await response.Content.ReadAsStreamAsync();
                    byte[] buf = new byte[1];
                    while (await stream.ReadAsync(buf, 0, 1, cts.Token) > 0) { }
                    throw new Exception("expected cancellation");
                }
                catch (OperationCanceledException)
                {
                    // expected
                }
                catch (IOException)
                {
                    // also acceptable — Java throws IOException on interrupted read
                }
            });

            await Scenario("concurrency", async handler =>
            {
                using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(15) };
                var tasks = new Task<string>[5];
                for (int i = 0; i < tasks.Length; i++)
                {
                    int idx = i;
                    tasks[i] = Task.Run(async () =>
                    {
                        var response = await client.GetAsync($"http://127.0.0.1:{TestPort}/ping?i={idx}");
                        return await response.Content.ReadAsStringAsync();
                    });
                }
                string[] bodies = await Task.WhenAll(tasks);
                for (int i = 0; i < bodies.Length; i++)
                    Expect(bodies[i].Contains($"/ping?i={i}"), $"req {i} got {bodies[i]}");
            });

            Debug.Log("HARNESS_DONE");
        }

        private static void Expect(bool condition, string message)
        {
            if (!condition) throw new Exception(message);
        }

        private async Task Scenario(string name, Func<HttpMessageHandler, Task> action)
        {
            try
            {
                var handler = new AndroidBoundHttpHandler(new[] { selectedTransport });
                await action(handler);
                Debug.Log($"HARNESS_PASS: {name}");
            }
            catch (Exception e)
            {
                Debug.Log($"HARNESS_FAIL: {name}: {e.GetType().Name}: {e.Message}");
            }
        }
    }
}
