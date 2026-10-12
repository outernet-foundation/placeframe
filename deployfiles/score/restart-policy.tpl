- op: set
  path: services.api-api.restart
  value: unless-stopped
  description: Keep the api serving across container restarts (compose only; Kubernetes restarts pods natively)
