# Vibe code: Gemini 3

"""
Convert OpenAPI 3.1.0 schema to OpenAPI 3.0.3 compatible format.

Handles the following 3.1.0 -> 3.0.3 conversions:
1. Type arrays like `type: ["null", "string"]` -> `type: "string", nullable: true`
2. `oneOf` with `{"type": "null"}` -> removes null option and adds `nullable: true`
3. `anyOf` with `{"type": "null"}` -> same treatment
4. Changes version from 3.1.0 to 3.0.3
5. Removes `examples` (3.1.0) and converts to `example` (3.0.3) if needed
"""

from __future__ import annotations

from typing import TypeAlias

# JSON-compatible types for OpenAPI schema
JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = "JsonPrimitive | JsonDict | JsonList"
JsonDict: TypeAlias = dict[str, "JsonValue"]
JsonList: TypeAlias = list["JsonValue"]


def downgrade_openapi_3_1_to_3_0(schema: JsonDict) -> JsonDict:
    """
    Convert an OpenAPI 3.1.0 schema to 3.0.3 compatible format.
    Modifies the schema in-place and returns it.

    Args:
        schema: The parsed OpenAPI JSON schema (as a dict)

    Returns:
        The modified schema (same object, modified in place)
    """
    # Update version
    if schema.get("openapi") == "3.1.0":
        schema["openapi"] = "3.0.3"

    # Recursively process the schema
    _process_node(schema)

    return schema


def _process_node(node: JsonValue) -> None:
    """Recursively process a node in the schema."""
    if isinstance(node, dict):
        _convert_dict_node(node)
        # Recurse into all values
        for value in node.values():
            _process_node(value)
    elif isinstance(node, list):
        for item in node:
            _process_node(item)


def _convert_dict_node(node: JsonDict) -> None:
    """Convert a single dict node from 3.1.0 to 3.0.3 format."""

    # Handle type arrays: `type: ["null", "string"]` -> `type: "string", nullable: true`
    type_value = node.get("type")
    if isinstance(type_value, list):
        types: list[str] = [t for t in type_value if isinstance(t, str)]
        has_null = "null" in types
        non_null_types = [t for t in types if t != "null"]

        if len(non_null_types) == 1:
            # Single non-null type
            node["type"] = non_null_types[0]
            if has_null:
                node["nullable"] = True
        elif len(non_null_types) > 1:
            # Multiple non-null types - convert to anyOf
            any_of_items: JsonList = []
            for t in non_null_types:
                item: JsonDict = {"type": t}
                # Array types require items in 3.0.3
                if t == "array":
                    item["items"] = {}
                any_of_items.append(item)
            del node["type"]
            node["anyOf"] = any_of_items
            if has_null:
                node["nullable"] = True
        elif has_null and len(non_null_types) == 0:
            # Only null type - use object as fallback
            node["type"] = "object"
            node["nullable"] = True

    # Ensure array types have items (required in 3.0.3)
    if node.get("type") == "array" and "items" not in node:
        node["items"] = {}

    # Handle oneOf/anyOf with {"type": "null"}
    for key in ["oneOf", "anyOf"]:
        key_value = node.get(key)
        if isinstance(key_value, list):
            items = key_value
            null_items: list[JsonDict] = [
                item for item in items if isinstance(item, dict) and item.get("type") == "null"
            ]
            non_null_items: list[JsonDict] = [
                item for item in items if isinstance(item, dict) and item.get("type") != "null"
            ]

            if null_items:
                # Has null option - set nullable and remove null from oneOf/anyOf
                node["nullable"] = True

                if len(non_null_items) == 0:
                    # Only had null - remove oneOf/anyOf entirely, set as nullable object
                    del node[key]
                    if "type" not in node:
                        node["type"] = "object"
                elif len(non_null_items) == 1:
                    # Single non-null item - inline it and remove oneOf/anyOf
                    del node[key]
                    single_item = non_null_items[0]
                    for k, v in single_item.items():
                        if k not in node:  # Don't overwrite nullable we just set
                            node[k] = v
                else:
                    # Multiple non-null items - keep oneOf/anyOf without null
                    node[key] = list(non_null_items)

    # Convert `examples` (3.1.0) to `example` (3.0.3)
    examples_value = node.get("examples")
    if isinstance(examples_value, list) and len(examples_value) > 0:
        # In schema context, examples array should become a single example
        # But only if we're in a schema context (not in response/requestBody examples)
        # We can detect schema context by checking if there's no "value" key in examples items
        first_example = examples_value[0]
        if not isinstance(first_example, dict) or "value" not in first_example:
            node["example"] = first_example
            del node["examples"]

    # Handle const (3.1.0) -> enum with single value (3.0.3)
    if "const" in node:
        node["enum"] = [node["const"]]
        del node["const"]

    # Handle exclusiveMinimum/exclusiveMaximum changes
    # In 3.1.0 these are numbers, in 3.0.3 they are booleans with separate minimum/maximum
    exclusive_min = node.get("exclusiveMinimum")
    if isinstance(exclusive_min, (int, float)):
        node["minimum"] = exclusive_min
        node["exclusiveMinimum"] = True

    exclusive_max = node.get("exclusiveMaximum")
    if isinstance(exclusive_max, (int, float)):
        node["maximum"] = exclusive_max
        node["exclusiveMaximum"] = True

    # Remove 3.1.0-only properties that aren't supported in 3.0.3
    unsupported_keys = ["contentMediaType", "contentEncoding", "$comment"]
    for key in unsupported_keys:
        if key in node:
            del node[key]


if __name__ == "__main__":
    import json
    import sys
    from typing import cast

    if len(sys.argv) < 2:
        print("Usage: python fix_openapi_schema.py <input.json> [output.json]")
        raise SystemExit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    with open(input_file, "r") as f:
        schema = cast(JsonDict, json.load(f))

    converted = downgrade_openapi_3_1_to_3_0(schema)

    output = json.dumps(converted, indent=2)

    if output_file:
        with open(output_file, "w") as f:
            _ = f.write(output)
        print(f"Converted schema written to {output_file}")
    else:
        print(output)
