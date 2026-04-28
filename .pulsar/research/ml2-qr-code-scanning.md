# Magic Leap 2 QR Code Scanning: Deep Link vs. In-App SDK

Research conducted 2026-03-08. Context: T91 needs a way for ML2 users to receive credentials from a phone app via QR code.

## The question

What are the two viable paths for getting QR code data into a Unity app on Magic Leap 2, and how practical is each?

- **Path 1 — Deep link**: User scans a QR code with the ML2's system QR Reader app, which dispatches a `placeframe://` deep link to our Unity app via Android intent.
- **Path 2 — In-app scanning**: Our Unity app uses `MagicLeapMarkerUnderstandingFeature` (OpenXR marker detection) to scan QR codes directly through the headset cameras.

Constraints: Unity project, ML2 hardware, officially supported paths only, FOSS dependencies.

## Path 1: Deep Link (External Scanner)

### ML2 system QR Reader

ML OS 1.2.0+ ships a **QR Reader** system app, accessible from the app launcher or via a shortcut in the built-in browser. It shows a camera viewfinder and highlights detected QR codes in yellow.

### Custom URI scheme support — undocumented

The QR Reader is documented as opening URLs in the browser. Whether it dispatches Android intents for **custom URI schemes** (e.g. `placeframe://pair?...`) is **not officially documented**. One developer on the Magic Leap forum reported it worked as of LuminOS 1.3, but this is a single anecdotal report with no official backing.

ML2 runs AOSP Android 10 with **no Google Play Services**. This means Android App Links (verified-domain deep linking) do not work. Only basic `android.intent.action.VIEW` intent-filter matching is available. The ML2 team confirmed this explicitly on the forum.

### Implementation effort

~10 lines of C# + an AndroidManifest intent filter:

```xml
<intent-filter>
  <action android:name="android.intent.action.VIEW" />
  <category android:name="android.intent.category.DEFAULT" />
  <category android:name="android.intent.category.BROWSABLE" />
  <data android:scheme="placeframe" android:host="pair" />
</intent-filter>
```

```csharp
Application.deepLinkActivated += url => { /* parse credentials from url */ };
if (!string.IsNullOrEmpty(Application.absoluteURL))
    OnDeepLinkActivated(Application.absoluteURL);
```

### UX concerns

- At least **two context switches**: launcher → QR Reader → app launch/resume. Clunky on a head-mounted display.
- ML2 has no app store. Apps are sideloaded via Magic Leap Hub, ADB, or MDM. The QR Reader is pre-installed.
- ML2 does not support true multitasking — one immersive app at a time, with the launcher as the switching mechanism.

### Risk assessment

The fundamental risk is **relying on undocumented behavior**. If the system QR Reader only passes URLs to the browser (ignoring custom schemes), this path is dead. There is no fallback without asking users to install a third-party QR scanner (no app store — they'd have to sideload one).

## Path 2: MagicLeapMarkerUnderstandingFeature (In-App Scanning)

### What it provides

The ML2 OpenXR SDK includes `MagicLeapMarkerUnderstandingFeature` for detecting markers (QR, ArUco, AprilTag, barcodes) using the headset's cameras. For each detected marker it provides:

- **`MarkerData.MarkerString`** — the decoded string content of the QR code
- **`MarkerData.MarkerPose`** — 6DOF position + rotation in world space
- **`MarkerData.MarkerLength`** — estimated physical size in meters

We only need the string content for credential pairing.

### Implementation effort

~40 lines for a minimal QR string reader:

```csharp
// Start: get feature, create detector
var feature = OpenXRSettings.Instance.GetFeature<MagicLeapMarkerUnderstandingFeature>();
var settings = new MarkerDetectorSettings { MarkerType = MarkerType.QR };
settings.QRSettings.EstimateQRLength = true;
feature.CreateMarkerDetector(settings);

// Update (polling model, not event-driven):
feature.UpdateMarkerDetectors();
foreach (var detector in feature.MarkerDetectors)
    if (detector.Status == MarkerDetectorStatus.Ready)
        foreach (var data in detector.Data)
            ProcessQRContent(data.MarkerString);

// Destroy: feature.DestroyAllMarkerDetectors();
```

Project settings required: enable `MARKER_TRACKING` permission, enable "Magic Leap 2 Marker Understanding" OpenXR feature (already enabled in `BuildScript.cs`).

### Known limitations

| Factor | Detail |
|---|---|
| **Detection distance** | Recommended 30-90cm. ~10cm QR code detectable up to ~2.5m. |
| **Initial lag** | 1-2 second spike when creating the detector (blocks main thread). |
| **Occasional misreads** | Gibberish text returned — need debouncing (compare consecutive reads). |
| **Duplicate atoms** | Same physical QR sometimes detected with different identifiers. |
| **Lighting** | Needs more ambient light than HoloLens 2. |
| **Motion blur** | Small QR codes sensitive to motion blur — user may need to hold still. |
| **Camera conflict** | Cannot record video while tracking markers. |
| **Inverted QR** | White-on-black QR codes not supported. |
| **String length** | Fixed in SDK 2.2.0 — earlier versions truncated at 100 chars. |

### Required SDK versions

| Component | Minimum |
|---|---|
| Magic Leap Unity SDK (`com.magicleap.unitysdk`) | >= 2.2.0 (fixes string truncation bug) |
| Unity Editor | >= 2022.3 LTS |
| OpenXR Plugin (`com.unity.xr.openxr`) | >= 1.10.0 |
| Magic Leap OS | >= 1.2.0 |

### Reliability mitigations

For credential pairing (scan once, persist forever), the reliability issues are manageable:
- **Debounce**: require 2-3 consecutive identical reads before accepting
- **UI feedback**: show detected string to user, let them confirm before applying
- The QR code will be displayed on a phone screen at close range — optimal conditions for the detector

## Comparison

| Factor | Deep Link | In-App SDK |
|---|---|---|
| **Implementation effort** | ~10 lines + manifest | ~40-80 lines + 2 project settings |
| **UX** | 2+ context switches (launcher → QR Reader → app) | Zero context switches — scan from within the app |
| **Custom scheme support** | Undocumented, single anecdotal report | Documented first-party API |
| **Decoded string** | Yes (via URL) | Yes (`MarkerString`) |
| **Works if app not running** | Yes (intent launches app) | No (app must be running) |
| **Camera conflict** | None (system app owns camera) | Cannot record video while tracking |
| **Dependency risk** | High — undocumented behavior | Low — documented SDK API with known bugs |
| **First boot experience** | Scan QR → app auto-launches with credentials | Open app → see "scan QR" screen → scan |

## Recommendation

**Path 2 (in-app SDK scanning) is the stronger choice.** Reasons:

1. **Documented API vs. undocumented behavior.** The deep link path's viability hinges on whether the system QR Reader dispatches custom URI schemes — a behavior with no official documentation and only one anecdotal forum report. Building on this is fragile.

2. **Better UX.** The in-app approach keeps the user in a single app. The ML2 login screen shows "Point your headset at the QR code on your phone" — one action, no app switching. The deep link approach requires navigating to the QR Reader, scanning, then context-switching back.

3. **Manageable implementation cost.** ~40 lines of C# for the scanner, plus debouncing logic. The `MagicLeapMarkerUnderstandingFeature` is already enabled in `BuildScript.cs`. The known reliability issues (occasional misreads) are solved by requiring consecutive identical reads — acceptable for a one-time credential pairing.

4. **No external dependencies.** The scanning uses the ML2 SDK that's already in the project. No additional libraries needed on the ML2 side.

The deep link approach could serve as a **fallback** if in-app scanning proves unreliable in practice, but should not be the primary path given the undocumented custom scheme behavior.

## Sources

- [QR Reader — Care | Magic Leap](https://www.magicleap.care/hc/en-us/articles/15515327797005-QR-Reader)
- [Marker Understanding API Overview | MagicLeap Developer Documentation](https://developer-docs.magicleap.cloud/docs/guides/unity-openxr/marker-understanding/unity-marker-understanding-api/)
- [Marker Understanding Example | MagicLeap Developer Documentation](https://developer-docs.magicleap.cloud/docs/guides/unity-openxr/marker-understanding/unity-marker-understanding-example/)
- [Marker Tracking | MagicLeap Developer Documentation](https://developer-docs.magicleap.cloud/docs/guides/features/marker-tracking/)
- [Marker Understanding Overview | MagicLeap Developer Documentation](https://developer-docs.magicleap.cloud/docs/guides/unity-openxr/marker-understanding/marker-understanding-overview/)
- [Forum: Opening app using an URL scheme with deep link](https://forum.magicleap.cloud/t/opening-app-using-an-url-scheme-with-deep-link/1652)
- [Forum: Marker tracking QR codes errors](https://forum.magicleap.cloud/t/marker-tracking-qr-codes-errors/1238)
- [Forum: QR code contents occasionally read incorrectly](https://forum.magicleap.cloud/t/using-openxr-api-the-qr-code-contents-occasionally-are-being-read-incorrectly-and-distinct-atoms-are-returned-for-the-same-qr-code/2977)
- [Unity Manual: Deep linking on Android](https://docs.unity3d.com/Manual/deep-linking-android.html)
- [Intents | MagicLeap Developer Documentation](https://developer-docs.magicleap.cloud/docs/guides/features/android-intents/android-intents-overview/)
- [Installing and Uninstalling Apps — Care | Magic Leap](https://www.magicleap.care/hc/en-us/articles/5951496255885-Installing-and-Uninstalling-Apps)
- [GitHub: MagicLeapUnitySDK Releases](https://github.com/magicleap/MagicLeapUnitySDK/releases)
- [Cross-platform QR tracking blog](https://localjoost.github.io/Cross-platform-spatial-QR-code-tracking-for-HoloLens-2-and-Magic-Leap-2-with-a-ServiceFramework-Service,-part-1/)
- [2.2.0 Unity SDK Release Notes](https://developer-docs.magicleap.cloud/docs/releases/release-2024-may/unity-sdk-release-notes/)
