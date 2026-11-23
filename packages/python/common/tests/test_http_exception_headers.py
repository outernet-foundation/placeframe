from __future__ import annotations

from litestar import Litestar, get
from litestar.exceptions import HTTPException
from litestar.openapi.config import OpenAPIConfig
from litestar.testing import TestClient
from placeframe_common.litestar import create_litestar_app


@get("/unavailable")
def unavailable() -> None:
    raise HTTPException(status_code=503, detail="Localization unavailable", headers={"Retry-After": "60"})


@get("/masked")
def masked() -> None:
    raise HTTPException(status_code=500, detail="secret detail", headers={"Retry-After": "30"})


def make_client() -> TestClient[Litestar]:
    application = create_litestar_app(
        [unavailable, masked], OpenAPIConfig("placeframe-common test", "0.1.0"), logging_config=None
    )
    return TestClient(app=application)


def test_client_error_forwards_extra_headers() -> None:
    with make_client() as client:
        response = client.get("/unavailable")

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "60"
    # 503 rides the >=500 branch: the detail stays masked, only the header forwards
    assert response.json() == {"detail": "Internal Server Error"}


def test_server_error_masks_the_detail_but_still_forwards_extra_headers() -> None:
    with make_client() as client:
        response = client.get("/masked")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    assert response.headers["Retry-After"] == "30"
