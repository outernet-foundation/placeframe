# The auto-built wait-for-resources gate aggregates every provisioner service with
# required: true, which breaks profile-gated services: docker compose treats an
# inactive-profile service as undefined, so any operator not enabling
# tunnel-ngrok/tunnel-rathole would fail on "depends on undefined service". The gate
# entries are also semantically wrong for relays — the gateway forwards traffic to
# whatever tunnel happens to run alongside it; it does not depend on the relay being
# up. This template carves every profile-gated service out of the gate — the set is
# derived from the generated compose itself, so a future profile-gated service needs
# no edit here — leaving profiles as the sole activation switch.
{{- range $serviceName, $service := .Compose.services }}
{{- if $service.profiles }}
- op: delete
  path: services.wait-for-resources.depends_on.{{ $serviceName }}
  description: Exclude profile-gated {{ $serviceName }} from the resources gate
{{- end }}
{{- end }}
