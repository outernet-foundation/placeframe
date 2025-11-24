# Acknowledgements
This project is being built in association with The Outernet Foundation, and was made possible
thanks to a generous donation by the The Robert Halper Foundation.

This project was inspired by and heavily cribs from the extremely useful Hierarchical-Localization repo.
# About
Plerion is an MIT-licensed fullstack solution for creating, serving, and accurately localizing against
"maps" of most of environments. Localization is the process used by virtual and augmented reality
systems to determine their precise position and orientation in space, with respect to a "map" that the system has
of its environment.

Using plerion, arbitrary augmented reality clients can create and share these maps,
and therefore agree upon
a shared reference frame, such that a piece of AR content appearing in a certain place for one user
appears there for every user.

Notable features:
- Unity localization package
- Android mobile reference app
- Zed capture app for large environments (wip)
- Tooling for registering maps against Cesium tilesets (wip)
- Rig-aware geometric verification using colmap 3.13
- Superpoint/Lightglue for feature point descriptor extraction and matching
- deep-image-retrieval for image retrieval descriptor extraction
- FAISS OPQ for compressing feature point descriptors
- Typed Rest API clients (currently python and C#) using openapi-generator-cli
- Pulumi AWS IaaC (wip)
- Postgres RLS with with Keycloak Auth

Notable missing features (that I'd love to add):
- On-device localization (running an Onnx module with Unity Sentis might work)
- Image segmentation to clean up reconstruction inputs
- Other localization clients (Unreal, Godot, WebXR)
# Building and deploying the server
### Prerequisites
- CUDA recommended
- uv
- docker engine
- default-jre (optional, for (re)generating typed openapi clients)
- ngrok tunnel (optional)
  - Simple way to get a static domain name
  - Sign up for a free account and follow their instructions to start a tunnel on port 8080 from
    your machine to your ngrok "dev domain"
### Clone submodules
Superpoint and deep-image-retrieval have no packaging files. Git submodules work, but I will
probably fork later and just add packaging files.

```
git submodule update --init --recursive
```
### Sync python packages
```
uv sync --all-packages
```
### (Re)generate datamodels and clients (optional)
If you modify the database schema or any of the apis, use these commands to regenerate datamodels
from the schema or typed clients from the apis
```
uv run --project scripts --no_workspace 
  generate-datamodels 
  --database plerion 
  --datamodels-path packages\datamodels\src\datamodels
  
uv run --project scripts --no_workspace 
  generate-clients 
  --config openapi-projects.json 
  [--no-cache (optional)]
```
### Create env file
Copy `./.env.sample` to `.env` and change PUBLIC_URL in that file to your domain url (e.g. from ngrok)
### Build images and serve
```
docker compose --profile ephemeral build
docker compose up -d
```
# Building the Android Mobile app
- Install Unity 6000.0.56f1 with Android Build Support
- Open apps/PlerionAndroidMobile in Unity
- Configure plerion url
  - TODO
- Switch platorm to Android Mobile and build main scene
# Building, installing, and running the Zed capture app
TODO
