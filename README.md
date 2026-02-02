# Placeframe

Placeframe is tool for connecting physical places to shared XR reference frames, using any XR device that provides developer access to a color camera. It is free, open source, and designed to be easily self-hosted.

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

The backend provides a reference [Keycloak](https://www.keycloak.org/) implementation for authentication and authorization, so you will need to authorize yourself in order to test requests. By default, you can use the username "user", and the password "password". This is configured in the file: `docker\keycloak\realm-export\placeframe.json`

## Capture Tool

Placeframe has a tool build in Unity for capturing and submitting map data, as well validating reconstructed maps by localizing aginst them. It can be dowloaded on the [releases page](https://github.com/outernet-foundation/placeframe/releases/download/alpha/AndroidMobile.apk).

With this application, you can login into your Placeframe backend, capture data of your environment (we recommend walking the perimeter of the envrionment with camera facing inwards), submit that data to the backend for localization map reconstruction, and finally validate that map by localizing against it. A few moments after starting relocalization, you will see a point cloud in your environment, tracking your environment.

**NOTE:** In this application, the point cloud will be constantly moving. This is because, at present, the capture application simply runs relocalization continously and applies every result as it arrives. Future releases will add tools for controlling how and when relocalization are applied, letting the device's native world tracking system handle the high precision, low latency tracking, and only apply relocalizations when that native tracking drifts away from the current localization map.

## Map Registration Tool

Placeframe also has a tool built in Unity for **registering** maps against Cesium Tilesets. Currently, this tool can be explored directly in the Unity editor using play mode; a future release will include downloadable builds of this tool. You can find it in this folder: `apps\MapRegistrationTool`.

Using this tool, previously constructed localization maps can be visualized using their point clouds and visually aligned with Open Street Map (OSM) building geometry, or Google Photorealistic Tiles. This can be used to georeference localization maps, allowing Placeframe applications to anchor AR content using GPS coordinates.

## Unity Package

Finally, Placeframe has Unity packages (currently supporting ARFoundation, with Magic Leap 2 support coming in a future release) for communicating between an Unity app and a Placeframe backend deployment. It can currently be included using git URLs; a future release will add a scope package registry. You can find it in this folder: `packages\unity\Placeframe`.
