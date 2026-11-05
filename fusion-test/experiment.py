"""Replay one or more fusion algorithms over a run (or a stretch of it), print their metrics, and
open the viewer.

    python experiment.py runs/cd35267b_77963c74
    python experiment.py runs/cd35267b_77963c74 --algo kalman --algo "kalman:gate_chi2=60,slew_s=1"
    python experiment.py runs/cd35267b_77963c74 --start 40 --end 90 --seed-still 160 --algo window:fit_scale=true
    python experiment.py runs/cd35267b_77963c74 --perturb 40:3:0.5 --drop 41,42 --headless

Run it with the workspace venv (numpy, scipy, matplotlib, pillow): ../.venv/bin/python experiment.py ...
Algorithms and their parameters: fusion/algorithms/ (spec "name:param=value,param=value").
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fusion import algorithms, data, metrics, schedule
from fusion.replay import Result, replay


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("run", type=Path, help="Run folder from export.py")
    parser.add_argument("--start", type=float, default=0.0, help="Replay from this time (s)")
    parser.add_argument("--end", type=float, default=None, help="Replay to this time (s)")
    parser.add_argument("--seed-still", type=int, help="Hand this still's fix to the algorithm before the first frame")
    parser.add_argument(
        "--schedule",
        choices=["device", "every"],
        default="device",
        help="device: one request per --interval, dropped while one is in flight; every: every still",
    )
    parser.add_argument("--interval", type=float, default=1.0, help="VPS request interval (s)")
    parser.add_argument("--latency", type=float, default=2.0, help="VPS request-to-answer latency (s)")
    parser.add_argument("--stills", help="Use exactly these stills' fixes (comma-separated), instead of a schedule")
    parser.add_argument("--drop", help="Leave out these stills' fixes (comma-separated)")
    parser.add_argument("--min-inliers", type=int, default=0, help="Leave out fixes with fewer inliers")
    parser.add_argument(
        "--perturb",
        action="append",
        default=[],
        metavar="STILL:DEG:M",
        help="Corrupt a still's fix by a random rotation (deg) and shift (m)",
    )
    parser.add_argument("--delay", action="append", default=[], metavar="STILL:S", help="Delay a still's fix")
    parser.add_argument("--ref-min-inliers", type=int, default=150, help="Fixes the reference is built from")


def build_requests(run: data.Run, args: argparse.Namespace) -> list[schedule.Request]:
    if args.stills:
        requests = schedule.at_stills(run, [int(s) for s in args.stills.split(",")], args.latency)
    elif args.schedule == "every":
        requests = schedule.every_still(run, args.latency, args.start, args.end)
    else:
        requests = schedule.device(run, args.interval, args.latency, args.start, args.end)
    if args.drop:
        requests = schedule.drop(requests, {int(s) for s in args.drop.split(",")})
    if args.min_inliers:
        requests = schedule.min_inliers(requests, args.min_inliers)
    scheduled = {r.still for r in requests}
    for spec in args.perturb:
        still, degrees, metres = spec.split(":")
        _warn_unscheduled(int(still), scheduled, "--perturb")
        requests = schedule.perturb(requests, int(still), float(degrees), float(metres))
    for spec in args.delay:
        still, seconds = spec.split(":")
        _warn_unscheduled(int(still), scheduled, "--delay")
        requests = schedule.delay(requests, int(still), float(seconds))
    return requests


def _warn_unscheduled(still: int, scheduled: set[int], option: str) -> None:
    if still not in scheduled:
        print(f"{option}: still {still} is not in the schedule (scheduled: {sorted(scheduled)})", file=sys.stderr)


def print_table(rows: list[dict[str, float | str]], file=sys.stdout) -> None:  # noqa: ANN001
    if not rows:
        return
    keys = list(rows[0])
    text = [[f"{row[k]:.3g}" if isinstance(row[k], float) else str(row[k]) for k in keys] for row in rows]
    widths = [max(len(k), *(len(r[i]) for r in text)) for i, k in enumerate(keys)]
    print("  ".join(k.ljust(w) for k, w in zip(keys, widths, strict=True)), file=file)
    for r in text:
        print("  ".join(v.ljust(w) for v, w in zip(r, widths, strict=True)), file=file)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_arguments(parser)
    parser.add_argument(
        "--algo", action="append", help="Algorithm spec, e.g. kalman or window:fit_scale=true (repeatable)"
    )
    parser.add_argument("--headless", action="store_true", help="Print metrics only")
    args = parser.parse_args()

    run = data.load(args.run)
    requests = build_requests(run, args)
    ref = metrics.reference(run, min_inliers=args.ref_min_inliers)
    results: list[Result] = []
    for spec in args.algo or ["kalman"]:
        algorithm = algorithms.make(spec)
        results.append(replay(run, algorithm, requests, args.start, args.end, args.seed_still))
    for request in requests:
        if request.note:
            print(f"still {request.still}: {request.note}")
    print_table([metrics.summarize(run, result, ref) for result in results])

    if not args.headless:
        from viz.viewer import Viewer  # noqa: PLC0415 -- matplotlib's window only when asked for

        Viewer(run, results, ref).show()


if __name__ == "__main__":
    main()
