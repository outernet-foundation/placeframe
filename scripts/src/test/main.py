#!/usr/bin/env python3
import json
from pathlib import Path
from time import sleep
from typing import cast
from uuid import UUID

from common.classes import PinholeIntrinsics, PointCloudPoint, Transform

from src.test.auth import password_login  # unify types with visualize.py

from .curl import curl
from .visualize import generate_visualization

API_BASE_URL = "https://desktop-otd3rch-api.outernetfoundation.org"
CAPTURE_ID = "d9c5b05e-c152-4070-b0b4-239af5a499e5"  # TODO: replace
SCRIPT_DIR = Path(__file__).parent
TEST_IMAGE_PATH = SCRIPT_DIR / "test_image.jpg"
OUTPUT_HTML_PATH = SCRIPT_DIR / "vls_test_result.html"

# Pinhole intrinsics (the session currently accepts PINHOLE)
intrinsics: PinholeIntrinsics = {
    "model": "PINHOLE",
    "width": 640,
    "height": 480,
    "fx": 461.35528564453127,
    "fy": 460.8520812988281,
    "cx": 318.46484375,
    "cy": 239.83949279785157,
}


def main() -> None:
    print("Authenticating")
    password_login()  # ensure we can auth before doing anything

    print(f"Checking for reconstruction for capture {CAPTURE_ID}")
    # if there's an existing reconstruction for this capture, use it
    existing_reconstructions: list[UUID] = json.loads(
        curl("GET", f"{API_BASE_URL}/capture_sessions/{CAPTURE_ID}/reconstructions")
    )
    reconstruction_id: UUID
    if len(existing_reconstructions) > 0:
        reconstruction_id = existing_reconstructions[0]
        print(f"Using existing reconstruction {reconstruction_id} for capture {CAPTURE_ID}")
    else:
        print(f"Creating reconstruction for capture {CAPTURE_ID}")
        reconstruction_id = json.loads(
            curl("POST", f"{API_BASE_URL}/reconstructions", json_data={"capture_session_id": CAPTURE_ID})
        )["id"]

        print(f"Waiting for reconstruction {reconstruction_id} to succeed (this can take a while)")
        while True:
            sleep(10)
            status = curl("GET", f"{API_BASE_URL}/reconstructions/{reconstruction_id}/status")
            print(f"Reconstruction status: {status}")
            if status == "succeeded":
                break
            if status == "failed" or status == "exited":
                raise RuntimeError("Reconstruction failed")

    localization_map_id: UUID | None = cast(
        UUID | None, curl("GET", f"{API_BASE_URL}/reconstructions/{reconstruction_id}/localization_map")
    )
    if localization_map_id is not None:
        print(f"Using existing localization map {localization_map_id} for capture {CAPTURE_ID}")
    else:
        print("Creating localization map with dummy ECEF")
        loc_map = json.loads(
            curl(
                "POST",
                f"{API_BASE_URL}/localization_maps",
                json_data={
                    "reconstruction_id": reconstruction_id,
                    "tx_ecef": 0.0,
                    "ty_ecef": 0.0,
                    "tz_ecef": 0.0,
                    "qx_ecef": 0.0,
                    "qy_ecef": 0.0,
                    "qz_ecef": 0.0,
                    "qw_ecef": 1.0,
                },
            )
        )
        localization_map_id = loc_map["id"]

        print(f"Localization map: {localization_map_id}")
    assert localization_map_id is not None

    print("Creating localization session")
    session_id = json.loads(curl("POST", f"{API_BASE_URL}/localization_sessions", json_data={}, connect_timeout_s=120))[
        "id"
    ]

    print(f"Waiting for session {session_id} to become ready")
    while True:
        sleep(5)
        status = curl("GET", f"{API_BASE_URL}/localization_sessions/{session_id}/status")
        print(f"Session status: {status}")
        if status == "failed" or status == "exited":
            raise RuntimeError("Session failed to start")
        if status == "ready":
            break

    print(f"Loading localization map {localization_map_id} into session {session_id}")
    curl(
        "POST",
        f"{API_BASE_URL}/localization_sessions/{session_id}/maps",
        json_data=[localization_map_id],
        print_command=True,
    )

    print(f"Waiting for map {localization_map_id} to load into session {session_id}")
    while True:
        sleep(5)
        status = curl("GET", f"{API_BASE_URL}/localization_sessions/{session_id}/maps/{localization_map_id}/status")
        print(f"Map load status: {status}")
        if status == "failed" or status == "exited":
            raise RuntimeError("Map failed to load")
        if status == "ready":
            break

    print("Localizing test image")
    camera_json = json.dumps(intrinsics)
    localization_result: dict[UUID, Transform] = json.loads(
        curl(
            "POST",
            f"{API_BASE_URL}/localization_sessions/{session_id}/localization",
            form_data={"image": f"@{TEST_IMAGE_PATH}", "camera": camera_json},
        )
    )

    print("Localization result:")
    print(json.dumps(localization_result, indent=2))

    print("Fetching point cloud")
    result = curl("GET", f"{API_BASE_URL}/reconstructions/{reconstruction_id}/points")
    point_cloud: list[PointCloudPoint] = json.loads(result)

    print("Fetch image poses")
    result = curl("GET", f"{API_BASE_URL}/reconstructions/{reconstruction_id}/image_poses")
    reconstruction_image_poses: list[Transform] = json.loads(result)

    print(f"Generating visualization → {OUTPUT_HTML_PATH}")
    html = generate_visualization(
        point_cloud, reconstruction_image_poses, localization_result[reconstruction_id], intrinsics
    )

    OUTPUT_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML_PATH.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
