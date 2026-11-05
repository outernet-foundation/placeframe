"""An interactive matplotlib player for replays: each frame's image with the map points projected
through each algorithm's fused pose, a top-down view, and timelines of what the algorithms did.

Keys
  left / right        step a frame (Shift: 10 frames)
  space               play / pause (at the recording's own pace)
  ] / [               next / previous still (VPS's inliers are drawn on stills)
  n / b               next / previous fix the first algorithm was given
  i                   inliers on / off: VPS's features (yellow rings), where each algorithm's pose
                      puts their map points (dots), and the error between them (lines)
  v                   also project the inliers with the still's own VPS pose (white +)
  c                   colour the map points by algorithm / by depth
  m                   map points on / off
  s                   on a still, show the full-resolution still instead of the video frame
  z                   top-down view: follow the camera / whole run
  home / end          first / last frame
Click a timeline to jump there.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.widgets import Slider
from PIL import Image

from fusion.data import Run
from fusion.metrics import Reference, Registration, reference_error, registration
from fusion.replay import Result

COLORS = ["#22d3ee", "#f472b6", "#a3e635", "#fb923c", "#c084fc"]
FEATURE = "#fde047"
REJECTED = "#ef4444"
FAILED = "#9ca3af"
DEFAULT_GATE = 16.81
NO_M2 = 0.05  # where decisions without a Mahalanobis distance sit on the m² timeline
DEPTH_MAX_M = 25.0
IMAGE_CACHE = 240
FOLLOW_HALF_WIDTH_M = 10.0


class Viewer:
    def __init__(self, run: Run, results: list[Result], ref: Reference | None = None, title: str = "") -> None:
        if not results:
            raise ValueError("Nothing to show")
        self.run = run
        self.results = results
        self.ref = ref
        self.frames = results[0].frames
        self.position = 0  # row into self.frames
        self.playing = False
        self.show_inliers = True
        self.show_vps_pose = False
        self.show_points = True
        self.depth_colors = False
        self.show_still = False
        self.follow = True
        self._full_redraw = True
        self._shown_width = 0
        self._images: OrderedDict[Path, np.ndarray] = OrderedDict()
        self._timer = None
        self._play_from: tuple[float, float] | None = None
        self.still_at_frame = {v: i for i, v in enumerate(run.still_video_index) if v is not None}
        self.registrations: list[Registration] = [registration(run, r) for r in results]
        self.ref_errors = [reference_error(r, ref)[0] if ref is not None else None for r in results]

        self.fig = plt.figure(figsize=(17, 10.5))
        self.fig.canvas.manager.set_window_title(title or f"fusion-test · {run.directory.name}")  # type: ignore[union-attr]
        grid = self.fig.add_gridspec(
            6,
            2,
            width_ratios=[3, 1.25],
            height_ratios=[4.2, 0.8, 0.8, 0.8, 0.8, 0.22],
            left=0.04,
            right=0.99,
            top=0.97,
            bottom=0.03,
            hspace=0.12,
            wspace=0.08,
        )
        self.ax_image = self.fig.add_subplot(grid[0, 0])
        self.ax_map = self.fig.add_subplot(grid[0, 1])
        self.ax_info = self.fig.add_subplot(grid[1:5, 1])
        self.ax_m2 = self.fig.add_subplot(grid[1, 0])
        self.ax_correction = self.fig.add_subplot(grid[2, 0], sharex=self.ax_m2)
        self.ax_ref = self.fig.add_subplot(grid[3, 0], sharex=self.ax_m2)
        self.ax_registration = self.fig.add_subplot(grid[4, 0], sharex=self.ax_m2)
        self.timelines = [self.ax_m2, self.ax_correction, self.ax_ref, self.ax_registration]
        slider_ax = self.fig.add_subplot(grid[5, 0])

        self._build_image()
        self._build_map()
        self._build_timelines()
        self.ax_info.axis("off")
        self.info = self.ax_info.text(
            0, 1, "", va="top", ha="left", family="monospace", fontsize=8.5, transform=self.ax_info.transAxes
        )
        self.slider = Slider(slider_ax, "", 0, len(self.frames) - 1, valinit=0, valstep=1)
        self.slider.valtext.set_visible(False)
        self.slider.on_changed(self._on_slider)
        self.slider.drawon = False
        self._background = None
        self._view_centre: np.ndarray | None = None
        self.animated = [
            self.image,
            *self.point_sets,
            self.features,
            *self.inlier_dots,
            *self.inlier_lines,
            self.vps_pose_dots,
            self.image_title,
            *[a for pair in self.map_markers for a in pair],
            *self.cursors,
            self.info,
            self.slider.poly,
            self.slider._handle,  # noqa: SLF001
        ]
        for artist in self.animated:
            artist.set_animated(True)
        self.fig.canvas.mpl_connect("draw_event", self._on_draw)
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.update()

    # --- building ---------------------------------------------------------------------------

    def _build_image(self) -> None:
        intrinsics = self.run.video_intrinsics
        self.image = self.ax_image.imshow(np.zeros((intrinsics.height, intrinsics.width, 3), dtype=np.uint8))
        self.ax_image.set_axis_off()
        self.point_sets = []
        for k, _ in enumerate(self.results):
            scatter = self.ax_image.scatter([], [], s=3, c=COLORS[k % len(COLORS)], linewidths=0)
            scatter.set_cmap("turbo")
            scatter.set_clim(0, DEPTH_MAX_M)
            self.point_sets.append(scatter)
        self.features = self.ax_image.scatter([], [], s=28, facecolors="none", edgecolors=FEATURE, linewidths=0.9)
        self.inlier_dots = [
            self.ax_image.scatter([], [], s=9, c=COLORS[k % len(COLORS)], linewidths=0)
            for k, _ in enumerate(self.results)
        ]
        self.inlier_lines = [
            LineCollection([], colors=COLORS[k % len(COLORS)], linewidths=0.8, alpha=0.9)
            for k, _ in enumerate(self.results)
        ]
        for lines in self.inlier_lines:
            self.ax_image.add_collection(lines)
        self.vps_pose_dots = self.ax_image.scatter([], [], s=14, c="white", marker="+", linewidths=0.8)
        self.image_title = self.ax_image.set_title("", fontsize=9, loc="left")

    def _build_map(self) -> None:
        ax = self.ax_map
        points = self.run.map.points
        stride = max(1, len(points) // 40000)
        ax.scatter(
            points[::stride, 0], points[::stride, 2], s=0.3, c="#9ca3af", alpha=0.35, linewidths=0, rasterized=True
        )
        positions = np.array([f.map_from_camera[:3, 3] for f in self.run.fixes if f.ok])
        if len(positions):
            ax.scatter(positions[:, 0], positions[:, 2], s=4, c="#6b7280", linewidths=0, label="VPS, every still")
        if self.ref is not None:
            path = self.ref.map_from_camera[:, :3, 3]
            ax.plot(path[:, 0], path[:, 2], color="#111827", lw=0.8, label="reference")
        self.map_markers = []
        for k, result in enumerate(self.results):
            color = COLORS[k % len(COLORS)]
            path = result.map_from_camera[:, :3, 3]
            ax.plot(path[:, 0], path[:, 2], color=color, lw=1.2, label=result.name)
            accepted, rejected = self._request_positions(result)
            if len(accepted):
                ax.scatter(accepted[:, 0], accepted[:, 2], s=22, c=color, edgecolors="black", linewidths=0.5, zorder=3)
            if len(rejected):
                ax.scatter(rejected[:, 0], rejected[:, 2], s=22, c=REJECTED, marker="x", linewidths=1.2, zorder=3)
            (marker,) = ax.plot([], [], marker="o", color=color, markeredgecolor="black", ms=7, zorder=4)
            (heading,) = ax.plot([], [], color=color, lw=2, zorder=4)
            self.map_markers.append((marker, heading))
        ax.set_aspect("equal")
        ax.tick_params(labelsize=7)
        ax.set_title("top-down (map x, z)", fontsize=9, loc="left")
        ax.legend(fontsize=7, loc="lower right", framealpha=0.8)
        everything = np.concatenate([r.map_from_camera[:, :3, 3] for r in self.results] + [positions.reshape(-1, 3)])
        everything = everything[~np.isnan(everything).any(axis=1)]
        self.map_bounds = (everything.min(axis=0) - 3, everything.max(axis=0) + 3) if len(everything) else None

    def _request_positions(self, result: Result) -> tuple[np.ndarray, np.ndarray]:
        accepted, rejected = [], []
        for request, decision in zip(result.requests, result.decisions, strict=True):
            if decision is None or not request.fix.ok:
                continue
            (accepted if decision.accepted else rejected).append(request.fix.map_from_camera[:3, 3])
        return np.array(accepted).reshape(-1, 3), np.array(rejected).reshape(-1, 3)

    def _build_timelines(self) -> None:
        for ax, label in zip(
            self.timelines,
            ["VPS m² (log)", "correction cm/frame", "error vs ref cm", "registration px (log)"],
            strict=True,
        ):
            ax.set_ylabel(label, fontsize=8)
            ax.tick_params(labelsize=7)
            ax.grid(True, color="#e5e7eb", lw=0.6)
        for ax in self.timelines[:-1]:
            plt.setp(ax.get_xticklabels(), visible=False)
        self.ax_registration.set_xlabel("t (s)", fontsize=8)
        self.ax_m2.set_yscale("log")
        self.ax_m2.axhline(DEFAULT_GATE, color="#6b7280", lw=0.8, ls="--")
        self.ax_m2.axhspan(NO_M2 / 2, NO_M2 * 2, color="#f3f4f6", zorder=0)
        self.ax_m2.text(0.002, 0.04, "no m²", transform=self.ax_m2.transAxes, fontsize=7, color="#6b7280")
        failed_t = sorted({
            r.apply_t
            for result in self.results
            for r, d in zip(result.requests, result.decisions, strict=True)
            if d is not None and not r.fix.ok
        })
        self.ax_m2.vlines(failed_t, 0, 1, transform=self.ax_m2.get_xaxis_transform(), color=FAILED, lw=0.6, alpha=0.6)
        for k, result in enumerate(self.results):
            color = COLORS[k % len(COLORS)]
            spans, accepted, rejected = [], [], []
            for request, decision in zip(result.requests, result.decisions, strict=True):
                if decision is None or not request.fix.ok:
                    continue
                m2 = decision.mahalanobis_sq if decision.mahalanobis_sq is not None else NO_M2
                spans.append([(request.request_t, m2), (request.apply_t, m2)])
                (accepted if decision.accepted else rejected).append((request.apply_t, m2))
            self.ax_m2.add_collection(LineCollection(spans, colors=color, linewidths=0.6, alpha=0.6))
            if accepted:
                a = np.array(accepted)
                self.ax_m2.scatter(a[:, 0], a[:, 1], s=18, c=color, edgecolors="black", linewidths=0.4, zorder=3)
            if rejected:
                a = np.array(rejected)
                self.ax_m2.scatter(a[:, 0], a[:, 1], s=22, c=REJECTED, marker="x", linewidths=1.1, zorder=3)
            self.ax_correction.plot(result.t, result.correction_m * 100, color=color, lw=0.9)
            if self.ref_errors[k] is not None:
                self.ax_ref.plot(result.t, self.ref_errors[k] * 100, color=color, lw=0.9)
            reg = self.registrations[k]
            self.ax_registration.plot(reg.t, reg.median_px, color=color, lw=0.8, marker="o", ms=2.5)
        self.ax_registration.set_yscale("log")
        self.ax_correction.set_ylim(bottom=0)
        self.ax_ref.set_ylim(bottom=0)
        self.ax_m2.set_xlim(self.results[0].t[0], self.results[0].t[-1])
        self.cursors = [ax.axvline(0, color="black", lw=0.9) for ax in self.timelines]

    # --- drawing ----------------------------------------------------------------------------

    def _load(self, path: Path) -> np.ndarray:
        image = self._images.get(path)
        if image is None:
            with Image.open(path) as handle:
                image = np.asarray(handle.convert("RGB"))
            self._images[path] = image
            if len(self._images) > IMAGE_CACHE:
                self._images.popitem(last=False)
        else:
            self._images.move_to_end(path)
        return image

    def update(self) -> None:
        frame_index = int(self.frames[self.position])
        frame = self.run.video[frame_index]
        still = self.still_at_frame.get(frame_index)
        use_still = self.show_still and still is not None
        intrinsics = self.run.still_intrinsics if use_still else self.run.video_intrinsics
        if intrinsics.width != self._shown_width:
            self._shown_width = intrinsics.width
            self._full_redraw = True
        image = self._load(self.run.stills[still].image if use_still and still is not None else frame.image)
        self.image.set_data(image)
        self.image.set_extent((-0.5, intrinsics.width - 0.5, intrinsics.height - 0.5, -0.5))
        self.ax_image.set_xlim(-0.5, intrinsics.width - 0.5)
        self.ax_image.set_ylim(intrinsics.height - 0.5, -0.5)

        for k, result in enumerate(self.results):
            row = result.at(frame_index)
            scatter = self.point_sets[k]
            if row is None or np.isnan(result.map_from_camera[row, 0, 0]) or not self.show_points:
                scatter.set_offsets(np.zeros((0, 2)))
                continue
            map_from_camera = result.map_from_camera[row]
            visible = self.run.map.visible_points(map_from_camera)
            camera_from_map = np.linalg.inv(map_from_camera)
            xyz = self.run.map.points[visible] @ camera_from_map[:3, :3].T + camera_from_map[:3, 3]
            uv, z = intrinsics.project(xyz)
            inside = (
                (z > 0.1)
                & (uv[:, 0] >= 0)
                & (uv[:, 0] < intrinsics.width)
                & (uv[:, 1] >= 0)
                & (uv[:, 1] < intrinsics.height)
            )
            scatter.set_offsets(uv[inside])
            if self.depth_colors and k == 0:
                scatter.set_array(z[inside])
            else:
                scatter.set_array(None)
                scatter.set_facecolor(COLORS[k % len(COLORS)])

        self._draw_inliers(frame_index, still, intrinsics, use_still)
        self._draw_map(frame_index)
        for cursor in self.cursors:
            cursor.set_xdata([frame.t, frame.t])
        self.image_title.set_text(
            f"frame {frame_index}  t {frame.t:.3f} s  {frame.tracking_state}"
            + (f"   still {still}" if still is not None else "")
            + ("  (full-resolution still)" if use_still else "")
        )
        self.info.set_text(self._info_text(frame_index, still))
        if self.slider.val != self.position:
            self.slider.eventson = False
            self.slider.set_val(self.position)
            self.slider.eventson = True
        if self._background is None or self._full_redraw:
            self._full_redraw = False
            self.fig.canvas.draw_idle()
            return
        canvas = self.fig.canvas
        canvas.restore_region(self._background)
        for artist in self.animated:
            self.fig.draw_artist(artist)
        canvas.blit(self.fig.bbox)

    def _on_draw(self, _event) -> None:  # noqa: ANN001
        self._background = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        for artist in self.animated:
            self.fig.draw_artist(artist)

    def _draw_inliers(self, frame_index: int, still: int | None, intrinsics, use_still: bool) -> None:  # noqa: ANN001
        empty = np.zeros((0, 2))
        fix = self.run.fixes[still] if still is not None else None
        if not self.show_inliers or fix is None or not fix.ok or not len(fix.inlier_points):
            self.features.set_offsets(empty)
            self.vps_pose_dots.set_offsets(empty)
            for dots, lines in zip(self.inlier_dots, self.inlier_lines, strict=True):
                dots.set_offsets(empty)
                lines.set_segments([])
            return
        scale = 1.0 if use_still else self.run.video_intrinsics.width / self.run.still_intrinsics.width
        detected = fix.inlier_uv * scale
        self.features.set_offsets(detected)
        xyz = self.run.map.points[fix.inlier_points]
        for k, result in enumerate(self.results):
            row = result.at(frame_index)
            if row is None or np.isnan(result.map_from_camera[row, 0, 0]):
                self.inlier_dots[k].set_offsets(empty)
                self.inlier_lines[k].set_segments([])
                continue
            camera_from_map = np.linalg.inv(result.map_from_camera[row])
            uv, z = intrinsics.project(xyz @ camera_from_map[:3, :3].T + camera_from_map[:3, 3])
            ok = z > 0.1
            self.inlier_dots[k].set_offsets(uv[ok])
            self.inlier_lines[k].set_segments(np.stack([detected[ok], uv[ok]], axis=1))
        if self.show_vps_pose and fix.camera_from_map is not None:
            camera_from_map = fix.camera_from_map
            uv, z = intrinsics.project(xyz @ camera_from_map[:3, :3].T + camera_from_map[:3, 3])
            self.vps_pose_dots.set_offsets(uv[z > 0.1])
        else:
            self.vps_pose_dots.set_offsets(empty)

    def _draw_map(self, frame_index: int) -> None:
        centre = None
        for (marker, heading), result in zip(self.map_markers, self.results, strict=True):
            row = result.at(frame_index)
            if row is None or np.isnan(result.map_from_camera[row, 0, 0]):
                marker.set_data([], [])
                heading.set_data([], [])
                continue
            pose = result.map_from_camera[row]
            position = pose[:3, 3]
            forward = pose[:3, 2] / np.linalg.norm(pose[:3, 2])
            marker.set_data([position[0]], [position[2]])
            heading.set_data([position[0], position[0] + 2 * forward[0]], [position[2], position[2] + 2 * forward[2]])
            centre = position if centre is None else centre
        if self.follow and centre is not None:
            view = self._view_centre
            if view is None or np.max(np.abs(centre[[0, 2]] - view)) > FOLLOW_HALF_WIDTH_M / 2:
                self._view_centre = centre[[0, 2]].copy()
                self.ax_map.set_xlim(centre[0] - FOLLOW_HALF_WIDTH_M, centre[0] + FOLLOW_HALF_WIDTH_M)
                self.ax_map.set_ylim(centre[2] - FOLLOW_HALF_WIDTH_M, centre[2] + FOLLOW_HALF_WIDTH_M)
                self._full_redraw = True
        elif not self.follow and self.map_bounds is not None and self._view_centre is not None:
            self._view_centre = None
            low, high = self.map_bounds
            self.ax_map.set_xlim(low[0], high[0])
            self.ax_map.set_ylim(low[2], high[2])
            self._full_redraw = True

    def _info_text(self, frame_index: int, still: int | None) -> str:
        frame = self.run.video[frame_index]
        lines = [f"frame {frame_index}/{len(self.run.video) - 1}   t {frame.t:.3f} s", ""]
        if still is not None:
            fix = self.run.fixes[still]
            if fix.ok:
                m = fix.metrics
                lines.append(
                    f"still {still}: {fix.num_inliers} inliers ({m.get('inlier_ratio', 0):.2f}), "
                    f"conf {m.get('confidence_loose', 0):.2f}, {len(fix.inlier_points)} tied to points"
                )
            else:
                lines.append(f"still {still}: VPS failed ({(fix.error or '').rsplit(': ', 1)[-1][:50]})")
            lines.append("")
        for k, result in enumerate(self.results):
            row = result.at(frame_index)
            lines.append(f"[{k + 1}] {result.name}")
            if row is None:
                lines.append("    not replayed here")
                continue
            details = [
                f"{key} {values[row]:.3g}" for key, values in result.diagnostics.items() if not np.isnan(values[row])
            ]
            for chunk in range(0, len(details), 3):
                lines.append("    " + ", ".join(details[chunk : chunk + 3]))
            last = self._last_decision(result, frame_index)
            if last is not None:
                index, request, decision = last
                verdict = "accepted" if decision.accepted else "rejected"
                m2 = f" m² {decision.mahalanobis_sq:.1f}" if decision.mahalanobis_sq is not None else ""
                note = decision.note.rsplit(": ", 1)[-1] if decision.note else ""
                extra = f" ({note[:40]})" if note else ""
                snapped = " snap" if decision.snapped and decision.accepted else ""
                lines.append(
                    f"    last fix #{index + 1} (still {request.still}): {verdict}{snapped}{m2}{extra}, "
                    f"{frame.t - request.apply_t:.1f} s ago"
                )
            if self.ref_errors[k] is not None and not np.isnan(self.ref_errors[k][row]):
                lines.append(f"    vs reference {self.ref_errors[k][row] * 100:.1f} cm")
            reg = self.registrations[k]
            before = np.flatnonzero(reg.t <= frame.t + 1e-6)
            if len(before):
                lines.append(
                    f"    registration at still {reg.still[before[-1]]}: {reg.median_px[before[-1]]:.1f} px median"
                )
            correction = result.correction_m[row]
            if not np.isnan(correction) and correction > 0:
                lines.append(f"    correction this frame {correction * 100:.1f} cm")
        lines += [
            "",
            "keys: ←/→ (⇧×10) step  space play  ]/[ still  n/b fix",
            "      i inliers  v VPS pose  c colour  m points",
            "      s still image  z zoom",
        ]
        return "\n".join(lines)

    def _last_decision(self, result: Result, frame_index: int):  # noqa: ANN202
        best = None
        for i, (request, decision, applied) in enumerate(
            zip(result.requests, result.decisions, result.apply_frame, strict=True)
        ):
            if decision is not None and applied is not None and applied <= frame_index:
                if best is None or applied >= best[3]:
                    best = (i, request, decision, applied)
        return None if best is None else best[:3]

    # --- navigation -------------------------------------------------------------------------

    def seek(self, position: int) -> None:
        self.position = int(np.clip(position, 0, len(self.frames) - 1))
        self.update()

    def _seek_frame(self, frame_index: int) -> None:
        self.seek(int(np.searchsorted(self.frames, frame_index)))

    def _on_slider(self, value: float) -> None:
        self._stop()
        self.position = int(value)
        self.update()

    def _on_click(self, event) -> None:  # noqa: ANN001
        if event.inaxes in self.timelines and event.xdata is not None:
            self._stop()
            self._seek_frame(self.run.frame_at(event.xdata))

    def _on_key(self, event) -> None:  # noqa: ANN001, C901
        key = event.key or ""
        frame_index = int(self.frames[self.position])
        if key in ("right", "left", "shift+right", "shift+left"):
            self._stop()
            step = 10 if key.startswith("shift") else 1
            self.seek(self.position + (step if key.endswith("right") else -step))
        elif key == " ":
            self._stop() if self.playing else self._play()
        elif key in ("]", "["):
            stills = sorted(self.still_at_frame)
            target = [f for f in stills if f > frame_index] if key == "]" else [f for f in stills if f < frame_index]
            if target:
                self._seek_frame(target[0] if key == "]" else target[-1])
        elif key in ("n", "b"):
            applied = sorted(f for f in self.results[0].apply_frame if f is not None)
            target = [f for f in applied if f > frame_index] if key == "n" else [f for f in applied if f < frame_index]
            if target:
                self._seek_frame(target[0] if key == "n" else target[-1])
        elif key in ("i", "v", "c", "m", "s", "z"):
            attribute = {
                "i": "show_inliers",
                "v": "show_vps_pose",
                "c": "depth_colors",
                "m": "show_points",
                "s": "show_still",
                "z": "follow",
            }[key]
            setattr(self, attribute, not getattr(self, attribute))
            self._full_redraw = True
            self.update()
        elif key == "home":
            self.seek(0)
        elif key == "end":
            self.seek(len(self.frames) - 1)

    def _play(self) -> None:
        if self.position >= len(self.frames) - 1:
            self.position = 0
        self.playing = True
        self._play_from = (time.perf_counter(), self.run.video[int(self.frames[self.position])].t)
        self._timer = self.fig.canvas.new_timer(interval=15)
        self._timer.add_callback(self._tick)
        self._timer.start()

    def _stop(self) -> None:
        self.playing = False
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def _tick(self) -> None:
        if not self.playing or self._play_from is None:
            return
        wall, t0 = self._play_from
        target = t0 + time.perf_counter() - wall
        times = self.results[0].t
        position = int(np.searchsorted(times, target, side="right")) - 1
        if position >= len(self.frames) - 1:
            self._stop()
            position = len(self.frames) - 1
        if position != self.position:
            self.position = position
            self.update()

    def show(self) -> None:
        plt.show()
