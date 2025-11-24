#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Sequence, cast

from plerion_api_client.models.pinhole_camera import PinholeCamera
from plerion_api_client.models.point_cloud_point import PointCloudPoint
from plerion_api_client.models.quaternion import Quaternion
from plerion_api_client.models.transform import Transform
from plerion_api_client.models.vector3 import Vector3
from scipy.spatial.transform import Rotation


def _world_to_camera_extrinsics_to_camera_world_pose(pose_world_from_camera: Transform) -> Transform:
    # pose_world_from_camera is "camera_from_world" (world->camera extrinsics)
    qw = float(pose_world_from_camera.rotation.w)
    qx = float(pose_world_from_camera.rotation.x)
    qy = float(pose_world_from_camera.rotation.y)
    qz = float(pose_world_from_camera.rotation.z)
    tx = float(pose_world_from_camera.position.x)
    ty = float(pose_world_from_camera.position.y)
    tz = float(pose_world_from_camera.position.z)

    R_cw = Rotation.from_quat([qx, qy, qz, qw])
    R_wc = R_cw.inv()
    Rm = cast(list[list[float]], R_wc.as_matrix().tolist())

    Cx = -(Rm[0][0] * tx + Rm[0][1] * ty + Rm[0][2] * tz)
    Cy = -(Rm[1][0] * tx + Rm[1][1] * ty + Rm[1][2] * tz)
    Cz = -(Rm[2][0] * tx + Rm[2][1] * ty + Rm[2][2] * tz)

    qx2, qy2, qz2, qw2 = R_wc.as_quat()

    # Construct a new Transform (don't mutate input)
    return Transform(
        position=Vector3(x=float(Cx), y=float(Cy), z=float(Cz)),
        rotation=Quaternion(w=float(qw2), x=float(qx2), y=float(qy2), z=float(qz2)),
    )


def generate_visualization(
    point_cloud: Sequence[PointCloudPoint],
    reconstruction_image_poses: Sequence[Transform],
    localization: Transform,
    intrinsics: PinholeCamera,
) -> str:
    intr = intrinsics  # already PinholeCamera

    axes = dict(
        visible=True,
        showbackground=False,
        showgrid=True,
        gridcolor="#2a2f3a",
        showline=True,
        linewidth=1,
        tickmode="linear",
        tick0=0.0,
        dtick=1.0,
        color="#aab2bf",
    )

    localization_cam_world = _world_to_camera_extrinsics_to_camera_world_pose(localization)
    localization_x, localization_y, localization_z = _frustum_coords(localization_cam_world, intr, size=0.6)

    recon_rx: list[float | None] = []
    recon_ry: list[float | None] = []
    recon_rz: list[float | None] = []
    recon_gx: list[float | None] = []
    recon_gy: list[float | None] = []
    recon_gz: list[float | None] = []
    recon_bx: list[float | None] = []
    recon_by: list[float | None] = []
    recon_bz: list[float | None] = []

    image_poses_x_all: list[float | None] = []
    image_poses_y_all: list[float | None] = []
    image_poses_z_all: list[float | None] = []

    # Convert all reconstruction poses to camera->world for viz
    recon_cam_world = [_world_to_camera_extrinsics_to_camera_world_pose(p) for p in reconstruction_image_poses]

    for pose in recon_cam_world:
        x_coords, y_coords, z_coords = _frustum_coords(pose, intr, size=0.45)
        image_poses_x_all += x_coords
        image_poses_y_all += y_coords
        image_poses_z_all += z_coords

        (rx, ry, rz), (gx, gy, gz), (bx, by, bz) = _axes_gizmo_coords(pose, length=0.22)
        recon_rx += rx
        recon_ry += ry
        recon_rz += rz
        recon_gx += gx
        recon_gy += gy
        recon_gz += gz
        recon_bx += bx
        recon_by += by
        recon_bz += bz

    (loc_rx, loc_ry, loc_rz), (loc_gx, loc_gy, loc_gz), (loc_bx, loc_by, loc_bz) = _axes_gizmo_coords(
        localization_cam_world, length=0.30
    )

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>VLS Result</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    :root {{
      --bg: #0b0d10;
      --panel: #12151a;
      --text: #e6e9ee;
      --muted: #aab2bf;
      --grid: #2a2f3a;
      --accent: rgb(255, 200, 50);
      --accent2: rgb(120, 170, 255);
    }}
    html, body {{
      height: 100%;
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, sans-serif;
    }}
    .info {{
      position: sticky;
      top: 0;
      z-index: 10;
      padding: 16px 20px;
      background: var(--panel);
      border-bottom: 1px solid var(--grid);
    }}
    .info h2 {{
      margin: 0 0 8px 0;
      font-weight: 600;
    }}
    .info p {{
      margin: 4px 0;
      color: var(--muted);
    }}
    #plot {{
      width: 100vw;
      height: 100vh;
      display: block;
    }}
  </style>
</head>
<body>
  <div class="info">
    <h2>Localization</h2>
    <p><strong>Position:</strong> [{localization_cam_world.position.x:.4f}, {localization_cam_world.position.y:.4f}, {
        localization_cam_world.position.z:.4f}]</p>
    <p><strong>Quaternion:</strong> [{localization_cam_world.rotation.w:.4f}, {localization_cam_world.rotation.x:.4f}, {
        localization_cam_world.rotation.y:.4f}, {localization_cam_world.rotation.z:.4f}]</p>
    <p><strong>Points:</strong> {len(point_cloud)}</p>
    <p><strong>Reconstruction Cameras:</strong> {len(recon_cam_world)}</p>
  </div>
  <div id="plot"></div>
  <script>
    var data = {
        json.dumps([
            {
                "type": "scatter3d",
                "mode": "markers",
                "x": [float(p.position.x) for p in point_cloud],
                "y": [float(p.position.y) for p in point_cloud],
                "z": [float(p.position.z) for p in point_cloud],
                "marker": {
                    "size": 1.8,
                    "color": [f"rgb({int(p.color.r)},{int(p.color.g)},{int(p.color.b)})" for p in point_cloud],
                    "opacity": 0.95,
                },
                "name": "Point Cloud",
                "showlegend": True,
            },
            _trace(
                x_coords=image_poses_x_all,
                y_coords=image_poses_y_all,
                z_coords=image_poses_z_all,
                color="rgb(150,150,255)",
                width=1,
                name="Reconstruction Cameras",
            ),
            _trace(
                x_coords=localization_x,
                y_coords=localization_y,
                z_coords=localization_z,
                color="rgb(50,220,70)",
                width=3,
                name="Localized Camera",
            ),
            _trace(
                recon_rx,
                recon_ry,
                recon_rz,
                color="rgb(255,80,80)",
                width=2,
                name="X axis (recon)",
                showlegend=False,
                hoverinfo="skip",
            ),
            _trace(
                recon_gx,
                recon_gy,
                recon_gz,
                color="rgb(80,255,80)",
                width=2,
                name="Y axis (recon)",
                showlegend=False,
                hoverinfo="skip",
            ),
            _trace(
                recon_bx,
                recon_by,
                recon_bz,
                color="rgb(80,80,255)",
                width=2,
                name="Z axis (recon)",
                showlegend=False,
                hoverinfo="skip",
            ),
            _trace(
                loc_rx,
                loc_ry,
                loc_rz,
                color="rgb(255,0,0)",
                width=4,
                name="X axis (localized)",
                showlegend=False,
                hoverinfo="skip",
            ),
            _trace(
                loc_gx,
                loc_gy,
                loc_gz,
                color="rgb(0,255,0)",
                width=4,
                name="Y axis (localized)",
                showlegend=False,
                hoverinfo="skip",
            ),
            _trace(
                loc_bx,
                loc_by,
                loc_bz,
                color="rgb(0,0,255)",
                width=4,
                name="Z axis (localized)",
                showlegend=False,
                hoverinfo="skip",
            ),
        ])
    };

    var layout = {
        json.dumps({
            "scene": {
                "xaxis": {**axes, "title": "X (m)"},
                "yaxis": {**axes, "title": "Y (m)"},
                "zaxis": {**axes, "title": "Z (m)"},
                "aspectmode": "data",
            },
            "paper_bgcolor": "#0b0d10",
            "plot_bgcolor": "#0b0d10",
            "font": {"color": "#e6e9ee"},
            "title": "Visual Localization Result",
            "showlegend": True,
            "legend": {"bgcolor": "#12151a", "bordercolor": "#2a2f3a"},
        })
    };

    function sizePlot() {{
      var header = document.querySelector('.info');
      var plot = document.getElementById('plot');
      var headerH = header ? header.offsetHeight : 0;
      var newH = window.innerHeight - headerH;
      if (newH < 200) newH = 200;
      plot.style.height = newH + 'px';
      if (window.Plotly) {{
        Plotly.relayout('plot', {{height: newH, width: window.innerWidth}});
      }}
    }}

    window.addEventListener('resize', sizePlot);
    document.addEventListener('DOMContentLoaded', function() {{
      Plotly.newPlot('plot', data, layout).then(sizePlot);
    }});
  </script>
</body>
</html>"""


def _trace(
    x_coords: list[float | None],
    y_coords: list[float | None],
    z_coords: list[float | None],
    color: str = "rgb(50,220,70)",
    width: int = 3,
    name: str = "Localized Camera",
    showlegend: bool = True,
    hoverinfo: str | None = None,
):
    return {
        "type": "scatter3d",
        "mode": "lines",
        "x": x_coords,
        "y": y_coords,
        "z": z_coords,
        "line": {"color": color, "width": width},
        "name": name,
        "showlegend": showlegend,
        **({"hoverinfo": hoverinfo} if hoverinfo is not None else {}),
    }


def _frustum_coords(pose: Transform, intrinsics: PinholeCamera, size: float):
    px = float(pose.position.x)
    py = float(pose.position.y)
    pz = float(pose.position.z)

    R = cast(
        list[list[float]],
        Rotation.from_quat([
            float(pose.rotation.x),
            float(pose.rotation.y),
            float(pose.rotation.z),
            float(pose.rotation.w),
        ])
        .as_matrix()
        .tolist(),
    )

    w, h = float(intrinsics.width), float(intrinsics.height)
    fx, fy, cx, cy = float(intrinsics.fx), float(intrinsics.fy), float(intrinsics.cx), float(intrinsics.cy)

    corners_2d = [(0.0, 0.0), (w, 0.0), (w, h), (0.0, h)]

    corners_3d: list[list[float]] = []
    for u, v in corners_2d:
        x = (u - cx) / fx * size
        y = (v - cy) / fy * size
        z = size
        xw = R[0][0] * x + R[0][1] * y + R[0][2] * z + px
        yw = R[1][0] * x + R[1][1] * y + R[1][2] * z + py
        zw = R[2][0] * x + R[2][1] * y + R[2][2] * z + pz
        corners_3d.append([xw, yw, zw])

    x_coords: list[float | None] = []
    y_coords: list[float | None] = []
    z_coords: list[float | None] = []

    for cx3d, cy3d, cz3d in corners_3d:
        x_coords += [px, cx3d, None]
        y_coords += [py, cy3d, None]
        z_coords += [pz, cz3d, None]

    for i in range(4):
        j = (i + 1) % 4
        ax, ay, az = corners_3d[i]
        bx, by, bz = corners_3d[j]
        x_coords += [ax, bx, None]
        y_coords += [ay, by, None]
        z_coords += [az, bz, None]

    return x_coords, y_coords, z_coords


def _axes_gizmo_coords(
    pose: Transform, length: float
) -> tuple[
    tuple[list[float | None], list[float | None], list[float | None]],
    tuple[list[float | None], list[float | None], list[float | None]],
    tuple[list[float | None], list[float | None], list[float | None]],
]:
    px = float(pose.position.x)
    py = float(pose.position.y)
    pz = float(pose.position.z)

    R = cast(
        list[list[float]],
        Rotation.from_quat([
            float(pose.rotation.x),
            float(pose.rotation.y),
            float(pose.rotation.z),
            float(pose.rotation.w),
        ])
        .as_matrix()
        .tolist(),
    )

    def world_tip(cx: float, cy: float, cz: float) -> tuple[float, float, float]:
        wx = R[0][0] * cx + R[0][1] * cy + R[0][2] * cz
        wy = R[1][0] * cx + R[1][1] * cy + R[1][2] * cz
        wz = R[2][0] * cx + R[2][1] * cy + R[2][2] * cz
        return px + length * wx, py + length * wy, pz + length * wz

    tips = [world_tip(1, 0, 0), world_tip(0, 1, 0), world_tip(0, 0, 1)]

    def seg(tip: tuple[float, float, float]):
        tx, ty, tz = tip
        return [px, tx, None], [py, ty, None], [pz, tz, None]

    xr, yr, zr = seg(tips[0])
    xg, yg, zg = seg(tips[1])
    xb, yb, zb = seg(tips[2])
    return (xr, yr, zr), (xg, yg, zg), (xb, yb, zb)
