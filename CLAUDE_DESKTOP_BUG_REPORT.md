# Bug report — Claude Desktop (Windows): AppX container destroyed when Chromium falls back to software rendering

**Severity:** High — kills the app mid-task, repeatedly, destroying hours of unattended agent work
**Component:** Claude Desktop for Windows, MSIX package `Claude_pzs8sxrjxfjjc`
**Affected versions observed:** 1.32885.1.0, 1.37937.1.0, 1.37937.3.0, 1.40609.0.0 (all of them)
**Claude Code version:** 2.1.246 / 2.1.247 (running as a child of the desktop app)

---

## Summary

The app terminates without warning — no crash dialog, no entry in the Windows Application log — whenever
Chromium's GPU process falters and the renderer falls back to software rendering.

The fallback tries to load `vk_swiftshader.dll` from inside the MSIX package. **Windows Code Integrity
blocks that DLL**, because the package's `AppxMetadata\CodeIntegrity.cat` catalog cannot be loaded.
Process creation for the package then fails, and Windows destroys the entire Desktop AppX container,
taking the app and everything running in it down with it.

The DLL itself is fine — it is validly signed by Anthropic. The problem is that the package's integrity
**catalog** never registers, so the binary cannot be validated at the moment it is needed.

---

## Impact

I run long multi-agent Claude Code workflows (a quiz-bank build: ~16 concurrent research subagents,
heavy process spawning, sustained for 30–90 minutes). Under that load the app dies every time the
software-rendering fallback triggers.

- Observed across **three weeks** and **four package versions**.
- Each crash destroys the entire in-flight workflow (10M+ tokens of subagent work in the worst case),
  because nothing has checkpointed yet.
- Measured completion rate at low concurrency (3 subagents): **~80%** — 8 of 10 runs completed,
  2 died at 2.0 and 4.1 minutes.
- At high concurrency (12–16 subagents): runs died at **2.3, 2.8, 5.7, and 6.8 minutes**, essentially never
  completing.

Normal interactive chat use is unaffected, because it spawns few processes and drives little rendering.
That is why this looks like "the app randomly closes sometimes" to a normal user.

---

## Environment

| | |
|---|---|
| OS | Windows 11, build 10.0.26200 |
| CPU / RAM | 32 logical cores / 61.6 GB (44 GB free at crash time) |
| GPU | **Dual:** NVIDIA GeForce RTX 5090 (driver 32.0.16.1088, 2026-07-21) + AMD Radeon integrated |
| Display | 3440×1440 @ 179 Hz |
| Disk | 2.8 TB free |
| Install | MSIX at `C:\Program Files\WindowsApps\Claude_<ver>_x64__pzs8sxrjxfjjc\app\Claude.exe` |
| Smart App Control | **OFF** (`VerifiedAndReputablePolicyState = 0`) |
| HVCI / Memory Integrity | Enabled |
| Antivirus | Windows Defender only, no third-party security software |

The dual-GPU configuration is likely relevant: it gives the compositor an adapter-selection path that can
fail over, which is what triggers the SwiftShader fallback in the first place.

---

## Reproduction

1. Install Claude Desktop on Windows (MSIX, from the standard installer — not the Store).
2. Open Claude Code in the app, in a git repository.
3. Launch a workflow that spawns many concurrent subagents doing sustained web research
   (16 concurrent agents reliably reproduces; 3 reproduces intermittently).
4. Within 2–7 minutes the app vanishes. No crash dialog. No Application-log fault entry.

---

## Evidence

### The failure chain, from the Windows event logs

Every single death shows this exact sequence within a 1–2 second window:

```
Microsoft-Windows-CodeIntegrity/Operational
  Id=3033  Code Integrity determined that a process
           (\...\WindowsApps\Claude_<ver>_x64__pzs8sxrjxfjjc\app\claude.exe)
           attempted to load
           \...\WindowsApps\Claude_<ver>_x64__pzs8sxrjxfjjc\app\vk_swiftshader.dll
           that did not meet the Microsoft signing level requirements.

  Id=3010  Code Integrity was unable to load the
           \...\WindowsApps\Claude_<ver>_x64__pzs8sxrjxfjjc\AppxMetadata\CodeIntegrity.cat
           catalog.  Status 0xC000003A          [STATUS_OBJECT_PATH_NOT_FOUND]

Microsoft-Windows-AppModel-Runtime/Admin
  Id=6  ×5  0x3CFC: Cannot create the process for package <NULL> because an error was
            encountered while checking the machine-level package status.
            The application cannot be started. Try reinstalling the application to fix the problem.

  Id=217    Destroyed Desktop AppX container {…} for package Claude_<ver>_x64__pzs8sxrjxfjjc.
```

### Correlation with workflow deaths (each matches the run's last file write to the second)

| Crash timestamp | Package version | Workflow died |
|---|---|---|
| 2026-08-26 09:46:35 | 1.37937.1.0 | 09:46:35 |
| 2026-08-27 16:47:39 | 1.37937.1.0 | 16:47:39 |
| 2026-08-27 18:42:15 | 1.37937.1.0 | 18:42:15 |
| 2026-08-28 08:24:21 | 1.40609.0.0 | 08:24:20 |
| 2026-08-28 09:57:46 | 1.40609.0.0 | 09:57:46 |
| 2026-08-28 15:22:25 | 1.40609.0.0 | 15:22:25 |

### The DLL is correctly signed — this is a catalog problem, not a signing problem

```
Get-AuthenticodeSignature "...\app\vk_swiftshader.dll"

Status  : Valid
Subject : CN="Anthropic, PBC", O="Anthropic, PBC", L=San Francisco, S=California, C=US
Issuer  : CN=DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1
Valid   : 2025-10-13 → 2026-10-20
```

### Related deployment errors suggesting the package is not being trust-labeled correctly

```
Microsoft-Windows-AppXDeploymentServer/Operational
  Id=8107  Illegal non-AppStore or non-AppInstaller package integrity validation attempted
           for package Claude_1.40609.0.0_x64__pzs8sxrjxfjjc.  Flags: 0x0
  Id=8104  Failed to set the Trust Label on package Claude_1.40609.0.0_x64__pzs8sxrjxfjjc
           with flags 0x0.  Error: 0x80070057   [E_INVALIDARG]
```

---

## Root cause (proposed)

The installer stages the package in a way that leaves **`AppxMetadata\CodeIntegrity.cat` unregistered or
unreachable** (`STATUS_OBJECT_PATH_NOT_FOUND`), and the package's trust label fails to apply
(`8104 / E_INVALIDARG`, alongside `8107` complaining the integrity validation is being attempted through a
non-AppStore/non-AppInstaller path).

While the GPU path is healthy this is latent — nothing in the package needs catalog-backed validation.
The moment Chromium falls back to software rendering and tries to load `vk_swiftshader.dll`, Code
Integrity has no catalog to validate against, refuses the load, and the AppX container is torn down.

---

## Why the standard remedies do not work

All of these were tried, and none of them touch the fault:

- **Settings → Apps → Claude → Repair** — tried ~20 times. Repair re-registers the *per-user* copy from the
  same machine-level source, so it faithfully reproduces the same broken state.
- **Full uninstall + reinstall** — done; the fresh install exhibits the identical failure.
- **Reset** — done; additionally wipes user settings (see workaround below).
- **Reboot** — machine-level package state persists across reboots.
- **Disabling hardware acceleration** — would make this **worse**, since software rendering is precisely
  what loads the blocked DLL.

---

## Partial workaround (not a fix)

Pinning the app to the discrete GPU appears to reduce how often the fallback triggers:

```powershell
$k = 'HKCU:\Software\Microsoft\DirectX\UserGpuPreferences'
New-ItemProperty -Path $k -Name 'Claude_pzs8sxrjxfjjc!Claude' -Value 'GpuPreference=2;' -PropertyType String -Force
New-ItemProperty -Path $k -Name '<full path to Claude.exe>'   -Value 'GpuPreference=2;' -PropertyType String -Force
# restart the app
```

Honest caveat: crashes still occur with this set (2026-08-28 15:22:25 happened with it active), so it
lowers frequency at best. It also gets wiped by app Reset, and the exe-path entry is invalidated by every
package update.

---

## Suggested fix

1. Ensure the installer registers `AppxMetadata\CodeIntegrity.cat` so package binaries can be validated
   (this alone should eliminate the crash, since the DLL is already correctly signed).
2. Investigate the `8104 Failed to set the Trust Label … E_INVALIDARG` and `8107 Illegal non-AppStore …`
   deployment errors — they look like the upstream cause of the missing catalog registration.
3. Defensively: if `vk_swiftshader.dll` cannot be loaded, degrade gracefully rather than allowing the
   AppX container to be destroyed. Losing software rendering should not be fatal to the whole app.
4. Consider testing on a dual-GPU (discrete + integrated) Windows machine under sustained multi-process
   load — that is the configuration that surfaces this.

---

## Verification commands (for whoever picks this up)

```powershell
# The blocking events
Get-WinEvent -LogName 'Microsoft-Windows-CodeIntegrity/Operational' |
  Where-Object { $_.Message -match 'vk_swiftshader' }

# The container teardown
Get-WinEvent -LogName 'Microsoft-Windows-AppModel-Runtime/Admin' |
  Where-Object { $_.Id -in 6,217 }

# The deployment trust-label failures
Get-WinEvent -LogName 'Microsoft-Windows-AppXDeploymentServer/Operational' |
  Where-Object { $_.Id -in 8104,8107 }
```
