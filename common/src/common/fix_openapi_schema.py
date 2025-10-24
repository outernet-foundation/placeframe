# Vibe coded using gpt5

"""
Purpose: work around an OpenAPI codegen gotcha. FastAPI/Pydantic emits implicit
schema titles and `anyOf[*, null]`. Many generators (incl. OpenAPI Generator C#)
reuse inline schemas by (title-derived) name and singularize array titles
(e.g., "Ids" → "Id"). Depending on traversal order, this can collide with other
"Id" schemas (some nullable) and leak into array element types—producing
`List<Guid?>` where `List<Guid>` is expected.

Fix (conceptual): make inline array items uniquely named and non-nullable, and
eliminate fragile titles/nullable unions so codegen can’t alias them.

This pass:
- assigns a stable `x-schema-name` to every inline array item
  (`{operationId}_{where}_item`);
- strips `title` from arrays/items;
- rewrites `anyOf[*, null]` to `nullable: true` on the non-null branch;
- defaults array **item** `nullable` to `False`.

It runs over parameters, request bodies, and responses, and uses small TypeGuard
helpers so strict type checkers don’t flag “Unknown” while walking the JSON.
"""

from typing import Any, Dict, List, TypeAlias, TypeGuard, cast

JSON: TypeAlias = Dict[str, Any]

# ---------- Type guards & accessors ----------


def is_json_dict(v: object) -> TypeGuard[JSON]:
    return isinstance(v, dict)


def is_json_dict_list(v: object) -> TypeGuard[List[JSON]]:
    if not isinstance(v, list):
        return False
    xs = cast(List[object], v)  # <— anchor element type; avoids list[Unknown]
    for e in xs:
        if not isinstance(e, dict):
            return False
    return True


def get_json(d: JSON, key: str) -> JSON | None:
    v = d.get(key)
    return v if is_json_dict(v) else None


def get_json_list(d: JSON, key: str) -> List[JSON] | None:
    v = d.get(key)
    return v if is_json_dict_list(v) else None


# ---------- Schema helpers ----------


def _collapse_anyof_null(s: JSON) -> None:
    anyof_obj = s.get("anyOf")
    if not isinstance(anyof_obj, list):
        return
    anyof_list = cast(List[object], anyof_obj)  # <— anchor element type

    if len(anyof_list) != 2:
        return

    has_null = False
    non_null_dict: JSON | None = None
    for b_obj in anyof_list:
        if is_json_dict(b_obj):
            if b_obj.get("type") == "null":
                has_null = True
            else:
                non_null_dict = b_obj

    if not has_null or not is_json_dict(non_null_dict):
        return

    s.clear()
    s.update(non_null_dict)
    s["nullable"] = True


def _name_array_items(op_id: str, where: str, s: JSON) -> None:
    _collapse_anyof_null(s)
    if s.get("type") != "array":
        return

    s.pop("title", None)

    items_obj = s.get("items")
    if is_json_dict(items_obj):
        items: JSON = items_obj
        items.pop("title", None)
    else:
        items = {}

    _collapse_anyof_null(items)
    items.setdefault("x-schema-name", f"{op_id}_{where}_item")
    items.setdefault("nullable", False)

    s["items"] = items


def _fix_media_schema(op_id: str, where: str, media: JSON) -> None:
    sch = get_json(media, "schema")
    if not sch:
        return
    _name_array_items(op_id, where, sch)
    media["schema"] = sch


def fix_inline_schemas(spec: JSON) -> None:
    paths = get_json(spec, "paths")
    if not paths:
        return

    for path, ops in paths.items():
        if not is_json_dict(ops):
            continue

        for method, op in ops.items():
            if not is_json_dict(op):
                continue

            op_id = str(op.get("operationId") or f"{method}_{str(path).replace('/', '_')}")

            params = get_json_list(op, "parameters")
            if params:
                for p in params:
                    sch = get_json(p, "schema")
                    if not sch:
                        continue
                    where = f"param_{str(p.get('name', '_'))}"
                    _name_array_items(op_id, where, sch)
                    p["schema"] = sch

            rb = get_json(op, "requestBody")
            if rb:
                content = get_json(rb, "content")
                if content:
                    for ctype, media in content.items():
                        if is_json_dict(media):
                            where = f"body_{str(ctype).replace('/', '_')}"
                            _fix_media_schema(op_id, where, media)

            resps = get_json(op, "responses")
            if not resps:
                continue
            for code, resp in resps.items():
                if not is_json_dict(resp):
                    continue
                content = get_json(resp, "content")
                if not content:
                    continue
                for ctype, media in content.items():
                    if is_json_dict(media):
                        where = f"resp_{code}_{str(ctype).replace('/', '_')}"
                        _fix_media_schema(op_id, where, media)
