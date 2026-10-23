# ROCm device access for GPU-marked workloads (metadata annotation placeframe.io/gpu):
# the render/video device nodes plus the groups allowed to open them, matching the
# hand compose.rocm.yml posture (score-compose's output schema wants DeviceMapping
# objects and string group ids). Per-variant twin of gpu-cuda.tpl — the {gpu} token in
# the registered template name selects this file for the rocm compose output.
{{- range $workloadName, $workload := .Workloads }}
{{- if eq (dig "metadata" "annotations" "placeframe.io/gpu" "" $workload) "true" }}
{{- range $containerName, $_ := $workload.containers }}
- op: set
  path: services.{{ $workloadName }}-{{ $containerName }}.devices
  value:
    - source: /dev/kfd
      target: /dev/kfd
    - source: /dev/dri
      target: /dev/dri
  description: ROCm device nodes for {{ $workloadName }}-{{ $containerName }}
- op: set
  path: services.{{ $workloadName }}-{{ $containerName }}.group_add
  value:
    - "44"
    - "110"
  description: ROCm render/video group membership for {{ $workloadName }}-{{ $containerName }}
{{- end }}
{{- end }}
{{- end }}
