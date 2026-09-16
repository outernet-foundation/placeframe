using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using Cysharp.Threading.Tasks;
using Newtonsoft.Json;

namespace Placeframe.Auth
{
    public class TokenServerHttpHandler : DelegatingHandler
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

        public string authTokenURL { get; private set; }
        public string authAudience { get; private set; }
        public string username { get; private set; }
        public string password { get; private set; }
        public TokenResponse tokenResponse;

        private HttpClient _httpClient;
        private DateTimeOffset _accessTokenExpiresAt;
        private DateTimeOffset _refreshTokenExpiresAt;
        private readonly TimeSpan _skew = TimeSpan.FromSeconds(60);

        private Action<string> _logInfo;
        private Action<string> _logWarning;
        private Action<string> _logError;

        private void StampExpiries(TokenResponse tr)
        {
            var now = DateTimeOffset.UtcNow;
            _accessTokenExpiresAt = now.AddSeconds(Math.Max(0, tr.expires_in));
            _refreshTokenExpiresAt = now.AddSeconds(Math.Max(0, tr.refresh_expires_in));
        }

        public TokenServerHttpHandler(
            Action<string> logInfo = default,
            Action<string> logWarning = default,
            Action<string> logError = default,
            HttpMessageHandler httpMessageHandler = default
        )
        {
            _logInfo = logInfo ?? Console.WriteLine;
            _logWarning = logWarning ?? Console.WriteLine;
            _logError = logError ?? Console.WriteLine;
            _httpClient = new HttpClient(httpMessageHandler ?? new HttpClientHandler());
        }

        public async UniTask Login(string authTokenUrl, string clientId, string username, string password)
        {
            authTokenURL = authTokenUrl;
            authAudience = clientId;
            this.username = username;
            this.password = password;
            await LoginInternal();
        }

        private async UniTask LoginInternal()
        {
            _logInfo($"[Auth] Logging in to {authTokenURL} as {username}");

            HttpResponseMessage response;
            try
            {
                response = await _httpClient.PostAsync(
                    authTokenURL,
                    new FormUrlEncodedContent(
                        new Dictionary<string, string>
                        {
                            ["grant_type"] = "password",
                            ["client_id"] = authAudience,
                            ["username"] = username,
                            ["password"] = password,
                            ["scope"] = "openid",
                        }
                    )
                );
            }
            catch (Exception ex)
            {
                _logInfo($"[Auth] Login failed: {ex.Message}");
                throw new Exception("Login failed", ex);
            }

            var body = await response.Content.ReadAsStringAsync();

            if (!response.IsSuccessStatusCode)
            {
                var message = $"Login failed: {(int)response.StatusCode} {response.ReasonPhrase} {body}";
                if ((int)response.StatusCode >= 500)
                    _logError($"[Auth] {message}");
                else
                    _logInfo($"[Auth] {message}");
                throw new Exception(message);
            }

            var parsed = JsonConvert.DeserializeObject<TokenResponse>(body);
            if (parsed == null)
                throw new Exception("Failed to deserialize token response");

            tokenResponse = parsed;
            StampExpiries(tokenResponse);
        }

        public async UniTask<string> GetOrRefreshToken()
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
                        authTokenURL,
                        new FormUrlEncodedContent(
                            new Dictionary<string, string>
                            {
                                ["grant_type"] = "refresh_token",
                                ["client_id"] = authAudience,
                                ["refresh_token"] = tokenResponse.refresh_token,
                                ["scope"] = "openid",
                            }
                        )
                    );
                }
                catch (Exception ex)
                {
                    _logError($"[Auth] Refresh failed with exception: {ex}");
                }

                if (response != null)
                {
                    var body = await response.Content.ReadAsStringAsync();

                    if (!response.IsSuccessStatusCode)
                    {
                        _logWarning($"[Auth] Refresh failed: {(int)response.StatusCode} {response.ReasonPhrase} {body}");
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
                            _logWarning("[Auth] Refresh failed: could not deserialize token response.");
                        }
                    }
                }
            }

            // If refresh is invalid/expired or refresh request failed, do a full login
            await LoginInternal();
            return tokenResponse.access_token;
        }

        protected override async System.Threading.Tasks.Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken
        )
        {
            var token = await GetOrRefreshToken();
            request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
            return await base.SendAsync(request, cancellationToken);
        }
    }
}
