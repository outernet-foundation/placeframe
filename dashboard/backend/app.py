"""Dashboard backend: a thin HTTP wrapper around `uv run howard-test`.

Every action the dashboard offers is literally the corresponding `howard-test` subcommand run as
a subprocess with `--json`, executed with cwd set to the placeframe repo root so `uv run` resolves
against *that* workspace (this project deliberately isn't a member of it — see dashboard/AGENTS.md
if that file exists, or the placeframe conversation history that motivated this layout).

Run with (from this directory): uv run uvicorn app:app --reload --port 8010
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from litestar import Litestar, Request, get, post
from litestar.config.cors import CORSConfig
from litestar.exceptions import HTTPException, NotFoundException
from litestar.response import File

PLACEFRAME_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PLACEFRAME_ROOT / "data"
RECONSTRUCTIONS_DIR = DATA_DIR / "reconstructions"

# Wall-clock cap on a background reconstruct job's status-poll loop; mirrors howard_test.py's own
# RECONSTRUCTION_TIMEOUT_S so a stuck reconstruction doesn't poll forever.
RECONSTRUCT_POLL_TIMEOUT_S = 1800.0
RECONSTRUCT_POLL_INTERVAL_S = 3.0

JobKind = Literal["reconstruct", "visualize"]
JobStatus = Literal["running", "succeeded", "failed"]


@dataclass
class Job:
    id: str
    kind: JobKind
    status: JobStatus = "running"
    reconstruction_id: str | None = None
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


@get("/api/captures")
async def list_captures() -> list[dict[str, Any]]:
    return await _run_howard_test_json_async("captures")


@get("/api/reconstructions")
async def list_reconstructions() -> list[dict[str, Any]]:
    return await _run_howard_test_json_async("reconstructions")


@dataclass
class ReconstructRequest:
    capture_id: str
    options_json: str | None = None


@dataclass
class VisualizeRequest:
    reconstruction_id: str


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
                raise TimeoutError(f"Reconstruction {job.reconstruction_id} did not finish within {deadline}s")
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
        "result": job.result,
        "error": job.error,
    }


@get("/api/reconstructions/{reconstruction_id:str}/png")
async def get_png(reconstruction_id: str) -> File:
    path = RECONSTRUCTIONS_DIR / f"{reconstruction_id}.png"
    if not path.exists():
        raise NotFoundException("No PNG cached for this reconstruction yet — run Create PNG first")
    return File(path=path, media_type="image/png")


def _exception_handler(_: Request[Any, Any, Any], exc: Exception) -> HTTPException:
    return HTTPException(status_code=500, detail=str(exc))


cors_config = CORSConfig(allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"])

app = Litestar(
    route_handlers=[
        list_captures,
        list_reconstructions,
        start_reconstruct,
        start_visualize,
        get_job,
        get_png,
    ],
    cors_config=cors_config,
    exception_handlers={RuntimeError: _exception_handler},
)
