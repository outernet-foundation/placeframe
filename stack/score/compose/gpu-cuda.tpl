# CUDA device access for GPU-marked workloads (metadata annotation placeframe.io/gpu),
# matching the hand compose.cuda.yml `gpus: all` semantics in the long-form device
# reservation (score-compose's output schema accepts no `gpus` scalar and no `count:
# all`; an omitted count means every GPU). Per-variant twin of gpu-rocm.tpl — the {gpu}
# token in the registered template name selects this file for the cuda compose output.
# Service names are computed from the workload/container pair, never hardcoded.
{{- range $workloadName, $workload := .Workloads }}
{{- if eq (dig "metadata" "annotations" "placeframe.io/gpu" "" $workload) "true" }}
{{- range $containerName, $_ := $workload.containers }}
- op: set
  path: services.{{ $workloadName }}-{{ $containerName }}.deploy.resources.reservations.devices
  value:
    - driver: nvidia
      capabilities: [gpu]
  description: CUDA device access for {{ $workloadName }}-{{ $containerName }}
{{- end }}
{{- end }}
{{- end }}
