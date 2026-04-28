---
id: T94
title: Rename installed app display names across all Unity projects
status: ready
depends_on: []
---

# T94: Rename installed app display names across all Unity projects

## Goal

Update the user-visible installed app names (and related identifiers) to reflect current project naming. No folder renames or project restructuring — only PlayerSettings fields and build script references.

## Context

The apps currently have legacy names from earlier project iterations. "Ogment" is an obsolete company/project name. "Android Data Recorder" and "Outernet NYC" are not descriptive of what the apps do now. The Outernet.Client project produces different apps depending on the `AUTHORING_TOOLS_ENABLED` scripting define, so its display name should vary per build.

## Key files

- `apps/AndroidMobile/ProjectSettings/ProjectSettings.asset:16` — `productName: Android Data Recorder` → `PlaceframeScanner`
- `apps/MapRegistrationTool/ProjectSettings/ProjectSettings.asset:16` — `productName: Map Registration Tool` → `PlaceframeRegistrationTool`
- `legacy/Outernet.Client/ProjectSettings/ProjectSettings.asset:16` — `productName: Outernet Authoring Tools (Beta)` (default, used by authoring builds)
- `legacy/Outernet.Client/Assets/Settings/Build Profiles/Android Mobile.asset:38` — `productName: Outernet Authoring Tools (Beta)`
- `legacy/Outernet.Client/Assets/Settings/Build Profiles/Magic Leap.asset:38` — `productName: Outernet NYC`
- `legacy/Outernet.Client/Assets/OuternetClient/Editor/BuildScript.cs:153` — APK output filename `OgmentUnity.apk`
- `legacy/Outernet.Client/ProjectSettings/ProjectSettings.asset:15` — `companyName: Ogment`
- `legacy/Outernet.Client/ProjectSettings/ProjectSettings.asset:172` — `applicationIdentifier: com.Ogment.OuternetNYC.Beta`
- `legacy/Outernet.Client/Assets/Settings/Build Profiles/Android Mobile.asset:191` — `applicationIdentifier: com.Ogment.OuternetNYC.Beta`
- `legacy/Outernet.Client/Assets/Settings/Build Profiles/Magic Leap.asset:199` — `applicationIdentifier: com.Ogment.OuternetNYC.Beta`

## Approach

Change `productName` in PlayerSettings.asset files directly for AndroidMobile and MapRegistrationTool. For Outernet.Client, set `PlayerSettings.productName` conditionally in `BuildScript.cs` per build method — `OuternetAuthoringTool` when `AUTHORING_TOOLS_ENABLED` is true, `OuternetClient` otherwise. Update `companyName` and `applicationIdentifier` to remove "Ogment" references. Rename APK output from `OgmentUnity.apk`.

## Design decisions

- **No folder or project renames.** Only the installed app display name and related identifiers change.
- **Conditional naming for Outernet.Client via BuildScript.cs.** The build script already configures per-build settings — add `PlayerSettings.productName` assignment in each build method.

## Done when

- AndroidMobile installs as "PlaceframeScanner"
- MapRegistrationTool installs as "PlaceframeRegistrationTool"
- Outernet.Client authoring build installs as "OuternetAuthoringTool"
- Outernet.Client non-authoring builds install as "OuternetClient"
- No references to "Ogment" remain in PlayerSettings or BuildScript
