#!/bin/sh
# SeaweedFS ships S3 credentials and the audit-log sink as config files, not
# flags; render both from env at container start, then hand off to the
# upstream entrypoint (which adds -dir=/data -volume.max=0
# -master.volumeSizeLimitMB=1024 to `server`).
set -e
mkdir -p /etc/seaweedfs
cat > /etc/seaweedfs/s3.json <<EOF
{
  "identities": [
    {
      "name": "admin",
      "credentials": [{"accessKey": "${S3_ACCESS_KEY}", "secretKey": "${S3_SECRET_KEY}"}],
      "actions": ["Admin", "Read", "Write", "List", "Tagging"]
    }
  ]
}
EOF
cat > /etc/seaweedfs/fluent.json <<EOF
{"fluent_host": "seaweedfs-audit", "fluent_port": 24224}
EOF

exec /entrypoint.sh "$@"
