---
name: tauri-v2-dev
description: >-
  Development, verification, build, and debugging runbook for Tauri v2 desktop applications
  with React and Rust on Windows. Use when working on tauri-desktop, compiling Rust code,
  handling Windows DWM styling, or testing the desktop companion.
---

# Tauri v2 Desktop Development & Verification Runbook (Windows)

This skill provides the standard workflow for building, checking, and troubleshooting the Tauri v2 desktop companion on Windows.

## 1. Environment & CLI Execution Rules

### Rust Compiler Toolchain PATH
On Windows PowerShell, Cargo may not be in the default session PATH. Always prefix Cargo commands with the user profile cargo bin directory:
```powershell
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"; cargo check
```

### Node / NPM / NPX Execution Policy
Never invoke `.ps1` script wrappers directly on Windows PowerShell due to execution policy restrictions. Always route via `cmd.exe`:
```powershell
cmd.exe /c "npm run build"
cmd.exe /c "npx.cmd <command>"
```

---

## 2. Windows DWM & Desktop Mode Guidelines

- **Stealth Background Launch**: The app must start completely hidden (`visible: false`, `skipTaskbar: true`). Only show window when explicitly toggled or launched with flags (`--overlay`, `--docked`, `--sidedeck`).
- **Never use `set_fullscreen(true)` for Overlay**:
  Exclusive fullscreen causes Windows DWM fights and click-through crashes. Always use physical bounds matching monitor dimensions:
  ```rust
  let _ = window.set_fullscreen(false);
  let _ = window.set_position(Position::Physical(*screen_pos));
  let _ = window.set_size(Size::Physical(*screen_size));
  let _ = window.set_always_on_top(true);
  ```
- **Strip Decorations & Disable DWM Shadow**:
  Call `strip_window_decorations(hwnd)` and `DwmSetWindowAttribute` with `DWMNCRP_DISABLED` (value `1`) to prevent window clipping artifacts.
- **Position Memory**: Mini Orb (`docked`, 120px) and Sidedeck (`sidedeck`, 370x540) positions must be recorded in `AppState` upon drag and restored on mode switch.

---

## 3. Mandatory 5-Step Verification Protocol

After modifying any file in `tauri-desktop/`:

1. **Build Frontend**:
   ```powershell
   cmd.exe /c "npm run build" # inside tauri-desktop
   ```
2. **Verify Rust Syntax & Types**:
   ```powershell
   $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"; cargo check # inside tauri-desktop/src-tauri
   ```
3. **Compile Binary**:
   ```powershell
   $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"; cargo build # inside tauri-desktop/src-tauri
   ```
4. **Test in Debug Console Mode**:
   Execute `scripts/run_tauri_debug.bat` to verify real-time stdout and tray event handling.
5. **Inspect Logs**:
   Confirm 0 errors in `logs/desktop.log` and verify `logs/panic.log` is completely clean.
