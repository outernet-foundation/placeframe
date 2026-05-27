# Placeframe

Placeframe is a tool for connecting physical places to shared XR reference frames, using any XR device that provides developer access to a color camera. It is free, open source, and designed to be easily self-hosted.

## Why This Tool Exists

**Placeframe** solves a problem known as "relocalization", or the determination of an XR device's position and rotation in space, relative to a previously established, canonical reference frame for that space. It is the same sort of problem that is solved by products like:

- Niantic Spatial's **Localize** Visual Positioning System (formerly **Lightship VPS**)
- Microsoft's **Azure Spatial Anchors** (now defunct)
- Apples's **Shared World Anchors** (visionOS) or **Collaborative Sessions** (iOS)
- Google's ARCore **Cloud Anchors**
- Snap's **Connected Lenses**

However, all of these products restrict developer freedom.

Most of them are incompatible with each other (Apple's own two products aren't even compatible with each other, at time of writing). Most of them require that users stream their camera feeds to private servers, sometimes with the express intention of harvesting monetizable data from those camera feeds. Most of them make it expensive or impossible to maintain complete data sovereignty while using them. One of them (Azure Spatial Anchors) vendor-locked whole companies into their ecosystem and then sunsetted the entire product, leaving those companies stranded without recourse.

And none of them let you get your hands dirty. If you want to expand support to a novel device, or if you hit a weird edge case limitation that only matters to your application, all you can do is complain and cross your fingers.

The XR industry, and particularly the AR industry, is already a risky one. And most interesting AR applications fundamentally require the ability to establish shared reference frames between AR devices, a requirement that has historically had nothing but risky, restrictive solutions.

The lack of a permissive alternative has immeasurably hampered the growth of the AR industry. Placeframe fixes that.

# Acknowledgements

Built in association with [The Outernet](https://outernet.nyc), and made possible by a generous donation from The Robert Halper Foundation.

Powered by [epjecha](https://github.com/epjecha)'s awesome [Stateful](https://github.com/epjecha/StatefulUnity), [ObserveThing](https://github.com/outernet-foundation/ObserveThing), and [Nessle](https://github.com/outernet-foundation/Nessle) Unity packages, for reactive state management and declarative UI in Unity.

Inspired by (and heavily borrowing from) the extremely useful [Hierarchical-Localization](https://github.com/cvg/Hierarchical-Localization) repo.

# Quick Start

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [NVIDIA CUDA](https://developer.nvidia.com/cuda-downloads) (experimental [ROCm](https://rocm.docs.amd.com/) support also available)
- A way to give the host a public-internet address (see [Exposure modes](#exposure-modes) below)

## Exposure modes

The backend speaks HTTPS for the API/auth surface and WebRTC (UDP + TCP) for the LiveKit data-channel relay. The host needs to be reachable on those ports from wherever your XR clients are.

### Public internet, via Localtonet (recommended for engineer dev)

[Localtonet](https://localtonet.com) is a tunneling service that forwards HTTP, TCP, and UDP. Unlike HTTP-only tunnels (ngrok, Cloudflare Tunnel, Tailscale Funnel), it can carry the UDP media path that LiveKit's WebRTC stack requires. You get a free `<yourname>.localto.net` subdomain, real Let's Encrypt certificates for your HTTPS surface, and reservable public ports for the LiveKit listeners.

#### Picking the right tunnel type per service

Localtonet offers four tunnel types in their dashboard. You'll only need three of them for placeframe; the choice between **HTTP** and **TCP** matters and is worth understanding up front:

- **HTTP tunnel** — Localtonet terminates TLS at their edge with a real Let's Encrypt cert and forwards plain HTTP to your local service. Use this for anything that's HTTP at the wire level *and* that you want exposed at `https://<yourname>.localto.net` (no port number in the URL). The placeframe gateway (Caddy) is the only service of this kind.
- **TCP tunnel** — Localtonet just forwards the raw TCP bytes between a reserved public port on `<yourname>.localto.net:<port>` and a local port. No TLS handling on Localtonet's side; whatever the protocol speaks goes through untouched. Use this for the LiveKit signaling channel (which is WebSocket — technically HTTP-shaped, but easier to forward as raw TCP than to wrestle with the HTTP-tunnel WebSocket-upgrade path) and the LiveKit TURN/TCP fallback (which is the [TURN protocol](https://en.wikipedia.org/wiki/Traversal_Using_Relays_around_NAT) and not HTTP at all).
- **UDP tunnel** — same as TCP but for UDP. Use this for the LiveKit RTC media path.
- **TLS tunnel** — TLS passthrough. Localtonet forwards the encrypted bytes and you terminate TLS yourself. *Don't use this for placeframe* — the gateway's HTTP tunnel is simpler and gets you a free cert.

#### Step-by-step

1. **Sign up** at [localtonet.com](https://localtonet.com). The free plan only gives you one tunnel total, so you'll need to upgrade — the Basic plan is the cheapest tier that covers what placeframe needs (5 reserved-port TCP/UDP tunnels and the HTTP one).

2. **Get your authtoken.** Dashboard → **My Tokens** → copy the token. You'll paste it into `.env` as `LOCALTONET_AUTHTOKEN` below.

3. **Create the three tunnels.** From the dashboard, hit "New Tunnel" (or equivalent) for each row. Localtonet doesn't let one subdomain serve multiple tunnels, so each tunnel below gets its own distinct subdomain:

   | # | Tunnel type | Subdomain (each one distinct) | Public port | Local address | What it's for |
   |---|---|---|---|---|---|
   | 1 | **HTTP** | e.g. `<yourname>-placeframe.localto.net` | 443 (implicit on HTTP tunnels) | `localhost:58080` | placeframe gateway — Caddy reverse-proxies to the API, Keycloak, Loki, etc. behind one HTTPS endpoint |
   | 2 | **TCP** | e.g. `<yourname>-livekit-signaling.localto.net` | reserve port `7880` | `localhost:7880` | LiveKit signaling channel (WebSocket, plaintext `ws://`) |
   | 3 | **UDP** | e.g. `<yourname>-livekit.localto.net` | reserve port `7882` | `localhost:7882` | LiveKit RTC media path (the actual audio/video/data UDP packets) |

   For tunnels 2 and 3, **reserve the specific port numbers `7880` and `7882`** to match LiveKit's default bind ports — LiveKit advertises its bind port as its public port and there's no separate "translated port" config, so these must agree. If Localtonet doesn't let you pick those exact ports, see "Port-reservation alternative" below.

   After creating each tunnel, mark it as **"Start"** so the Localtonet agent (which runs as a container in the placeframe stack) brings it up automatically.

   We do not include a TURN/TCP fallback tunnel. LiveKit's `node_ip` is a single value used for both UDP RTC and TCP TURN, and these two would need to live on the same Localtonet edge IP — which means the same subdomain, which Localtonet doesn't allow. Skipping TURN means clients on networks that block UDP (some corporate / hotel / conference networks) won't be able to connect; for normal home / cellular / office wifi this is invisible.

4. **Copy `.env.sample` to `.env`** and fill in:

   | Variable | Value |
   |---|---|
   | `COMPOSE_PROFILES` | `localtonet` — runs the Localtonet agent as a container alongside the rest of the stack |
   | `LOCALTONET_AUTHTOKEN` | The token from step 2 |
   | `GATEWAY_TLS_MODE` | `plain` — Localtonet handles TLS at the edge, so Caddy serves plain HTTP internally |
   | `PUBLIC_DOMAIN` | The subdomain from tunnel 1, e.g. `<yourname>-placeframe.localto.net` |
   | `LIVEKIT_SIGNALING_DOMAIN` | The subdomain from tunnel 2, e.g. `<yourname>-livekit-signaling.localto.net` |
   | `LIVEKIT_SIGNALING_PORT` | `7880` (or whatever public port tunnel 2 ended up on) |
   | `LIVEKIT_RTC_DOMAIN` | The subdomain from tunnel 3, e.g. `<yourname>-livekit.localto.net` |
   | `LIVEKIT_RTC_PORT` | `7882` (or whatever public port tunnel 3 ended up on) |

   Leave the other env vars at their defaults unless you have a reason to change them.

5. **Bring it up:** `uv run lock-python` (one-time, to pin the Localtonet agent image digest) then `uv run up`. Visit `https://<your-gateway-subdomain>.localto.net` to confirm the gateway is reachable.

#### Port-reservation alternative

If your Localtonet tier doesn't let you reserve specific port numbers (7880 / 7882) and just assigns you random ports, see [this thread / future work] — supporting that needs LiveKit configured to bind locally to the assigned ports rather than its defaults, which requires a mounted `livekit.yaml` config and isn't wired up in this branch.

### LAN-only / air-gapped

For a self-contained deployment with no internet (or one where every client is on the same LAN), set:

- `COMPOSE_PROFILES=` (empty — the Localtonet agent service does not run).
- `GATEWAY_TLS_MODE=internal` — Caddy terminates TLS itself with an internal CA.
- `PUBLIC_DOMAIN=localhost` or the host's LAN hostname.
- `LIVEKIT_SIGNALING_DOMAIN=<host's LAN IP or hostname>`, `LIVEKIT_SIGNALING_PORT=7880`.
- `LIVEKIT_RTC_DOMAIN=<host's LAN IP or hostname>`, `LIVEKIT_RTC_PORT=7882`.

No Localtonet agent runs, no internet required.

## Backend

Once `.env` is filled in for your chosen exposure mode, bring up the backend with:

```
uv run up
```

You can pass `--attached` to this command in order to stream interlaced server container logs, but this is very difficult to read. The VS Code extension [ms-azuretools.vscode-docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker) is a better alternative for easily viewing individual container logs.

To bring down the backend, run:

```
uv run down
```

While the server is running, you can visit `https://${PUBLIC_DOMAIN}` in a web browser to browse the OpenAPI schema and test requests.

The backend provides a reference [Keycloak](https://www.keycloak.org/) implementation for authentication and authorization, so you will need to authorize yourself in order to test requests. By default, you can use the username "user", and the password "password". This is configured in the [Keycloak realm configuration file](docker/keycloak/realm-export/placeframe.json).

The backend also includes the following admin UIs, accessible from your public domain:

- **Grafana** (`/grafana/`) — centralized log viewer, aggregating logs from all services via Loki
- **CloudBeaver** (`/cloudbeaver/`) — web-based database UI for browsing the PostgreSQL database

## Capture Tool

Placeframe has a tool built in Unity for capturing and submitting map data, as well as validating reconstructed maps by localizing against them. An Android build is available on the [releases page](https://github.com/outernet-foundation/placeframe/releases/latest).

With this application, you can log in to your Placeframe backend, capture data of your environment (we recommend walking the perimeter of the environment with camera facing inwards), submit that data to the backend for localization map reconstruction, and finally validate that map by localizing against it. A few moments after starting relocalization, you will see a point cloud in your environment, tracking your environment.

**NOTE:** In this application, relocalization runs at a higher frequency than is ideal for real applications. Placeframe defers to the device's native world tracking for high-precision, low-latency localization, only intervening to correct drift against its canonical reference frame, by filtering out low-confidence and low-novelty relocalization results. However, this filtering is currently fairly primitive — more sophisticated tools for controlling this behavior will ship in a future release.

## Map Registration Tool

Placeframe also has a tool built in Unity for **registering** maps against Cesium Tilesets. Windows and Linux standalone builds are available on the [releases page](https://github.com/outernet-foundation/placeframe/releases/latest).

Using this tool, previously constructed localization maps can be visualized using their point clouds and visually aligned with Open Street Map (OSM) building geometry, or Google Photorealistic Tiles. This can be used to georeference localization maps, allowing Placeframe applications to anchor AR content using GPS coordinates.

## Unity Packages

Placeframe has Unity packages for ARFoundation and Magic Leap 2 that handle communication between a Unity app and a Placeframe backend deployment. They are published to npm and can be installed via the Unity Package Manager using a [scoped registry](https://docs.unity3d.com/Manual/upm-scoped.html):

| Package | npm |
|---|---|
| `org.outernet.placeframe` | [Core](https://www.npmjs.com/package/org.outernet.placeframe) |
| `org.outernet.placeframe.arfoundation` | [ARFoundation](https://www.npmjs.com/package/org.outernet.placeframe.arfoundation) |
| `org.outernet.placeframe.magicleap` | [Magic Leap](https://www.npmjs.com/package/org.outernet.placeframe.magicleap) |
