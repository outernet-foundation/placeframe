---
id: T91
title: Login support for non-authoring Outernet.Client builds (Android mobile + Magic Leap 2)
status: in-progress
depends_on: [T90]
plan: t91-plan.md
---

# T91: Login support for non-authoring Outernet.Client builds (Android mobile + Magic Leap 2)

## Goal

Make the T90 login screen work correctly when `AUTHORING_TOOLS_ENABLED` is false. This flag being false produces two fundamentally different apps: a phone-based Android mobile client and a Magic Leap 2 XR headset client. The phone case is straightforward; the headset case has major UX and input challenges.

## Context

T90 added a login screen (`LoginScreen.cs`) to Outernet.Client using code-generated uGUI components (TMP_InputField, Button, Canvas). The login flow components (SettingsManager, AuthManager, LoginScreen) are instantiated unconditionally in `AppSetup.cs` — they are NOT gated behind `#if AUTHORING_TOOLS_ENABLED`. So the code already runs in non-authoring builds, but the UI has problems:

**Android mobile build** (`OUTERNET_ANDROID_MOBILE` scripting define, ARCore loader, ARM64):
- The `LoginScreen.cs` creates a `Canvas` with `RenderMode.ScreenSpaceOverlay`, which should render correctly on a phone screen.
- `TMP_InputField` on Android should bring up the system keyboard for text input.
- This case is likely close to working — the main question is whether the current `CanvasScaler` reference resolution (1920x1080) and panel sizing (500px wide) look reasonable on phone screens. May need adjustment but is not a blocking issue.

**Magic Leap 2 build** (`MAGIC_LEAP` + `OUTERNET_MAGIC_LEAP` scripting defines, OpenXR loader, x86_64):
- `RenderMode.ScreenSpaceOverlay` does not work in XR — the canvas won't render or will render at the wrong depth. XR apps need world-space canvases positioned in 3D space relative to the headset.
- There is no system keyboard on Magic Leap 2. The `TMP_InputField` tap-to-type flow that works on phone/desktop does not exist. Magic Leap's SDK does not provide a built-in virtual keyboard for text input.
- Even if a virtual keyboard were implemented (e.g., a world-space keyboard operated by controller ray or hand tracking), typing a domain name, username, and password on a headset is an extremely poor user experience.

**Hard constraint**: The APK is a generic release artifact (distributed via GitHub). Users self-host their own backend with their own ngrok domain and credentials. Credentials cannot be baked at build time — they must be provided at runtime on the device.

**The core design question is how Magic Leap 2 users provide their credentials (domain, username, password).** Several approaches were considered:

**Rejected approaches:**
- **Build-time baked credentials**: Ruled out by the self-hosted constraint above. The APK must work against any backend.
- **World-space virtual keyboard**: Terrible UX for typing URLs and passwords in XR. Significant implementation effort for a bad experience.
- **Network discovery / mDNS**: Requires same-network assumption, has security implications (broadcasting credentials).
- **WebSocket pairing**: Requires backend changes, violates the "no cloud component" principle.
- **Standalone HTML configuration tool**: A static HTML file that generates QR codes from user-entered credentials. Works but introduces a separate artifact to distribute and explain. Less clean than keeping everything in the APK.

**Likely best approach — QR code pairing via phone app:**

The Android mobile version of the same APK already has a working login screen with keyboard input. After the user logs in on their phone, the phone app can display a QR code encoding the current credentials (domain, username, password). The ML2 user scans this QR code, and the headset app receives the credentials and logs in.

This approach is attractive because:
- Fully self-contained — the APK is the only artifact, used on both phone and headset
- No cloud/hosting component
- The phone has already validated the credentials work
- One-time setup — `SettingsManager` persists to `settings.json`, subsequent launches auto-fill
- Natural workflow — user sets up their phone first, then pairs their headset

**What building this involves:**

*Phone side (QR generation):*
- A C# QR code generation library (e.g. ZXing.Net, MIT licensed, pure C#, no native deps). Need to verify FOSS governance/independence per project principles.
- A "Pair Headset" button somewhere in the phone app UI (post-login)
- Encode credentials as a URI or JSON string, render QR code to a `RawImage` texture
- Relatively straightforward — maybe 50-100 lines of new code plus the library

*ML2 side (QR scanning):*
- This is the harder part. The ML2 needs to detect and decode QR codes using its cameras.
- `MagicLeapMarkerUnderstandingFeature` is already enabled in `BuildScript.cs:76`. This is the ML2 OpenXR extension for marker detection (QR codes, ArUco, April tags). However:
  - Unknown how reliable it is for QR code detection in practice (detection distance, lighting sensitivity, how detailed/small the QR can be)
  - Unknown how much boilerplate is needed to initialize the subsystem, configure it for QR mode, and extract decoded data
  - Hard to test without actual ML2 hardware
- Alternative: Android's built-in camera/QR scanner. ML2 runs Android — the system camera app or Google Lens can scan QR codes. If the QR encodes a deep link URI (`placeframe://login?domain=X&user=Y&pass=Z`), the ML2 could handle it via Android intent filter in `AndroidManifest.xml` without building a custom scanner. This avoids the `MagicLeapMarkerUnderstandingFeature` uncertainty entirely. Requires:
  - Intent filter in AndroidManifest.xml (~5 lines)
  - `DeepLinkHandler.cs` that reads `Application.absoluteURL` on launch and `Application.deepLinkActivated` at runtime (~30 lines)
  - But: unclear whether ML2 has a system QR scanner app, or whether the user would need to install one

*ML2 login screen:*
- Regardless of QR approach, the ML2 needs a login screen variant. `RenderMode.ScreenSpaceOverlay` doesn't work in XR — needs a world-space canvas. The screen should show a "Scan QR code from your phone to configure" message (not text input fields). If credentials are already saved from a previous session, skip this screen and auto-login.

The `SettingsManager` already persists credentials to `{Application.persistentDataPath}/settings.json`, so any approach that gets credentials into that file once means subsequent launches auto-fill (same as the authoring tools version).

## Key files

**Current login implementation (from T90):**
- `legacy/Outernet.Client/Assets/OuternetClient/LoginScreen.cs` — code-generated uGUI login form, uses `ScreenSpaceOverlay` canvas
- `legacy/Outernet.Client/Assets/OuternetClient/AuthManager.cs` — observes `loginRequested`, calls `VisualPositioningSystem.Login()`
- `legacy/Outernet.Client/Assets/OuternetClient/SettingsManager.cs` — JSON persistence of domain/username/password
- `legacy/Outernet.Client/Assets/OuternetClient/ClientState.cs` — `SettingsState` with domain/username/password observables
- `legacy/Outernet.Client/Assets/OuternetClient/AppSetup.cs` — instantiates login components unconditionally, splits pre/post-login setup

**Build configuration:**
- `legacy/Outernet.Client/Assets/OuternetClient/Editor/BuildScript.cs` — defines scripting symbols for Magic Leap vs Android Mobile, enables OpenXR features including `MagicLeapMarkerUnderstandingFeature`

**Platform-specific code:**
- `legacy/Outernet.Client/Assets/OuternetClient/Platform/MagicLeapPlatform.cs` — ML2-specific Platform MonoBehaviour (foveated rendering, focus distance)
- `legacy/Outernet.Client/Assets/OuternetClient/AppSetup.cs:222-232` — `GetProvider()` returns different `ICameraProvider` per platform (`MAGIC_LEAP`, `UNITY_ANDROID`, `UNITY_EDITOR`)

**Reference implementation:**
- `apps/AndroidMobile/Assets/Scripts/Capture/LoginUI.cs` — Nessle-based login UI (not available in Outernet.Client, but shows the field layout pattern)

## Approach

Existing login components (`SettingsManager`, `AuthManager`) are platform-agnostic — no changes needed. Only the login screen gets platform-specific variants. `AppSetup.cs` conditionally creates `MagicLeapLoginScreen` (ML2) or `LoginScreen` (phone/desktop) via `#if` guards. A post-login `QRPairingOverlay` on the phone generates QR codes for headset pairing using ZXing.Net (Apache 2.0, via NuGetForUnity).

ML2 login screen uses a world-space canvas with QR scan instructions. `QRCredentialScanner` uses the `MagicLeapMarkerUnderstandingFeature` OpenXR API (already enabled in `BuildScript.cs`) to detect QR codes, with 3-read debouncing for reliability. Credentials encoded as JSON (`{"domain":"...","username":"...","password":"..."}`), parsed with SimpleJSON. Auto-login on subsequent launches when persisted credentials exist.

## Done when

**Android mobile (`AUTHORING_TOOLS_ENABLED=false`, `OUTERNET_ANDROID_MOBILE`):**
- Login screen renders correctly on phone screen
- System keyboard appears for text input
- Credentials persist and pre-fill on subsequent launches

**Magic Leap 2 (`AUTHORING_TOOLS_ENABLED=false`, `MAGIC_LEAP`):**
- User can provide domain, username, and password by scanning a QR code displayed on the phone app
- ML2 app uses `MagicLeapMarkerUnderstandingFeature` to scan QR codes in-app (no external app needed)
- ML2 login screen is a world-space canvas with "scan QR code" instructions (not text input fields)
- Credentials persist and pre-fill on subsequent launches
- Login completes and app proceeds to normal XR flow

## Design decisions

- **ML2 QR scanning: in-app SDK, not deep link.** The deep link approach (system QR Reader → Android intent → custom URI scheme) relies on undocumented behavior — whether the ML2 system QR Reader dispatches intents for custom URI schemes has no official documentation, only one anecdotal forum report. The in-app `MagicLeapMarkerUnderstandingFeature` approach uses a documented first-party API, avoids context-switching between apps, and is ~40 lines of C#. Research: `.pulsar/research/ml2-qr-code-scanning.md`.
- **QR library: ZXing.Net via NuGetForUnity.** Apache 2.0, community-maintained (micjahn/ZXing.Net), pure C#. Added via `packages.config` using the same mechanism as existing NuGet dependencies (Newtonsoft.Json, MessagePack, etc.).
- **QR data format: JSON, not URI.** Simple `{"domain":"...","username":"...","password":"..."}` — parsed with SimpleJSON (already in project). Avoids URL encoding complexity for special characters in passwords.

## Next step

Check CI compilation result on `feature/pulsar` (Unity workflow run 22828898703). If green, manual verification on device: test Android mobile login, test ML2 QR pairing flow, confirm NuGetForUnity restores ZXing.Net correctly.
