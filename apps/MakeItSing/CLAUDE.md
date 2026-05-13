# apps/MakeItSing/CLAUDE.md

MakeItSing is a Unity multiplayer XR client. See `SPEC.md` for architecture, replication model, Placeframe colocalization handshake, and the rationale behind the path-as-schema replication. Read `SPEC.md` before changing anything in `Assets/App/Managers/PhotonConnectionManager.cs`, `Assets/App/Scene/`, or `Assets/App/Serialization/`.

## Compile check

Verify C# changes compile without opening the Unity GUI:

```bash
/opt/unity/$(awk '/^m_EditorVersion:/{print $2}' apps/MakeItSing/ProjectSettings/ProjectVersion.txt)/Editor/Unity \
  -batchmode -nographics -quit \
  -projectPath apps/MakeItSing \
  -logFile - 2>&1 | grep -E "error CS|Compilation"
```

`error CS####` indicates compilation failure. `dotnet build` of standalone .NET projects does not catch Unity `.asmdef` issues — use this command.

## Don't "fix" these

The following look like bugs but are intentional, load-bearing absences, or blocked on coordination with the codebase author (Elliot Pjecha). See `SPEC.md` § Known gaps for full context. Do not patch without explicit instruction:

- `AppState.sceneOriginEcefPosition` and `sceneOriginEcefRotation` are never written. The pose-update half of localization (writing the VPS device→map alignment into state so `SceneOrigin.UpdateOriginPose` can run) is intentionally unimplemented pending design clarification. `roughGrainedLocation` is also never written, but the map-fetch flow does not depend on it — `LocalizationManager.cs:23-24`'s recursive subscription fires on `loggedIn` becoming true regardless.
- `Assets/App/Managers/LocalizationManager.cs:81` zeroes the ECEF position before calling Placeframe. This is load-bearing for the current single-map-at-ECEF-(0,0,0) deployment, not a debug stub; the dead lat/lon→ECEF code above line 81 is the part that would be deleted in a cleanup.
- `Main.unity` is missing an `ARSession` GameObject; ARCore never starts, AR passthrough doesn't render, and `VPS.StartLocalizing`'s camera loop gets no frames. Fix is a scene edit (add an `ARSession` to `Main.unity` or a referenced prefab), not a code change. Don't patch around this in code.
- `Assets/App/Managers/CesiumCreditSystemUI.cs` body is entirely commented out. Workaround for the cesium-unity fork swap; the type must exist to satisfy a reference.
- `AppSetup.GetPlatform` (`Assets/App/AppSetup.cs:325`) has no default return. Compiles only with `PLERION_MAGIC_LEAP` or `PLERION_ANDROID_MOBILE` defined. The missing branch documents "plain Android is not a supported target."

## Build > Configure is destructive

The editor's `Build > Configure > {MagicLeap, AndroidMobile}` menu items rewrite scripting defines, XR loader settings, render pipeline, and target architecture at the project level. Building bundles for one target leaves the editor in that target's configuration. There is no per-build-target preservation.

## AssetBundle naming

The existing checked-in bundle is named `test scene` (with a literal space). Don't propagate the pattern — new bundles should be lower-case with no whitespace. The space appears in HTTP paths and on-disk paths and is fragile.

## Tests

The only tests are `Assets/App/Serialization/Editor/Tests/PhotonSerializationTests.cs` (binary serializer round-trip). There is no integration test coverage — don't assume the test suite catches regressions in networking, state replication, or platform handling.
