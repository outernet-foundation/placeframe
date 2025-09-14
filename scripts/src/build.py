from __future__ import annotations

import json
import os
import shlex
import tempfile
from pathlib import Path
from subprocess import CalledProcessError
from typing import Literal, NotRequired, Optional, TypedDict, cast

from common.run_command import run_command, run_streaming
from pydantic import TypeAdapter
from typer import Option, Typer

workspace_directory = Path("..").resolve()
images_path = workspace_directory / "images.json"
images_lock_path = workspace_directory / "images-lock.json"
infrastructure_directory = workspace_directory / "infra"


class Image(TypedDict):
    stack: str
    first_party: bool
    context: NotRequired[str]
    dockerfile: NotRequired[str]
    hash_paths: NotRequired[list[str]]


class ImageLock(TypedDict):
    digest: str
    tags: list[str]


class FirstPartyPlan(TypedDict):
    kind: Literal["first_party"]
    stack: str
    image_repo_url: str
    context: str
    dockerfile: str
    tree_sha: str


class ThirdPartyPlan(TypedDict):
    kind: Literal["third_party"]
    stack: str
    image_repo_url: str


def create_plan(images: Optional[list[str]] = None, all_: Optional[bool] = False):
    # Load images.json and images-lock.json
    all_images = TypeAdapter(dict[str, Image]).validate_python(json.load(images_path.open("r", encoding="utf-8")))
    images_lock = TypeAdapter(dict[str, ImageLock]).validate_python(
        json.load(images_lock_path.open("r", encoding="utf-8")) if images_lock_path.is_file() else {}
    )

    # Select images
    selected_images = all_images if not images else {name: all_images[name] for name in images}

    # Get Pulumi stack outputs for selected images
    stacks: dict[str, dict[str, str]] = {}
    for stack in {img["stack"] for img in selected_images.values()}:
        stacks[stack] = json.loads(
            run_command(f"pulumi stack output --stack {shlex.quote(stack)} --json", cwd=infrastructure_directory)
        )

    # Create plan
    plan: dict[str, FirstPartyPlan | ThirdPartyPlan] = {}
    for image_name, image in selected_images.items():
        result = create_image_plan(
            image_name, image, images_lock.get(image_name), stacks[image["stack"]][f"{image_name}-image-repo-url"]
        )
        if result is not None:
            image_name, image_plan = result
            plan[image_name] = image_plan

    return images_lock, plan


def create_image_plan(
    image_name: str, image: Image, image_lock: ImageLock | None, image_repo_url: str
) -> tuple[str, FirstPartyPlan | ThirdPartyPlan] | None:
    stack = image["stack"]

    # If this is a third party image and is not locked, return a plan to lock it
    if not image["first_party"]:
        if image_lock is not None:
            return

        return image_name, {"kind": "third_party", "stack": stack, "image_repo_url": image_repo_url}

    # This is a first party image and must have context and dockerfile
    if "context" not in image or "dockerfile" not in image:
        raise ValueError(f"first_party image '{image_name}' requires 'context' and 'dockerfile'")

    context = image["context"]

    # Compute tree SHA by creating a temporary git index and object directory
    with tempfile.TemporaryDirectory() as temporary_directory:
        environment = os.environ.copy()
        environment["GIT_INDEX_FILE"] = str(Path(temporary_directory) / "index")
        environment["GIT_OBJECT_DIRECTORY"] = str(Path(temporary_directory) / "objects")
        Path(environment["GIT_OBJECT_DIRECTORY"]).mkdir(parents=True, exist_ok=True)
        quoted_paths_string = " ".join(
            shlex.quote(path) for path in (image["hash_paths"] if "hash_paths" in image else [context])
        )
        run_command(f"git add -A -- {quoted_paths_string}", env=environment, cwd=workspace_directory)
        tree_sha = run_command("git write-tree", env=environment, cwd=workspace_directory).strip()
        # temp nonce
        tree_sha += "5"

    # If the image is already locked to this tree SHA, skip it
    if image_lock is not None and tree_sha == next(
        (tag[5:] for tag in image_lock["tags"] if tag.startswith("tree-")), None
    ):
        return

    return image_name, {
        "kind": "first_party",
        "stack": stack,
        "image_repo_url": image_repo_url,
        "context": context,
        "dockerfile": image["dockerfile"],
        "tree_sha": tree_sha,
    }


def lock_images(
    images_lock: dict[str, ImageLock],
    plan: dict[str, FirstPartyPlan | ThirdPartyPlan],
    cache_type: str,
    output_path: Path | None = None,
):
    git_sha = run_command("git rev-parse HEAD", cwd=workspace_directory).strip()

    if output_path is None:
        output_path = images_lock_path
    else:
        images_lock = {}

    for image_name, image_plan in plan.items():
        print(f"Processing image: {image_name}")
        images_lock[image_name] = lock_image(image_name, image_plan, git_sha, cache_type)

    print(f"Writing {output_path}")
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(images_lock, file, indent=2)


def lock_image(
    image_name: str, image_plan: FirstPartyPlan | ThirdPartyPlan, git_sha: str, cache_type: str
) -> ImageLock:
    # If this is a third party image, just get the latest digest, which will pull the image if not present
    if image_plan["kind"] == "third_party":
        digest = get_digest(image_plan["image_repo_url"] + ":latest")
        return {"digest": digest if digest is not None else "", "tags": ["latest"]}

    # Construct tags
    tree_sha_tag = f"{image_plan['image_repo_url']}:tree-{image_plan['tree_sha']}"
    git_sha_tag = f"{image_plan['image_repo_url']}:git-{git_sha}"

    print(f"Checking for existing image with tag: {tree_sha_tag}")
    digest = get_digest(tree_sha_tag)

    if digest is not None:
        print(f"Image with tag {tree_sha_tag} already exists, skipping build.")
    else:
        print(f"Building and pushing image: {image_name}")
        cache_type_extra: str = ""
        if cache_type == "registry":
            cache_type_extra += f"ref={image_plan['image_repo_url']}"
        elif cache_type == "gha":
            cache_type_extra += f"scope={image_name}"
        else:
            raise ValueError(f"Unknown cache type: {cache_type}")

        run_streaming(
            "docker buildx build --push --platform linux/amd64 --provenance=false"
            + f" --cache-from type={cache_type},{cache_type_extra}:cache"
            + f" --cache-to type={cache_type},{cache_type_extra}:cache,mode=max"
            + f" -t {git_sha_tag} -t {tree_sha_tag}"
            + f' -f "{workspace_directory / image_plan["context"] / image_plan["dockerfile"]}"'
            + f' "{workspace_directory / image_plan["context"]}"'
        )

        print(f"Getting digest for image with tag: {tree_sha_tag}")
        digest = get_digest(tree_sha_tag)

        if digest is None:
            raise RuntimeError(f"Failed to get digest for image {image_name} after push.")

    return {"digest": digest, "tags": [f"tree-{image_plan['tree_sha']}", f"git-{git_sha}"]}


class ManifestDict(TypedDict, total=False):
    digest: str


def get_digest(ref: str):
    try:
        return cast(
            ManifestDict,
            json.loads(
                run_command(f"docker buildx imagetools inspect --format '{{{{json .Manifest}}}}' {shlex.quote(ref)}")
            ),
        ).get("digest")  # now str | None, not Unknown
    except CalledProcessError:
        return None


ImageOption = Option(None, "--image", "-i", help="Image name; can be repeated.")
AllOption = Option(False, "--all", "-a", help="Select all images in images.json")
PlanOption = Option(None, "--plan", "-p", help="Path to a plan JSON file (dict keyed by image name).")
CacheTypeOption = Option("registry", "--cache-type", "-c", help="Type of cache to use when building images.")
PlanOutputPathOption = Option(..., "--output", "-o", help="Path to write the plan JSON file.")
LockOutputPathOption = Option(None, "--output", "-o", help="Path to write the images-lock.json file.")

app = Typer()


@app.command()
def plan(
    images: Optional[list[str]] = ImageOption, all_: Optional[bool] = AllOption, plan_path: str = PlanOutputPathOption
):
    if images is None and not all_:
        raise ValueError("Either '--images' or '--all' must be provided")

    if not images_path.is_file():
        raise FileNotFoundError(f"{images_path} not found")

    _, plan = create_plan(images, all_)

    with open(plan_path, "w") as plan_file:
        json.dump(plan, plan_file, indent=2)


@app.command()
def lock(
    images: Optional[list[str]] = ImageOption,
    all_: bool = AllOption,
    plan_path: Optional[str] = PlanOption,
    cache_type: str = CacheTypeOption,
    output_path: Optional[Path] = LockOutputPathOption,
):
    if images is None and not all_ and plan_path is None:
        raise ValueError("One of '--images', '--all', or '--plan' must be provided")

    if plan_path:
        if not Path(plan_path).is_file():
            raise FileNotFoundError(f"{plan_path} not found")

        with open(plan_path) as plan_file, open(images_lock_path) as images_lock_file:
            plan = TypeAdapter(dict[str, FirstPartyPlan | ThirdPartyPlan]).validate_python(json.load(plan_file))
            images_lock = TypeAdapter(dict[str, ImageLock]).validate_python(json.load(images_lock_file))
    else:
        if not images_path.is_file():
            raise FileNotFoundError(f"{images_path} not found")

        images_lock, plan = create_plan(images, all_)

    lock_images(images_lock, plan, cache_type, output_path)


if __name__ == "__main__":
    app()
