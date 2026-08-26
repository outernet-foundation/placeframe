"""Dashboard backend: a thin HTTP wrapper around `uv run howard-test`.

Every action the dashboard offers is literally the corresponding `howard-test` subcommand run as
a subprocess with `--json`, executed with cwd set to the placeframe repo root so `uv run` resolves
against *that* workspace (this project deliberately isn't a member of it — see dashboard/AGENTS.md
if that file exists, or the placeframe conversation history that motivated this layout).

Run with (from this directory): uv run uvicorn app:app --reload --port 8010
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, NoReturn

from litestar import Litestar, Request, delete, get, post
from litestar.config.cors import CORSConfig
from litestar.exceptions import NotFoundException
from litestar.response import File, Response

PLACEFRAME_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PLACEFRAME_ROOT / "data"
RECONSTRUCTIONS_DIR = DATA_DIR / "reconstructions"
LOCALIZATIONS_DIR = DATA_DIR / "localizations"

# This backend runs from its own `uv`-managed venv (dashboard/backend/.venv); without stripping
# VIRTUAL_ENV, the `uv run howard-test` subprocess below inherits it and prints a spurious "doesn't
# match the project environment" warning to stderr on every invocation, polluting the error
# messages callers see when a real failure occurs.
_HOWARD_TEST_ENV = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}

# Wall-clock cap on a background reconstruct job's status-poll loop; mirrors howard_test.py's own
# RECONSTRUCTION_TIMEOUT_S so a stuck reconstruction doesn't poll forever.
RECONSTRUCT_POLL_TIMEOUT_S = 1800.0
RECONSTRUCT_POLL_INTERVAL_S = 3.0

JobKind = Literal["reconstruct", "visualize", "localize"]
JobStatus = Literal["running", "succeeded", "failed"]


@dataclass
class Job:
    id: str
    kind: JobKind
    status: JobStatus = "running"
    reconstruction_id: str | None = None
    run_id: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


JOBS: dict[str, Job] = {}
# Keep references to in-flight background tasks; asyncio.create_task alone doesn't hold one and
# an unreferenced task can be garbage-collected mid-run.
_BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


def _spawn(coro: Any) -> None:
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)


def _run_howard_test_json(*args: str) -> Any:
    result = subprocess.run(
        ["uv", "run", "howard-test", *args, "--json"],
        cwd=PLACEFRAME_ROOT,
        env=_HOWARD_TEST_ENV,
        capture_output=True,
        text=True,
        check=False,
    )
    # A reconstruction landing in FAILED/CANCELLED makes the CLI exit 1 *after* printing its JSON
    # payload (see _report_reconstruction in howard_test.py) — that payload, with its `error`
    # field, is exactly what callers want, so a parseable stdout wins regardless of return code.
    if result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    raise RuntimeError(result.stderr.strip() or f"howard-test {' '.join(args)} exited {result.returncode}")


async def _run_howard_test_json_async(*args: str) -> Any:
    return await asyncio.to_thread(_run_howard_test_json, *args)


def _run_howard_test_bytes(*args: str) -> bytes:
    result = subprocess.run(
        ["uv", "run", "howard-test", *args],
        cwd=PLACEFRAME_ROOT,
        env=_HOWARD_TEST_ENV,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(detail or f"howard-test {' '.join(args)} exited {result.returncode}")
    return result.stdout


async def _run_howard_test_bytes_async(*args: str) -> bytes:
    return await asyncio.to_thread(_run_howard_test_bytes, *args)


def _browse_directories(path: str | None) -> dict[str, Any]:
    target = Path(path).expanduser().resolve() if path else Path.home()
    if not target.is_dir():
        raise NotFoundException(f"Not a directory: {target}")
    try:
        children = sorted(
            (p for p in target.iterdir() if p.is_dir() and not p.name.startswith(".")),
            key=lambda p: p.name.lower(),
        )
    except PermissionError:
        children = []
    entries = [{"name": p.name, "path": str(p)} for p in children]
    parent = str(target.parent) if target.parent != target else None
    return {"path": str(target), "parent": parent, "entries": entries}


# Server-local directory browser for the Localize tab's image-directory picker. A plain
# `<input type=file webkitdirectory>` can't be used here — browsers never expose the absolute
# filesystem path of a picked directory, only a File list with paths relative to the picked root,
# and the CLI this dashboard wraps needs a real absolute path. Since the dashboard always runs on
# the same machine as the CLI (see module docstring), walking the real filesystem server-side and
# returning absolute paths is the direct equivalent of a native picker here.
@get("/api/browse-directories")
async def browse_directories(path: str | None = None) -> dict[str, Any]:
    return await asyncio.to_thread(_browse_directories, path)


@get("/api/captures")
async def list_captures() -> list[dict[str, Any]]:
    return await _run_howard_test_json_async("captures")


@get("/api/reconstructions")
async def list_reconstructions() -> list[dict[str, Any]]:
    return await _run_howard_test_json_async("reconstructions")


@delete("/api/reconstructions/{reconstruction_id:str}")
async def delete_reconstruction(reconstruction_id: str) -> None:
    # 204 No Content on success; a failure (including the API's "has an associated localization
    # map" refusal — see docker/api/src/routers/reconstructions.py) raises RuntimeError from
    # _run_howard_test_json, which the RuntimeError exception handler turns into a 500 with detail.
    await _run_howard_test_json_async("delete-reconstruction", reconstruction_id)


def _list_localizations() -> list[dict[str, Any]]:
    if not LOCALIZATIONS_DIR.exists():
        return []
    runs: list[dict[str, Any]] = []
    for run_dir in LOCALIZATIONS_DIR.iterdir():
        results_path = run_dir / "results.json"
        if not results_path.exists():
            continue
        try:
            data = json.loads(results_path.read_text())
        except json.JSONDecodeError:
            continue
        images = data.get("images", [])
        runs.append({
            "run_id": data.get("run_id", run_dir.name),
            "reconstruction_id": data.get("reconstruction_id"),
            "created_at": data.get("created_at"),
            "image_count": len(images),
            "valid_count": sum(1 for img in images if img.get("status") == "ok"),
        })
    runs.sort(key=lambda r: r["created_at"] or "", reverse=True)
    return runs


@get("/api/localizations")
async def list_localizations() -> list[dict[str, Any]]:
    return await asyncio.to_thread(_list_localizations)


@dataclass
class ReconstructRequest:
    capture_id: str
    options_json: str | None = None


@dataclass
class VisualizeRequest:
    reconstruction_id: str


@dataclass
class LocalizeRequest:
    reconstruction_id: str
    image_dir: str
    retrieval_top_k: int | None = None
    ransac_threshold: float | None = None


@dataclass
class SaveTableRequest:
    output_path: str


@dataclass
class SaveImagesRequest:
    output_dir: str


@dataclass
class ExportPosesRequest:
    reconstruction_id: str
    output_path: str


@post("/api/reconstruct")
async def start_reconstruct(data: ReconstructRequest) -> dict[str, str]:
    job = Job(id=str(uuid.uuid4()), kind="reconstruct")
    JOBS[job.id] = job
    _spawn(_run_reconstruct_job(job, data.capture_id, data.options_json))
    return {"job_id": job.id}


@post("/api/visualize")
async def start_visualize(data: VisualizeRequest) -> dict[str, str]:
    job = Job(id=str(uuid.uuid4()), kind="visualize", reconstruction_id=data.reconstruction_id)
    JOBS[job.id] = job
    _spawn(_run_visualize_job(job, data.reconstruction_id))
    return {"job_id": job.id}


@post("/api/localize")
async def start_localize(data: LocalizeRequest) -> dict[str, str]:
    # The run id is generated here, up front, rather than left to the CLI to generate — that way
    # the frontend can start polling GET /api/localizations/{run_id}/progress the moment the job
    # id comes back, instead of waiting for the whole (possibly slow, many-image) subprocess to
    # finish and report its own run_id in job.result.
    run_id = str(uuid.uuid4())
    job = Job(id=str(uuid.uuid4()), kind="localize", reconstruction_id=data.reconstruction_id, run_id=run_id)
    JOBS[job.id] = job
    _spawn(_run_localize_job(job, data, run_id))
    return {"job_id": job.id, "run_id": run_id}


def _raise_poll_timeout(reconstruction_id: str | None) -> NoReturn:
    raise TimeoutError(f"Reconstruction {reconstruction_id} did not finish within {RECONSTRUCT_POLL_TIMEOUT_S}s")


async def _run_reconstruct_job(job: Job, capture_id: str, options_json: str | None) -> None:
    try:
        create_args = ["reconstruct", capture_id]
        if options_json:
            create_args += ["--options-json", options_json]
        created = await _run_howard_test_json_async(*create_args)
        job.reconstruction_id = created["id"]
        job.result = created

        deadline = time.monotonic() + RECONSTRUCT_POLL_TIMEOUT_S
        status = created
        while status["status"] not in ("succeeded", "failed", "cancelled"):
            if time.monotonic() > deadline:
                _raise_poll_timeout(job.reconstruction_id)
            await asyncio.sleep(RECONSTRUCT_POLL_INTERVAL_S)
            # --cache: once the reconstruction succeeds, download and cache its tar locally so
            # the Visualize tab's "Create PNG" doesn't re-download it.
            status = await _run_howard_test_json_async("show", job.reconstruction_id, "--cache")
            job.result = status

        if status["status"] == "succeeded":
            job.status = "succeeded"
        else:
            job.status = "failed"
            job.error = status.get("error") or f"Reconstruction ended as {status['status']}"
    except Exception as exc:  # subprocess/parse failure, timeout, etc. — surfaced to the poller
        job.status = "failed"
        job.error = str(exc)


async def _run_visualize_job(job: Job, reconstruction_id: str) -> None:
    try:
        job.result = await _run_howard_test_json_async("visualize", reconstruction_id)
        job.status = "succeeded"
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)


async def _run_localize_job(job: Job, data: LocalizeRequest, run_id: str) -> None:
    try:
        args = ["localize", data.reconstruction_id, data.image_dir, "--run-id", run_id]
        if data.retrieval_top_k is not None:
            args += ["--retrieval-top-k", str(data.retrieval_top_k)]
        if data.ransac_threshold is not None:
            args += ["--ransac-threshold", str(data.ransac_threshold)]
        job.result = await _run_howard_test_json_async(*args)
        job.status = "succeeded"
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)


@get("/api/jobs/{job_id:str}")
async def get_job(job_id: str) -> dict[str, Any]:
    job = JOBS.get(job_id)
    if job is None:
        raise NotFoundException(f"No job {job_id}")
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "reconstruction_id": job.reconstruction_id,
        "run_id": job.run_id,
        "result": job.result,
        "error": job.error,
    }


@get("/api/reconstructions/{reconstruction_id:str}/png")
async def get_png(reconstruction_id: str) -> File:
    path = RECONSTRUCTIONS_DIR / f"{reconstruction_id}.png"
    if not path.exists():
        raise NotFoundException("No PNG cached for this reconstruction yet — run Create PNG first")
    return File(path=path, media_type="image/png")


@get("/api/reconstructions/{reconstruction_id:str}/points")
async def get_points(reconstruction_id: str) -> Response[bytes]:
    # Raw passthrough of `howard-test points`'s binary stdout (count, then flat float32 xyz, then
    # flat uint8 rgb) — see that command's docstring in howard_test.py. The interactive viewer
    # parses this directly with DataView/typed-array views; no JSON round trip either side.
    data = await _run_howard_test_bytes_async("points", reconstruction_id)
    return Response(content=data, media_type="application/octet-stream")


@get("/api/localizations/{run_id:str}")
async def get_localization(run_id: str) -> dict[str, Any]:
    path = LOCALIZATIONS_DIR / run_id / "results.json"
    if not path.exists():
        raise NotFoundException(f"No localization run {run_id}")
    return json.loads(path.read_text())


@get("/api/localizations/{run_id:str}/progress")
async def get_localization_progress(run_id: str) -> dict[str, Any]:
    # The CLI writes this file the instant it starts (completed=0, total=<image count>) and
    # rewrites it after each image, so it's readable well before results.json exists. If the
    # subprocess hasn't even created the run directory yet (a brief window right after the job
    # is spawned), report an empty/unknown progress rather than 404 — the frontend treats that as
    # "still starting" instead of an error.
    path = LOCALIZATIONS_DIR / run_id / "progress.json"
    if not path.exists():
        return {"completed": 0, "total": 0}
    return json.loads(path.read_text())


@post("/api/localizations/{run_id:str}/save-table")
async def save_localization_table(run_id: str, data: SaveTableRequest) -> dict[str, Any]:
    return await _run_howard_test_json_async("localize-save-table", run_id, data.output_path)


@post("/api/localizations/{run_id:str}/save-images")
async def save_localization_images(run_id: str, data: SaveImagesRequest) -> dict[str, Any]:
    return await _run_howard_test_json_async("localize-save-images", run_id, data.output_dir)


@post("/api/tools/export-poses")
async def export_poses(data: ExportPosesRequest) -> dict[str, Any]:
    return await _run_howard_test_json_async("export-poses", data.reconstruction_id, data.output_path)


@dataclass
class ScreenshotRequest:
    plot_title: str
    image_base64: str


_UNSAFE_TITLE_CHARS = re.compile(r"[^A-Za-z0-9._ -]")
_CAPTURE_FILENAME = re.compile(r"^(?P<title>.+)_capture(?P<n>\d+)\.png$")


def _sanitize_title(title: str) -> str:
    cleaned = _UNSAFE_TITLE_CHARS.sub("_", title.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "reconstruction"


@post("/api/screenshots")
async def save_screenshot(data: ScreenshotRequest) -> dict[str, str]:
    title = _sanitize_title(data.plot_title)
    folder = RECONSTRUCTIONS_DIR / title
    folder.mkdir(parents=True, exist_ok=True)

    next_n = 0
    numbers = [int(m["n"]) for f in folder.glob(f"{title}_capture*.png") if (m := _CAPTURE_FILENAME.match(f.name))]
    if numbers:
        next_n = max(numbers) + 1

    path = folder / f"{title}_capture{next_n}.png"
    path.write_bytes(base64.b64decode(data.image_base64))
    return {"path": str(path)}


def _exception_handler(_: Request[Any, Any, Any], exc: Exception) -> Response[dict[str, str]]:
    return Response({"detail": str(exc)}, status_code=500)


cors_config = CORSConfig(allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"])

app = Litestar(
    route_handlers=[
        browse_directories,
        list_captures,
        list_reconstructions,
        delete_reconstruction,
        list_localizations,
        start_reconstruct,
        start_visualize,
        start_localize,
        get_job,
        get_png,
        get_points,
        get_localization,
        get_localization_progress,
        save_localization_table,
        save_localization_images,
        export_poses,
        save_screenshot,
    ],
    cors_config=cors_config,
    exception_handlers={RuntimeError: _exception_handler},
)
