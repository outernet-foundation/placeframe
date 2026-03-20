from __future__ import annotations

import typer
from common.bash import bash, bash_output

from ...shared.ci_step import ci_step

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def main() -> None:
    with ci_step("Tag built images"):
        sha = bash_output("git rev-parse HEAD").strip()
        tag = f"built-{sha}"
        bash(f"git tag -f {tag}")
        bash(f"git push -f origin {tag}")
        print(f"Pushed tag: {tag}")
