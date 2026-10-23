# KEDA owns /spec/replicas for workloads declaring a keda-scaled-object resource, so
# the rendered Deployment starts at zero: no queue means no pods, and a fresh apply
# must not boot a GPU worker before the operator is watching. Argo's selfHeal fights
# KEDA over this field unless the Application carries ignoreDifferences — infra-side
# configuration, not artifact content. .Workloads is captured before the range (see
# gpu-pod.tpl).
{{- $workloads := .Workloads }}
{{- range $i, $manifest := .Manifests }}
{{- if eq $manifest.kind "Deployment" }}
{{- $workloadName := dig "metadata" "annotations" "k8s.score.dev/workload-name" "" $manifest }}
{{- if $workloadName }}
{{- $workload := index $workloads $workloadName }}
{{- if $workload }}
{{- range $_, $resource := $workload.resources }}
{{- if eq $resource.type "keda-scaled-object" }}
- op: set
  path: {{ $i }}.spec.replicas
  value: 0
  description: Scale-to-zero start for KEDA-managed {{ $workloadName }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
