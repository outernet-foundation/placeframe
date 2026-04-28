---
id: T90
title: Add login/config screen to Outernet.Client
status: in-review
plan: t90-plan.md
depends_on: []
---

# T90: Add login/config screen to Outernet.Client

## Goal

Replace the hard-coded credentials and `.env`-only domain configuration in Outernet.Client with a runtime login screen (domain, username, password) that persists across launches — mirroring the pattern already implemented in the AndroidMobile app.

## Context

The AndroidMobile app (`apps/AndroidMobile/`) has a working login flow: on first launch it shows a login screen with domain, username, and password fields. Credentials are persisted to `{Application.persistentDataPath}/settings.json` via `SettingsManager`, so subsequent launches pre-fill the fields. The screen is shown/hidden reactively based on an observable `loggedIn` state derived from `authStatus`.

Outernet.Client (`legacy/Outernet.Client/`) currently hard-codes `"user"` / `"password"` in two places in `AppSetup.cs` (lines 58-62 for `Auth.Login` and lines 115-119 for `VisualPositioningSystem.Login`). The domain is read from a `.env` file via `UnityEnv.cs` at build/editor time only — there is no way to change it at runtime. This means every deployment requires a pre-configured `.env` and the default dev credentials.

Both app modes need this: the normal XR client mode and the authoring tools mode (`AUTHORING_TOOLS_ENABLED`). Both paths currently call the same hard-coded auth in `AppSetup.cs`.

## Key files

**Reference implementation (AndroidMobile — read, don't modify):**
- `apps/AndroidMobile/Assets/SettingsManager.cs` — JSON persistence to `persistentDataPath`
- `apps/AndroidMobile/Assets/Scripts/Capture/LoginUI.cs` — Nessle declarative login UI
- `apps/AndroidMobile/Assets/Scripts/Capture/AppState.cs` — `SettingsState` + `AuthStatus` + derived `loggedIn`
- `apps/AndroidMobile/Assets/AuthManager.cs` — observes `loginRequested`, calls `VisualPositioningSystem.Login()`
- `apps/AndroidMobile/Assets/Scripts/Capture/CaptureController.cs` — conditional render of LoginUI vs MainAppUI

**Files to modify in Outernet.Client:**
- `legacy/Outernet.Client/Assets/OuternetClient/AppSetup.cs` — remove hard-coded credentials, defer login to user action
- `legacy/Outernet.Client/Assets/OuternetClient/UnityEnv.cs` — domain may become a fallback default rather than the sole source
- `legacy/Outernet.Client/Assets/OuternetClient/App.cs` — add auth state, conditional UI gating

**Files to create in Outernet.Client:**
- Settings persistence (equivalent to AndroidMobile's `SettingsManager.cs`)
- Login UI (equivalent to AndroidMobile's `LoginUI.cs`)
- Auth state management (settings state + auth status observables)

## Approach

Port the AndroidMobile login pattern to Outernet.Client. Add observable settings state (domain, username, password) with JSON file persistence using FofX.Stateful. Build a login UI using standard uGUI components (TMP_InputField, Button, TextMeshProUGUI) matching the existing SettingsPanel pattern. Gate app initialization on successful login in both `AUTHORING_TOOLS_ENABLED` and normal mode. Remove hard-coded credentials from `AppSetup.cs`. Use the `.env` domain as the default value for the domain field on first launch (rather than null like AndroidMobile does).

## Done when

**Verifiable now:**
- No hard-coded `"user"` / `"password"` strings remain in `AppSetup.cs`
- Settings (domain, username, password) persist to a JSON file in `Application.persistentDataPath`
- App compiles under both `AUTHORING_TOOLS_ENABLED` and normal scripting define configurations

**Requires manual verification:**
- On first launch, a login screen appears with domain (pre-filled from `.env` if available), username, and password fields
- After entering credentials and logging in, the app proceeds to its normal flow
- On subsequent launches, saved credentials are pre-filled in the login form
- Login works in both authoring tools mode and normal XR client mode

## Design decisions

- **UI framework**: Standard uGUI (TMP_InputField, Button, TextMeshProUGUI) with FofX.Stateful for persistence. Nessle is not available in this project. The authoring tools `Control<T>` system is ruled out because it depends on `App.state.context` (not initialized pre-login) and is gated behind `AUTHORING_TOOLS_ENABLED`.

## Log

Clean implementation, no issues.

## Observations

- `App.cs:313` — `ConnectionManager.Terminate()` has a comment `// BUG, this is async` indicating a known issue with async teardown in the quit handler.
- `AppSetup.cs` previously had race conditions: `Auth.Login()` and `VisualPositioningSystem.Login()` were fire-and-forget (`.Forget()`) but `ConnectionManager.Initialize()` and `LocalizationManager` depended on auth being complete. The new deferred initialization via `PostLoginSetup()` resolves this.
