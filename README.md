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
- One of the two deployment shapes below

## Deployment shapes

Placeframe has two equally-supported ways to make the backend reachable from XR clients. Pick whichever fits your network — both are tested first-class paths.

| | Tunneled via ngrok | Air-gapped on LAN |
|---|---|---|
| **Reach** | Public internet | Local network only |
| **Internet at the host** | Required | Not required |
| **Transport to clients** | HTTPS (ngrok terminates TLS) | Cleartext HTTP |
| **Auth** | Keycloak OAuth (default) or disabled | `AUTH_MODE=disabled` (cleartext + OAuth is rejected at boot) |
| **What clients enter** | `PUBLIC_URL=https://<sub>.ngrok-free.app` | `PUBLIC_URL=http://<host-LAN-IP>:<port>` |

Consumers that layer additional services on top of placeframe (e.g. the Make-it-Sing multiplayer client, which adds a LiveKit server) may require additional ports and a different tunnel agent — see those consumers' own setup docs.

### Tunneled via ngrok

[ngrok](https://ngrok.com) is a tunneling service that forwards HTTP. Placeframe ships with the ngrok agent as a container alongside the stack; one HTTP tunnel covers the gateway, which is all placeframe-on-its-own needs.

1. **Sign up** at [ngrok.com](https://ngrok.com) and grab your authtoken from the dashboard.
2. **Reserve a domain** (ngrok's free tier gives one static subdomain on `*.ngrok-free.app`; paid tiers can use a custom domain).
3. **Copy `.env.sample` to `.env`** and fill in:

   | Variable | Value |
   |---|---|
   | `PUBLIC_URL` | `https://<your-ngrok-domain>` — the URL Unity clients will hit |
   | `NGROK_DOMAIN` | `<your-ngrok-domain>` (just the host portion, no scheme) |
   | `NGROK_AUTHTOKEN` | The token from step 1 |

   The ngrok agent activates when `NGROK_DOMAIN` is set; leaving it empty disables the tunnel.

4. **Bring it up:** `uv run up`. Visit `https://<your-ngrok-domain>` to confirm the gateway is reachable.

### Air-gapped on LAN

For a self-contained deployment with no internet — every XR client on the same LAN as the server — set:

| Variable | Value |
|---|---|
| `PUBLIC_URL` | `http://<host-LAN-IP>:<GATEWAY_PORT>`, e.g. `http://192.168.1.100:58080` |
| `AUTH_MODE` | `disabled` |

Leave `NGROK_DOMAIN` empty — the ngrok container will start and exit cleanly. The gateway serves cleartext HTTP on the LAN; distributing an internal CA to every Unity client is the cert-handling overhead this mode exists to avoid. `AUTH_MODE=keycloak` is rejected against a cleartext `PUBLIC_URL` because OAuth credentials must not flow without TLS.

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

While the server is running, you can visit `${PUBLIC_URL}` in a web browser to browse the OpenAPI schema and test requests.

The backend provides a reference [Keycloak](https://www.keycloak.org/) implementation for authentication and authorization, so you will need to authorize yourself in order to test requests. By default, you can use the username "user", and the password "password". This is configured in the [Keycloak realm configuration file](docker/auth-initializer/realm-export/placeframe.json).

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
