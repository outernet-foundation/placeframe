# Placeframe Dashboard

## Summary

Built the v1 dashboard at `placeframe/dashboard/`:

**`howard_test.py`** (`scripts/src/scripts/howard_test.py`) — added `--json` output to `captures`, `reconstructions`, `show`, `reconstruct`, `visualize`; added local caching (`show --cache` and `reconstruct`'s `--wait` path download the reconstruction tar to `data/reconstructions/<id>.tar` once it succeeds; `visualize` reads from that cache first and defaults its PNG there too — confirmed this cuts a repeat visualize from ~40-60s down to ~1.6s).

**`dashboard/backend/`** — standalone Litestar app (own `.venv`, not part of the placeframe uv workspace) on port 8010. Every route shells out to `uv run howard-test ... --json` with cwd pinned to the placeframe repo root. `POST /api/reconstruct` returns a job id immediately (after the fast "create" call), then a background task polls `show --cache` every 3s until terminal status — so the tar gets cached automatically as soon as a reconstruction succeeds, before anyone even clicks "Create PNG". `POST /api/visualize` is the same fire-and-poll shape. `GET /api/jobs/{id}` is what the frontend polls.

**`dashboard/frontend/`** — Vite + React + TypeScript on port 5174. Reconstruct tab (capture list → dialog with capture picker + options JSON → live job status banner) and Visualize tab (reconstruction list → Create PNG / disabled Interactive stub / View → inline point-cloud image).

Verified end-to-end in the browser: capture list loads, dialog opens, reconstructions list shows live status for an in-flight job (`queued` → `matching_features` → `reconstructing`, tracked via a real background reconstruction), and "View" renders the cached PNG inline.

## Key decisions (from the clarifying-questions round)

- **Location**: inside the placeframe repo, in `dashboard/`, not a separate sibling repo — so it always runs against this checkout's `uv run howard-test` and `.env` with no path configuration.
- **Tech stack**: lighter, no Docker — Litestar backend + Vite/React/TS frontend, run directly via `uv run` / `npm run dev`, no Postgres/containers. Can containerize later once the shape settles.
- **Long jobs**: fire-and-poll — backend kicks off the CLI command in the background and returns immediately; frontend polls a status endpoint for live progress.
- **Local caching**: yes — `reconstruct` downloads/keeps the finished reconstruction tar at `data/reconstructions/<id>.tar`; `visualize` reads from that cache when present and writes its PNG there too.

## Running it

Both dev servers run independently, outside Docker:

```bash
cd dashboard/backend && uv run uvicorn app:app --reload --port 8010
cd dashboard/frontend && npm run dev   # http://localhost:5174
```

`dashboard/backend` is a standalone `uv` project (its own `pyproject.toml`, `.venv`) — not a member of the root placeframe uv workspace — specifically so it doesn't get swept into `uv sync --all-packages`, `lock-python`, `preflight`, or codegen. It only needs `litestar` + `uvicorn`.

`data/`, `dashboard/backend/.venv/`, `dashboard/backend/__pycache__/`, `dashboard/frontend/node_modules/`, and `dashboard/frontend/dist/` are all gitignored.

## Not yet built

- **Interactive tab**: the "Interactive" button in the Visualize tab is a disabled stub. Eventual scope: an interactive 3D window for point clouds and camera poses (raw and corrected).
- **Odometry drift correction**: absolute-pose-estimate correction of odometry drift, surfaced in the interactive viewer as "raw" vs "corrected" poses. Not started.
- **Capture upload UI**: the Reconstruct tab only lists and reconstructs *existing* server-side captures; there's no dashboard flow yet for uploading a new capture tar (the CLI's `upload`/`run` commands still work standalone, just aren't wired into the UI).

## Reference

- `scripts/AGENTS.md` — `howard-test` sits alongside the other `scripts/` CLIs; this dashboard is purely a UI over it, no new business logic.
- `docker/AGENTS.md` — reconstruction is a worker-pull architecture (lease-server), which is why "create" and "start" are the same API call and why the dashboard's poll loop is necessary (there's no server-side push of progress).
