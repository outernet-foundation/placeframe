# apps/MakeItSing/SPEC.md

## What this is

MakeItSing is a state-driven multiplayer XR client that loads demo scenes as Unity AssetBundles from Supabase and replicates a custom scene-graph over Photon Realtime. It targets Magic Leap 2 and Android Mobile. The app is Placeframe's demo harness — its purpose is to put two colocalized users in a shared virtual scene anchored to a real physical place via Placeframe's relocalization service. Authored by Elliot Pjecha; the application code lives under `Assets/App/`.

## Shape

### Boot

A single startup scene, `Assets/App/Scenes/Main.unity`, contains a GameObject named `App` with an `AppSetup` component. `AppSetup` is one-shot scaffolding that wires the rest of the app and then destroys itself:

    [RuntimeInit] AppSetup.Initialize     -- Logger + UnityEnv + exception handler
            |
            v
    AppSetup.Awake                         -- Sets SupabaseAPI keys; inits SceneReferences,
            |                                 Prefabs, VisualPositioningSystem; spawns App;
            |                                 conditionally adds Photon/Localization managers;
            v                                 fetches remote Supabase config; self-destructs.
    App.Awake                              -- Cross-cutting state subscriptions
            |
            v
    [user login]                           -- Tasks.Login -> VisualPositioningSystem.Login
            |
            v
    [room select]                          -- SupabaseContentHelper polls /rest/v1/rooms every 10s
            |
            v
    [join room]                            -- Photon ConnectionManager.ConnectToRoomAsync
            |
            v
    InRoomManager loads demo scene         -- One of: EMBEDDED://, EDITOR://, FILE://, Supabase
            |
            v
    Master client seeds scene state        -- Walks DemoSceneSetup.SceneViews, writes initial state
            |
            v
    inRoomAndSynchronized = true           -- Local player avatar added to replicated scene

Login POSTs to `https://{domain}/auth/realms/placeframe-dev/protocol/openid-connect/token` via Placeframe's `Auth.Login`. Supabase is a separate, anon-keyed REST surface used for app config and AssetBundle hosting — there is no per-user Supabase auth.

### Replicated scene-graph

The state-of-the-world per master client lives in `AppState.scene` (a `SceneState`), built from `FofX.Stateful` primitives — an observable tree where every mutation goes through `App.ExecuteTransaction(...)`. The networking layer is diff propagation:

- `PhotonConnectionManager.HandleSceneChanged` (`Assets/App/Managers/PhotonConnectionManager.cs:370`) watches every mutation, writes `(path, opType, payload)` triples into `_incrementalSyncStream`, and broadcasts them next `LateUpdate` as Photon raw event 2.
- Remote clients run `ApplyIncrementalSyncAction` (`Assets/App/AppActions.cs:80`), which uses the path string to locate the same node and apply the op. **Paths are the schema** — there is no field-level codec.
- Initial sync: when a new client joins, master sends event code 1 carrying the entire `App.state.scene` serialized via `ToJSON(x => !x.derived)`. Decoded on the joiner via `JSONNode.Parse`. Initial sync is JSON; incremental sync is the project's custom binary format (`Assets/App/Serialization/PhotonSerialization.cs`).
- High-frequency channel: registered `IStateValue`s (today: avatar `localPosition`, `localRotation` at 16Hz) bypass the reliable diff stream — owners write `(id, value)` pairs into `_highFrequencySyncStream` and broadcast unreliably as event code 3.

Views are `ISceneObjectViewComponent` MonoBehaviours placed in a scene by an author (`Assets/App/Scene/ISceneObjectViewComponent.cs`). The contract has three methods: `WriteInitialState` (master only, seeds state at room-join time), `Setup` (all clients, binds the component to its state-tree entry), `Teardown`. Existing implementations: `TransformViewComponent`, `AvatarViewComponent`, `XRGrabbableViewComponent`.

`DemoSceneSetup` is a per-loaded-scene singleton (`Assets/App/Scene/DemoSceneSetup.cs`); its `_sceneViews` list is auto-populated by `Assets/App/Editor/SceneObjectViewManifestHelper.cs:29` at save and play-mode transitions. At room-join time the master walks this list in deterministic order, assigns each entry a negative `SceneObjectId` (`-1, -2, ...`), and calls `WriteInitialState`. Joiners re-walk the same list and bind. Dynamic spawn is a separate path: positive-id objects with non-null `viewPrefab` are instantiated from `Resources` (`Assets/App/Managers/SceneViewManager.cs:53`). Today the only thing that spawns dynamically is the player avatar.

ID space is sliced: each player owns ids `playerId*10000 .. (playerId+1)*10000-1` for newly-allocated `SceneObjectId`s and `HighFrequencyPrimitiveId`s (`Assets/App/Scene/PlayerIdHelper.cs`). Scene-baked objects use negative ids, so collisions are impossible.

`PhotonConnectionManager` is ~530 lines and is the entire networking layer.

### Supabase and AssetBundle pipeline

Supabase project (`UnityEnv.supabaseProjectId`) hosts:

- `/rest/v1/rooms` — `{id, name, version, demo_scene}` rows. `demo_scene` is just the AssetBundle filename. `SupabaseContentHelper.PollContent` (`Assets/App/Managers/SupabaseContentHelper.cs:25`) refreshes `App.state.rooms` every 10s.
- `/rest/v1/config` — rows of `GetConfigResponse` with optional `device_id`, `app_version`, `device_type` keys and override fields (log levels, `photon_project_id`, `domain`, `username`, `password`, `room`). `SupabaseAPI.GetPrioritizedConfig` merges matching rows in priority order. This is how the Photon AppId reaches the client in production.
- `/storage/v1/object/demoScenes/{version}/{platform}/{name}` — bucket for the AssetBundles, one sub-folder per `Application.version`, then one per `PlatformConfig.supabaseBucket`.

A "demo scene" is one Unity AssetBundle. `InRoomManager.LoadScene` (`Assets/App/Managers/InRoomManager.cs:123`) dispatches on the room's `demo_scene` field by prefix: `EDITOR://`, `EMBEDDED://N`, `FILE://`, or a name that falls through to `SupabaseAPI.GetDemoSceneAssetBundle`. The bundle is loaded additively; the first scene inside it is unioned with `Main.unity`.

The editor-side publishing tool is `Window > Asset Bundle Manager` (`Assets/App/Editor/AssetBundleManagerWindow.cs`). It builds bundles for selected platforms via `BuildPipeline.BuildAssetBundles`, then `POST`s them to the Supabase storage path with the anon API key.

`AppSetup.cs` gates Supabase calls on `SupabaseAPI.IsConfigured` — if the gitignored `UnityEnv.asset` is missing, Supabase calls log a warning and skip rather than failing. Photon and the localization stack are unaffected.

### Placeframe integration

`packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` (VPS) is the integration surface. The current wiring:

- `VPS.Initialize` (`AppSetup.cs:81`): platform-selected `ICameraProvider` — `MagicLeapCameraProvider` on ML2, ARFoundation's `CameraProvider` on Android Mobile, `NoOpCameraProvider` in the editor. Hardcoded audience `placeframe-api` and Keycloak realm `placeframe-dev`.
- `VPS.Login` (`Tasks.cs:16`): OAuth2 password-grant against Placeframe's Keycloak.
- `VPS.StartLocalizing(1f)` (`LocalizationManager.cs:32`): runs the camera-frame → localizer-API loop at 1 Hz once `App.state.loggedIn` flips true.
- `LocalizationMapManager` (`Assets/App/Prefabs.cs:11`, instantiated by `AppSetup.cs:92`): wires itself into VPS via `SetLocalizationMapManager`, owns per-map `LocalizationMap` GameObjects, renders reconstruction points as `ParticleSystem` particles and frame trails via `Graphics.DrawMesh` cylinders (`packages/unity/Placeframe/.../LocalizationMap.cs:131`).
- `SceneOrigin` (`Assets/App/Scene/SceneOrigin.cs`, auto-attached to the loaded demo scene's root by `InRoomManager.LoadScene:174`): reads `App.state.sceneOriginEcefPosition/Rotation`, calls `VPS.EcefToUnityWorld(...)`, lerps its transform toward the result on every alignment update.

The handshake intended for shared-scene colocalization is a hardcoded-map-ID model rather than the GPS-driven map-discovery the general Placeframe API supports. Each demo targets one known physical place and one known map; the map's local frame is the demo author's coordinate frame; two clients converge by virtue of localizing against the same map. The pieces that exist:

- `VPS.SetLocalizationMaps(Guid[])` (`VisualPositioningSystem.cs:128`) takes map IDs directly, bypassing the lat/lon → nearby-maps query.
- `LocalizationMap.cs:106` already downloads a specific map's reconstruction by ID and renders it.
- `Assets/App/Editor/ReconstructionDownloadHelperWindow.cs` (menu `Window > Reconstruction Download Helper`): editor utility that takes a reconstruction ID, fetches its points via `VPS.GetReconstructionPoints`, and writes them as a static `Mesh.asset` (`MeshTopology.Points`) into the project. Suggests an editor-time bake of point clouds into demo scenes rather than (or in addition to) live runtime visualization.

The pieces that do not exist:

- A source-of-truth for the per-demo map ID. No field on `RoomData`, `GetRoomResponse`, `UnityEnv`, `DemoSceneSetup`, or any scene script carries one. (See `## In flight`.)
- A connector that reads that map ID and calls `VPS.SetLocalizationMaps(new[] { mapId })`.
- Anchoring of the demo scene root to the map's pose in Unity world.

The existing `LocalizationManager` (`Assets/App/Managers/LocalizationManager.cs`) implements the map-fetch half of the localization flow and is wired up in practice. On `loggedIn=true` (via the recursive subscription at `LocalizationManager.cs:23` — fires on either `roughGrainedLocation` or `loggedIn` changing, but the former is never written so only `loggedIn` triggers it), it calls `VPS.SetLocalizationMaps(ecefPosition, MAP_LOAD_RADIUS=100m)` which issues `GET /localization-maps?position_x=0&position_y=0&position_z=0&radius=100` and downloads the matching map(s). The line-81 `ecefPosition = new double3(0, 0, 0)` overwrite — previously described as a debug stub — is load-bearing for the current single-map-at-ECEF-(0,0,0) deployment: the radius-100 query against the origin is the call shape that returns that map. The lat/lon → ECEF computation above line 81 (via `WGS84.CartographicToEcef` and `SceneReferences.GroundTileset.SampleHeightMostDetailed`) is dead code today; it depends on the never-written `App.state.roughGrainedLocation` and the zero-out discards its output regardless. The pose-update half — VPS writes its device→map alignment back into `App.state.sceneOriginEcefPosition` / `sceneOriginEcefRotation` so `SceneOrigin.UpdateOriginPose` can fire — is still unimplemented; both fields are declared, read by `SceneOrigin`, and never written.

The `placeframe-api` audience and `placeframe-dev` realm name are hardcoded in `VisualPositioningSystem.cs:90` and `AppSetup.cs:83`.

### Platform handling

Two production targets, both Android: Magic Leap 2 (OpenXR with ML feature set) and Android Mobile (ARFoundation/ARCore). Branch points:

- Scripting defines, set by `Assets/App/Editor/BuildScript.cs:52, 86`:
  - Magic Leap: `PLERION_MAGIC_LEAP;MAGIC_LEAP;USE_ML_OPENXR;...`
  - Android Mobile: `PLERION_ANDROID_MOBILE;...`
- Camera provider (`AppSetup.cs:342`): `#if UNITY_EDITOR` → `NoOpCameraProvider`; `MAGIC_LEAP` → `MagicLeapCameraProvider`; `UNITY_ANDROID` (default) → ARFoundation `CameraProvider`.
- UI (`Assets/App/UI/AppUI.cs`): Magic Leap gets a worldspace canvas; other platforms get screen-space. Hamburger menu is hidden on ML.
- AssetBundle binary: built per platform; published to `PlatformConfig.supabaseBucket`-named subfolders.

The editor's `Build > Configure > {MagicLeap, AndroidMobile}` menu items destructively flip project settings (scripting defines, XR loaders, render pipeline). Building bundles for one target leaves the editor in that target's configuration.

`Platform.Windows`, `Linux`, and `OSX` exist in `PlatformConfig` but no editor build action emits them.

## Rationale

The non-obvious shape of this app is the path-as-schema replication model. Several pieces fall out of that choice and are worth knowing about.

**Raw Photon Realtime over Fusion/PUN.** Fusion's tick-driven model expects a fixed-schema, generated-code wire format; it composes poorly with an arbitrary observable state tree where the wire format *is* the mutation set. Raw Realtime gives full control over the four event codes (1: initial sync, 2: incremental diff, 3: high-frequency, plus Photon presence). Tradeoff: no Photon-provided ownership/interest management — the codebase implements its own (`PlayerIdHelper`, `ownerID`, last-writer-wins).

**Custom binary serializer rather than Photon's built-in.** The state tree contains application types (`Vector3`, `Quaternion`, `BezierKnot`, the project's own `SceneObjectId`) that need stable wire encoding independent of Unity's serialization. `Assets/App/Serialization/PhotonSerialization.cs` is the only piece of the codebase with a corresponding test (`PhotonSerializationTests.cs`).

**JSON for initial sync, binary for incremental.** Initial sync runs once per join and benefits from human-debuggability over wire size. Incremental sync runs every frame; the binary format saves bandwidth at the cost of opacity.

**Master-client seeds scene state, negative IDs for scene-baked objects.** Eliminates an entire class of coordination problems: scene-baked entries get `-1, -2, -3, ...` in the order `DemoSceneSetup.SceneViews` produces them, which is deterministic across clients because the manifest is itself replicated content. Positive IDs are sliced (`playerId * 10000`) so no two players ever allocate the same id without consensus.

**One `Main.unity`, additive demo scenes.** Keeps `AppSetup`'s managers persistent across content swaps and lets a single editor play-action work with any scene the artist has open (via `DemoSceneSetup.InitializeApp` and the `EDITOR://` source).

**Classic AssetBundles over Addressables.** Inferred (no in-code rationale): simpler model, no dependency-graph or remote-catalog overhead. The pipeline is one-platform-one-bucket-folder-one-file; Addressables' value-prop is amortized across many bundles, which doesn't apply at the current scale.

**Anon Supabase key with no RLS.** Inferred: zero-friction artist publishing. The cost is that the anon key is effectively read+write for any holder, and is baked into player builds. This is a known trust boundary, not an oversight.

**Hardcoded map ID per demo over GPS-driven map discovery.** The general Placeframe API supports lat/lon → nearby-maps lookup, but each MakeItSing demo targets a known physical location and a known map. Skipping the discovery step removes the GPS permission flow, the WGS84 → ECEF math, the master-broadcasts-anchor coordination between clients, and the question of what happens during the pre-localization window. The cost: the demo's spatial extent is bounded by the chosen map's coverage, and switching demo locations requires a build. Both acceptable for the demo-harness use case. The existing ECEF-driven scaffolding (`AppState.roughGrainedLocation`, `sceneOriginEcefPosition/Rotation`, the `LocalizationManager.UpdateMaps` chain) is leftover from this direction having been started before the simplification.

## Known issues

- `SupabaseAPI.cs:148` merge bug in `GetPrioritizedConfig`: `result.photon_project_id = config.photon_project_id ?? config.photon_project_id` — both sides reference `config`, breaking prioritized merge for Photon AppId. Other fields use `result.X = result.X ?? config.X`.
- `AppSetup.cs:325` (`GetPlatform`) has no default return — a build with `UNITY_ANDROID` defined but neither `PLERION_*` define won't compile. Documents "plain Android is not a supported target."
- `SupabaseAPI.cs:111` (`GetRooms`) null check on a list that's empty-not-null; URL always contains `?and=()`. Cosmetic.
- `AppActions.cs:77` cleanup of objects owned by a leaving player is unimplemented; mid-session disconnects orphan their owned objects.
- `Assets/App/Editor/AppEditor.cs:15-33` `_additionalDrawers` is dead code after the upstream API removed its argument.
- `Assets/App/Editor/AssetBundleManagerWindow.cs:26` excludes `ardebugmenu` from the bundle list; no such bundle exists in the tree.
- `Build > Asset Bundles` has no OSX action even though `PlatformConfig` lists it.
- AssetBundle filename `test scene` contains a literal space; the space propagates into HTTP paths and on-disk paths.
- `Assets/App/Managers/CesiumCreditSystemUI.cs` body is entirely commented out; the type exists only to satisfy a reference, workaround for the `org.outernet.cesium-unity` fork swap.
- `Assets/App/UnityEnv.cs:80` creates the editor-only `UnityEnv.asset` under `Assets/_LocalWorkspace/Resources/`; production builds rely on the asset being shipped or on the `SupabaseAPI.IsConfigured` gate. Production credentials path is unverified.
- Supabase anon key is baked into player builds; the storage bucket is effectively public-write to anyone with the key.
- Hardcoded realm name `placeframe-dev` in `packages/unity/Placeframe/.../VisualPositioningSystem.cs:90`; hardcoded Loki app id `placeframe-api` in `AppSetup.cs:83` and `Assets/App/Editor/ReconstructionDownloadHelperWindow.cs:52`.

## In flight

The colocalization handshake. Three small pieces, none committed:

1. **Map ID source.** No field on `RoomData`, `GetRoomResponse`, `UnityEnv`, `DemoSceneSetup`, or any scene script carries a map ID today. Reasonable hosts: a new `MonoBehaviour` on the demo scene root carrying `Guid mapId` (bundled with the demo); a `localization_map_id` field on Supabase `rooms` rows (per-room override); or a global on `UnityEnv.asset` (one map for all demos in a build).
2. **Connector.** On `loggedIn=true`, read (1) and call `VPS.SetLocalizationMaps(new[] { mapId })`. Replaces the `LocalizationManager.UpdateMaps` chain that currently keys off the never-written `App.state.roughGrainedLocation` and zeroes the ECEF result before calling VPS.
3. **Scene-root anchoring.** Either write the map's ECEF pose (fetched via `VPS.GetMapData(mapId)`) into `App.state.sceneOriginEcefPosition/Rotation` so the existing `SceneOrigin` math lands at the map's Unity world position; or rewrite `SceneOrigin` to track `LocalizationMap.transform` directly and delete the ECEF-driven state values. The first approach is the smaller patch and reuses the master-replicates-to-joiners machinery for free.

## See also

- `packages/unity/Placeframe/SPEC.md` — the Placeframe Unity package, which is MakeItSing's primary integration surface (`VisualPositioningSystem`, `Auth`, `EcefToUnityWorldTransform`). Pending an audit against the new style guide.
