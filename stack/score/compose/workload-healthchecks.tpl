# score-compose validates and drops workload livenessProbes (httpGet is not a
# supported compose concept), so the generated compose would gate nothing on
# workload health while the k8s rendering emits real probes. This patch-template
# class closes that drift: it reads the same livenessProbe declarations from
# .Workloads and emits a compose healthcheck against the computed
# <workload>-<container> service name. The probe runs via python urllib because
# the placeframe workload images are python-based and ship neither wget nor curl;
# timing parameters mirror the hand compose stack's api/lease-server checks.
{{- range $workloadName, $workload := .Workloads }}
{{- range $containerName, $container := $workload.containers }}
{{- with $container.livenessProbe.httpGet }}
- op: set
  path: services.{{ $workloadName }}-{{ $containerName }}.healthcheck
  value:
    test:
      [
        "CMD",
        "python",
        "-c",
        "import urllib.request; urllib.request.urlopen('http://localhost:{{ .port }}{{ .path }}')",
      ]
    interval: 5s
    start_period: 5s
    timeout: 5s
    retries: 3
  description: Healthcheck from livenessProbe for {{ $workloadName }}-{{ $containerName }}
{{- end }}
{{- end }}
{{- end }}
