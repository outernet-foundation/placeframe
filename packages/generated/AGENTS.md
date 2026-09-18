# packages/generated/

**Do not hand-edit anything in this directory.** Every file here is generated from upstream sources and gets overwritten on the next codegen run.

Two pipelines populate this tree:

- **`uv run generate-datamodels`** — populates `python/datamodels/` from the live PostgreSQL schema. Requires Docker + postgres running (`uv run up`).
- **`uv run generate-clients --config build/openapi-projects.json`** — populates the rest (`python/api-client/`, `python/zed-capture-client/`, `python/localizer-client/`, `csharp/api-client/`, `csharp/zed-capture-client/`, etc.) from each service's OpenAPI spec. Requires Java (JDK 11+). To regenerate only the API and zed-capture C# clients (skipping the localizer, which needs PyTorch/pycolmap), pass `--project docker/api` and `--project docker/zed-capture` in separate invocations. Set `--no-cache` to force regeneration when only the templates changed (spec-unchanged short-circuit lives in `_dump_openapi_spec`). The zed-capture spec dump needs `CODEGEN=1 ZED_BOX_ID=codegen` in the environment.

If something here looks wrong, fix the source — either the OpenAPI spec (in the relevant `docker/<service>/`), the SQL schema (`database/*.sql`), or the openapi-generator template patches in `build/openapi-generator/templates-patches/<lang>/`. Then re-run the appropriate generator. Codegen output always lives in its own commit with one of these canonical messages: `Run generate-clients`, `Run generate-datamodels`, or `Run generate-clients and generate-datamodels`.
