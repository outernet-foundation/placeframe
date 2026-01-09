import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx
import jwt

SKEW_SECONDS = 60


@dataclass
class TokenManager:
    token_url: str
    client_id: str
    private_key_path: Path

    _access_token: Optional[str] = field(default=None, init=False)
    _expires_at: float = field(default=0.0, init=False)
    _private_key_bytes: bytes = field(init=False)

    def __post_init__(self):
        self._private_key_bytes = self.private_key_path.read_bytes()

    async def get_token(self):
        if self._access_token and time.time() < (self._expires_at - SKEW_SECONDS):
            return self._access_token

        now = int(time.time())

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                        "client_assertion": jwt.encode(
                            {
                                "iss": self.client_id,
                                "sub": self.client_id,
                                "aud": self.token_url,
                                "jti": str(uuid.uuid4()),
                                "exp": now + 60,
                                "iat": now,
                            },
                            self._private_key_bytes,
                            algorithm="RS256",
                        ),
                    },
                    timeout=10.0,
                )
                response.raise_for_status()

                data = response.json()
                self._expires_at = time.time() + int(data.get("expires_in", 300))
                self._access_token = data["access_token"]

                return self._access_token

            except httpx.HTTPError as e:
                print(f"[Auth] Failed to fetch token: {e}")
                raise
