#!/bin/sh
set -euo pipefail

# (1) Bootstrap logging
exec > >(tee -a /var/log/beacon-bootstrap.log) 2>&1

# (2) Fetch runtime config from env or SSM
: "${SECRET_ARN:?SECRET_ARN must be set}"
: "${TAILNET_NAME:?TAILNET_NAME must be set}"
: "${CADDY_SERVICES:=api:8000 cloudbeaver:8978 minio:9000 minioconsole:9001}"
REGION="${REGION:-us-east-1}"

# (3) Start CloudWatch Agent
sed "s|\${REGION}|${REGION}|g" /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json.tmpl \
  > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# (4) Start tailscaled and auth
systemctl enable --now tailscaled
AUTH_KEY=$(aws secretsmanager get-secret-value \
  --region "$REGION" --secret-id "$SECRET_ARN" \
  --query SecretString --output text)
TS_AUTHKEY="$AUTH_KEY" tailscale up --hostname=beacon --accept-dns=true

# (5) Render Caddyfile from template
sb=""
for kv in $CADDY_SERVICES; do
  name=${kv%%:*}; port=${kv##*:}
  sb+="    $name  $port\n"
done
awk -v sb="$sb" -v tn="$TAILNET_NAME" \
  '{gsub("#SERVICES#", sb); gsub("\\${TAILNET_NAME}", tn); print}' \
  /etc/caddy/Caddyfile.tmpl >/etc/caddy/Caddyfile

# (6) Launch Caddy
caddy validate --config /etc/caddy/Caddyfile
exec caddy run --config /etc/caddy/Caddyfile
