from __future__ import annotations

import json
import os
import shlex
import tempfile
from pathlib import Path
from subprocess import CalledProcessError
from typing import Literal, NotRequired, Optional, TypedDict, cast

from pydantic import TypeAdapter
from typer import Option, Typer

from .run_command import run_command

workspace_directory = Path("..").resolve()
images_path = workspace_directory / "images.json"
images_lock_path = workspace_directory / "images.lock"
infrastructure_directory = workspace_directory / "infrastructure"


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


def create_plan(images: Optional[list[str]] = None, stack: Optional[str] = None):
    # Load images.json and images.lock
    all_images = TypeAdapter(dict[str, Image]).validate_python(json.load(images_path.open("r", encoding="utf-8")))
    images_lock = TypeAdapter(dict[str, ImageLock]).validate_python(
        json.load(images_lock_path.open("r", encoding="utf-8")) if images_lock_path.is_file() else {}
    )

    # Select images
    selected_images: dict[str, Image]
    if images:
        selected_images = {name: all_images[name] for name in images}
    else:
        assert stack is not None
        if stack == "all":
            selected_images = {name: image for name, image in all_images.items()}
        else:
            selected_images = {name: image for name, image in all_images.items() if image["stack"] == stack}

    # Get Pulumi stack outputs for selected images
    stacks: dict[str, dict[str, str]] = {}
    for stack in {img["stack"] for img in selected_images.values()}:
        print(f"Getting Pulumi stack outputs for stack: {stack}")
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
        print(f"Computed tree SHA for image {image_name}: {tree_sha}")

    # If the image is already locked to this tree SHA, skip it
    if image_lock is not None and tree_sha == next(
        (tag[5:] for tag in image_lock["tags"] if tag.startswith("tree-")), None
    ):
        print(f"Image {image_name} is already locked to tree SHA {tree_sha}")
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

    if plan == {}:
        print("Nothing to lock")
        return

    for image_name, image_plan in plan.items():
        print(f"Locking image: {image_name}")
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

        if cache_type == "registry":
            cache_type = f"registry,ref={image_plan['image_repo_url']}:cache"
        elif cache_type == "gha":
            cache_type = f"gha,scope={image_name}"
        else:
            raise ValueError(f"Unknown cache type: {cache_type}")

        run_command(
            "docker buildx build --push --platform linux/amd64 --provenance=false"
            + f" --cache-from type={cache_type}"
            + f" --cache-to type={cache_type},mode=max"
            + f" -t {git_sha_tag} -t {tree_sha_tag}"
            + f' -f "{workspace_directory / image_plan["context"] / image_plan["dockerfile"]}"'
            + f' "{workspace_directory / image_plan["context"]}"',
            stream_log=True,
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
        # IMPORTANT: exactly two braces, not four.
        fmt = '"{{json .Manifest}}"'
        # Put the ref before --format (more robust on Windows CLIs)
        cmd = f"docker buildx imagetools inspect {ref} --format {fmt}"
        out = run_command(cmd, log=True)
        return cast(ManifestDict, json.loads(out)).get("digest")
    except CalledProcessError as exception:
        if "authorization failed" in exception.stderr:
            # If you hit this, you might need to add a credHelper to your ~/.docker/config.json
            # e.g.
            # "credHelpers": {
            #     "339712749848.dkr.ecr.us-east-1.amazonaws.com": "ecr-login"
            # }
            print(f"Warning: Failed to get digest for {ref}: authorization failed")
            raise exception

        # This is brittle; we should first inspect the repo itself and reraise if that fails,
        # then inspect the the full ref and reraise if that fails with anything other than "not found"
        return None


ImageOption = Option(None, "--image", "-i", help="Image name; can be repeated.")
StackOption = Option(None, "--stack", "-s", help="Pulumi stack name, or all")
PlanOption = Option(None, "--plan", "-p", help="Path to a plan JSON file (dict keyed by image name).")
CacheTypeOption = Option("registry", "--cache-type", "-c", help="Type of cache to use when building images.")
PlanOutputPathOption = Option(..., "--output", "-o", help="Path to write the plan JSON file.")
LockOutputPathOption = Option(None, "--output", "-o", help="Path to write the images-lock.json file.")

app = Typer()


@app.command()
def plan(
    images: Optional[list[str]] = ImageOption, stack: Optional[str] = StackOption, plan_path: str = PlanOutputPathOption
):
    if images is None and not stack:
        raise ValueError("Either '--images' or '--stack' must be provided")
    if stack and images is not None:
        raise ValueError("Cannot provide both '--images' and '--stack'")

    if not images_path.is_file():
        raise FileNotFoundError(f"{images_path} not found")

    _, plan = create_plan(images, stack)

    with open(plan_path, "w") as plan_file:
        json.dump(plan, plan_file, indent=2)


@app.command()
def lock(
    images: Optional[list[str]] = ImageOption,
    stack: Optional[str] = StackOption,
    plan_path: Optional[str] = PlanOption,
    cache_type: str = CacheTypeOption,
    output_path: Optional[Path] = LockOutputPathOption,
):
    if images is None and not stack and plan_path is None:
        raise ValueError("Either '--images', '--stack', or '--plan' must be provided")
    if sum([bool(stack), images is not None, plan_path is not None]) > 1:
        raise ValueError("Only one of '--stack', '--images', or '--plan' may be provided")

    if plan_path:
        if not Path(plan_path).is_file():
            raise FileNotFoundError(f"{plan_path} not found")

        with open(plan_path) as plan_file, open(images_lock_path) as images_lock_file:
            plan = TypeAdapter(dict[str, FirstPartyPlan | ThirdPartyPlan]).validate_python(json.load(plan_file))
            images_lock = TypeAdapter(dict[str, ImageLock]).validate_python(json.load(images_lock_file))
    else:
        if not images_path.is_file():
            raise FileNotFoundError(f"{images_path} not found")

        images_lock, plan = create_plan(images, stack)

    lock_images(images_lock, plan, cache_type, output_path)


if __name__ == "__main__":
    app()
