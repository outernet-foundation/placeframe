"""Sweep an algorithm's parameters over a run, headless, and write the metrics as CSV.

    python sweep.py runs/cd35267b_77963c74 --algo kalman --grid gate_chi2=16.81,30,60,120 --grid slew_s=0.5,1,2
    python sweep.py runs/cd35267b_77963c74 --algo window --grid fit_scale=false,true --grid window_fixes=5,10,20 \
        --csv sweeps/window.csv --sort ref_error_median_cm

Takes the same schedule and stretch options as experiment.py. The fixed part of the spec (--algo)
is combined with every combination of the grid.
"""

from __future__ import annotations

import argparse
import csv
import itertools
from pathlib import Path

from experiment import add_arguments, build_requests, print_table
from fusion import algorithms, data, metrics
from fusion.replay import replay


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_arguments(parser)
    parser.add_argument("--algo", default="kalman", help="Algorithm spec with the fixed parameters")
    parser.add_argument("--grid", action="append", default=[], metavar="PARAM=V1,V2,...")
    parser.add_argument("--csv", type=Path, help="Write the table here")
    parser.add_argument("--sort", default="registration_median_px", help="Sort by this metric")
    args = parser.parse_args()

    run = data.load(args.run)
    requests = build_requests(run, args)
    ref = metrics.reference(run, min_inliers=args.ref_min_inliers)
    name, fixed = algorithms.parse(args.algo)
    axes = [(key, values.split(",")) for key, _, values in (g.partition("=") for g in args.grid)]

    rows = []
    for combination in itertools.product(*(values for _, values in axes)):
        settings = {
            **{k: str(v) for k, v in fixed.items()},
            **dict(zip((k for k, _ in axes), combination, strict=True)),
        }
        spec = name + (":" + ",".join(f"{k}={v}" for k, v in settings.items()) if settings else "")
        result = replay(run, algorithms.make(spec), requests, args.start, args.end, args.seed_still)
        row = {"spec": spec, **metrics.summarize(run, result, ref)}
        row.pop("algorithm")
        rows.append(row)
        print(f"done {spec}", flush=True)
    rows.sort(key=lambda r: r[args.sort] if isinstance(r[args.sort], float) and r[args.sort] == r[args.sort] else 1e18)
    print_table(rows)
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {args.csv}")


if __name__ == "__main__":
    main()
