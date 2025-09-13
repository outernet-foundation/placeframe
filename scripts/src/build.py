from __future__ import annotations

import json
import os
import shlex
import tempfile
from pathlib import Path
from typing import Literal, TypedDict, cast

from common.run_command import run_command, run_streaming
from pydantic import TypeAdapter
from rich import Optional
from typer import Option, Typer

workspace_directory = Path("..").resolve()
images_path = workspace_directory / "images.json"
images_lock_path = workspace_directory / "images-lock.json"
infrastructure_directory = workspace_directory / "infra"


class Image(TypedDict):
    stack: str
    first_party: bool
    context: str
    dockerfile: str
    hash_paths: list[str]
    tag: str


class ImageLock(TypedDict):
    digest: str
    tags: list[str]


class FirstPartyPlan(TypedDict):
    name: str
    kind: Literal["first_party"]
    stack: str
    repo: str
    context: str
    dockerfile: str
    tree_sha: str


class ThirdPartyPlan(TypedDict):
    name: str
    kind: Literal["third_party"]
    stack: str
    repo: str


class _Manifest(TypedDict, total=False):
    digest: str


ImagesOption = Option(None, "--image", "--images", "-i", help="Image name; can be repeated.")
AllOption = Option(False, "--all", "-all", help="Select all images in images.json")

app = Typer()


@app.command()
def plan(images: Optional[list[str]] = ImagesOption, all_: Optional[bool] = AllOption):
    _, plan = create_plan(images, all_)
    print(json.dumps(plan, indent=2))


@app.command()
def lock(image: list[str] = ImagesOption, all_: bool = AllOption):
    images_lock, plan = create_plan(image, all_)
    lock_images(images_lock, plan)


def create_plan(images: Optional[list[str]] = None, all_: Optional[bool] = False):
    if images is None and not all_:
        raise ValueError("Either 'images' or 'all_' must be provided")

    if not images_path.is_file():
        raise FileNotFoundError(f"{images_path} not found")

    all_images = TypeAdapter(dict[str, Image]).validate_json(json.load(images_path.open("r", encoding="utf-8")))
    images_lock = TypeAdapter(dict[str, ImageLock]).validate_json(
        json.load(images_lock_path.open("r", encoding="utf-8"))
    )

    selected_images = all_images if not images else {name: all_images[name] for name in images}

    return images_lock, [
        image_plan
        for image_plan in (
            create_image_plan(image_name, image, images_lock.get(image_name))
            for image_name, image in selected_images.items()
        )
        if image_plan is not None
    ]


def create_image_plan(
    image_name: str, image: Image, image_lock: ImageLock | None
) -> FirstPartyPlan | ThirdPartyPlan | None:
    if image["first_party"] and (not image.get("context") or not image.get("dockerfile")):
        raise ValueError(f"first_party image '{image_name}' requires 'context' and 'dockerfile'")

    stack = image["stack"]

    image_repo = run_command(
        f"pulumi stack output --stack {stack} {image_name}-image-repo-url", cwd=infrastructure_directory
    ).strip()

    if not image["first_party"]:
        if image_lock is not None:
            return

        return {"name": image_name, "kind": "third_party", "stack": stack, "repo": image_repo}

    context = image["context"]

    with tempfile.TemporaryDirectory() as temporary_directory:
        environment = os.environ.copy()
        environment["GIT_INDEX_FILE"] = str(Path(temporary_directory) / "index")
        environment["GIT_OBJECT_DIRECTORY"] = str(Path(temporary_directory) / "objects")
        Path(environment["GIT_OBJECT_DIRECTORY"]).mkdir(parents=True, exist_ok=True)
        quoted_paths_string = " ".join(
            shlex.quote(path) for path in (image["hash_paths"] if "hash_paths" in image else [context])
        )
        run_command(f"git add -A -- {quoted_paths_string}", env=environment, cwd=workspace_directory)
        tree_sha_value = run_command("git write-tree", env=environment, cwd=workspace_directory).strip()

    if image_lock is not None and tree_sha_value == next(
        (tag[5:] for tag in image_lock["tags"] if tag.startswith("tree-")), None
    ):
        return

    return {
        "name": image_name,
        "kind": "first_party",
        "stack": stack,
        "repo": image_repo,
        "context": str((workspace_directory / context).resolve()),
        "dockerfile": str((workspace_directory / context / image["dockerfile"]).resolve()),
        "tree_sha": tree_sha_value,
    }


def lock_images(images_lock: dict[str, ImageLock], plan: list[FirstPartyPlan | ThirdPartyPlan]) -> None:
    git_sha = run_command("git rev-parse --short HEAD", cwd=workspace_directory).strip()

    for image_plan in plan:
        if image_plan["kind"] == "third_party":
            print(f"Skipping third-party image: {image_plan['name']}")
            continue

        image_repo_url = run_command(
            f"pulumi stack output --stack {image_plan['stack']} {image_plan['name']}-image-repo-url",
            cwd=infrastructure_directory,
        ).strip()

        tree_sha_tag = f"{image_repo_url}:tree-{image_plan['tree_sha']}"
        git_sha_tag = f"{image_repo_url}:git-{git_sha}"
        digest = get_digest(tree_sha_tag)

        if digest is not None:
            print(f"Image with tag {tree_sha_tag} already exists, skipping build.")
        else:
            print(f"Building and pushing image: {image_plan['name']}")

            run_streaming(
                "docker buildx build --push --platform linux/amd64 --provenance=false"
                + f" -t {git_sha_tag} -t {tree_sha_tag}"
                + f' -f "{workspace_directory / image_plan["context"] / image_plan["dockerfile"]}"'
                + f' "{workspace_directory / image_plan["context"]}"'
            )

            digest = get_digest(tree_sha_tag)

            if digest is None:
                raise RuntimeError(f"Failed to get digest for image {image_plan['name']} after push.")

        images_lock[image_plan["name"]] = {
            "digest": digest,
            "tags": [f"tree-{image_plan['tree_sha']}", f"git-{git_sha}"],
        }

    with images_lock_path.open("w", encoding="utf-8") as file:
        json.dump(images_lock, file, indent=2)


def get_digest(ref: str) -> str | None:
    return cast(
        _Manifest,
        json.loads(
            run_command(f"docker buildx imagetools inspect --format '{{{{json .Manifest}}}}' {shlex.quote(ref)}")
        ),
    ).get("digest")
