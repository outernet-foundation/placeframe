using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX;
using UnityEngine;
using UnityEngine.Networking;

namespace Plerion.MakeItSing
{
    public record GetRoomResponse
    {
        public Guid id;
        public string name;
        public string version;
        public string demo_scene;
    }

    public record GetConfigResponse
    {
        public string id;
        public string device_id;
        public string app_version;
        public string device_type;
        public int? log_groups;
        public Outernet.Logging.LogLevel? log_level;
        public Outernet.Logging.LogLevel? stack_trace_level;
        public Outernet.Logging.LogLevel? notification_level;
        public string photon_project_id;
        public bool? login_automatically;
        public string domain;
        public string username;
        public string password;
        public Guid? room;
        public bool? disable_system_ui;
    }

    public record FileData
    {
        public string name;
        public string bucket_id;
        public Guid? owner;
        public Guid? id;
        public DateTime? updated_at;
        public DateTime? created_at;
        public DateTime? last_accessed_at;
    }

    [Serializable]
    public record GetFileDataRequest
    {
        public string prefix;
        public int limit;
        public int offset;
        public OrderParameters sort_by;
    }

    [Serializable]
    public record OrderParameters
    {
        public string column;
        public string order;
    }

    [Serializable]
    public record CreateRoomRequest
    {
        public string name;
        public string demo_scene;
        public string version;
    }

    [Serializable]
    public record CreateRoomResponse
    {
        public Guid id;
        public string name;
        public string demo_scene;
        public string version;
    }

    public static class SupabaseAPI
    {
        public static string ProjectId;
        public static string ApiKey;

        public static bool IsConfigured => !string.IsNullOrEmpty(ProjectId) && !string.IsNullOrEmpty(ApiKey);

        public static string BaseUrl => $"https://{ProjectId}.supabase.co";

        public static UniTask<CreateRoomResponse> CreateRoom(string roomName, string roomDemoScene, string version)
            => POST<CreateRoomResponse[]>($"/rest/v1/rooms", new CreateRoomRequest() { name = roomName, demo_scene = roomDemoScene, version = version }, new Dictionary<string, string>() { { "Prefer", "return=representation" } }).ContinueWith(x => x[0]);

        public static UniTask<GetRoomResponse[]> GetRooms(Guid id = default, string name = default, string version = default, string demoScene = default, CancellationToken cancellationToken = default)
        {
            var url = $"/rest/v1/rooms";

            List<string> queryParams = new List<string>();

            if (id != Guid.Empty)
                queryParams.Add($"id.eq.{id}");

            if (!string.IsNullOrEmpty(name))
                queryParams.Add($"name.eq.{name}");

            if (!string.IsNullOrEmpty(version))
                queryParams.Add($"version.eq.{version}");

            if (!string.IsNullOrEmpty(demoScene))
                queryParams.Add($"demoScene.eq.{demoScene}");

            if (queryParams != null)
                url += $"?and=({string.Join(",", queryParams)})";

            return GET<GetRoomResponse[]>(url);
        }

        // "/rest/v1/config?or=(" +
        //     $"and(deviceType.is.null,device.is.null)," +
        //     $"and(deviceType.eq.{deviceType},device.is.null)," +
        //     $"and(deviceType.eq.{deviceType},device.eq.{deviceId})" +
        // ")"

        public static UniTask<GetConfigResponse[]> GetConfigs()
            => GET<GetConfigResponse[]>($"/rest/v1/config");

        public async static UniTask<GetConfigResponse> GetPrioritizedConfig(string deviceId, string appVersion, string deviceType)
        {
            var configs = await GetConfigs();

            GetConfigResponse result = new GetConfigResponse();

            var prioritizedConfigs = configs
                .Where(x =>
                    (x.device_id == deviceId || x.device_id == null) &&
                    (x.app_version == appVersion || x.app_version == null) &&
                    (x.device_type == deviceType || x.device_type == null)
                )
                .OrderByDescending(x => x.device_id)
                .ThenByDescending(x => x.app_version)
                .ThenByDescending(x => x.device_type);

            foreach (var config in prioritizedConfigs)
            {
                result.log_groups = result.log_groups ?? config.log_groups;
                result.log_level = result.log_level ?? config.log_level;
                result.stack_trace_level = result.stack_trace_level ?? config.stack_trace_level;
                result.notification_level = result.notification_level ?? config.notification_level;
                result.photon_project_id = config.photon_project_id ?? config.photon_project_id;
                result.login_automatically = result.login_automatically ?? config.login_automatically;
                result.domain = result.domain ?? config.domain;
                result.username = result.username ?? config.username;
                result.password = result.password ?? config.password;
                result.room = result.room ?? config.room;
                result.disable_system_ui = result.disable_system_ui ?? config.disable_system_ui;
            }

            return result;
        }

        public static UniTask<AssetBundle> GetDemoSceneAssetBundle(string version, string platform, string assetBundle)
        {
            var subdomain = $"/storage/v1/object/demoScenes/{version}/{platform}/{assetBundle}";
            return GET(subdomain, new DownloadHandlerAssetBundle($"{BaseUrl}/{subdomain}", 0)).ContinueWith(x => DownloadHandlerAssetBundle.GetContent(x));
        }

        public static UniTask<UnityWebRequest> UploadDemoSceneAssetBundle(string name, string version, string platform, byte[] scene, bool allowOverwrite = false)
        {
            if (allowOverwrite)
            {
                return POST($"/storage/v1/object/demoScenes/{version}/{platform}/{name}", scene, "application/octet-stream", new Dictionary<string, string>() { { "x-upsert", "true" } });
            }
            else
            {
                return POST($"/storage/v1/object/demoScenes/{version}/{platform}/{name}", scene, "application/octet-stream");
            }
        }

        public static UniTask<FileData[]> GetDemoScenes(string version, string platform)
            => POST<FileData[]>($"/storage/v1/object/list/demoScenes", new GetFileDataRequest() { prefix = $"{version}/{platform}", limit = 1000, sort_by = new() { column = "name", order = "asc" } });

        private static UniTask<TResponse> POST<TResponse>(string subdomain, object body, Dictionary<string, string> additionalHeaders = default)
            => POST(subdomain, body, additionalHeaders).ContinueWith(x => Newtonsoft.Json.JsonConvert.DeserializeObject<TResponse>(x.downloadHandler.text));

        private static UniTask<UnityWebRequest> POST(string subdomain, object body, Dictionary<string, string> additionalHeaders = default)
            => POST(subdomain, System.Text.Encoding.UTF8.GetBytes(Newtonsoft.Json.JsonConvert.SerializeObject(body)), "application/json", additionalHeaders);

        private static UniTask<TResponse> POST<TResponse>(string subdomain, byte[] body, string contentType, Dictionary<string, string> additionalHeaders = default)
            => POST(subdomain, body, contentType, additionalHeaders).ContinueWith(x => Newtonsoft.Json.JsonConvert.DeserializeObject<TResponse>(x.downloadHandler.text));

        private static UniTask<TResponse> GET<TResponse>(string subdomain, Dictionary<string, string> additionalHeaders = default)
            => GET(subdomain, new DownloadHandlerBuffer(), additionalHeaders).ContinueWith(x => Newtonsoft.Json.JsonConvert.DeserializeObject<TResponse>(x.downloadHandler.text));

        private static UniTask<UnityWebRequest> GET(string subdomain, Dictionary<string, string> additionalHeaders = default)
            => GET(subdomain, new DownloadHandlerBuffer(), additionalHeaders);

        private static async UniTask<UnityWebRequest> GET(string subdomain, DownloadHandler downloadHandler, Dictionary<string, string> additionalHeaders = default)
        {
            if (!IsConfigured)
                throw new InvalidOperationException("SupabaseAPI is not configured (UnityEnv.supabaseProjectId / supabaseApiKey are empty). Gate the call site on SupabaseAPI.IsConfigured.");

            var url = BaseUrl;

            if (!string.IsNullOrEmpty(subdomain))
                url += subdomain;

            // Use UnityWebRequest.Put for a simple byte-stream upload
            UnityWebRequest request = new UnityWebRequest($"{url}", "GET");

            request.downloadHandler = downloadHandler;

            request.SetRequestHeader("Authorization", "Bearer " + ApiKey);
            request.SetRequestHeader("apikey", ApiKey);

            if (additionalHeaders != null)
            {
                foreach (var kvp in additionalHeaders)
                    request.SetRequestHeader(kvp.Key, kvp.Value);
            }

            await request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
                throw new Exception($"Upload failed: {request.error}\nResponse: {request.downloadHandler.text}");

            return request;
        }

        private static async UniTask<UnityWebRequest> POST(string subdomain, byte[] body, string contentType, Dictionary<string, string> additionalHeaders = default)
        {
            if (!IsConfigured)
                throw new InvalidOperationException("SupabaseAPI is not configured (UnityEnv.supabaseProjectId / supabaseApiKey are empty). Gate the call site on SupabaseAPI.IsConfigured.");

            // Use UnityWebRequest.Put for a simple byte-stream upload
            UnityWebRequest request = new UnityWebRequest($"{BaseUrl}/{subdomain}", "POST");
            request.uploadHandler = new UploadHandlerRaw(body);
            request.downloadHandler = new DownloadHandlerBuffer();

            request.SetRequestHeader("Authorization", "Bearer " + ApiKey);
            request.SetRequestHeader("apikey", ApiKey);
            request.SetRequestHeader("Content-Type", contentType);

            if (additionalHeaders != null)
            {
                foreach (var kvp in additionalHeaders)
                    request.SetRequestHeader(kvp.Key, kvp.Value);
            }

            await request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
                throw new Exception($"Upload failed: {request.error}\nResponse: {request.downloadHandler.text}");

            return request;
        }
    }
}