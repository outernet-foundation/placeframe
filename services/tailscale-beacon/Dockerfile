# 1) Base on AL2023 so you get DNF, AWS CLI v2, CloudWatch Agent, etc.
FROM amazonlinux:2023

# 2) Install Tailscale & Caddy in one layer
RUN set -euxo pipefail \
  && yum -y install curl dnf-plugins-core \
  && curl -fsSL https://tailscale.com/install.sh | sh \
  # add Caddy repo and install
  && rpm --import https://rpm.caddyserver.com/pubkey.gpg \
  && dnf config-manager --add-repo https://rpm.caddyserver.com/caddy.repo \
  && yum -y install caddy \
  # install CloudWatch Agent
  && yum -y install amazon-cloudwatch-agent \
  && mkdir -p /opt/aws/amazon-cloudwatch-agent/etc

# 3) Copy in your Caddyfile template
COPY Caddyfile.tmpl /etc/caddy/Caddyfile.tmpl

# 4) Add our tiny entrypoint
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

RUN apt-get update \
 && apt-get install -y dos2unix \
 && dos2unix /usr/local/bin/entrypoint.sh
 
# 5) Default command
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
