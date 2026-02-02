# Placeframe

Placeframe is tool for connecting physical places to shared XR reference frames, using any XR device that provides developer access to a color camera. It is free, open source, and designed to be easily self-hosted.

## Why This Tool Exists

**Placeframe** solves the same sort of problem as products like:

- Niantic Spatial's **Localize** Visual Positioning System (formerly **Lightship VPS**)
- Microsoft's **Azure Spatial Anchors** (now defunct)
- Apples's **Shared World Anchors** (visionOS) or **Collaborative Sessions** (iOS)
- Google's ARCore **Cloud Anchors**
- Snap's **Connected Lenses**

However, all of these comparable products restrict developer freedom in crippling ways.

Most of these solutions are incompatible with each other (Apple's own two products aren't even compatible with each other, at time of writing). Most of them require that users stream their camera feeds to private servers, sometimes with the express intention of harvesting monetizable data from those camera feeds. Most of them make it expensive or impossible to maintain complete data sovereignty while using them. One of them (Azure Spatial Anchors) vendor-locked whole companies into their ecosystem and then sunsetted the entire product, leaving those companies stranded without recourse.

And none of them let you get your hands dirty. If you want to expand support to a novel device, or if you hit a weird edge case limitation that only matters to your application, all you can do is complain and cross your fingers.

The XR industry, and particularly the AR industry, is already a risky one. And most interesting AR applications fundamentally require the ability to establish shared reference frames between AR devices, a requirement that has historically had nothing but risky, restrictive solutions. The lack of a permissive alternative has immeasurably hampered the growth of the AR industry.

Placeframe fixes that.

# Acknowledgements

Built in association with [The Outernet](https://outernet.nyc), and made possible by a generous donation from The Robert Halper Foundation.

Powered by [epjecha](https://github.com/epjecha)’s awesome [Stateful](https://github.com/epjecha/StatefulUnity), [ObserveThing](https://github.com/outernet-foundation/ObserveThing), and [Nessle](https://github.com/outernet-foundation/Nessle) Unity packages, for reactive state management and declarative UI in Unity.

Inspired by (and heavily borrowing from) the extremely useful [Hierarchical-Localization](https://github.com/cvg/Hierarchical-Localization) repo.

# Quick Start

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [NVIDIA CUDA](https://developer.nvidia.com/cuda-downloads) (experimental [ROCm](https://rocm.docs.amd.com/) support also available)
- An free [ngrok](https://ngrok.com/) account with:
  - An auth token
  - A static domain (your "dev domain")

## Backend

To bring up the backend, first copy `.env.sample` to `.env` and configure `PUBLIC_DOMAIN` and `NGROK_AUTHTOKEN` in that file, for your specific ngrok account. Then run:

```
uv run up
```

You can pass `--attached` to this command in order to stream interlaced server container logs, but this is very difficult to read. The VS Code extension [ms-azuretools.vscode-docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker) is a better alternative for easily viewing individual container logs.

To bring down the backend, run:

```
uv run down
```

While the server is running, you can visit you ngrok static domain in a web browser to browse the OpenAPI schema and test requests.

The backend provides a reference [Keycloak](https://www.keycloak.org/) implementation for authentication and authorization, so you will need to authorize yourself in order to test requests. By default, you can use the username "user", and the password "password". This is configured in the file `docker\keycloak\realm-export\placeframe.json`

## Frontend

Placeframe has a complete Unity reference application for Android Mobile in `apps\AndroidMobile`, which can be used to capture data for an environment, submit it to the backend for map construction, and then localize against that constructed map, with a point cloud visualization that conveys the localized alignment between the real world and the localization map. **TODO finish**

Placeframe also has a tool build in Unity for "registering" maps against Cesium Tilesets in `apps\MapRegistrationTool`, by visually aligning a maps point cloud visualization with Open Street Map (OSM) building geometry, or Google Photorealistic Tiles. This can be use to georeference localization maps, allowing Placeframe applications to anchor AR content using GPS coordinates. **TODO finish**

Finally, Placeframe has a Unity package (currently supporting ARFoundation) for communicating between an Unity app and a Placeframe backend deployment. It can be included in your own project by using a git link. **TODO finish**
