from __future__ import annotations

import typer
from bashrun import bash_output

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def main() -> None:
    existing = bash_output("gh pr list --head dev --base main --state open --json number --jq '.[0].number'").strip()
    if existing:
        print(f"Release PR already exists: #{existing}")
    else:
        bash_output(
            'gh pr create --head dev --base main --title "Next release"'
            ' --body "Persistent release gate PR from `dev` → `main`. Merge when ready to cut a release."'
        )
        print("Created release PR")
