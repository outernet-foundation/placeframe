import json
from pathlib import Path

from pydantic import BaseModel


class UnityProjectConfig(BaseModel, extra="forbid"):
    path: Path
    package: str | None = None
    builds: list[str] | None = None
    execute_methods: dict[str, str] | None = None
    grant_permissions: list[str] = []


class UnityProjectsFile(BaseModel, extra="forbid"):
    projects: dict[str, UnityProjectConfig]


def load_unity_projects() -> UnityProjectsFile:
    return UnityProjectsFile(**json.loads((Path(__file__).parents[3] / "unity-projects.json").read_text()))
