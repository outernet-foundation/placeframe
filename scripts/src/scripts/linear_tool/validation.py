from __future__ import annotations

import re

WHY_HEADER = "**Why:**"
DONE_HEADER = "**Done when:**"
LINKS_HEADER = "**Links:**"

SAME_LINE_HEADERS = (WHY_HEADER, DONE_HEADER)

RETIRED_MARKERS = ("SPEC.md", ".pulsar/memories")

_LINK_TARGET = re.compile(r"\]\(\s*<?([^)>]+?)>?\s*\)")
_TITLE_PREFIX = re.compile(
    r"^\s*(\[|\d+[.)]\s|PLE-\d+|(repo|type|bug|chore|feature|refactor|docs|improvement):)", re.IGNORECASE
)


def validate_title(title: str) -> list[str]:
    if _TITLE_PREFIX.match(title):
        return [
            "title carries an ordinal or label prefix — sequence lives in blocks relations and labels carry repo/type"
        ]

    return []


def validate_body(body: str) -> list[str]:
    violations: list[str] = []

    for header in (WHY_HEADER, DONE_HEADER, LINKS_HEADER):
        if header not in body:
            violations.append(f"missing canonical section header {header!r}")

    for header in SAME_LINE_HEADERS:
        index = body.find(header)
        if index == -1:
            continue

        first_line = body[index + len(header) :].split("\n", 1)[0]
        if not first_line.strip():
            violations.append(f"{header!r} must be followed by its text on the same line, not the next line")

    for marker in RETIRED_MARKERS:
        if marker in body:
            violations.append(f"retired reference {marker!r} — link the co-located AGENTS.md by GitHub blob URL instead")

    for target in _LINK_TARGET.findall(body):
        if not target.startswith(("http://", "https://")):
            violations.append(f"link target {target!r} is not an absolute URL — use a full github.com blob URL on dev")

    return violations


def orphan_design_docs(doc_names: list[str], ticket_bodies: list[str]) -> list[str]:
    corpus = "\n".join(ticket_bodies)
    return [name for name in doc_names if f"design/{name}" not in corpus]
