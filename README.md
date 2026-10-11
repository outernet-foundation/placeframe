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

Built by [The Outernet Foundation](https://outernetfoundation.org), and made possible by a generous donation from The Robert Halper Foundation.

Powered by [epjecha](https://github.com/epjecha)'s awesome [Stateful](https://github.com/epjecha/StatefulUnity), [ObserveThing](https://github.com/outernet-foundation/ObserveThing), and [Nessle](https://github.com/outernet-foundation/Nessle) Unity packages, for reactive state management and declarative UI in Unity.

Inspired by (and heavily borrowing from) the extremely useful [Hierarchical-Localization](https://github.com/cvg/Hierarchical-Localization) repo.

# Quick Start

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [NVIDIA CUDA](https://developer.nvidia.com/cuda-downloads) (experimental [ROCm](https://rocm.docs.amd.com/) support also available)
- An [ngrok](https://ngrok.com) account (the free tier works)

## Initial Setup

1. **Sign up** at [ngrok.com](https://ngrok.com) and grab your authtoken from the dashboard.
2. **Reserve a domain** (ngrok's free tier gives one static subdomain on `*.ngrok-free.app`; paid tiers can use a custom domain).
3. **Copy `.env.sample` to `.env`** and fill in:

   | Variable | Value |
   |---|---|
   | `PUBLIC_URL` | `https://<your-ngrok-domain>` — the URL Unity clients will hit |
   | `NGROK_DOMAIN` | `<your-ngrok-domain>` (just the host portion, no scheme) |
   | `NGROK_AUTHTOKEN` | The token from step 1 |

## Backend

Once `.env` is filled in, bring up the backend with:

```
uv run up
```

You can pass `--attached` to this command in order to stream interlaced server container logs, but this is very difficult to read. The VS Code extension [ms-azuretools.vscode-docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker) is a better alternative for easily viewing individual container logs.

To bring down the backend, run:

```
uv run down
```

While the server is running, you can visit `${PUBLIC_URL}` in a web browser to browse the OpenAPI schema and test requests.

The backend provides a reference [Keycloak](https://www.keycloak.org/) implementation for authentication and authorization, so you will need to authorize yourself in order to test requests. By default, you can use the username "user", and the password "password". This is configured in the [Keycloak realm configuration file](workloads/auth-initializer/realm-export/placeframe.json).

## Capture Tool

You can find a complete Android Mobile application demonstrating placeframe - including capturing scan data, creating maps, and localizing against those maps - in the [Placeframe Capture Tool](https://github.com/outernet-foundation/placeframe-capture-tool) repo, also maintained by The Outernet Foundation.

## Unity Packages

Placeframe ships a variety of Unity packages for communicating with a Placeframe backend deployment. To use any of them, you will need to add two scoped registries to your application's package manifest:

```json
  "scopedRegistries": [
    {
      "name": "npmjs",
      "url": "https://registry.npmjs.org",
      "scopes": [ "org.outernet" ]
    },
    {
      "name": "UnityNuGet",
      "url": "https://unitynuget-registry.openupm.com",
      "scopes": [ "org.nuget" ]
    }
  ]
```

Placeframe has first class support for Android Mobile and Magic Leap 2, with more platforms planned:

| Package | npm |
|---|---|
| `org.outernet.placeframe.arfoundation` | [ARFoundation](https://www.npmjs.com/package/org.outernet.placeframe.arfoundation) |
| `org.outernet.placeframe.magicleap` | [Magic Leap](https://www.npmjs.com/package/org.outernet.placeframe.magicleap) |

You can also build support for custom platforms on top of the core Placeframe package (which is pulled in transitively by the existing platform packages):

| Package | npm |
|---|---|
| `org.outernet.placeframe` | [Core](https://www.npmjs.com/package/org.outernet.placeframe) |

Placeframe also ships several utility packages that are use by the [Placeframe Capture Tool](https://github.com/outernet-foundation/placeframe-capture-tool), including a lower level C# typed api client for interacting directly with the backend, and jwt-based auth handler for Unity, and a logging package for Unity that provides a variety of features, including integration with Grafana Loki:

| Package | npm |
|---|---|
| `org.outernet.placeframe.apiclient` | [API Client](https://www.npmjs.com/package/org.outernet.placeframe.apiclient) |
| `org.outernet.placeframe.auth` | [Auth](https://www.npmjs.com/package/org.outernet.placeframe.auth) |
| `org.outernet.logging` | [Logging](https://www.npmjs.com/package/org.outernet.logging) |



