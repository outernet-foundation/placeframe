# T91 Implementation Plan: Login Support for Non-Authoring Builds

## Context

T90 added a login screen to Outernet.Client that works for desktop/authoring builds. The same components (`SettingsManager`, `AuthManager`, `LoginScreen`) are instantiated unconditionally, but the `ScreenSpaceOverlay` canvas and `TMP_InputField`-based UI don't work on Magic Leap 2 (no XR canvas rendering, no keyboard). This ticket makes login work on two non-authoring platforms: Android mobile (mostly works already) and ML2 (needs QR-based credential pairing).

## Approach

### Architecture

The existing login components (`SettingsManager`, `AuthManager`) are platform-agnostic and need no changes. Only the **login screen** needs platform-specific variants. `AppSetup.cs` conditionally creates either `LoginScreen` (phone/desktop) or `MagicLeapLoginScreen` (ML2) using `#if` guards. A post-login `QRPairingOverlay` on the phone generates a QR code for headset pairing.

### Step 1: Add MARKER_TRACKING permission to AndroidManifest.xml

Add `<uses-permission android:name="com.magicleap.permission.MARKER_TRACKING" />` alongside existing ML2 permissions. This is ML2-specific and has no effect on Android mobile builds.

### Step 2: Add ZXing.Net dependency

Add `<package id="ZXing.Net" version="0.16.9" manuallyInstalled="true" />` to `Assets/packages.config` (NuGetForUnity, same mechanism as Newtonsoft.Json, MessagePack, etc. already in the file). NuGetForUnity installs the DLL to `Assets/Packages/`. Version 0.16.9 is the last stable release of the original line, Apache 2.0 licensed, community-maintained by Michael Jahn — satisfies FOSS governance check. If `slimRestore` in NuGet.config strips the needed DLL, fall back to vendoring the .NET Standard 2.0 DLL manually.

### Step 3: Create QRCredentialScanner.cs (ML2 QR scanner)

**File:** `legacy/Outernet.Client/Assets/OuternetClient/QRCredentialScanner.cs`
**Guard:** `#if !UNITY_EDITOR && MAGIC_LEAP`

Responsibilities:
- Request `Permissions.MarkerTracking` via `Permissions.RequestPermission()` (same pattern as `DynamicFocusDistanceSystem.cs:32-36`)
- Get `MagicLeapMarkerUnderstandingFeature` from `OpenXRSettings.Instance.GetFeature<>()`
- Create a `MarkerDetector` configured for QR codes:
  ```csharp
  var settings = new MarkerDetectorSettings();
  settings.MarkerDetectorProfile = MarkerDetectorProfile.Default;
  settings.MarkerType = MarkerType.QR;
  settings.QRSettings.EstimateQRLength = true;
  markerFeature.CreateMarkerDetector(settings);
  ```
- In `Update()`: call `markerFeature.UpdateMarkerDetectors()`, iterate `detector.Data`, read `MarkerString`
- **Debounce:** Ring buffer of last 3 decoded strings. Accept only when all 3 are identical and non-empty
- Parse JSON payload: `{"domain":"...","username":"...","password":"..."}`  using SimpleJSON (`JSONNode.Parse()`)
- Write values to `App.state.settings.domain/username/password` via `ExecuteSetOrDelay()`
- Set `App.state.loginRequested.ExecuteSetOrDelay(true)`
- Expose an `Action<string>` callback for status updates ("Scanning...", "QR detected, verifying...")
- Cleanup: `markerFeature.DestroyMarkerDetector(detector)` in `OnDestroy()`

**SDK API reference** (verified from source):
- `MagicLeapMarkerUnderstandingFeature.CreateMarkerDetector(settings)` → returns `MarkerDetector`
- `MagicLeapMarkerUnderstandingFeature.UpdateMarkerDetectors()` → updates all detectors
- `MarkerDetector.Status` → `MarkerDetectorStatus.Ready` when data is available
- `MarkerDetector.Data` → `IReadOnlyList<MarkerData>`, each has `.MarkerString`
- `MagicLeapMarkerUnderstandingFeature.DestroyMarkerDetector(detector)` → cleanup

### Step 4: Create MagicLeapLoginScreen.cs (ML2 world-space login screen)

**File:** `legacy/Outernet.Client/Assets/OuternetClient/MagicLeapLoginScreen.cs`
**Guard:** `#if !UNITY_EDITOR && MAGIC_LEAP`

Responsibilities:
- Create a **world-space Canvas** (`RenderMode.WorldSpace`) — `ScreenSpaceOverlay` does not render in XR
- Position 1.5m in front of `Camera.main` at camera height, facing toward camera
- Canvas pixel size 400x300, `localScale = Vector3.one * 0.001f` (≈0.4m x 0.3m in world space)
- **Auto-login check** in `Start()`: if all three credential fields (`domain`, `username`, `password`) are non-empty, immediately set `loginRequested = true` (skip QR screen, use persisted credentials)
- If credentials empty: show "Point your headset at the QR code on your phone" instruction text
- Create `QRCredentialScanner` as a sibling component, subscribe to its status callback to show scan feedback
- Observe `App.state.authStatus` + `App.state.authError` (same pattern as `LoginScreen.cs:38`)
- On `AuthStatus.LoggedIn`: deregister observer, destroy scanner, destroy self (`Destroy(gameObject)`)
- On `AuthStatus.Error`: show error text, allow re-scanning
- On `AuthStatus.LoggingIn`: show "Logging in..." status

UI elements (code-generated, following `LoginScreen.cs` pattern):
- Title text: "Placeframe"
- Instruction text: "Scan QR code from your phone to connect"
- Status text: scan progress / "Logging in..." / error messages

### Step 5: Create QRPairingOverlay.cs (phone-side QR display)

**File:** `legacy/Outernet.Client/Assets/OuternetClient/QRPairingOverlay.cs`
**Guard:** `#if !UNITY_EDITOR && OUTERNET_ANDROID_MOBILE`

Responsibilities:
- Post-login component (created in `AppSetup.PostLoginSetup()`)
- Creates a `ScreenSpaceOverlay` canvas with a small "Pair Headset" button (top-right corner)
- When tapped: generate QR code from current credentials using ZXing.Net `BarcodeWriterPixelData`
  ```csharp
  var writer = new BarcodeWriterPixelData {
      Format = BarcodeFormat.QR_CODE,
      Options = new QrCodeEncodingOptions { Width = 512, Height = 512, Margin = 2 }
  };
  var payload = new JSONObject();
  payload["domain"] = App.state.settings.domain.value;
  payload["username"] = App.state.settings.username.value;
  payload["password"] = App.state.settings.password.value;
  var pixelData = writer.Write(payload.ToString());
  ```
- Convert pixel data to `Texture2D`, display on a full-screen `RawImage` overlay with dark background
- "Done" button to dismiss QR overlay (destroys overlay, button remains for re-use)

### Step 6: Modify AppSetup.cs (conditional wiring)

**File:** `legacy/Outernet.Client/Assets/OuternetClient/AppSetup.cs`

**In `Awake()` at line 107** — replace:
```csharp
var loginScreen = new GameObject("LoginScreen", typeof(LoginScreen));
```
with:
```csharp
#if !UNITY_EDITOR && MAGIC_LEAP
    var loginScreen = new GameObject("LoginScreen", typeof(MagicLeapLoginScreen));
#else
    var loginScreen = new GameObject("LoginScreen", typeof(LoginScreen));
#endif
```

**In `PostLoginSetup()` after line 136** — add:
```csharp
#if !UNITY_EDITOR && OUTERNET_ANDROID_MOBILE
    new GameObject("QRPairingOverlay", typeof(QRPairingOverlay));
#endif
```

This follows existing conditional patterns in `AppSetup.cs` (`#if AUTHORING_TOOLS_ENABLED` blocks, `GetProvider()` with `#if MAGIC_LEAP`).

## QR data format

Simple JSON: `{"domain":"example.ngrok.app","username":"user","password":"pass"}`
- Parsed with SimpleJSON (already in the project, used by `SettingsManager`)
- No URL encoding complexity for special characters in passwords

## Key files

| File | Action | Notes |
|------|--------|-------|
| `legacy/Outernet.Client/Assets/OuternetClient/QRCredentialScanner.cs` | Create | ML2 marker detection + debouncing |
| `legacy/Outernet.Client/Assets/OuternetClient/MagicLeapLoginScreen.cs` | Create | World-space canvas + auto-login logic |
| `legacy/Outernet.Client/Assets/OuternetClient/QRPairingOverlay.cs` | Create | Phone QR generation + display |
| `legacy/Outernet.Client/Assets/OuternetClient/AppSetup.cs` | Modify | Conditional login screen creation (line 107), post-login QR overlay (after line 136) |
| `legacy/Outernet.Client/Assets/Plugins/Android/AndroidManifest.xml` | Modify | Add MARKER_TRACKING permission |
| `legacy/Outernet.Client/Assets/packages.config` | Modify | Add ZXing.Net 0.16.9 |

**Files NOT changed:**
- `LoginScreen.cs` — existing ScreenSpaceOverlay + CanvasScaler works on Android phones
- `AuthManager.cs` — platform-agnostic, observes `loginRequested` generically
- `SettingsManager.cs` — platform-agnostic, persists/loads credentials for all platforms
- `ClientState.cs` — no new state needed
- `BuildScript.cs` — `MagicLeapMarkerUnderstandingFeature` already enabled at line 75

**Reference files to follow patterns from:**
- `LoginScreen.cs` — observer registration, self-destruct on login, code-generated UI
- `DynamicFocusDistanceSystem.cs:32-36` — ML2 permission request pattern
- `MarkerUnderstandingSample.cs` (SDK sample) — marker detector creation and polling
- `MagicLeapMarkerUnderstandingFeature.cs` / `MagicLeapMarkerUnderstandingData.cs` — API types

## Verification

- Unity batchmode compilation check — build with each platform's scripting defines to verify `#if` guards
- Code review against SDK sample patterns for marker detection
- Pattern consistency: `App.RegisterObserver()`/`DeregisterObserver()`, `ExecuteSetOrDelay()`, `Permissions.RequestPermission()` with three callbacks
- No runtime testing possible without ML2/Android hardware — structure code to be linear and simple
