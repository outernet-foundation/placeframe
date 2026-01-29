using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using Cysharp.Threading.Tasks;
using Newtonsoft.Json;

namespace Placeframe.Core
{
    public class AuthHttpHandler : DelegatingHandler
    {
        protected override async System.Threading.Tasks.Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken
        )
        {
            var token = await Auth.GetOrRefreshToken();
            request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
            return await base.SendAsync(request, cancellationToken);
        }
    }

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

        public static bool Initialized { get; private set; } = false;
        public static string AuthTokenURL { get; private set; }
        public static string AuthAudience { get; private set; }
        public static string Username { get; private set; }
        public static string Password { get; private set; }
        public static TokenResponse tokenResponse;

        private static readonly HttpClient _httpClient = new HttpClient();
        private static DateTimeOffset _accessTokenExpiresAt;
        private static DateTimeOffset _refreshTokenExpiresAt;
        private static readonly TimeSpan _skew = TimeSpan.FromSeconds(60);

        private static Action<string> LogInfo;
        private static Action<string> LogWarning;
        private static Action<string> LogError;

        private static void Info(string message) => (LogInfo ?? Console.WriteLine).Invoke(message);

        private static void Warn(string message) => (LogWarning ?? Console.WriteLine).Invoke(message);

        private static void Error(string message) => (LogError ?? Console.WriteLine).Invoke(message);

        private static void StampExpiries(TokenResponse tr)
        {
            var now = DateTimeOffset.UtcNow;
            _accessTokenExpiresAt = now.AddSeconds(Math.Max(0, tr.expires_in));
            _refreshTokenExpiresAt = now.AddSeconds(Math.Max(0, tr.refresh_expires_in));
        }

        public static void Initialize(
            string authTokenUrl,
            string authAudience,
            Action<string> logInfo,
            Action<string> logWarning,
            Action<string> logError
        )
        {
            AuthTokenURL = authTokenUrl;
            AuthAudience = authAudience;
            LogInfo = logInfo;
            LogWarning = logWarning;
            LogError = logError;
            Initialized = true;
        }

        public static async UniTask Login(string username, string password)
        {
            if (!Initialized)
                throw new InvalidOperationException("Auth.Initialize() must be called before calling Login()");

            Username = username;
            Password = password;
            await LoginInternal();
        }

        private static async UniTask LoginInternal()
        {
            Info($"[Auth] Logging in to {AuthTokenURL} as {Username}");

            HttpResponseMessage response;
            try
            {
                response = await _httpClient.PostAsync(
                    AuthTokenURL,
                    new FormUrlEncodedContent(
                        new Dictionary<string, string>
                        {
                            ["grant_type"] = "password",
                            ["client_id"] = AuthAudience,
                            ["username"] = Username,
                            ["password"] = Password,
                        }
                    )
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
            if (
                tokenResponse != null
                && !string.IsNullOrEmpty(tokenResponse.access_token)
                && nowWithSkew < _accessTokenExpiresAt
            )
            {
                return tokenResponse.access_token;
            }

            // If access token is stale but refresh token is still good, refresh
            if (
                tokenResponse != null
                && !string.IsNullOrEmpty(tokenResponse.refresh_token)
                && nowWithSkew < _refreshTokenExpiresAt
            )
            {
                HttpResponseMessage response = null;
                try
                {
                    response = await _httpClient.PostAsync(
                        AuthTokenURL,
                        new FormUrlEncodedContent(
                            new Dictionary<string, string>
                            {
                                ["grant_type"] = "refresh_token",
                                ["client_id"] = AuthAudience,
                                ["refresh_token"] = tokenResponse.refresh_token,
                            }
                        )
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
            await LoginInternal();
            return tokenResponse.access_token;
        }
    }
}
