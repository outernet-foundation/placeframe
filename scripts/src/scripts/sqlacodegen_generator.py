# Custom sqlacodegen generator that fixes things the stock DeclarativeGenerator gets wrong:
#
# - ENUM COLUMNS: sqlacodegen renders PostgreSQL enums as inline Enum('val1', 'val2', name='...')
#   with Mapped[str] type annotations. We need strict Python enum.Enum subclasses so that
#   Pydantic can validate enum values in DTOs and so the generated models are type-safe.
#   render_column_type() and render_column_python_type() intercept enum columns to emit
#   PascalCase enum classes (e.g. DeviceType, OrchestrationStatus) with a values_callable,
#   and generate() inserts those class definitions between the imports and the Base declaration.
#
# - PASSIVE DELETES: sqlacodegen never emits passive_deletes=True on relationships, even when
#   the underlying FK has ON DELETE CASCADE. Without it, SQLAlchemy issues SELECT+DELETE for
#   every child row before the parent delete — which races against the DB cascade and causes
#   500 errors (e.g. deleting a LocalizationMap that has camera positions). render_relationship()
#   detects CASCADE FKs on ONE_TO_MANY relationships and injects passive_deletes=True.
#
# - ARRAY GENERIC PARAM: sqlacodegen renders array columns as `ARRAY(<inner>)`, but
#   `mapped_column(ARRAY(<inner>))` triggers basedpyright `reportUnknownArgumentType` because
#   `ARRAY[_T]`'s element type can't be inferred from a `_TypeEngineArgument[_T]` whose
#   inner is itself a generic-without-binding (e.g. `Double()` is `Double[Unknown]`).
#   render_column_type() rewrites these as `ARRAY[<python_type>](<inner>)`, binding ARRAY's
#   type parameter explicitly — pyright then back-infers the inner type from ARRAY's _T.

from collections.abc import Sequence
from typing import Any, cast

from humps import pascalize
from sqlalchemy import Column, Connection, Engine, MetaData
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.sqltypes import ARRAY
from sqlalchemy.sql.sqltypes import Enum as SAEnum
from sqlalchemy.types import TypeEngine

from sqlacodegen.generators import DeclarativeGenerator
from sqlacodegen.models import Model, RelationshipAttribute, RelationshipType
from sqlacodegen.utils import render_callable


class PlaceframeDeclarativeGenerator(DeclarativeGenerator):
    def __init__(
        self,
        metadata: MetaData,
        bind: Connection | Engine,
        options: Sequence[str],
        **kwargs: Any,
    ) -> None:
        super().__init__(metadata, bind, options, **kwargs)
        self._enum_classes: dict[str, list[str]] = {}

    def render_column_type(self, coltype: TypeEngine[Any]) -> str:
        if isinstance(coltype, ARRAY):
            item_type = cast(TypeEngine[Any], coltype.item_type)
            inner_rendered = super().render_column_type(item_type)
            python_type_name = item_type.python_type.__name__
            return f"ARRAY[{python_type_name}]({inner_rendered})"

        if not isinstance(coltype, SAEnum):
            return super().render_column_type(coltype)

        assert coltype.name is not None
        class_name = str(pascalize(coltype.name))
        self._enum_classes[class_name] = list(coltype.enums)

        kwargs: dict[str, str] = {"name": repr(coltype.name), "values_callable": "enum_values"}
        schema = str(coltype.schema) if coltype.schema is not None else None  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        if schema is not None:
            kwargs["schema"] = repr(schema)

        return render_callable("Enum", class_name, kwargs=kwargs)

    def render_column_python_type(self, column: Column[Any]) -> str:
        # JSONB columns: stock sqlacodegen emits Mapped[dict] (no parameter), which trips
        # basedpyright's reportMissingTypeArgument. Bind to dict[str, Any] explicitly so
        # consumers get a concrete type for the opaque payload.
        if isinstance(column.type, JSONB):
            self.add_literal_import("typing", "Any")
            inner = "dict[str, Any]"
            if column.nullable:
                self.add_literal_import("typing", "Optional")
                return f"Optional[{inner}]"
            return inner

        if not isinstance(column.type, SAEnum):
            return super().render_column_python_type(column)

        assert column.type.name is not None
        class_name = str(pascalize(column.type.name))
        if column.nullable:
            self.add_literal_import("typing", "Optional")
            return f"Optional[{class_name}]"
        return class_name

    def render_relationship(self, relationship: RelationshipAttribute) -> str:
        rendered = super().render_relationship(relationship)

        if (
            relationship.type is RelationshipType.ONE_TO_MANY
            and relationship.constraint is not None
            and relationship.constraint.ondelete
            and relationship.constraint.ondelete.upper() == "CASCADE"
        ):
            idx = rendered.rfind(")")
            rendered = rendered[:idx] + ", passive_deletes=True)"

        return rendered

    def generate(self) -> str:
        self.generate_base()

        sections: list[str] = []

        for table in list(self.metadata.tables.values()):
            if self.should_ignore_table(table):
                self.metadata.remove(table)
                continue

            if "noindexes" in self.options:
                table.indexes.clear()

            if "noconstraints" in self.options:
                table.constraints.clear()

            if "nocomments" in self.options:
                table.comment = None

            for column in table.columns:
                if "nocomments" in self.options:
                    column.comment = None

        for table in self.metadata.tables.values():
            self.fix_column_types(table)

        models: list[Model] = self.generate_models()

        variables = self.render_module_variables(models)
        if variables:
            sections.append(variables + "\n")

        rendered_models = self.render_models(models)
        if rendered_models:
            sections.append(rendered_models)

        self.collect_imports(models)

        if self._enum_classes:
            self.add_module_import("enum")

        groups = self.group_imports()
        imports = "\n\n".join("\n".join(line for line in group) for group in groups)
        if imports:
            sections.insert(0, imports)

        if self._enum_classes:
            enum_block = self._render_enum_block()
            sections.insert(1, enum_block)

        return "\n\n".join(sections) + "\n"

    def _render_enum_block(self) -> str:
        lines: list[str] = []

        lines.append("def enum_values(x: list[enum.Enum]) -> list[str]:")
        lines.append("    return [str(e.value) for e in x]")
        lines.append("")

        for class_name, values in self._enum_classes.items():
            lines.append("")
            lines.append(f"class {class_name}(enum.Enum):")
            for v in values:
                key = v.upper().replace("-", "_").replace(" ", "_")
                lines.append(f"    {key} = '{v}'")
            lines.append("")

        return "\n".join(lines)
