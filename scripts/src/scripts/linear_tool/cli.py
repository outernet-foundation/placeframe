from __future__ import annotations

import json
import sys
from collections.abc import Callable, Iterator
from functools import cache
from os import environ
from pathlib import Path
from typing import Annotated

import httpx
import typer
from placeframe_stack.modes import parse_env_file
from pydantic import BaseModel, ConfigDict, Field

from .validation import orphan_design_docs, validate_body, validate_title

LINEAR_ENDPOINT = "https://api.linear.app/graphql"
OPERATIONS_DOCUMENT = "linear_operations.graphql"


class _Model(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class PageInfo(_Model):
    has_next_page: bool = Field(alias="hasNextPage")
    end_cursor: str | None = Field(default=None, alias="endCursor")


class _Connection[NodeT](_Model):
    page_info: PageInfo = Field(alias="pageInfo")
    nodes: list[NodeT]


class _NodeList[NodeT](_Model):
    nodes: list[NodeT]


class TeamNode(_Model):
    id: str
    key: str


class IssueStateNode(_Model):
    name: str
    type: str


class IssueLabelName(_Model):
    name: str


class ProjectRef(_Model):
    id: str
    name: str


class IssueListNode(_Model):
    id: str
    identifier: str
    title: str
    description: str | None = None
    url: str
    created_at: str = Field(alias="createdAt")
    state: IssueStateNode
    labels: _NodeList[IssueLabelName]
    project: ProjectRef | None = None


class IssueDetailNode(_Model):
    identifier: str
    title: str
    description: str | None = None
    url: str
    created_at: str = Field(alias="createdAt")
    state: IssueStateNode
    project: ProjectRef | None = None


class ProjectListNode(_Model):
    id: str
    name: str
    url: str
    state: str


class RelatedIssueNode(_Model):
    identifier: str


class IssueRelationNode(_Model):
    type: str
    related_issue: RelatedIssueNode | None = Field(default=None, alias="relatedIssue")


class IssueRelationsNode(_Model):
    identifier: str
    relations: _NodeList[IssueRelationNode]


class WorkflowStateNode(_Model):
    id: str
    name: str
    type: str


class LabelParent(_Model):
    id: str


class LabelNode(_Model):
    id: str
    name: str
    color: str | None = None
    is_group: bool = Field(default=False, alias="isGroup")
    parent: LabelParent | None = None


class CreatedLabel(_Model):
    id: str
    name: str


class CreatedProject(_Model):
    id: str
    url: str


class CreatedIssue(_Model):
    id: str
    identifier: str
    url: str


class CommentNode(_Model):
    id: str
    url: str


class IssueLabelMutationPayload(_Model):
    success: bool
    issue_label: CreatedLabel | None = Field(default=None, alias="issueLabel")


class IssueLabelDeletePayload(_Model):
    success: bool


class ProjectMutationPayload(_Model):
    success: bool
    project: CreatedProject | None = None


class IssueMutationPayload(_Model):
    success: bool
    issue: CreatedIssue | None = None


class IssueRelationCreatePayload(_Model):
    success: bool


class CommentCreatePayload(_Model):
    success: bool
    comment: CommentNode | None = None


class CommentDeletePayload(_Model):
    success: bool


class TeamsData(_Model):
    teams: _NodeList[TeamNode]


class IssuesData(_Model):
    issues: _Connection[IssueListNode]


class IssueDetailData(_Model):
    issue: IssueDetailNode


class ProjectsData(_Model):
    projects: _Connection[ProjectListNode]


class IssueRelationsData(_Model):
    issues: _Connection[IssueRelationsNode]


class WorkflowStatesData(_Model):
    workflow_states: _NodeList[WorkflowStateNode] = Field(alias="workflowStates")


class LabelsData(_Model):
    issue_labels: _NodeList[LabelNode] = Field(alias="issueLabels")


class IssueLabelCreateData(_Model):
    issue_label_create: IssueLabelMutationPayload = Field(alias="issueLabelCreate")


class IssueLabelUpdateData(_Model):
    issue_label_update: IssueLabelMutationPayload = Field(alias="issueLabelUpdate")


class IssueLabelDeleteData(_Model):
    issue_label_delete: IssueLabelDeletePayload = Field(alias="issueLabelDelete")


class ProjectCreateData(_Model):
    project_create: ProjectMutationPayload = Field(alias="projectCreate")


class ProjectUpdateData(_Model):
    project_update: ProjectMutationPayload = Field(alias="projectUpdate")


class IssueCreateData(_Model):
    issue_create: IssueMutationPayload = Field(alias="issueCreate")


class IssueUpdateData(_Model):
    issue_update: IssueMutationPayload = Field(alias="issueUpdate")


class IssueRelationCreateData(_Model):
    issue_relation_create: IssueRelationCreatePayload = Field(alias="issueRelationCreate")


class CommentCreateData(_Model):
    comment_create: CommentCreatePayload = Field(alias="commentCreate")


class CommentDeleteData(_Model):
    comment_delete: CommentDeletePayload = Field(alias="commentDelete")


app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command(name="list-issues")
def list_issues(
    team: Annotated[str | None, typer.Option("--team", help="Team key to filter by, e.g. PLE")] = None,
) -> None:
    for issue in _paginate("Issues", {"filter": _team_filter(team)}, IssuesData, lambda data: data.issues):
        _emit({
            "id": issue.id,
            "identifier": issue.identifier,
            "title": issue.title,
            "state": issue.state.name,
            "state_type": issue.state.type,
            "labels": [label.name for label in issue.labels.nodes],
            "project": issue.project.name if issue.project else None,
            "created_at": issue.created_at,
            "url": issue.url,
        })


@app.command(name="get-issue")
def get_issue(
    issue_id: Annotated[str, typer.Option("--id", help="Issue id to fetch")],
) -> None:
    issue = graphql("Issue", {"id": issue_id}, IssueDetailData).issue
    _emit({
        "identifier": issue.identifier,
        "title": issue.title,
        "state": issue.state.name,
        "project": issue.project.name if issue.project else None,
        "created_at": issue.created_at,
        "url": issue.url,
        "description": issue.description,
    })


@app.command(name="list-relations")
def list_relations(
    team: Annotated[str | None, typer.Option("--team", help="Team key to filter by, e.g. PLE")] = None,
) -> None:
    for issue in _paginate(
        "IssueRelations", {"filter": _team_filter(team)}, IssueRelationsData, lambda data: data.issues
    ):
        for relation in issue.relations.nodes:
            if relation.related_issue is None:
                continue

            _emit({"source": issue.identifier, "target": relation.related_issue.identifier, "type": relation.type})


@app.command(name="list-projects")
def list_projects() -> None:
    for project in _paginate("Projects", {}, ProjectsData, lambda data: data.projects):
        _emit({"id": project.id, "name": project.name, "state": project.state, "url": project.url})


@app.command(name="lint")
def lint(
    team: Annotated[str | None, typer.Option("--team", help="Team key to filter by, e.g. PLE")] = None,
    design_orphans: Annotated[
        bool, typer.Option("--design-orphans", help="Also flag design/ docs that no open ticket links")
    ] = False,
) -> None:
    offenders = 0
    open_bodies: list[str] = []
    for issue in _paginate("Issues", {"filter": _team_filter(team)}, IssuesData, lambda data: data.issues):
        if issue.state.type in ("completed", "canceled"):
            continue

        open_bodies.append(issue.description or "")
        violations = validate_title(issue.title) + validate_body(issue.description or "")
        if violations:
            offenders += 1
            _emit({"identifier": issue.identifier, "title": issue.title, "violations": violations})

    if design_orphans:
        design_dir = _find_up("design/AGENTS.md").parent
        doc_names = [
            path.name for path in sorted(design_dir.glob("*.md")) if path.name not in ("AGENTS.md", "CLAUDE.md")
        ]
        for name in orphan_design_docs(doc_names, open_bodies):
            offenders += 1
            _emit({"design_orphan": f"design/{name}", "violations": ["no open Linear ticket links this design doc"]})

    if offenders:
        raise typer.Exit(1)


@app.command(name="ensure-label")
def ensure_label(
    name: Annotated[str, typer.Option("--name", help="Leaf label name")],
    parent: Annotated[str | None, typer.Option("--parent", help="Parent label-group name to nest under")] = None,
) -> None:
    labels = graphql("Labels", {}, LabelsData).issue_labels.nodes
    parent_id = _ensure_label_record(labels, parent, None, is_group=True) if parent is not None else None
    leaf_id = _ensure_label_record(labels, name, parent_id, is_group=False)
    _emit({"id": leaf_id})


@app.command(name="list-labels")
def list_labels() -> None:
    labels = graphql("Labels", {}, LabelsData).issue_labels.nodes
    names_by_id = {label.id: label.name for label in labels}
    for label in labels:
        parent_name = names_by_id.get(label.parent.id) if label.parent else None
        _emit({
            "id": label.id,
            "name": label.name,
            "color": label.color,
            "is_group": label.is_group,
            "parent": parent_name,
        })


@app.command(name="update-label")
def update_label(
    label_id: Annotated[str, typer.Option("--id", help="Label id to update")],
    name: Annotated[str | None, typer.Option("--name", help="New label name")] = None,
    parent: Annotated[str | None, typer.Option("--parent", help="Parent group name to reparent under")] = None,
    color: Annotated[str | None, typer.Option("--color", help="New label color as a hex string, e.g. #eb5757")] = None,
) -> None:
    fields: dict[str, object] = {}
    if name is not None:
        fields["name"] = name
    if color is not None:
        fields["color"] = color
    if parent is not None:
        labels = graphql("Labels", {}, LabelsData).issue_labels.nodes
        groups = [node for node in labels if node.is_group and node.name == parent]
        if len(groups) != 1:
            typer.echo(f"Expected exactly one group named {parent!r}, found {len(groups)}", err=True)
            raise typer.Exit(1)

        fields["parentId"] = groups[0].id

    _require_fields(fields, "Nothing to update; pass --name, --parent, and/or --color")

    payload = graphql("UpdateLabel", {"id": label_id, "input": fields}, IssueLabelUpdateData).issue_label_update
    label = _require(payload.success, payload.issue_label, f"Failed to update label {label_id!r}")
    _emit({"id": label.id, "name": label.name})


@app.command(name="delete-label")
def delete_label(
    label_id: Annotated[str, typer.Option("--id", help="Label id to delete")],
) -> None:
    payload = graphql("DeleteLabel", {"id": label_id}, IssueLabelDeleteData).issue_label_delete
    _require_ok(payload.success, f"Failed to delete label {label_id!r}")
    _emit({"id": label_id, "deleted": True})


@app.command(name="create-project")
def create_project(
    name: Annotated[str, typer.Option("--name", help="Project name")],
    team: Annotated[str, typer.Option("--team", help="Team key the project belongs to, e.g. PLE")],
    summary: Annotated[str, typer.Option("--summary", help="One-line project description")] = "",
) -> None:
    content = _read_stdin()
    fields: dict[str, object] = {"name": name, "teamIds": [_resolve_team_id(team)]}
    if summary:
        fields["description"] = summary
    if content.strip():
        fields["content"] = content

    payload = graphql("CreateProject", {"input": fields}, ProjectCreateData).project_create
    project = _require(payload.success, payload.project, f"Failed to create project {name!r}")
    _emit({"id": project.id, "url": project.url})


@app.command(name="update-project")
def update_project(
    project_id: Annotated[str, typer.Option("--id", help="Project id to update")],
    name: Annotated[str | None, typer.Option("--name", help="New project name")] = None,
    summary: Annotated[str | None, typer.Option("--summary", help="New one-line description")] = None,
) -> None:
    content = _read_stdin()
    fields: dict[str, object] = {}
    if name is not None:
        fields["name"] = name
    if summary is not None:
        fields["description"] = summary
    if content.strip():
        fields["content"] = content

    _require_fields(fields, "Nothing to update; pass --name, --summary, or a body on stdin")

    payload = graphql("UpdateProject", {"id": project_id, "input": fields}, ProjectUpdateData).project_update
    project = _require(payload.success, payload.project, f"Failed to update project {project_id!r}")
    _emit({"id": project.id, "url": project.url})


@app.command(name="create-issue")
def create_issue(
    title: Annotated[str, typer.Option("--title", help="Issue title")],
    team: Annotated[str, typer.Option("--team", help="Team key, e.g. PLE")],
    project: Annotated[str | None, typer.Option("--project", help="Project id to file the issue under")] = None,
    label: Annotated[list[str] | None, typer.Option("--label", help="Label id to attach (repeatable)")] = None,
) -> None:
    description = _read_stdin()
    _enforce_conventions(title, description)
    fields: dict[str, object] = {"teamId": _resolve_team_id(team), "title": title}
    if description.strip():
        fields["description"] = description
    if project is not None:
        fields["projectId"] = project
    if label:
        fields["labelIds"] = label

    payload = graphql("CreateIssue", {"input": fields}, IssueCreateData).issue_create
    issue = _require(payload.success, payload.issue, f"Failed to create issue {title!r}")
    _emit({"id": issue.id, "identifier": issue.identifier, "url": issue.url})


@app.command(name="update-issue")
def update_issue(
    issue_id: Annotated[str, typer.Option("--id", help="Issue id to update")],
    title: Annotated[str | None, typer.Option("--title", help="New issue title")] = None,
    project: Annotated[str | None, typer.Option("--project", help="Project id to move the issue under")] = None,
    label: Annotated[list[str] | None, typer.Option("--label", help="Replaces the label set (repeatable)")] = None,
    state: Annotated[str | None, typer.Option("--state", help="Workflow state name to move the issue to")] = None,
    team: Annotated[str | None, typer.Option("--team", help="Team key that owns the state, e.g. PLE")] = None,
) -> None:
    description = _read_stdin()
    _enforce_conventions(title, description if description.strip() else None)
    fields: dict[str, object] = {}
    if title is not None:
        fields["title"] = title
    if description.strip():
        fields["description"] = description
    if project is not None:
        fields["projectId"] = project
    if label:
        fields["labelIds"] = label
    if state is not None:
        if team is None:
            typer.echo("--state requires --team to resolve the workflow state", err=True)
            raise typer.Exit(1)

        states = graphql("WorkflowStates", {"filter": _team_filter(team)}, WorkflowStatesData).workflow_states.nodes
        matches = [candidate for candidate in states if candidate.name.casefold() == state.casefold()]
        if len(matches) != 1:
            available = ", ".join(sorted(candidate.name for candidate in states))
            typer.echo(f"No unique state {state!r} in team {team!r}; available: {available}", err=True)
            raise typer.Exit(1)

        fields["stateId"] = matches[0].id

    _require_fields(fields, "Nothing to update; pass --title, --label, --state, or a body on stdin")

    payload = graphql("UpdateIssue", {"id": issue_id, "input": fields}, IssueUpdateData).issue_update
    issue = _require(payload.success, payload.issue, f"Failed to update issue {issue_id!r}")
    _emit({"id": issue.id, "identifier": issue.identifier, "url": issue.url})


@app.command()
def link(
    blocker: Annotated[str, typer.Option("--blocker", help="Issue id that does the blocking")],
    blocked: Annotated[str, typer.Option("--blocked", help="Issue id that is blocked")],
) -> None:
    fields: dict[str, object] = {"issueId": blocker, "relatedIssueId": blocked, "type": "blocks"}
    payload = graphql("CreateRelation", {"input": fields}, IssueRelationCreateData).issue_relation_create
    _require_ok(payload.success, "Failed to create blocking relation")
    _emit({"blocker": blocker, "blocked": blocked, "type": "blocks"})


@app.command()
def comment(
    issue_id: Annotated[str, typer.Option("--issue", help="Issue id to comment on")],
) -> None:
    body = _read_stdin()
    if not body.strip():
        typer.echo("No comment body on stdin", err=True)
        raise typer.Exit(1)

    payload = graphql("CreateComment", {"input": {"issueId": issue_id, "body": body}}, CommentCreateData).comment_create
    created = _require(payload.success, payload.comment, f"Failed to comment on issue {issue_id!r}")
    _emit({"id": created.id, "url": created.url})


@app.command(name="delete-comment")
def delete_comment(
    comment_id: Annotated[str, typer.Option("--id", help="Comment id to delete")],
) -> None:
    payload = graphql("DeleteComment", {"id": comment_id}, CommentDeleteData).comment_delete
    _require_ok(payload.success, f"Failed to delete comment {comment_id!r}")
    _emit({"id": comment_id, "deleted": True})


def _paginate[T: _Model, NodeT](
    operation: str,
    variables: dict[str, object],
    model: type[T],
    select: Callable[[T], _Connection[NodeT]],
) -> Iterator[NodeT]:
    after: str | None = None
    while True:
        connection = select(graphql(operation, {**variables, "after": after}, model))
        yield from connection.nodes
        if not connection.page_info.has_next_page:
            break

        after = connection.page_info.end_cursor


def graphql[T: _Model](operation: str, variables: dict[str, object], model: type[T]) -> T:
    response = httpx.post(
        LINEAR_ENDPOINT,
        headers={"Authorization": _api_key(), "Content-Type": "application/json"},
        json={"query": _operations(), "operationName": operation, "variables": variables},
        timeout=30.0,
    )
    try:
        payload: dict[str, object] = response.json()
    except json.JSONDecodeError:
        typer.echo(
            f"Linear API returned a non-JSON response (HTTP {response.status_code}): {response.text[:200]}", err=True
        )
        raise typer.Exit(1) from None

    errors = payload.get("errors")
    if errors:
        typer.echo(f"Linear API error: {json.dumps(errors)}", err=True)
        raise typer.Exit(1)

    data = payload.get("data")
    if data is None:
        typer.echo(f"Linear API returned no data (HTTP {response.status_code})", err=True)
        raise typer.Exit(1)

    return model.model_validate(data)


def _enforce_conventions(title: str | None, body: str | None) -> None:
    violations: list[str] = []
    if title is not None:
        violations.extend(validate_title(title))
    if body is not None:
        violations.extend(validate_body(body))
    if not violations:
        return

    for violation in violations:
        typer.echo(f"convention violation: {violation}", err=True)

    typer.echo("Refusing to write: fix the title/body to match linear_tool/AGENTS.md conventions.", err=True)
    raise typer.Exit(1)


def _resolve_team_id(key: str) -> str:
    teams = graphql("Teams", {}, TeamsData).teams.nodes
    for team in teams:
        if team.key == key:
            return team.id

    available = ", ".join(sorted(team.key for team in teams))
    typer.echo(f"No team with key {key!r}; available keys: {available}", err=True)
    raise typer.Exit(1)


def _ensure_label_record(labels: list[LabelNode], name: str, parent_id: str | None, is_group: bool) -> str:
    for label in labels:
        label_parent_id = label.parent.id if label.parent else None
        if label.name == name and label.is_group == is_group and label_parent_id == parent_id:
            return label.id

    fields: dict[str, object] = {"name": name}
    if is_group:
        fields["isGroup"] = True
    if parent_id is not None:
        fields["parentId"] = parent_id

    payload = graphql("CreateLabel", {"input": fields}, IssueLabelCreateData).issue_label_create
    return _require(payload.success, payload.issue_label, f"Failed to create label {name!r}").id


def _require[T](success: bool, value: T | None, message: str) -> T:
    if not success or value is None:
        typer.echo(message, err=True)
        raise typer.Exit(1)

    return value


def _require_ok(success: bool, message: str) -> None:
    if not success:
        typer.echo(message, err=True)
        raise typer.Exit(1)


def _require_fields(fields: dict[str, object], message: str) -> None:
    if not fields:
        typer.echo(message, err=True)
        raise typer.Exit(1)


def _read_stdin() -> str:
    return sys.stdin.read() if not sys.stdin.isatty() else ""


def _team_filter(team: str | None) -> dict[str, object]:
    return {"team": {"key": {"eq": team}}} if team is not None else {}


@cache
def _operations() -> str:
    return Path(__file__).with_name(OPERATIONS_DOCUMENT).read_text(encoding="utf-8")


def _find_up(marker: str) -> Path:
    for directory in (Path.cwd(), *Path.cwd().parents):
        candidate = directory / marker
        if candidate.is_file():
            return candidate

    raise RuntimeError(f"No {marker} found in the current directory or any parent; run from inside the repo")


def _api_key() -> str:
    key = environ.get("LINEAR_API_KEY")
    if not key:
        key = parse_env_file(_find_up(".env")).get("LINEAR_API_KEY")
    if not key:
        raise RuntimeError("LINEAR_API_KEY not found in environment or .env")

    return key


def _emit(record: dict[str, object]) -> None:
    typer.echo(json.dumps(record))
