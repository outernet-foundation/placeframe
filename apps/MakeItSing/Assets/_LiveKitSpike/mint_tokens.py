import os
import time

import jwt


def mint(identity: str, api_key: str, api_secret: str, room: str = "smoke") -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "iss": api_key,
            "sub": identity,
            "iat": now,
            "exp": now + 24 * 3600,
            "video": {
                "room": room,
                "roomJoin": True,
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True,
            },
        },
        api_secret,
        algorithm="HS256",
    )


def main() -> None:
    api_key = os.environ.get("LIVEKIT_API_KEY", "devkey")
    api_secret = os.environ.get(
        "LIVEKIT_API_SECRET",
        "devsecretmustbeatleast32charslongforhmacsha256",
    )
    for identity in ("ml2", "mobile", "bot"):
        print(f"{identity:8s} {mint(identity, api_key, api_secret)}")


if __name__ == "__main__":
    main()
