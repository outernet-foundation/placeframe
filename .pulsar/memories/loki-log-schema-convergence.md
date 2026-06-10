---
updated: 2026-06-10
---

# Loki logging converged on native OTLP ingestion (landed)

## Outcome

Placeframe's two divergent Loki log schemas are collapsed into one canonical shape, produced
by **Loki native OTLP ingestion**. Every producer — backend services, the ZED box, and the
phone — now lands the same shape, and `loki-query` renders all of them uniformly. This
replaces the prior split where Alloy's `otelcol.exporter.loki` JSON-serialized the whole OTel
record into the log line and the reader was built for the phone's minority Serilog shape.

The durable truth now lives in the SPECs/CLAUDE.md (this memory is the landing record):
`docker/SPEC.md` (Observability), `docker/loki/config.yaml` (`otlp_config`),
`packages/unity/Logging/SPEC.md` (phone sink), `docker/zed-capture/CLAUDE.md` (box drain).

## Canonical shape (verified against live Loki 3.5.0)

- **Log line = the OTel `body`** (the human message), a bare string. No JSON wrapper.
- **Indexed labels = `service.name` + `deployment.environment.name` only.** Pinned via
  `limits_config.otlp_config` with `ignore_defaults: true`. `service.instance.id` is
  deliberately *not* a label (it is the container id and would churn the label set on every
  restart) — it, `service.namespace`, severity, scope, and all log attributes are structured
  metadata, queryable with `| key="value"` (no `| json`).
- Severity rides as `severity_text`; Loki derives `detected_level` from it.
- `query_range` returns each unique (labels+metadata) tuple as its own `stream` object with
  2-element `[ts, line]` values; metadata is merged into the `stream` dict in the response.

## What changed

1. **Alloy** (`docker/alloy/config.alloy`): `otelcol.exporter.otlphttp` → Loki `/otlp/v1/logs`,
   dropping the old `otelcol.exporter.loki` + `loki.write` path and the label-promotion
   processor (label policy now lives in Loki's `otlp_config`). Env var renamed
   `LOKI_WRITE_ENDPOINT` → `LOKI_OTLP_ENDPOINT` in `compose.yml` and `compose.rig.yml`.
2. **Loki** (`config.yaml`, `box.yaml`): added the `otlp_config` label policy above.
3. **Reader** (`scripts/src/scripts/loki_query.py`): the line is the body; level/group/exception
   come from the per-stream structured-metadata dict, not `json.loads(line)`.
4. **Phone producer** (`LokiSink.cs`, `JTokenFromSerilogProperty.cs`, `App.cs`): emits the
   canonical shape over the **Loki push API** using 3-element `[ts, body, metadata]` values
   (verified: the metadata object lands as structured metadata, not labels). The bespoke
   offline buffer/dedup is unchanged; label `app` → `service_name`. No OTLP-exporter dependency
   was added — the push API produces an identical result.
5. **AOA relay** (`LogDrainController.cs`): the box-Loki query response merges labels and
   metadata into one dict; the drain splits it back into canonical labels +
   structured-metadata 3rd element before re-pushing (dropping Loki-derived `detected_level`),
   so box logs stay low-cardinality on the backend. Restamping/cursor logic unchanged. This is
   faithful relay of the already-canonical box shape — not the rejected "normalize in the
   drain toward the non-standard shape" anti-pattern.

## Open thread

- **Phone full-OTLP-exporter** (Serilog → OTLP exporter instead of the push API) remains a
  possible future simplification, but carries no functional gain now that the push API yields
  the canonical shape, and would add an IL2CPP-boundary dependency. Not pursued.
- Old-schema lines ingested before the switch age out within Loki retention; `loki-query`
  prints their raw JSON-blob line during that window (acceptable, no dual-mode reader).
