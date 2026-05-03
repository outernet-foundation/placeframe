# Accessing placeframe Docker containers from host VS Code

Notes from a session where we tried to view the `placeframe-*` Docker containers
from the host's VS Code Container Tools extension. We did not implement any of
the options below — this is a record of what we learned so we can revisit later.

## Why this is non-trivial

The development environment is a stack:

1. **Host** — runs Incus and COI (Code on Incus). The host has its own Docker
   daemon (or none); whatever it has does not see placeframe containers.
2. **Incus system container** named `pulsar`, built from the COI profile at
   `/workspace/.coi/profiles/placeframe/{config.toml,build.sh}`. This is where
   `claude`, `uv run up`, etc. all execute.
3. **Docker daemon inside the Incus container**, listening only on
   `/var/run/docker.sock`. All `placeframe-*` containers (api, postgres,
   reconstructor-cuda, etc.) are children of this daemon.

VS Code's Container Tools / Docker extension talks to whatever `DOCKER_HOST`
(or the active docker context) points at. By default that's the host's local
unix socket, which has no visibility into the daemon nested inside the Incus
container.

The Incus container has **no sshd installed** and Docker is **not exposed over
TCP** — only the local unix socket. So there is no out-of-the-box path from the
host extension to the nested daemon.

## Three options, ordered by effort

### Option 1 — Incus proxy device exposing the socket on the host

Lowest effort, no profile changes, easily reversible. From the host:

```
incus config device add pulsar dockersock proxy \
  listen=unix:/tmp/pulsar-docker.sock \
  connect=unix:/var/run/docker.sock \
  bind=host
```

Then on the host, point VS Code at it via either:

- `DOCKER_HOST=unix:///tmp/pulsar-docker.sock` in the environment that launches
  VS Code, or
- a new docker context (`docker context create pulsar --docker
  host=unix:///tmp/pulsar-docker.sock`) and switch the extension to it via the
  Docker: Contexts pane.

Container Tools should then list all `placeframe-*` containers, with
shell/logs/exec/inspect all working as if they were local.

Teardown: `incus config device remove pulsar dockersock`.

**Caveat:** root on the host socket equals root in the nested daemon. The
listen socket's ownership/permissions on the host should restrict to your user.
The proxy device persists across container restarts.

### Option 2 — Install sshd in the COI profile + use `DOCKER_HOST=ssh://...`

Edit `/workspace/.coi/profiles/placeframe/build.sh` to install and enable
openssh-server, then rebuild the image (`uv run setup-agent-sandbox --rebuild`
on the host). Add an Incus proxy device for port 22 if needed. From the host,
set `DOCKER_HOST=ssh://code@<container-ip>` (or use a docker context). VS
Code's docker extension natively supports the `ssh://` transport.

More VS-Code-native than the unix-socket proxy and arguably more secure (auth
gated by SSH keys), but the profile is shared infra — adding sshd affects every
slot built from it.

### Option 3 — VS Code Remote-SSH into the Incus container

Same prerequisite as Option 2 (sshd must be installed in the profile). Open
the container itself as a remote workspace; the Container Tools extension then
runs *inside* the container and uses the local docker socket directly. No
proxy needed.

This is the most ergonomic if you want to *edit code* in the container too,
not just inspect docker state. Heavier setup than Option 1 if container
inspection is the only goal.

## Recommendation

If the only goal is "see the placeframe containers in the VS Code Docker
panel," **Option 1** is the right call: one Incus command on the host, no
profile changes, trivial to remove. Revisit Options 2/3 only if we want a
broader "open the sandbox in VS Code" workflow.
