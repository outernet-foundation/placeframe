from os import environ

from litestar import Litestar, get, post
from livekit.api import AccessToken, VideoGrants
from pydantic import BaseModel


class TokenRequest(BaseModel, extra="allow"):
    room_name: str
    participant_identity: str


class ConnectionDetails(BaseModel):
    server_url: str
    participant_token: str


@post("/connection-details", status_code=200)
async def issue_token(data: TokenRequest) -> ConnectionDetails:
    token = (
        AccessToken(environ["LIVEKIT_API_KEY"], environ["LIVEKIT_API_SECRET"])
        .with_identity(data.participant_identity)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=data.room_name,
                can_publish=False,
                can_publish_data=True,
                can_subscribe=True,
            )
        )
        .to_jwt()
    )

    return ConnectionDetails(
        server_url=environ["LIVEKIT_SERVER_URL"],
        participant_token=token,
    )


@get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


app = Litestar([issue_token, health])
