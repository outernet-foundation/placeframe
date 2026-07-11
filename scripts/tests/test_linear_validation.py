from __future__ import annotations

from scripts.linear_tool.validation import orphan_design_docs, validate_body, validate_title

CONFORMING = (
    "**Why:** The thing is broken in a specific, self-contained way.\n\n"
    "**Done when:** A grep-able invariant holds.\n\n"
    "**Links:** [reconstructor/AGENTS.md](https://github.com/outernet-foundation/placeframe/blob/dev/docker/reconstructor/AGENTS.md)"
)


def test_conforming_body_has_no_violations() -> None:
    assert validate_body(CONFORMING) == []


def test_missing_headers_are_flagged() -> None:
    violations = validate_body("just some prose with no structure")
    assert any("**Why:**" in v for v in violations)
    assert any("**Done when:**" in v for v in violations)
    assert any("**Links:**" in v for v in violations)


def test_period_dialect_is_flagged() -> None:
    period_style = CONFORMING.replace("**Why:**", "**Why.**")
    assert any("**Why:**" in v for v in validate_body(period_style))


def test_next_line_body_is_flagged() -> None:
    next_line = CONFORMING.replace("**Why:** The thing", "**Why:**\nThe thing")
    assert any("same line" in v for v in validate_body(next_line))


def test_retired_pointers_are_flagged() -> None:
    spec = CONFORMING.replace("AGENTS.md](https", "SPEC.md](https")
    assert any("SPEC.md" in v for v in validate_body(spec))

    memory = CONFORMING + "\n\nDesign source: `.pulsar/memories/relocalization-redesign.md`"
    assert any(".pulsar/memories" in v for v in validate_body(memory))


def test_relative_link_target_is_flagged() -> None:
    relative = CONFORMING.replace(
        "[reconstructor/AGENTS.md](https://github.com/outernet-foundation/placeframe/blob/dev/docker/reconstructor/AGENTS.md)",
        "[reconstructor/AGENTS.md](docker/reconstructor/AGENTS.md)",
    )
    assert any("not an absolute URL" in v for v in validate_body(relative))


def test_angle_bracketed_absolute_link_is_accepted() -> None:
    bracketed = CONFORMING.replace(
        "(https://github.com/outernet-foundation/placeframe/blob/dev/docker/reconstructor/AGENTS.md)",
        "(<https://github.com/outernet-foundation/placeframe/blob/dev/docker/reconstructor/AGENTS.md>)",
    )
    assert validate_body(bracketed) == []


def test_orphan_design_docs_flags_unlinked() -> None:
    bodies = [
        "**Links:** [x](<https://github.com/outernet-foundation/placeframe/blob/dev/design/foo.md>)",
        "no links in this body",
    ]
    assert orphan_design_docs(["foo.md", "bar.md"], bodies) == ["bar.md"]


def test_imperative_title_is_accepted() -> None:
    assert validate_title("Delete the VIO-EM pair-consistency gate from the reconstructor") == []


def test_prefixed_titles_are_flagged() -> None:
    assert validate_title("[T3] Delete the gate") != []
    assert validate_title("1. Delete the gate") != []
    assert validate_title("PLE-339 Delete the gate") != []
    assert validate_title("bug: Delete the gate") != []
