# Acknowledgements

Built in association with [The Outernet](https://outernet.nyc), and made possible by a generous donation from The Robert Halper Foundation.

Powered by [epjecha](https://github.com/epjecha)’s awesome [Stateful](https://github.com/epjecha/StatefulUnity), [ObserveThing](https://github.com/outernet-foundation/ObserveThing), and [Nessle](https://github.com/outernet-foundation/Nessle) Unity packages, for reactive state management and declarative UI in Unity.

Inspired by (and heavily borrowing from) the extremely useful [Hierarchical-Localization](https://github.com/cvg/Hierarchical-Localization) repo.

# About

**Plerion** is an MIT-licensed fullstack solution for creating, serving, and accurately localizing against
**visual localization maps** of real-world environments.

Localization is the process used by Augmented and Virtual Reality (AR/VR)
systems to determine their precise position and orientation in space, with respect to a "map" that the system has
of its environment. Using Plerion, arbitrary AR applications can create and share these maps,
and therefore agree upon
a shared reference frame, such that a piece of AR content that appears in a certain place in the real world for one user,
appears there for every user.

Plerion targets the same class of problems as products like Niantic’s visual positioning system (VPS), but is fully open-source, and was built from the ground up to be self-hostable.

## Notable features:

- **Unity localization package**
- **Android Mobile application**
  - Data capture client for capturing map construction inputs
  - Basic map management functionality
  - Reference implementation for using the Unity localization package
- **Learned local and global visual features**
  - [Superpoint/Lightglue](https://github.com/cvg/LightGlue) for feature point extraction and matching
  - [Deep Image Retrieval (DIR)](https://github.com/naver/deep-image-retrieval) for global descriptor extraction
  - FAISS OPQ for compressing feature point descriptors
- **Map construction based on [COLMAP 3.13](https://github.com/colmap/colmap/releases/tag/3.13.0)**
  - Rig-aware geometric verification
  - Support for deterministic map reconstructions
- **Typed REST API clients**
  - Generated clients for Python and C# using openapi-generator-cli
- **Infrastructure and security**
  - PostgreSQL with row-level-security (RLS)
  - Reference OAuth2 implemenation using Keycloak

## Work-in-progress features:

- Localization support for Magic Leap 2
- Zed data capture app for large environments
- Tooling for georeferencing maps by visually registering them against Cesium tilesets
- AWS IaaC using Pulumi
- CI/CD using Github actions

## Possible future features:

- On-device localization (e.g. running an Onnx module using Unity Sentis)
- AnyLoc-VLAD-DINOv2 instead of DIR for image retrieval
- Image segmentation to sanitize reconstruction inputs
- Other localization clients (Unreal, Godot, WebXR)

# Building and deploying the server

### Prerequisites

- CUDA recommended
- [Docker Engine](https://docs.docker.com/engine/)
- [ngrok](https://ngrok.com/) (optional)
  - Simple way to get a static domain name
  - Sign up for a free account and follow their instructions to start a tunnel on port 8080 from
    your machine to your ngrok "dev domain"

### Create env file

Copy `./.env.sample` to `.env` and change PUBLIC_URL in that file to your domain url (e.g. from ngrok).

### Build images and serve

```
docker compose --profile ephemeral build
docker compose up -d
```

### Verify

Visiting your public url should now take you to a Swagger UI for the API.

- In order to use the API, including via the Swagger UI, you will need to authorize yourself.
  - In the Swagger UI, click the "Authorize" button and then click the next "Authorize" button for the option called "oauth2 (OAuth2, authorizationCode with PKCE)"
  - This repo's docker-compose uses a built in Keycloak container for OAuth2, with a minimal default realm configuration defined at `./docker/keycloak/plerion.json`
  - This realm define two static users that you can login as; these two users are treated as separate tenants, enforced by Postgres RLS, and cannot see each others data via the API
    - Default username 1: user
    - Default password 1: password
    - Default username 2: user2
    - Default password 2: password
- You can inspect the database via Cloudbeaver by visiting http://localhost:8978
  - Admin username is found in your `.env` file
  - Default username: cbadmin (DO NOT change this to just 'admin', or Cloudbeaver will break. Any other username besides 'admin' is fine.)
  - Default password: password
- You can inspect the object store via the Minio console by visiting http://localhost:9001
  - Admin username is found in your `.env` file
  - Default username: user
  - Defualt password: password

# Development commands for the server

### Sync python packages

Ensure you have [uv](https://docs.astral.sh/uv/) installed, then run this command. Once synced, use the excellent [basedpyright](https://marketplace.visualstudio.com/items?itemName=detachhead.basedpyright) vscode extension to get static analysis in the vscode editor.

```
uv sync --all-packages
```

### (Re)generate lock files

This is a monorepo using a uv workspace, but the dockerfiles that are used to build images all rely on per-project lock files, and some dockerfiles also rely on per-dependency-group lock files (in order to separate heavy image build steps into their own layers, such as pre-caching neural network weights into the image's torch cache).

If you change any dependencies for any projects, use this command to regenerate all lock files.

```
uv run --project scripts --no_workspace generate-lock-files
```

### Migrate the database

The docker-compose comes with a database migration container that works well for the initial database migration, so if you want to migrate a database schema change and are ok with fully resetting your local deployment, you can migrate the schema by just tearing down and redeploying the docker-compose.

**_Warning: This will delete your entire server deployment, including all maps you have constructed._**

```
docker compose down -v
docker compose up -d
```

If instead you want to migrate your existing database without resetting everything, you can do so by installing [pg-schema-diff](https://github.com/stripe/pg-schema-diff) locally and running the below command. This will introspect your existing database to determine its current schema, compare that against the schema defined by SQL DDL files in the `./database` folder, generate a SQL migration, and then apply that migration.

```
uv run --project scripts --no_workspace migrate-database
```

If the generated migration has hazards, such as dropping data from the database or updating authorization, you can also pass a list of allowed hazards to the command.

**_Warning: Hazards are called hazards for a reason. Make sure you know what you're doing._**

```
uv run --project scripts --no_workspace migrate-database  --allow-hazards DELETES_DATA,AUTHZ_UPDATE
```

### (Re)generate datamodels

If you migrate the database schema using either of the above methods, use this command to regenerate python datamodels from the schema.

```
uv run --project scripts --no_workspace \
  generate-datamodels \
  --database plerion \
  --datamodels-path packages\datamodels\src\datamodels
```

### (Re)generate clients

If you change the signature any of the APIs, run this command to regenerate the typed API clients.

NOTE: This command uses [openapi-generator-cli](https://github.com/OpenAPITools/openapi-generator-cli), which requires that Java to be installed on your system and available on your PATH.

```
uv run --project scripts --no_workspace \
  generate-clients \
  --config openapi-projects.json \
  [--no-cache (optional)]
```

# Building the Android Mobile app

- Install Unity 6000.0.56f1 with Android Build Support
- Open `capture-app/android_mobile` in Unity
- Configure API url
  - Open `Assets/Scenes/Main.unity`
  - Open **App** object in scene hierarchy
  - Fill in "Plerion Base URL" in the inspector to match your public URL from earlier
  - (Optional) Tick the "Login Automatically" checkbox and fill in the Username and Passowrd (see **Verify** section above for where those credentials come from)
- Switch platorm to Android Mobile
- Build `Assets/Scenes/Main.unity`

# Building, installing, and running the Zed capture app

TODO
