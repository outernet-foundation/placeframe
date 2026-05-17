import json

from ..projects import load_unity_projects
from ..unity import PLATFORM_CONFIGS


def main() -> None:
    config = load_unity_projects()
    matrix: list[dict[str, str]] = []

    for name, project in config.projects.items():
        if not project.builds:
            continue
        for platform in project.builds:
            matrix.append({
                "project": str(project.path),
                "project-name": name,
                "cache-key": name.lower(),
                "platform": platform,
                "module": PLATFORM_CONFIGS[platform]["module"],
            })

    print(json.dumps({"include": matrix}))
