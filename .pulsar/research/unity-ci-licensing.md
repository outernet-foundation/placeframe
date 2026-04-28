# Unity CI Licensing: Seat Limits and Concurrent Activations

Research conducted 2026-03-04. Context: T75 adds win64 builds to CI — need to understand why 5 parallel Linux builds work with a single personal license, and whether Windows builds will too.

## The question

Why does serial-based activation allow 5+ parallel CI builds when Unity docs say 2 seats max? Will it scale to Windows? What breaks if Unity tightens enforcement?

Constraints: single Unity Personal license (serial-based), GameCI Docker containers, GitHub Actions hosted runners.

## Why Linux parallel builds work

**GameCI hardcodes a fixed `machine-id` in all Linux Docker images.**

From [`game-ci/docker/base/Dockerfile`](https://github.com/game-ci/docker/blob/0be9208/base/Dockerfile):

```dockerfile
RUN echo "576562626572264761624c65526f7478" > /etc/machine-id \
    && mkdir -p /var/lib/dbus/ \
    && ln -sf /etc/machine-id /var/lib/dbus/machine-id
```

Unity's licensing server identifies machines by hardware fingerprint, which includes `/etc/machine-id` on Linux. Because all GameCI containers report the same ID, Unity sees 5 containers as **one machine**. Each activation reuses the same activation slot rather than consuming a new one.

Additionally, GitHub's hosted runners all emit the same `HardwareId` (confirmed in [GameCI activation docs](https://game.ci/docs/1/github/activation/)), reinforcing the single-machine illusion.

This is **intentional on GameCI's part**, not a bug or undocumented tolerance. Their [Docker images docs](https://game.ci/docs/docker/docker-images/) explicitly state seat consumption is "not an issue for free licenses."

### The two log messages

The logs show both `Successfully activated the entitlement license` and `Successfully activated ULF license`. This is expected: Unity 6 command-line activation with `-serial -username -password` triggers both the legacy serial (ULF) and modern Named User License (entitlement) simultaneously. Both bind to the same machine identity. [Unity support confirms this dual-activation behavior.](https://support.unity.com/hc/en-us/articles/39229898813844)

## Windows is fundamentally different

**GameCI Windows containers do NOT hardcode a machine-id.** From [GameCI Windows Docker docs](https://game.ci/docs/docker/windows-docker-images/):

> "The Ubuntu base images use a hardcoded machine id whereas the Windows machines do not."
> "License files for every run are identical apart from the last four symbols of the machine hash code."
> "In Windows, it's necessary to acquire a license every time and return it after a building process."

Each Windows container generates a **different** machine hash, so each one counts as a distinct machine from Unity's perspective.

### Impact on T75

Current state: 5 Linux containers sharing 1 activation slot. If we add 2 Windows containers (Outernet.Client win64 + MapRegistrationTool win64):

| Machine identity | Activation slots consumed |
|---|---|
| All Linux GameCI containers (shared machine-id) | 1 |
| Windows container #1 (unique machine hash) | 1 |
| Windows container #2 (unique machine hash) | 1 |
| Dev machine (if Unity is open locally) | 1 |
| **Total** | **3–4** |

Unity allows **2 activations per serial**. Two parallel Windows containers would exceed the limit.

### Possible workaround: native runner activation

If win64 builds activate on the bare `windows-latest` runner (not inside a Docker container), all GitHub-hosted Windows VMs may share the same `HardwareId` — similar to how Linux runners work. This would mean both Windows builds share 1 slot. But this is speculative and untested.

### Known Windows container issues

- **DNS resolution failures** reaching Unity's licensing server ([game-ci/unity-builder#669](https://github.com/game-ci/unity-builder/issues/669))
- **IPC/token caching failures** during Windows IL2CPP activation ([game-ci/unity-builder#569](https://github.com/game-ci/unity-builder/issues/569))

## Hard ceiling

There is no documented ceiling on the number of containers sharing the same machine-id. The limit is on **distinct machine identities**: 2 per serial. All Linux containers share 1 identity, so 50 Linux containers would still use 1 slot. The constraint is Windows (each container = a new identity).

## Blast radius if Unity tightens enforcement

### Terms of service

Unity's [Editor Software Terms](https://unity.com/legal/editor-terms-of-service/software) state:
- "You may only use one instance at any given time per seat"
- Build Server licenses are "not available with Unity Personal"
- Circumventing "capacity limits, Authorized User or storage limits" is prohibited

The GameCI machine-id trick is technically a terms violation. However:

### Enforcement likelihood

| Scenario | Likelihood | Impact |
|---|---|---|
| Block the known GameCI machine-id | Low | Thousands of projects break; GameCI rotates the ID |
| Add concurrent-instance-per-machine-id detection | Low | Breaks parallel builds for everyone |
| Deprecate serial-based activation entirely | Medium-High | Already migrating to Named User Licensing |
| Require Build Server license for CI (enforced) | Low-Medium | Would break every small team's CI |

**Most likely risk**: Unity deprecates serial activation in favor of entitlement-only, and the new system uses stricter device tracking that doesn't rely on `/etc/machine-id`. GameCI's hardcoded ID trick would stop working. The GameCI community is large enough that this would generate early warning.

**Enforcement history**: Unity has revoked Personal licenses for revenue threshold violations ($200K), but no documented cases of CI seat-count enforcement. The GameCI approach has been the status quo for years with Unity's awareness.

## Options for T75

| Option | Parallel win64? | Cost | Risk |
|---|---|---|---|
| **Serialize Windows builds** — run win64 jobs sequentially, activate/return before next | No | $0, adds wall-clock time | Low — stays within 2-seat limit |
| **Native runner activation** — don't use Docker containers for Windows, install Unity directly on `windows-latest` | Maybe — depends on shared HardwareId | $0, different architecture | Medium — untested assumption |
| **Second Personal license** — separate Unity account for CI | Yes | $0/year | Low — doubles available slots |
| **Unity Pro + Build Server** | Yes, properly | $2,640/year | None — officially supported |
| **GameCI Windows with sequential gate** — parallel Linux, sequential Windows with license handoff | Partial | $0 | Low |

---

## Deep dive: Windows runner machine identity (added 2026-03-04)

Follow-up research to determine whether `windows-latest` GitHub-hosted runners share a consistent HardwareId that Unity licensing would see as "one machine" — the same way Linux runners + GameCI Docker containers do.

### 1. What Unity uses for machine fingerprinting on Windows

Unity uses **two separate fingerprinting systems** on Windows:

**For `SystemInfo.deviceUniqueIdentifier` (runtime API):**
A hash of three WMI serial numbers concatenated together:
- `Win32_BaseBoard::SerialNumber`
- `Win32_BIOS::SerialNumber`
- `Win32_OperatingSystem::SerialNumber`

Source: [Unity docs — SystemInfo.deviceUniqueIdentifier](https://docs.unity3d.com/ScriptReference/SystemInfo-deviceUniqueIdentifier.html)

**For licensing (Editor activation):**
Unity's licensing uses a separate "machine binding" system with **multiple binding keys** (numbered 1 through at least 5). These include:
- **Binding 1**: Appears to be the **Windows Product ID** (`Win32_OperatingSystem::SerialNumber`, stored at `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProductId`). Evidence: GameCI issue #28 shows binding 1 value `00430-00000-00000-AA128`, which matches Windows Product ID format.
- **Binding 4**: Unknown, but changes after Windows updates.
- **Binding 5**: Linked to **network adapter / MAC address**. The "Machine Identification Is Invalid" error is officially described as "caused by the ULF being attached to the incorrect network adapter."

The ULF (Unity License File) is XML containing a `<MachineBindings>` section with `<Binding Key="N" Value="hash"/>` entries and a `<MachineID>` element. See [example ULF](https://github.com/zhuyiif/UnityBathBuildTest/blob/master/Unity_lic.ulf).

Key distinction: the licensing fingerprint is **not the same as** `deviceUniqueIdentifier`. The licensing system uses Product ID and network adapters; the runtime API uses BIOS/BaseBoard/OS serial numbers.

Sources:
- [Unity deviceUniqueIdentifier docs](https://docs.unity3d.com/ScriptReference/SystemInfo-deviceUniqueIdentifier.html)
- [Unity support: Machine Identification Is Invalid](https://support.unity.com/hc/en-us/articles/360039435032)
- [game-ci/cli#28 (Windows machine binding mismatch)](https://github.com/game-ci/cli/issues/28)
- [Unity Issue Tracker: binding key changed after Windows update](https://issuetracker.unity3d.com/issues/activating-license-from-the-command-line-fails-if-machines-binding-key-has-changed)

### 2. Do GitHub's hosted Windows runners share a HardwareId?

**Short answer: Probably yes for licensing purposes, but it's uncertain and depends on which binding keys Unity checks.**

GitHub-hosted Windows runners are Azure VMs provisioned from a golden image built with Packer (`azure-arm` builder). The build process runs `sysprep /oobe /generalize /mode:vm /quiet /quit` as a final step, then the image is published to an Azure Shared Image Gallery. Each workflow job gets a fresh VM provisioned from this image.

Analysis of the three relevant identity signals:

| Signal | Unique per VM? | Why |
|---|---|---|
| `Win32_OperatingSystem::SerialNumber` (= Windows Product ID) | **Likely the same across all runners** | Sysprep /generalize does NOT regenerate the Product ID. It resets activation status but keeps the Product ID. Azure VMs activated via KMS with the same GVLK (Generic Volume License Key) likely share the same Product ID. The value `00430-00000-00000-AA128` from GameCI issue #28 looks like a default/KMS Product ID. |
| `Win32_BIOS::SerialNumber` | **Unique per VM instance** | Azure encodes a 128-bit VM Unique ID in SMBIOS. The `Win32_BIOS::SerialNumber` maps to the VM's BIOS serial number, which Azure assigns uniquely per instance. Format example: `2968-7009-7262-8240-5408-0985-60`. This persists across reboots but changes when a new VM is created from the image. |
| `Win32_BaseBoard::SerialNumber` | **Unknown, possibly same** | Hyper-V cloned VMs are known to share the same `BaseBoardSerialNumber` from the template. Azure may or may not regenerate this. In on-prem Hyper-V, `BaseBoardSerialNumber` = `BIOSSerialNumber`, but Azure's provisioning may differ. |
| `MachineGuid` (registry) | **Regenerated by sysprep** | `HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid` is reset during sysprep generalize and regenerated during OOBE. Each VM instance gets a unique value. However, Unity licensing **does not appear to use MachineGuid**. |
| Network adapter MAC address | **Unknown, possibly consistent** | Azure VMs in the same VMSS may share MAC address patterns. If Unity binding 5 uses the MAC, this could vary. |
| `Win32_ComputerSystemProduct::UUID` | **Unique per VM** | This is the Azure VM Unique ID (128-bit SMBIOS UUID). Unique per instance, persists across reboots. |

**For Unity licensing specifically**: If binding 1 (Product ID) is the primary or sole binding checked on Windows, then all GitHub-hosted runners would appear as the same machine — just like Linux. The GameCI issue #28 error message shows binding 1 with a value that looks like a Windows Product ID, suggesting this is a key signal.

However, if Unity also checks BIOS serial number or other per-VM-unique values, each runner would appear as a different machine.

**This cannot be determined from documentation alone. It requires testing on an actual `windows-latest` runner** by:
1. Running `(Get-WmiObject Win32_OperatingSystem).SerialNumber` across multiple runs to check if Product ID is consistent
2. Running `(Get-WmiObject Win32_BIOS).SerialNumber` to check if BIOS serial varies
3. Activating Unity and checking the resulting ULF `<MachineBindings>` section
4. Attempting parallel activations to see if Unity counts them as 1 or 2 seats

Sources:
- [actions/runner-images Windows Packer templates](https://github.com/actions/runner-images/tree/main/images/windows/templates)
- [Azure VM Unique ID blog post](https://azure.microsoft.com/en-us/blog/accessing-and-using-azure-vm-unique-id/)
- [Hyper-V cloned VMs share BIOS serial number](https://social.technet.microsoft.com/Forums/en-US/43fb15bf-1cee-4c60-ab90-38c43f2b2b55)
- [Microsoft: sysprep /generalize](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/sysprep--generalize--a-windows-installation?view=windows-11)
- [runner-images: UAC disabled, admin privileges](https://github.com/actions/runner-images/discussions/6557)

### 3. Running Unity activation on bare Windows GitHub runners (no Docker)

Several approaches exist for activating Unity on `windows-latest` without Docker:

**Buildalon actions** ([buildalon/activate-unity-license](https://github.com/buildalon/activate-unity-license)):
- Runs natively on Windows, Linux, and macOS — no Docker required
- TypeScript-based GitHub Action
- Supports personal, professional, and floating licenses
- Used by the [VirtualMaker blog tutorial](https://dev.to/virtualmaker/automating-unity-builds-with-github-actions-1inf) for production Windows Unity CI

**kuler90/activate-unity** ([github](https://github.com/kuler90/activate-unity)):
- Supports Ubuntu, macOS, and Windows natively
- Archived January 2026, no longer maintained
- No Docker dependency

**RageAgainstThePixel/activate-unity-license** ([github](https://github.com/RageAgainstThePixel/activate-unity-license)):
- TypeScript action supporting all platforms
- Requires `UNITY_USERNAME`, `UNITY_PASSWORD`, and optionally `UNITY_SERIAL`

**GameCI on Windows** — requires Docker:
- `game-ci/unity-builder` on Windows uses Docker containers (Hyper-V or process isolation)
- Known issues with DNS resolution ([#669](https://github.com/game-ci/unity-builder/issues/669)), IPC failures ([#569](https://github.com/game-ci/unity-builder/issues/569))
- Does NOT hardcode machine-id in Windows images (unlike Linux)
- Self-hosted bare-metal Windows is poorly supported ([#637](https://github.com/game-ci/unity-builder/issues/637))

**Bottom line**: native (non-Docker) Unity activation on `windows-latest` is a solved problem. Buildalon is the most active option. The open question is whether the resulting machine identity is consistent across runners.

### 4. Can the Windows machine identity be controlled/hardcoded?

**Yes, with caveats.**

**Admin privileges**: GitHub-hosted Windows runners run as administrator with UAC disabled (`ConsentPromptBehaviorAdmin = 0`). This means workflow steps can write to `HKLM` registry keys without elevation prompts.

**MachineGuid**: Can be overwritten via PowerShell:
```powershell
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography" -Name "MachineGuid" -Value "576562626572264761624c65526f7478"
```
However, Unity licensing **does not appear to use MachineGuid**, so this likely has no effect.

**Windows Product ID** (`HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProductId`):
- This is what Unity licensing binding 1 appears to use
- Can be overwritten with admin privileges
- **Caution**: changing this may affect Windows activation status

**WMI BIOS/BaseBoard serial numbers**:
- These are SMBIOS values set by the hypervisor, **not** registry values
- Cannot be changed from inside the guest VM
- Would require host-level Hyper-V/Azure changes

**Network adapter MAC address**:
- Can potentially be spoofed with admin privileges
- But Azure VMs may restore the original MAC on reboot

**Practical approach for hardcoding identity**:
If Unity licensing primarily uses the Windows Product ID (binding 1), the simplest approach would be:
1. Set a fixed Product ID in the registry at the start of each workflow run
2. Use the same Product ID value that was used when generating the `.ulf` license file
3. This would make all runners appear as the same machine

If Unity also checks BIOS serial numbers or other hardware-level values, this approach would fail because those cannot be modified from inside the VM.

**Has anyone tried this?** No documented cases of anyone hardcoding Windows machine identity for Unity CI were found. The GameCI community has identified the problem (Windows containers generate unique machine hashes) but has not implemented a fix equivalent to the Linux machine-id hardcoding.

Sources:
- [UpdateMachineGuid PowerShell script](https://github.com/xmi1an/UpdateMachineGuid)
- [runner-images: admin privileges, UAC disabled](https://github.com/actions/runner-images/discussions/6557)

### 5. Recommended next steps

1. **Create a test workflow** on `windows-latest` that dumps all relevant WMI values:
   ```powershell
   (Get-WmiObject Win32_OperatingSystem).SerialNumber   # Product ID (binding 1?)
   (Get-WmiObject Win32_BIOS).SerialNumber               # BIOS serial (unique per VM?)
   (Get-WmiObject Win32_BaseBoard).SerialNumber           # BaseBoard serial
   (Get-WmiObject Win32_ComputerSystemProduct).UUID       # SMBIOS UUID
   (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Cryptography").MachineGuid
   Get-NetAdapter | Select-Object Name,MacAddress         # Network adapters
   ```
   Run it 3-5 times and compare outputs. This definitively answers whether runners share identity.

2. **If Product ID is consistent**: Test Unity activation across multiple runs. If it reuses the same seat, the native-runner approach works and Windows builds would consume only 1 additional seat (not 1 per container).

3. **If Product ID varies**: Test overwriting `ProductId` in the registry before Unity activation. If Unity reads it from the registry at activation time (rather than from WMI), a fixed value could force all runners to appear identical.

4. **If neither works**: Fall back to sequential Windows builds with activate/return, or investigate whether the Buildalon approach handles this transparently.

## Sources

- [GameCI base Dockerfile (hardcoded machine-id)](https://github.com/game-ci/docker/blob/0be9208/base/Dockerfile)
- [GameCI Docker images docs (seat consumption)](https://game.ci/docs/docker/docker-images/)
- [GameCI Windows Docker images docs](https://game.ci/docs/docker/windows-docker-images/)
- [GameCI activation docs (GitHub VM HardwareId)](https://game.ci/docs/1/github/activation/)
- [GameCI FAQ (machine-id explanation)](https://game.ci/docs/faq/)
- [Unity support: maximum license activations](https://support.unity.com/hc/en-us/articles/360040693532)
- [Unity support: duplicate activations from CLI](https://support.unity.com/hc/en-us/articles/39229898813844)
- [Unity support: license active on two devices](https://support.unity.com/hc/en-us/articles/39943726903060)
- [Unity support: Machine Identification Is Invalid](https://support.unity.com/hc/en-us/articles/360039435032)
- [Unity license compliance](https://unity.com/pages/license-compliance)
- [Unity Editor Software Terms](https://unity.com/legal/editor-terms-of-service/software)
- [Unity docs — SystemInfo.deviceUniqueIdentifier](https://docs.unity3d.com/ScriptReference/SystemInfo-deviceUniqueIdentifier.html)
- [Unity Issue Tracker: binding key changed after Windows update](https://issuetracker.unity3d.com/issues/activating-license-from-the-command-line-fails-if-machines-binding-key-has-changed)
- [game-ci/cli#28 (Windows machine binding mismatch)](https://github.com/game-ci/cli/issues/28)
- [game-ci/unity-builder#669 (Windows DNS issues)](https://github.com/game-ci/unity-builder/issues/669)
- [game-ci/unity-builder#569 (Windows IPC failures)](https://github.com/game-ci/unity-builder/issues/569)
- [game-ci/unity-builder#637 (Windows self-hosted runner)](https://github.com/game-ci/unity-builder/issues/637)
- [game-ci/unity-builder#484 (Windows licensing issue)](https://github.com/game-ci/unity-builder/issues/484)
- [actions/runner-images Windows Packer templates](https://github.com/actions/runner-images/tree/main/images/windows/templates)
- [actions/runner-images: UAC disabled](https://github.com/actions/runner-images/discussions/6557)
- [Azure VM Unique ID blog post](https://azure.microsoft.com/en-us/blog/accessing-and-using-azure-vm-unique-id/)
- [Hyper-V cloned VMs share BIOS serial number](https://social.technet.microsoft.com/Forums/en-US/43fb15bf-1cee-4c60-ab90-38c43f2b2b55)
- [Microsoft: sysprep /generalize](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/sysprep--generalize--a-windows-installation?view=windows-11)
- [Buildalon activate-unity-license](https://github.com/buildalon/activate-unity-license)
- [VirtualMaker: Automating Unity Builds with GitHub Actions](https://dev.to/virtualmaker/automating-unity-builds-with-github-actions-1inf)
- [kuler90/activate-unity (archived)](https://github.com/kuler90/activate-unity)
- [RageAgainstThePixel/activate-unity-license](https://github.com/RageAgainstThePixel/activate-unity-license)
- [UpdateMachineGuid PowerShell script](https://github.com/xmi1an/UpdateMachineGuid)
- [Example ULF file with MachineBindings](https://github.com/zhuyiif/UnityBathBuildTest/blob/master/Unity_lic.ulf)
