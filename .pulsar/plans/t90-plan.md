# T90 Plan: Add login/config screen to Outernet.Client

## Context

Outernet.Client hard-codes `"user"` / `"password"` in `AppSetup.cs` and reads the domain solely from a `.env` file at build time. Users cannot configure credentials or domain at runtime. The AndroidMobile app already has a working login screen pattern that we can adapt.

## Approach

Port the AndroidMobile login pattern (SettingsManager + AuthManager + LoginScreen + observable auth state) to Outernet.Client, using standard uGUI for the login UI and FofX.Stateful for state/persistence. Split `AppSetup.Awake()` into pre-login and post-login phases so auth-dependent initialization (API client, ConnectionManager, LocalizationManager) only runs after successful login.

### Step 1: Expand ClientState with auth and credential state

**Modify**: `legacy/Outernet.Client/Assets/OuternetClient/ClientState.cs`

Add `AuthStatus` enum (LoggedOut, LoggingIn, LoggedIn, Error) to the file.

Add to `ClientState`:
- `ObservablePrimitive<bool> loginRequested`
- `ObservablePrimitive<AuthStatus> authStatus`
- `ObservablePrimitive<string> authError`
- `ObservablePrimitive<bool> loggedIn` (derived from authStatus == LoggedIn, via `PostInitializeInternal`)

Expand existing `SettingsState` with credential fields:
- `ObservablePrimitive<string> domain`
- `ObservablePrimitive<string> username`
- `ObservablePrimitive<string> password`

The existing `animateNodeIndicators`, `showIndicators`, `visibleLayers` stay.

Follow the same `RegisterDerived` pattern used by `NodeState.visible` (line 79 of ClientState.cs) for the `loggedIn` derived property.

### Step 2: Add SetAuthStatusAction

**Modify**: `legacy/Outernet.Client/Assets/OuternetClient/AppActions.cs`

Add `SetAuthStatusAction : ObservableNodeAction<ClientState>` that sets both `authStatus` and `authError` atomically. Follows the pattern of existing actions like `SetLayersAction`.

### Step 3: Create SettingsManager

**Create**: `legacy/Outernet.Client/Assets/OuternetClient/SettingsManager.cs`

Direct port of `apps/AndroidMobile/Assets/SettingsManager.cs`. MonoBehaviour that:
- In `Awake()`: if `settings.json` exists at `persistentDataPath`, load via `settings.FromJSON()`. If not, set defaults: domain from `UnityEnv.GetOrCreateInstance().placeframeDomain`, username = `"user"`, password = `"password"`.
- Registers observer on `App.state.settings` to auto-save on any change.
- Skips save on `args.initialize` (same as AndroidMobile).

### Step 4: Create AuthManager

**Create**: `legacy/Outernet.Client/Assets/OuternetClient/AuthManager.cs`

Direct port of `apps/AndroidMobile/Assets/AuthManager.cs`. MonoBehaviour that:
- Observes `App.state.loginRequested`.
- On trigger: sets authStatus to LoggingIn, calls `VisualPositioningSystem.Login(domain, username, password)`.
- On success: sets authStatus to LoggedIn.
- On failure: sets authStatus to Error with exception message.
- Uses `TaskHandle` for cancellation (same pattern as AndroidMobile).

`VisualPositioningSystem.Login()` internally calls `Auth.Login()` AND creates `VisualPositioningSystem.Api`, so a single call replaces both hard-coded `.Forget()` calls currently in AppSetup.

### Step 5: Create LoginScreen (code-generated UI, no prefab)

**Create**: `legacy/Outernet.Client/Assets/OuternetClient/LoginScreen.cs`

MonoBehaviour that programmatically creates its UI in `Awake()` — avoids needing a prefab (which would require Unity Editor to wire serialized references and generate .meta files).

Creates:
- A `ScreenSpaceOverlay` Canvas with high sort order (renders on top of everything)
- Centered panel with VerticalLayoutGroup
- Three `TMP_InputField`s for domain, username, password (password uses contentType = Password)
- "Log In" button
- Error text (red, hidden by default)
- Status text ("Logging in...")

Binds:
- Input fields → `App.state.settings.{domain,username,password}` via `onValueChanged`
- Pre-fills from state on `Start()` (after SettingsManager has loaded)
- Login button → sets `App.state.loginRequested = true`
- Observes `authStatus`: disables button during login, shows error on failure, destroys self on success

### Step 6: Refactor AppSetup.cs — split into pre-login and post-login

**Modify**: `legacy/Outernet.Client/Assets/OuternetClient/AppSetup.cs`

**Pre-login phase (Awake):**
Keep everything that doesn't require auth:
- `AddCustomSerializers()`, `sceneReferences.Initialize()`
- Authoring tools setup (`#if AUTHORING_TOOLS_ENABLED` block)
- `UnityEnv` load
- `Auth.Initialize(...)`
- `Instantiate(prefabSystem)`, `gameObject.AddComponent<App>()`, `gameObject.AddComponent<Platform>()`
- `PrefabSystem.Create(cesiumCreditSystemUI)`
- `PlaneDetector.Initialize()`, `GPSManager`
- `VisualPositioningSystem.Initialize(...)`
- **NEW**: `gameObject.AddComponent<SettingsManager>()`
- **NEW**: `gameObject.AddComponent<AuthManager>()`
- **NEW**: `gameObject.AddComponent<LoginScreen>()`
- **NEW**: Register observer on `App.state.authStatus` for post-login trigger

**REMOVE** from Awake:
- `Auth.Login("user", "password").Forget()` (lines 58-62)
- `VisualPositioningSystem.Login("user", "password").Forget()` (lines 115-119)
- `ConnectionManager.Initialize()` (line 71)
- `Destroy(this)` (line 123) — keep AppSetup alive until post-login completes

**Post-login phase (new HandleAuthStatusChanged → PostLoginSetup):**
When `authStatus` becomes `LoggedIn`:
- Set `App.apiUrl` from `App.state.settings.domain.value` (user-entered domain, not .env)
- Call `App.InitializePostLogin()` (new method, see Step 7)
- `ConnectionManager.Initialize()`
- `#if !AUTHORING_TOOLS_ENABLED`: `SceneViewManager.Initialize()`, `TilesetManager.Initialize()`, `Instantiate(localizationMapManager)`
- `gameObject.AddComponent<LocalizationManager>()`
- Deregister observer, `Destroy(this)`

### Step 7: Refactor App.cs — defer API client and Start() logic

**Modify**: `legacy/Outernet.Client/Assets/OuternetClient/App.cs`

**Awake()**: Remove `DefaultApi` creation (lines 53-59) and hub connection requests (lines 64-66). Keep `base.Awake()` and `Application.wantsToQuit += WantsToQuit`.

**New `InitializePostLogin()` method**: Moves the API client creation and hub connection requests here. Called by `AppSetup.PostLoginSetup()`.

**Start()**: Guard the entire body with `if (!state.loggedIn.value) return;` — but since login is async and `Start()` runs on the first frame, it will always return early. The actual post-login behavior is kicked off by `InitializePostLogin()`. Move the `Start()` body contents into `InitializePostLogin()` (after API client creation).

## Key files

**Create:**
- `legacy/Outernet.Client/Assets/OuternetClient/SettingsManager.cs` — credential persistence
- `legacy/Outernet.Client/Assets/OuternetClient/AuthManager.cs` — login flow orchestration
- `legacy/Outernet.Client/Assets/OuternetClient/LoginScreen.cs` — code-generated uGUI login form

**Modify:**
- `legacy/Outernet.Client/Assets/OuternetClient/ClientState.cs` — add AuthStatus, auth state, expand SettingsState
- `legacy/Outernet.Client/Assets/OuternetClient/AppActions.cs` — add SetAuthStatusAction
- `legacy/Outernet.Client/Assets/OuternetClient/AppSetup.cs` — split pre/post-login, remove hard-coded creds
- `legacy/Outernet.Client/Assets/OuternetClient/App.cs` — defer API client + Start() logic

**Reference (read-only):**
- `apps/AndroidMobile/Assets/SettingsManager.cs` — persistence pattern
- `apps/AndroidMobile/Assets/AuthManager.cs` — auth flow pattern
- `apps/AndroidMobile/Assets/Scripts/Capture/AppState.cs` — state pattern

## Verification

1. **Compilation**: Run Unity batchmode on the Outernet.Client project with both scripting define configurations:
   - Default (no `AUTHORING_TOOLS_ENABLED`)
   - With `AUTHORING_TOOLS_ENABLED`
   - Check for `error CS` in output
2. **No hard-coded credentials**: Grep `AppSetup.cs` for `"user"` and `"password"` string literals — should find none
3. **Manual**: Launch the app, verify login screen appears, enter credentials, log in, verify app proceeds normally
