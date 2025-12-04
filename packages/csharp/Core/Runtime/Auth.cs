using Cysharp.Threading.Tasks;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Net.Http;

namespace Plerion.Core
{
    public static class Auth
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

        public static readonly string client_id = "plerion-api";

        public static Action<string> LogInfo;
        public static Action<string> LogWarning;
        public static Action<string> LogError;

        public static string url;
        public static string username;
        public static string password;
        public static TokenResponse tokenResponse;

        private static readonly HttpClient _httpClient = new HttpClient();
        private static DateTimeOffset _accessTokenExpiresAt;
        private static DateTimeOffset _refreshTokenExpiresAt;
        private static readonly TimeSpan _skew = TimeSpan.FromSeconds(90);

        private static void Info(string message)
            => (LogInfo ?? Console.WriteLine).Invoke(message);

        private static void Warn(string message)
            => (LogWarning ?? Console.WriteLine).Invoke(message);

        private static void Error(string message)
            => (LogError ?? Console.WriteLine).Invoke(message);

        private static void StampExpiries(TokenResponse tr)
        {
            var now = DateTimeOffset.UtcNow;
            _accessTokenExpiresAt = now.AddSeconds(Math.Max(0, tr.expires_in));
            _refreshTokenExpiresAt = now.AddSeconds(Math.Max(0, tr.refresh_expires_in));
        }

        public static async UniTask Login()
        {
            if (string.IsNullOrWhiteSpace(url))
                throw new InvalidOperationException("Auth.url must be set before calling Login()");
            if (string.IsNullOrWhiteSpace(username))
                throw new InvalidOperationException("Auth.username must be set before calling Login()");
            if (string.IsNullOrWhiteSpace(password))
                throw new InvalidOperationException("Auth.password must be set before calling Login()");

            Info($"[Auth] Logging in to {url} as {username}");

            HttpResponseMessage response;
            try
            {
                response = await _httpClient.PostAsync(
                    url,
                    new FormUrlEncodedContent(new Dictionary<string, string>
                    {
                        ["grant_type"] = "password",
                        ["client_id"] = client_id,
                        ["username"] = username,
                        ["password"] = password
                    })
                );
            }
            catch (Exception ex)
            {
                Error($"[Auth] Login failed with exception: {ex}");
                throw new Exception("Login failed", ex);
            }

            var body = await response.Content.ReadAsStringAsync();

            if (!response.IsSuccessStatusCode)
            {
                Error($"[Auth] Token error: {(int)response.StatusCode} {response.ReasonPhrase} {body}");
                throw new Exception("Login failed");
            }

            var parsed = JsonConvert.DeserializeObject<TokenResponse>(body);
            if (parsed == null)
                throw new Exception("Failed to deserialize token response");

            tokenResponse = parsed;
            StampExpiries(tokenResponse);
        }

        public static async UniTask<string> GetOrRefreshToken()
        {
            var nowWithSkew = DateTimeOffset.UtcNow.Add(_skew);

            // If access token is still good (with skew), use it
            if (tokenResponse != null &&
                !string.IsNullOrEmpty(tokenResponse.access_token) &&
                nowWithSkew < _accessTokenExpiresAt)
            {
                return tokenResponse.access_token;
            }

            // If access token is stale but refresh token is still good, refresh
            if (tokenResponse != null &&
                !string.IsNullOrEmpty(tokenResponse.refresh_token) &&
                nowWithSkew < _refreshTokenExpiresAt)
            {
                HttpResponseMessage response = null;
                try
                {
                    response = await _httpClient.PostAsync(
                        url,
                        new FormUrlEncodedContent(new Dictionary<string, string>
                        {
                            ["grant_type"] = "refresh_token",
                            ["client_id"] = client_id,
                            ["refresh_token"] = tokenResponse.refresh_token
                        })
                    );
                }
                catch (Exception ex)
                {
                    Error($"[Auth] Refresh failed with exception: {ex}");
                }

                if (response != null)
                {
                    var body = await response.Content.ReadAsStringAsync();

                    if (!response.IsSuccessStatusCode)
                    {
                        Warn($"[Auth] Refresh failed: {(int)response.StatusCode} {response.ReasonPhrase} {body}");
                    }
                    else
                    {
                        var refreshed = JsonConvert.DeserializeObject<TokenResponse>(body);

                        if (refreshed != null)
                        {
                            // Keycloak may rotate the refresh token—always replace with the new one.
                            tokenResponse = refreshed;
                            StampExpiries(tokenResponse);

                            if (!string.IsNullOrEmpty(tokenResponse.access_token))
                                return tokenResponse.access_token;
                        }
                        else
                        {
                            Warn("[Auth] Refresh failed: could not deserialize token response.");
                        }
                    }
                }
            }

            // If refresh is invalid/expired or refresh request failed, do a full login
            await Login();
            return tokenResponse.access_token;
        }
    }
}
