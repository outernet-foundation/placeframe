from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Literal

from pydantic import BaseModel, model_validator

services_dir = Path("../services").resolve()
infra_dir = Path("../infra").resolve()


def run_command(command: str, cwd: Path | None = None) -> str:
    print(f"Running command: {command}")

    try:
        process = subprocess.run(
            command.split(),
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True,
        )
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode,
                command,
                output=process.stdout,
                stderr=process.stderr,
            )
        if process.stdout:
            print(process.stdout)
        if process.stderr:
            print(process.stderr)
        return process.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command '{command}' failed with exit code {e.returncode}")
        if e.output:
            print("Output:")
            print(e.output)
        if e.stderr:
            print("Error output:")
            print(e.stderr)
        raise


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
    images_path = services_dir / "images.json"
    if not images_path.is_file():
        raise FileNotFoundError(f"Images file not found: {images_path}")
    with images_path.open("r", encoding="utf-8") as file:
        images = json.load(file)
        if image_name not in images:
            raise ValueError(f"Image '{image_name}' not found in {images_path}")
        return ImageSpec(**images[image_name])


def get_digest(ref: str):
    output = run_command(
        f"docker buildx imagetools inspect --format '{{{{json .}}}}' {ref}"
    )
    output = json.loads(output)
    return output["Digest"]


def build_push_lock(image_name: str):
    image_spec = get_image_spec(image_name)
    if image_spec.first_party is False:
        raise ValueError("build_push_lock is only for first-party images.")

    assert image_spec.context is not None

    # Compute tree hash
    tree_hash = hashlib.sha1(
        " ".join(
            [
                run_command(f"git rev-parse HEAD:{path}")
                for path in image_spec.hash_paths or [image_spec.context]
            ]
        ).encode()
    ).hexdigest()

    # Get current git hash
    git_hash = run_command("git rev-parse HEAD").strip()

    # Get repo URL from Pulumi
    repo_url = run_command(
        f"pulumi stack output --stack {image_spec.stack} {image_name}-image-repo-url",
        cwd=infra_dir,
    ).strip()

    # Check if image with this tag already exists and get its digest
    digest = get_digest(f"{repo_url}:{tree_hash}")

    # If the image doesn't exist, build and push it
    if digest is None:
        assert image_spec.dockerfile is not None

        # Build and push the image
        run_command(
            f"docker buildx build --push --platform linux/amd64,linux/arm64 -t {repo_url}:{tree_hash} -t {repo_url}:{git_hash} -f {services_dir / image_spec.dockerfile} {services_dir / image_spec.context}"
        )

        # Get the digest of the newly pushed image
        digest = get_digest(f"{repo_url}:{tree_hash}")
        if digest is None:
            raise RuntimeError("Failed to get digest of the pushed image")

    # Load the lock file or initialize an empty one
    lock_path = infra_dir / "image-lock.json"
    if lock_path.is_file():
        with lock_path.open("r", encoding="utf-8") as file:
            lock_data = json.load(file)
    else:
        lock_data = {}

    # Update the lock file
    lock_data[image_name] = {"tags": [tree_hash, git_hash], "digest": digest}

    # Write back the lock file
    with lock_path.open("w", encoding="utf-8") as file:
        json.dump(lock_data, file, indent=2)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run build_push_lock.py <image-name>")
        sys.exit(1)

    image_name = sys.argv[1]

    try:
        build_push_lock(image_name)
        print(f"Successfully built and pushed image '{image_name}'")
    except Exception as e:
        print(f"Error: {e}")
