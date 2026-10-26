# The relays are long-lived agents whose control endpoints flap; a bare default
# restart policy ("no") would leave a relay dead after its first reconnect
# failure. Both tunnel seams register this template.
{{- range $workloadName, $workload := .Workloads }}
{{- range $containerName, $_ := $workload.containers }}
- op: set
  path: services.{{ $workloadName }}-{{ $containerName }}.restart
  value: on-failure
  description: Restart the {{ $workloadName }}-{{ $containerName }} relay on failure
{{- end }}
{{- end }}
