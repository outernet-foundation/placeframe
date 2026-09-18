from __future__ import annotations

import os
from pathlib import Path

import typer
from bashrun import bash
from stack_lifecycle.image_refs import collect_repo_references

from unity_buildkit.ci_step import ci_step

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

MIRROR_PREFIX = "ghcr.io/outernet-foundation/mirror"
CRANE_VERSION = "v0.22.1"


@app.command()
def main() -> None:
    targets = {
        occurrence.reference: occurrence.reference[len(MIRROR_PREFIX) + 1 :]
        for occurrence in collect_repo_references(Path.cwd(), dockerfile_glob=None)
        if occurrence.reference.startswith(f"{MIRROR_PREFIX}/")
    }
    with ci_step("Install crane"):
        sudo = "sudo " if os.geteuid() != 0 else ""
        archive = "go-containerregistry_Linux_x86_64.tar.gz"
        bash(f"curl -fsSLO https://github.com/google/go-containerregistry/releases/download/{CRANE_VERSION}/{archive}")
        bash(f"{sudo}tar -xzf {archive} -C /usr/local/bin/ crane")
        Path(archive).unlink()
    for mirrored, upstream in sorted(targets.items()):
        with ci_step(f"Mirror {upstream} -> {mirrored}"):
            bash(f"crane copy {upstream} {mirrored}")
    print(f"Mirrored images: {len(targets)}")
