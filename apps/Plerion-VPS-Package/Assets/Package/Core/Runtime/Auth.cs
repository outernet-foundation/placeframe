using System;
using System.ComponentModel.DataAnnotations;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using PlerionApiClient.Client;
using UnityEngine;
using UnityEngine.Networking;

namespace Plerion.VPS
{
    internal static class Auth
    {
        [Serializable]
        public class TokenResponse
        {
            public string access_token;
            public int expires_in;
            public string refresh_token;
            public int refresh_expires_in;
            public string token_type;
            public string scope;
            public string error;
            public string error_description;
        }

        public static string url;
        public static string username;
        public static string password;

        public static readonly string client_id = "plerion-api";

        // current tokens
        public static TokenResponse tokenResponse;

        // expiry tracking
        private static DateTimeOffset _accessTokenExpiresAt;
        private static DateTimeOffset _refreshTokenExpiresAt;
        private static readonly TimeSpan _skew = TimeSpan.FromSeconds(90); // safety window

        private static void StampExpiries(TokenResponse tr)
        {
            var now = DateTimeOffset.UtcNow;
            _accessTokenExpiresAt = now.AddSeconds(Math.Max(0, tr.expires_in));
            _refreshTokenExpiresAt = now.AddSeconds(Math.Max(0, tr.refresh_expires_in));
        }

        public static async UniTask Login()
        {
            var form = new WWWForm();
            form.AddField("grant_type", "password");
            form.AddField("client_id", client_id);
            form.AddField("username", username);
            form.AddField("password", password);

            var url = Auth.url;
            Debug.Log($"Logging in to {url} as {username}");
            using var req = UnityWebRequest.Post(url, form);
            var op = req.SendWebRequest();
            while (!op.isDone) await Task.Yield();

            if (req.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"Token error: {req.responseCode} {req.error} {req.downloadHandler.text}");
                throw new Exception("Login failed");
            }

            tokenResponse = JsonUtility.FromJson<TokenResponse>(req.downloadHandler.text);
            StampExpiries(tokenResponse);
        }

        public static async UniTask<string> GetOrRefreshToken()
        {
            // If access token is still good (with skew), use it
            if (tokenResponse != null &&
                !string.IsNullOrEmpty(tokenResponse.access_token) &&
                DateTimeOffset.UtcNow.Add(_skew) < _accessTokenExpiresAt)
            {
                return tokenResponse.access_token;
            }

            // If access token is stale but refresh token is still good, refresh
            if (tokenResponse != null &&
                !string.IsNullOrEmpty(tokenResponse.refresh_token) &&
                DateTimeOffset.UtcNow.Add(_skew) < _refreshTokenExpiresAt)
            {
                var form = new WWWForm();
                form.AddField("grant_type", "refresh_token");
                form.AddField("client_id", client_id);
                form.AddField("refresh_token", tokenResponse.refresh_token);

                using var req = UnityWebRequest.Post(url, form);
                var op = req.SendWebRequest();
                while (!op.isDone) await Task.Yield();

                var body = req.downloadHandler.text;

                if (req.result != UnityWebRequest.Result.Success)
                {
                    Debug.LogWarning($"Refresh failed: {req.responseCode} {req.error} {body}");
                }
                else
                {
                    var refreshed = JsonUtility.FromJson<TokenResponse>(body);

                    // Keycloak may rotate the refresh token—always replace with the new one.
                    tokenResponse = refreshed;
                    StampExpiries(tokenResponse);

                    if (!string.IsNullOrEmpty(tokenResponse.access_token))
                        return tokenResponse.access_token;
                }
            }

            // If refresh is invalid/expired or refresh request failed, do a full login
            await Login();
            return tokenResponse.access_token;
        }
    }
}