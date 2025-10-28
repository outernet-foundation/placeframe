#!/usr/bin/env python3
import json
from pathlib import Path
from time import sleep
from uuid import UUID

from common.classes import CameraIntrinsics, PointCloudPoint, Transform

from src.test.auth import password_login  # unify types with visualize.py

from .curl import curl
from .visualize import generate_visualization

API_BASE_URL = "https://desktop-otd3rch-api.outernetfoundation.org"
CAPTURE_ID = "305bf81a-0dea-4ac6-94df-78b294965f1b"  # TODO: replace
SCRIPT_DIR = Path(__file__).parent
TEST_IMAGE_PATH = SCRIPT_DIR / "test_image.jpg"
OUTPUT_HTML_PATH = SCRIPT_DIR / "vls_test_result.html"

# Pinhole intrinsics (the session currently accepts PINHOLE)
intrinsics: CameraIntrinsics = {
    "model": "PINHOLE",
    "width": 640,
    "height": 480,
    "fx": 461.35528564453127,
    "fy": 460.8520812988281,
    "cx": 320.53515625,
    "cy": 239.83949279785157,
}


def main() -> None:
    print("Authenticating")
    password_login()  # ensure we can auth before doing anything

    print(f"Checking for reconstruction for capture {CAPTURE_ID}")
    # if there's an existing reconstruction for this capture, use it
    existing_reconstructions: list[UUID] = curl("GET", f"{API_BASE_URL}/capture_sessions/{CAPTURE_ID}/reconstructions")
    # existing_reconstructions = []
    reconstruction_id: UUID | None = None
    if len(existing_reconstructions) > 0:
        # pick the first reconstruction with 'succeeded' status
        for recon in existing_reconstructions:
            status = curl("GET", f"{API_BASE_URL}/reconstructions/{recon}/status")
            if status == "succeeded":
                reconstruction_id = recon
                break
        print(f"Using existing reconstruction {reconstruction_id} for capture {CAPTURE_ID}")

    if reconstruction_id is None:
        print(f"Creating reconstruction for capture {CAPTURE_ID}")
        reconstruction_id = curl(
            "POST",
            f"{API_BASE_URL}/reconstructions",
            json_data={
                "create": {"capture_session_id": CAPTURE_ID},
                "options": {
                    "neightbors_count": 12,
                    "max_keypoints_per_image": 2500,
                    "use_prior_position": True,
                    "ba_refine_sensor_from_rig": False,
                    "ba_refine_focal_length": False,
                    "ba_refine_principal_point": False,
                    "ba_refine_extra_params": False,
                },
            },
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

    # localization_map_id: UUID | None = curl(
    #     "GET", f"{API_BASE_URL}/reconstructions/{reconstruction_id}/localization_map"
    # )

    localization_map_id: UUID | None = None  # force creating a new map each time for testing
    if localization_map_id is not None:
        print(f"Using existing localization map {localization_map_id} for capture {CAPTURE_ID}")
    else:
        print("Creating localization map with dummy ECEF")
        loc_map = curl(
            "POST",
            f"{API_BASE_URL}/localization_maps",
            json_data={
                "reconstruction_id": reconstruction_id,
                "position_x": 0.0,
                "position_y": 0.0,
                "position_z": 0.0,
                "rotation_x": 0.0,
                "rotation_y": 0.0,
                "rotation_z": 0.0,
                "rotation_w": 1.0,
                "color": 0,
            },
        )

        localization_map_id = loc_map["id"]

        print(f"Localization map: {localization_map_id}")

    assert localization_map_id is not None

    print("Creating localization session")
    session_id = curl("POST", f"{API_BASE_URL}/localization_sessions", json_data={}, connect_timeout_s=120)["id"]

    print(f"Waiting for session {session_id} to become ready")
    while True:
        sleep(5)
        status = curl("GET", f"{API_BASE_URL}/localization_sessions/{session_id}/status")
        print(f"Session status: {status}")
        if status == "failed" or status == "exited":
            raise RuntimeError("Session failed to start")
        if status == "ready":
            break

    print("Setting camera intrinsics for localization session")
    curl("PUT", f"{API_BASE_URL}/localization_sessions/{session_id}/camera", json_data=intrinsics)

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
    localization_result = curl(
        "POST",
        f"{API_BASE_URL}/localization_sessions/{session_id}/localization",
        form_data={"image": f"@{TEST_IMAGE_PATH}", "camera": camera_json},
    )

    print("Localization result:")
    print(json.dumps(localization_result, indent=2))

    print("Fetching point cloud")
    point_cloud: list[PointCloudPoint] = curl("GET", f"{API_BASE_URL}/reconstructions/{reconstruction_id}/points")

    print("Fetch image poses")
    reconstruction_image_poses: list[Transform] = curl(
        "GET", f"{API_BASE_URL}/reconstructions/{reconstruction_id}/image_poses"
    )

    assert reconstruction_id is not None
    print(f"Generating visualization → {OUTPUT_HTML_PATH}")
    localization_dict: dict[UUID, Transform] = {loc["id"]: loc["transform"] for loc in localization_result}
    html = generate_visualization(
        point_cloud, reconstruction_image_poses, localization_dict[reconstruction_id], intrinsics
    )

    OUTPUT_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML_PATH.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
