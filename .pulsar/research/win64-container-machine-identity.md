# Win64 Container Machine Identity for Unity Licensing

Research conducted 2026-03-04. Context: T75 needs Windows containers to share a single Unity licensing seat, equivalent to GameCI's Linux `machine-id` hardcoding.

## The Linux approach (proven, working)

GameCI hardcodes `/etc/machine-id` to `576562626572264761624c65526f7478` in all Linux Docker images. Unity licensing reads this file. All containers appear as one machine. 5+ parallel builds share 1 activation slot.

## Unity's Windows machine bindings

Unity licensing on Windows uses numbered "machine bindings" stored in the ULF (Unity License File) XML:

| Binding | Likely identity signal | Controllable in container? |
|---|---|---|
| 1 | Windows Product ID (`HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProductId`) | Yes — registry value, persists in image layers |
| 2 | Possibly `MachineGuid` (`HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid`) | Yes — registry value |
| 4 | Unknown OS-level identifier (changes after Windows updates) | Unknown |
| 5 | Network adapter MAC address | Yes — `docker run --mac-address` |

Evidence for binding 1 = Product ID: GameCI CLI issue #28 shows binding 1 value `00430-00000-00000-AA128`, which matches Windows Product ID format.

Evidence for binding 5 = MAC: Unity support docs state "Machine Identification Is Invalid" is "caused by the ULF being attached to the incorrect network adapter." Multiple community reports confirm binding 5 relates to MAC address.

## Windows container registry isolation

Process-isolated Windows containers have fully isolated per-container registry hives (Windows "server silos"). The kernel's `VrpRegistryCallback` redirects `HKLM` access to a per-silo hive stack:

- **Base hive**: Immutable, baked into the image during `docker build`. All containers from the same image share identical base hive values.
- **Delta hive**: Per-container writable overlay for runtime changes. Discarded when the container stops.

This means `RUN Set-ItemProperty -Path 'HKLM:\...' -Name ProductId -Value '...'` in a Dockerfile persists into the image and is identical across all containers from that image — exactly like Linux's `RUN echo "..." > /etc/machine-id`.

## Why GameCI's Windows images have variable identity

GameCI's Windows images do NOT hardcode any identity signals. Their docs state: "In Windows, it's necessary to acquire a license every time and return it after a building process."

The Product ID (`00430-00000-00000-AA128`) is actually already fixed — it comes from Microsoft's Windows Server Core base image and is the same across all containers from that image. The variable element is **the MAC address**: Docker assigns a new random MAC to each container on every `docker run`. This changes binding 5, invalidating the license.

GameCI chose the acquire/return-per-run workaround rather than fixing the MAC. Nobody in the community has documented attempting the fixed-MAC approach.

## The proposed fix

1. **Product ID (binding 1)**: Already fixed across containers from the same base image. No action needed.
2. **MachineGuid (binding 2?)**: Can be hardcoded in the Dockerfile: `RUN Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Cryptography' -Name MachineGuid -Value '576562626572264761624c65526f7478' -Type String`
3. **MAC address (binding 5)**: Fix with `docker run --mac-address=02:42:ac:11:00:02` (or any valid fixed MAC). This flag works on Windows containers via HNS, with some restrictions on valid MAC byte patterns (addresses starting with certain bytes fail with `0x57`; `02:42:...` and `92:...` patterns are confirmed working).
4. **Binding 4**: Unknown and potentially uncontrollable (may be SMBIOS/WMI). If Unity tolerates a partial match (as it does on Linux, where only `machine-id` is controlled), this may not matter.

## Confidence assessment

~75% confidence the fixed-MAC approach works. Reasoning:

- **For**: The Linux approach controls only one signal (`machine-id`) and Unity tolerates it. The technical mechanism for controlling registry values and MAC in Windows containers is well-documented. The Product ID is already shared.
- **Against**: Nobody has tried this. Binding 4 is unknown and uncontrollable. Unity may have stricter matching on Windows than Linux. The licensing system could check more signals than the community has identified.

## Empirical test (10 minutes)

1. Pull a GameCI Windows image on the desktop
2. `docker run --mac-address=02:42:ac:11:00:02 <image>` — activate Unity with `-serial`
3. Stop the container
4. `docker run --mac-address=02:42:ac:11:00:02 <image>` — check if the license is valid without re-activation
5. If valid: approach works. If "Machine Identification Is Invalid": check which binding mismatched (the error message includes binding keys and values)

## Fallback

If the fixed-MAC approach fails: native Unity install on the self-hosted runner (no containers). The runner has a consistent machine identity by definition — same physical hardware, same OS install, same MAC, same BIOS serials. Activate once, license persists across builds.

## Sources

- [GameCI base Dockerfile — hardcoded machine-id](https://github.com/game-ci/docker/blob/main/images/ubuntu/base/Dockerfile)
- [GameCI Windows Docker Images docs](https://game.ci/docs/docker/windows-docker-images/)
- [GameCI CLI issue #28 — Windows machine binding mismatch](https://github.com/game-ci/cli/issues/28)
- [GameCI unity-builder issue #204 — binding mismatch across image families](https://github.com/game-ci/unity-builder/issues/204)
- [Unity support: Machine Identification Is Invalid](https://support.unity.com/hc/en-us/articles/360039435032)
- [Containerized registry hives in Windows — DFIR Blog](https://dfir.ru/2020/08/15/containerized-registry-hives-in-windows/)
- [Reversing Windows Container, episode I: Silo — Quarkslab](https://blog.quarkslab.com/reversing-windows-container-episode-i-silo.html)
- [Windows container networking architecture — Microsoft Learn](https://learn.microsoft.com/en-us/virtualization/windowscontainers/container-networking/architecture)
- [Docker for Windows MAC address issue — docker/for-win #2399](https://github.com/docker/for-win/issues/2399)
- [Unable to assign specific MAC to Windows container — Docker Forums](https://forums.docker.com/t/unable-to-assign-specefic-mac-address-to-a-windows-container/66181)
