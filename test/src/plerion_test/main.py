#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import MutableMapping, cast
from uuid import UUID

from plerion_api_client import ApiClient, Configuration
from plerion_api_client.api.default_api import DefaultApi
from plerion_api_client.models.camera import Camera
from plerion_api_client.models.load_state import LoadState
from plerion_api_client.models.localization_map_create import LocalizationMapCreate
from plerion_api_client.models.map_localization import MapLocalization
from plerion_api_client.models.pinhole_camera import PinholeCamera
from plerion_api_client.models.point_cloud_point import PointCloudPoint
from plerion_api_client.models.reconstruction_create import ReconstructionCreate
from plerion_api_client.models.reconstruction_create_with_options import ReconstructionCreateWithOptions
from plerion_api_client.models.reconstruction_options import ReconstructionOptions
from plerion_api_client.models.transform import Transform

from .auth import password_login
from .visualize import generate_visualization

API_BASE_URL = "https://desktop-otd3rch-api.outernetfoundation.org"
SCRIPT_DIR = Path(__file__).parent
OUTPUT_HTML_PATH = SCRIPT_DIR / "vls_test_result.html"


CAPTURE_ID = UUID("940c7be3-52fd-43d0-ae1f-3988749a638b")
TEST_IMAGE_PATH = SCRIPT_DIR / "test_image.jpg"

intrinsics = PinholeCamera(
    model="PINHOLE",
    width=1920,
    height=1080,
    mirroring="None",
    rotation="None",
    fx=1074.5068359375,
    fy=1074.5068359375,
    cx=939.377197265625,
    cy=560.67431640625,
)


async def visual_reconstruction_pointcloud(reconstruction_id: UUID):
    print("Authenticating")
    token = password_login()

    async with ApiClient(Configuration(host=API_BASE_URL)) as api_client:
        # Wire auth manually since your stripped spec has no auth scheme.
        headers = cast(MutableMapping[str, str], api_client.default_headers)
        headers["Authorization"] = f"Bearer {token}"
        api = DefaultApi(api_client)

        print(f"Fetching point cloud for reconstruction {reconstruction_id}")
        points = await api.get_reconstruction_points(reconstruction_id)
        print(f"Fetching image poses for reconstruction {reconstruction_id}")
        poses = await api.get_reconstruction_image_poses(reconstruction_id)

        print(f"Generating visualization → {OUTPUT_HTML_PATH}")
        html = generate_visualization(points, poses, None, intrinsics)

        OUTPUT_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_HTML_PATH.write_text(html, encoding="utf-8")


async def main_async():
    print("Authenticating")
    token = password_login()
    # NOTE: if password_login() doesn't return a token today,
    # change it to do so, or fetch the token from wherever it stores it.

    async with ApiClient(Configuration(host=API_BASE_URL)) as api_client:
        # Wire auth manually since your stripped spec has no auth scheme.
        headers = cast(MutableMapping[str, str], api_client.default_headers)
        headers["Authorization"] = f"Bearer {token}"
        api = DefaultApi(api_client)

        print(f"Checking for reconstruction for capture {CAPTURE_ID}")
        reconstruction_id: UUID | None = None

        if reconstruction_id is None:
            print(f"Creating reconstruction for capture {CAPTURE_ID}")

            recon_req = ReconstructionCreateWithOptions(
                create=ReconstructionCreate(capture_session_id=CAPTURE_ID),
                options=ReconstructionOptions(
                    random_seed=42,
                    neighbors_count=12,
                    max_keypoints_per_image=2500,
                    ransac_max_error=2.0,
                    ransac_min_inlier_ratio=0.15,
                    triangulation_minimum_angle=4.0,
                    triangulation_complete_max_reprojection_error=2.0,
                    triangulation_merge_max_reprojection_error=4.0,
                    mapper_filter_max_reprojection_error=2.0,
                    use_prior_position=True,
                    rig_verification=False,
                ),
            )

            recon_read = await api.create_reconstruction(recon_req)
            reconstruction_id = recon_read.id
            print(f"Reconstruction id: {reconstruction_id}")

            print(f"Waiting for reconstruction {reconstruction_id} to succeed (this can take a while)")
            while True:
                await asyncio.sleep(10)
                status = await api.get_reconstruction_status(reconstruction_id)
                print(f"Reconstruction status: {status}")
                if status == "succeeded":
                    break
                if status in ("failed", "exited"):
                    raise RuntimeError("Reconstruction failed")

        assert reconstruction_id is not None

        localization_map_id: UUID | None = None  # force new each run
        if localization_map_id is None:
            print("Creating localization map with dummy ECEF")
            loc_create = LocalizationMapCreate(
                reconstruction_id=reconstruction_id,
                position_x=0.0,
                position_y=0.0,
                position_z=0.0,
                rotation_x=0.0,
                rotation_y=0.0,
                rotation_z=0.0,
                rotation_w=1.0,
                color=0,
            )
            loc_map_read = await api.create_localization_map(loc_create)
            localization_map_id = loc_map_read.id
            print(f"Localization map: {localization_map_id}")

        assert localization_map_id is not None

        print("Creating localization session")
        session_read = await api.create_localization_session()
        session_id = session_read.id

        print(f"Waiting for session {session_id} to become ready")
        while True:
            await asyncio.sleep(5)
            status = await api.get_localization_session_status(session_id)
            print(f"Session status: {status}")
            if status in ("failed", "exited"):
                raise RuntimeError("Session failed to start")
            if status == "ready":
                break

        print("Setting camera intrinsics for localization session")
        await api.set_localization_session_camera_intrinsics(session_id, Camera(actual_instance=intrinsics))

        print(f"Loading localization map {localization_map_id} into session {session_id}")
        await api.load_localization_maps(session_id, [localization_map_id])

        print(f"Waiting for map {localization_map_id} to load into session {session_id}")
        while True:
            await asyncio.sleep(5)
            map_status = await api.get_map_load_status(session_id, localization_map_id)
            print(f"Map load status: {map_status}")
            if map_status.status == LoadState.FAILED:
                raise RuntimeError("Map failed to load")
            if map_status.status == LoadState.READY:
                break

        print("Localizing test image")
        image_bytes = TEST_IMAGE_PATH.read_bytes()
        localizations: list[MapLocalization] = await api.localize_image(session_id, (TEST_IMAGE_PATH.name, image_bytes))

        print("Localization result:")
        print(json.dumps([loc.model_dump(mode="json") for loc in localizations], indent=2))

        print("Fetching point cloud")
        point_cloud_models: list[PointCloudPoint] = await api.get_reconstruction_points(reconstruction_id)

        print("Fetch image poses")
        reconstruction_image_poses_models: list[Transform] = await api.get_reconstruction_image_poses(reconstruction_id)

        print(f"Generating visualization → {OUTPUT_HTML_PATH}")
        localization_dict = {loc.id: loc.transform for loc in localizations}
        html = generate_visualization(
            point_cloud_models, reconstruction_image_poses_models, localization_dict[localization_map_id], intrinsics
        )

        OUTPUT_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_HTML_PATH.write_text(html, encoding="utf-8")


def main():
    # asyncio.run(main_async())
    asyncio.run(visual_reconstruction_pointcloud(UUID("ed60ad43-d81e-44f8-8e1e-73d5588ca6b0")))


if __name__ == "__main__":
    main()
