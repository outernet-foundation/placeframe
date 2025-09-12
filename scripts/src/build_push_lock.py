from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Literal, TypedDict, cast

from pydantic import BaseModel, model_validator

workspace_dir = Path("..").resolve()
infra_dir = workspace_dir / "infra"


def run_command(command: str, cwd: Path | None = None, env: dict[str, str] | None = None):
    print(f"Running command: {command}")

    try:
        process = subprocess.run(
            shlex.split(command, posix=True), cwd=cwd, env=env, check=True, text=True, capture_output=True
        )
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, command, output=process.stdout, stderr=process.stderr
            )
        if process.stdout:
            print(process.stdout)
        if process.stderr:
            print(process.stderr)
        return process.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        if e.output:
            print(e.output)
        if e.stderr:
            print(e.stderr)
        raise


def run_streaming(command: str, cwd: Path | None = None) -> None:
    """
    Run a long command and stream combined stdout/stderr line-by-line to our console.
    Raises CalledProcessError on non-zero exit.
    """
    print(f"Running (streaming): {command}")
    proc = subprocess.Popen(
        shlex.split(command, posix=True),
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # line-buffered in text mode
    )
    assert proc.stdout is not None
    try:
        for line in proc.stdout:
            # docker buildx often emits frequent updates; flush so they appear immediately
            print(line, end="", flush=True)
    finally:
        rc = proc.wait()
        if rc != 0:
            raise subprocess.CalledProcessError(rc, command)


class ImageSpec(BaseModel):
    stack: Literal["core", "dev", "prod"]
    first_party: bool
    context: str | None = None
    dockerfile: str | None = None
    hash_paths: List[str] | None = None

    @model_validator(mode="after")
    def _enforce_relations(self) -> ImageSpec:
        if self.first_party:
            if not self.dockerfile:
                raise ValueError("first_party=true requires `dockerfile`.")
            if not self.context:
                raise ValueError("first_party=true requires `context`.")
        else:
            if self.hash_paths is not None:
                raise ValueError("`hash_paths` must be omitted when first_party=false.")
        return self


def get_image_spec(image_name: str) -> ImageSpec:
    images_path = workspace_dir / "images.json"
    if not images_path.is_file():
        raise FileNotFoundError(f"Images file not found: {images_path}")
    with images_path.open("r", encoding="utf-8") as file:
        images = json.load(file)
        if image_name not in images:
            raise ValueError(f"Image '{image_name}' not found in {images_path}")
        return ImageSpec(**images[image_name])


class _Manifest(TypedDict, total=False):
    digest: str


def get_digest(ref: str) -> str | None:
    try:
        output = run_command(f"docker buildx imagetools inspect --format '{{{{json .Manifest}}}}' {shlex.quote(ref)}")
        ouput_json = json.loads(output)
        return cast(_Manifest, ouput_json).get("digest")
    except subprocess.CalledProcessError:
        return None


def build_push_lock(image_name: str):
    image_spec = get_image_spec(image_name)
    if image_spec.first_party is False:
        raise ValueError("build_push_lock is only for first-party images.")

    assert image_spec.context is not None

    # Compute tree hash of the relevant paths
    # NOTE!!!: This creates a completely different hash than the logic in the workflow file
    with tempfile.TemporaryDirectory() as td:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(Path(td) / "index")
        env["GIT_OBJECT_DIRECTORY"] = str(Path(td) / "objects")
        os.makedirs(env["GIT_OBJECT_DIRECTORY"], exist_ok=True)
        hash_paths = image_spec.hash_paths or [image_spec.context]
        run_command(f"git add -A -- {(' '.join(shlex.quote(path) for path in hash_paths))}", env=env, cwd=workspace_dir)
        tree_hash_tag = f"tree-{run_command('git write-tree', env=env, cwd=workspace_dir).strip()}"

    # Current commit hash (tag like your CI's "git-<sha>")
    git_hash_tag = f"git-{run_command('git rev-parse HEAD').strip()}"

    # Get repo URL from Pulumi
    repo_url = run_command(
        f"pulumi stack output --stack {image_spec.stack} {image_name}-image-repo-url", cwd=infra_dir
    ).strip()

    # Check if image with this tag already exists and get its digest
    digest = get_digest(f"{repo_url}:{tree_hash_tag}")

    # If the image doesn't exist, build and push it
    if digest is not None:
        print(f"Image {image_name} with tag {tree_hash_tag} already exists, skipping build.")
    else:
        assert image_spec.dockerfile is not None

        # Build and push the image
        run_streaming(
            f'docker buildx build --push --platform linux/amd64 --provenance=false -t {repo_url}:{git_hash_tag} -t {repo_url}:{tree_hash_tag} -f "{workspace_dir / image_spec.context / image_spec.dockerfile}" "{workspace_dir / image_spec.context}"'
        )

        # Get the digest of the newly pushed image
        digest = get_digest(f"{repo_url}:{tree_hash_tag}")
        if digest is None:
            raise RuntimeError("Failed to get digest of the pushed image")

        print(f"Successfully built and pushed image '{image_name}'")

    # Load the lock file or initialize an empty one
    lock_path = infra_dir / "image-lock.json"
    if lock_path.is_file():
        with lock_path.open("r", encoding="utf-8") as file:
            lock_data = json.load(file)
    else:
        lock_data = {}

    # Update the lock file
    lock_data[image_name] = {"digest": digest, "tags": [tree_hash_tag, git_hash_tag]}

    # Write back the lock file
    with lock_path.open("w", encoding="utf-8") as file:
        json.dump(lock_data, file, indent=2)

    print(f"Updated lock file at {lock_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run build_push_lock.py <image-name>")
        sys.exit(1)

    image_name = sys.argv[1]

    try:
        build_push_lock(image_name)
    except Exception as e:
        print(f"Error: {e}")
