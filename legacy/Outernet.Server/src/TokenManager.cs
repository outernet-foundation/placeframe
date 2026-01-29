// Vibe-code: Gemini 3
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.Configuration;
using Microsoft.IdentityModel.Tokens;

namespace Outernet.Server
{
    public class TokenManager
    {
        private readonly string _tokenUrl;
        private readonly string _clientId;
        private readonly string _privateKeyPath;
        private readonly HttpClient _httpClient;

        // Cache state
        private string? _accessToken;
        private DateTimeOffset _expiresAt = DateTimeOffset.MinValue;
        private readonly TimeSpan _skew = TimeSpan.FromSeconds(60);

        public TokenManager(IConfiguration configuration, HttpClient httpClient)
        {
            _tokenUrl = configuration["AUTH_TOKEN_URL"] ?? throw new ArgumentNullException("AUTH_TOKEN_URL");
            _clientId = configuration["AUTH_CLIENT_ID"] ?? throw new ArgumentNullException("AUTH_CLIENT_ID");
            _privateKeyPath = configuration["PRIVATE_KEY_PATH"] ?? throw new ArgumentNullException("PRIVATE_KEY_PATH");
            _httpClient = httpClient;
        }

        public async Task<string> GetTokenAsync(CancellationToken cancellationToken = default)
        {
            var now = DateTimeOffset.UtcNow;
            if (!string.IsNullOrEmpty(_accessToken) && now < (_expiresAt - _skew))
            {
                return _accessToken;
            }

            var clientAssertion = GenerateClientAssertion();
            var request = new FormUrlEncodedContent(
                new[]
                {
                    new KeyValuePair<string, string>("grant_type", "client_credentials"),
                    new KeyValuePair<string, string>(
                        "client_assertion_type",
                        "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
                    ),
                    new KeyValuePair<string, string>("client_assertion", clientAssertion),
                }
            );

            var response = await _httpClient.PostAsync(_tokenUrl, request, cancellationToken);
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync(cancellationToken);
            var tokenResponse = JsonSerializer.Deserialize<TokenResponse>(json);

            if (tokenResponse == null)
                throw new Exception("Failed to deserialize token response");

            _accessToken = tokenResponse.AccessToken;
            _expiresAt = now.AddSeconds(tokenResponse.ExpiresIn);

            return _accessToken;
        }

        private string GenerateClientAssertion()
        {
            var pem = File.ReadAllText(_privateKeyPath);

            // Load the RSA key from PEM
            using var rsa = RSA.Create();
            rsa.ImportFromPem(pem);

            // We must duplicate the RSA parameters because the RsaSecurityKey
            // disposes the provider when it is disposed.
            var rsaKey = new RsaSecurityKey(rsa.ExportParameters(true));

            var handler = new JwtSecurityTokenHandler();
            var now = DateTime.UtcNow;

            var descriptor = new SecurityTokenDescriptor
            {
                Issuer = _clientId,
                Subject = new ClaimsIdentity(new[] { new Claim("sub", _clientId) }),
                Audience = _tokenUrl,
                Expires = now.AddMinutes(1),
                IssuedAt = now,
                SigningCredentials = new SigningCredentials(rsaKey, SecurityAlgorithms.RsaSha256),
            };

            // Add JTI manually if needed, though library often handles it.
            descriptor.Claims = new Dictionary<string, object> { { "jti", Guid.NewGuid().ToString() } };

            var token = handler.CreateToken(descriptor);
            return handler.WriteToken(token);
        }

        private class TokenResponse
        {
            [JsonPropertyName("access_token")]
            public string AccessToken { get; set; } = "";

            [JsonPropertyName("expires_in")]
            public int ExpiresIn { get; set; }
        }
    }
}
