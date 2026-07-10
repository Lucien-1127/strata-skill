---
name: windows-env-diagnostics
description: "Windows 環境診斷、開發工具調查、暫存清理與系統優化。從 git-bash/MSYS2 終端機執行的兼容操作。"
status: stable
---
# windows-env-diagnostics

## 📖 Description

Windows 環境診斷、開發工具調查、暫存清理與系統優化。從 git-bash/MSYS2 終端機執行的兼容操作。

---

# Windows Environment Diagnostics & Optimization

System survey, developer tool inventory, temp/cache cleanup, and optimization for Windows machines accessed via git-bash (MSYS2) terminal.

## Key Windows Quirks (git-bash context)

### pip points to wrong Python
On Windows via git-bash, `pip` (and `python3`) often point to Python 3.10 even though Hermes runs under Python 3.11. Always check:

```bash
pip -V            # Which Python does pip target?
python --version   # Which Python does the shell use?
```

Hermes runs from `~/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe` (Python 3.11).

### Hermes venv has no pip
The Hermes-installed venv is stripped — no `pip` or `pytest`. Install pip via `ensurepip`:

```bash
"$HERMES_VENV/python.exe" -m ensurepip --upgrade
"$HERMES_VENV/python.exe" -m pip install <package>
```

Never assume `pip` in the global shell can install into the Hermes venv.

### Hardware info commands
`wmic` does not exist in git-bash. Use these alternatives:

| Info | Command |
|------|---------|
| CPU | `cat /proc/cpuinfo \| grep "model name" \| head -1` |
| RAM | `grep MemTotal /proc/meminfo` |
| GPU | `powershell.exe -Command "Get-WmiObject Win32_VideoController \| Select-Object Name,AdapterRAM,DriverVersion \| Format-List"` |
| OS | `powershell.exe -Command "(Get-WmiObject Win32_OperatingSystem).Caption"` |
| Motherboard | `powershell.exe -Command "Get-WmiObject Win32_BaseBoard \| Select-Object Manufacturer,Product \| Format-List"` |
| Disk | `df -h /c` |

### PATH behavior
- `which <cmd>` works in git-bash (returns real path)
- `echo "$PATH" | tr ':' '\n'` for listing
- Paths with spaces (e.g. `Program Files (x86)`) use `/c/Program Files (x86)/...`
- Use `sort | uniq -c` to find duplicate paths

## Scan-First Principle

**Always diagnose the full chain before fixing.** When the user reports a broken shortcut, launcher, or tool:

1. **Layer 1 — Entry point**: Verify the shortcut/trigger binary (`.lnk` emoji health, target path)
2. **Layer 2 — Target script**: Check script existence, parseability (PowerShell `Parser::ParseFile`), encoding (BOM)
3. **Layer 3 — Encoding**: Test the script under the actual runtime (not just syntax check — simulate execution)
4. **Layer 4 — Referenced paths**: Every path the script references (executables, configs, child scripts) — verify existence
5. **Layer 5 — System health**: Disk space, memory, GPU, dev tool inventory

Do NOT fix Layer 1 until Layers 2–4 are understood. A shortcut may test clean but point at a broken script. A script may have correct syntax but fail due to encoding (BOM) that only appears at runtime. A script may parse correctly but reference paths that don't exist.

**The user's frustration "點了之後一樣閃退" (clicked and it flashed away) usually means the fix is at Layer 3 or 4, not Layer 1.** Jumping straight to recreating the shortcut is a regression pattern — verify the full chain, then present the fix at the right layer.

For a concrete walkthrough of this multi-layer pipeline, see `references/windows-launcher-diagnostics-session.md`.

## System Survey Procedure

### 1. Hardware

```bash
cat /proc/cpuinfo | grep -E "model name|cpu cores|siblings" | head -5
grep -E "MemTotal|MemFree|MemAvailable" /proc/meminfo
df -h /c
powershell.exe -Command "Get-WmiObject Win32_VideoController | Select-Object Name,AdapterRAM | Format-List"
```

### 2. Developer Tools

```bash
# Python versions
/c/Users/$USER/AppData/Local/Programs/Python/Python310/python.exe --version
/c/Users/$USER/AppData/Local/Programs/Python/Python311/python.exe --version 2>/dev/null || echo "no 3.11"
/c/Users/$USER/AppData/Local/Programs/Python/Python312/python.exe --version 2>/dev/null || echo "no 3.12"
python --version && python3 --version

# Node/npm
node --version && npm --version

# Git/gh
git --version && gh --version 2>&1 | head -1

# Docker
docker --version 2>/dev/null || echo "no docker"

# Package managers
uv --version 2>/dev/null || echo "no uv"
```

### 3. Important Paths

```bash
echo "HOME: $HOME"
echo "APPDATA: $APPDATA"
echo "LOCALAPPDATA: $LOCALAPPDATA"
ls ~/Documents/
ls ~/Desktop/
```

### 4. Hermes Environment

```bash
ls ~/AppData/Local/hermes/
hermes config check
hermes status 2>/dev/null | head -20
```

## System Optimization Procedure

### Temp Cleanup
```bash
# User temp (safely removable)
rm -rf /c/Users/$USER/AppData/Local/Temp/*
# After: du -sh /c/Users/$USER/AppData/Local/Temp
```

### pip Upgrade & Cache
```bash
# System Python 3.10
"/c/Users/$USER/AppData/Local/Programs/Python/Python310/python.exe" -m pip install --upgrade pip
pip cache purge

# Hermes venv
"/c/Users/$USER/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe" -m pip install --upgrade pip
```

### npm Update & Cache
```bash
npm update -g 2>&1 | tail -5
npm cache clean --force
```

### Disk Space Check After
```bash
df -h /c
```

## Windows Disguised Folder Forensics

Investigate desktop shortcuts and scripts that masquerade as legitimate applications (calculator, notepad, etc.) but actually guard password-protected hidden folders under `AppData\Local\`.

### Typical Pattern

A `.lnk` shortcut on the desktop displays a decoy icon (e.g., `calc.exe`) but executes `pythonw.exe` with a hidden Python script. The script presents a normal-looking GUI, but a secret keyboard trigger reveals a password dialog. Correct password unlocks a hidden vault directory (set with `attrib +h +s`).

### Quick Investigation Flow

```bash
# 1. Check desktop for suspicious LNK files
ls -la ~/Desktop/

# 2. Parse the LNK to find its real target
file "名稱.lnk"

# 3. Extract Unicode strings to find the script path and args
# (use the Python unicode-dump technique from the reference)

# 4. Read the Python script to get: trigger, password, vault path
read_file "~/disguised_calculator.py"

# 5. List and access the hidden vault
ls -la "/c/Users/<user>/AppData/Local/<VaultName>/"
explorer "C:\Users\<user>\AppData\Local\<VaultName>"
```

For the complete step-by-step with real code, see `references/windows-disguised-folder-forensics.md`.

## Additional Optimization Targets

### Desktop Organization — Full Procedure

**Phase 1 — Inventory:** List every item on the desktop (including subdirectory contents). Categorize each as:
- **Backup/archive** (can delete if redundant with git/Syncthing)
- **Standalone script** (.bat, .cmd, .ps1 — test before consolidating)
- **Shortcut** (.lnk — move into organized folders)
- **Work project** (git repo, data tracker — keep on root desktop)
- **Binary/installer** (.exe, .msi — move into umbrella folder)

**Phase 2 — Test .bat/.cmd scripts:** Before consolidating, verify each one:
- `which <command>` or `where <command>` for each referenced executable
- `ls "C:\path\to\file"` for each hardcoded path
- Mark broken entries (tool not installed, path doesn't exist)
- Distinguish one-time installers from daily launchers

**Phase 3 — Consolidate into a tool launcher:** Build an integrated `.cmd` file that:
- Keeps all working options from any existing launcher
- Adds newly discovered working scripts
- Marks broken options clearly ("請先安裝 X" or "已移除")
- Uses absolute `C:\...` paths; includes fallback paths for files that may move
- Inlines simple one-off scripts directly; deletes the standalone file afterward

**Phase 4 — Big-folder architecture:** Create one umbrella folder (e.g. `📁 桌面工具集`) and move all non-project items into it. Preserve original subdirectory structure — don't flatten.

**Phase 5 — Desktop shortcut (CRITICAL: use .lnk, NOT .cmd):** Do NOT place a `.cmd` file on the desktop that calls the launcher via `start "" "..."` — this creates an **intermediate** CMD window that closes immediately after spawning the real launcher, causing a visible **flash**. The user sees the window appear and vanish and thinks nothing happened. Instead, create a proper Windows **.lnk shortcut** using PowerShell's WScript.Shell ComObject:

```powershell
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("$env:USERPROFILE\Desktop\🚀 工具啟動台.lnk")
$s.TargetPath = "C:\Users\$env:USERNAME\Desktop\📁 桌面工具集\常用工具\工具啟動台.cmd"
$s.WorkingDirectory = "C:\Users\$env:USERNAME\Desktop\📁 桌面工具集\常用工具"
$s.WindowStyle = 1  # Normal window
$s.Description = "工具啟動台 — 一鍵啟動各項工具"
$s.Save()
```

Advantages over `.cmd` approach:
- **No intermediate window** — targets the launcher directly
- **Working directory set** — relative paths in the launcher resolve correctly
- **WindowStyle control** — normal, minimized, or maximized
- **Emoji-safe** — the `.lnk` target path is stored in binary format, safe from CMD encoding issues that plague emoji in file paths (`📁`)
- **No flash** — only one window, and it stays open because the launcher has a menu loop

**Detection of the flash bug:** The user reports "點了之後一樣閃退" (clicked it and it flashed away). The launcher actually IS running in a separate window, but the user's eye only catches the flash of the intermediate window closing.

**Phase 6 — Rename English shortcuts to Chinese:** After moving all items into the umbrella folder, rename any remaining English-named `.lnk` files to descriptive Chinese names. Use PowerShell's WScript.Shell to read each shortcut's target path, then rename by creating a new `.lnk` with the same target but a Chinese name:

```powershell
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("old_English.lnk")
$new = $ws.CreateShortcut("中文名稱.lnk")
$new.TargetPath = $s.TargetPath
$new.Arguments = $s.Arguments
$new.WorkingDirectory = $s.WorkingDirectory
$new.Save()
Remove-Item "old_English.lnk" -Force
```

Good Chinese names describe the target's function. For example: `Brave.lnk` → `Brave 瀏覽器.lnk`, `Terminal.lnk` → `終端機.lnk`. Use emoji prefixes (`🌐 Brave 瀏覽器.lnk`) for visual scanning — they survive in `.lnk` binary format.

Also delete any shortcuts whose target no longer exists (e.g. uninstalled apps, deleted scripts). Verify by checking `Test-Path $s.TargetPath`.

**Phase 7 — Verify:** `ls -la ~/Desktop/` and confirm only 3–5 items remain (work projects + umbrella folder + launcher .lnk shortcut). Delete any empty directories. Run the launcher once to confirm it opens without flashing.

For a detailed session walkthrough with real examples, see `references/windows-desktop-organization-session.md`.

### HuggingFace Cache
```bash
# Check size
du -sh /c/Users/$USER/.cache/huggingface
# Clean locks only (keep downloaded models)
rm -rf /c/Users/$USER/.cache/huggingface/hub/.locks 2>/dev/null
```

### Recycle Bin
```bash
du -sh "/c/\$Recycle.Bin/"
```
Cannot clean via git-bash — use Windows `cleanmgr.exe` or `rd /s C:\$Recycle.bin` via admin PowerShell.
### Windows Update Temp (Admin Required)
```bash
# Check size
ls /c/WINDOWS/SoftwareDistribution/Download/ 2>/dev/null | wc -l
```

Needs admin elevation. Create a `.bat` script:
```batch
@echo off
net stop wuauserv /y >nul 2>&1
del /f /s /q C:\\Windows\\SoftwareDistribution\\Download\\*.* >nul 2>&1
rmdir /s /q C:\\Windows\\SoftwareDistribution\\Download >nul 2>&1
net start wuauserv >nul 2>&1
echo Windows Update cache cleaned.
pause
```
Run the `.bat` as Administrator via right-click.

**Encoding note:** Do NOT add `chcp 65001` to batch files unless you know the console is NOT already in UTF-8 mode (see CMD Encoding & Crash Fix below for the decision tree).

### Windows Terminal as Default

After all registry fixes, point the user to Windows Terminal (`wt` in Run dialog). It handles UTF-8 natively, has tabs, doesn't crash, and supports GPU-accelerated rendering. Set via:

```powershell
# HKCU\Console\EnableWindowsTerminalControl = 1 (already done above)
```

User can press `Ctrl+Shift+,` inside Windows Terminal to configure font/theme.

---

## CMD Encoding & Crash Fix (Traditional Chinese / UTF-8)

Windows CMD on Traditional Chinese systems frequently shows garbled characters (亂碼) and crashes (閃退). The root cause depends on the console's current encoding state — **always diagnose before fixing**.

### Diagnosis — Check Console State First

```powershell
# What code page is the console ACTUALLY using?
[System.Console]::OutputEncoding.CodePage

# Is the system OEM code page 950 (Big5) or 65001 (UTF-8)?
[System.Globalization.CultureInfo]::CurrentCulture.TextInfo.OEMCodePage

# Are Windows Terminal features enabled?
Get-ItemProperty 'HKCU:\Console' 'VirtualTerminalLevel' -ErrorAction SilentlyContinue
Get-ItemProperty 'HKCU:\Console' 'EnableWindowsTerminalControl' -ErrorAction SilentlyContinue
```

### Decision Tree

**Case A — Console is already CP 65001 (UTF-8):**
- ⚠️ Do NOT add `chcp 65001` to batch files — it's redundant and can break `set /p`
- ⚠️ All `set /p` prompts MUST use ASCII-only text — Chinese prompts in a `set /p` string under CP 65001 is a **known Windows bug** that silently returns empty input
- Save batch files as **UTF-8 without BOM** (matches the console encoding)
- Focus on font registration (see Registry Fixes below)

**Case B — Console is CP 950 (Big5, legacy):**
- Save batch files as **ANSI/CP 950** (the system's native encoding)
- Chinese characters in `echo` and `set /p` work natively
- Add `chcp 65001 >nul 2>&1` only if you specifically need UTF-8 output for a command
- Consider setting Windows Terminal as default (handles UTF-8 natively)

### CRITICAL Pitfall: `set /p` + Chinese Prompts Under CP 65001

**This is the single most common bug in Taiwanese/Chinese batch files on modern Windows.**

When the console is in CP 65001 (UTF-8) mode and a `set /p` prompt contains Chinese characters:

```batch
REM ❌ BROKEN — `choice` will be EMPTY under CP 65001
set /p choice=請輸入選數 (0-16):

REM ✅ WORKS — ASCII-only prompts are safe
set /p choice=Enter number (0-16):
```

The user types a number and presses Enter, but the variable is empty. The batch file then falls through all `if` checks, prints "invalid choice", and loops. The user thinks the whole launcher is broken.

**Rule:** All `set /p` prompts must use ASCII characters only. Keep Chinese text in `echo` statements (which display fine under CP 65001 with proper font).

### Registry Fixes

Run these as PowerShell (some need admin elevation):

```powershell
# A — Register font for CP 65001 (ADMIN: HKLM)
# Without this, CMD falls back to raster font → boxes for Chinese
New-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Console' `
  -Name '65001' -Value 'Consolas' -PropertyType String -Force

# B — Top-level Console CodePage (HKCU, no admin)
# Affects ALL console apps (CMD, PowerShell, WSL) for this user
New-ItemProperty -Path 'HKCU:\Console' `
  -Name 'CodePage' -Value 65001 -PropertyType DWord -Force

# C — Per-user CMD console defaults (pre-Windows 10 fallback, no admin)
$cmdKey = 'HKCU:\Console\%SystemRoot%_system32_cmd.exe'
New-Item -Path $cmdKey -Force | Out-Null
New-ItemProperty -Path $cmdKey -Name 'CodePage' -Value 65001 -PropertyType DWord -Force
New-ItemProperty -Path $cmdKey -Name 'FaceName' -Value 'Consolas' -PropertyType String -Force
New-ItemProperty -Path $cmdKey -Name 'FontFamily' -Value 54 -PropertyType DWord -Force

# D — AutoRun: auto-switch CMD to UTF-8 at startup (HKCU, no admin)
New-Item -Path 'HKCU:\Software\Microsoft\Command Processor' -Force | Out-Null
New-ItemProperty -Path 'HKCU:\Software\Microsoft\Command Processor' `
  -Name 'AutoRun' -Value 'chcp 65001>nul' -PropertyType String -Force

# E — Enable ANSI escape codes (HKCU, no admin)
```

### Font Recommendations

| Font | CJK Support | Code Compat | Install |
|------|-------------|-------------|---------|
| Consolas | ❌ (boxes for Chinese) | ✅ Excellent | Built-in |
| Cascadia Code | ✅ (v2106+) | ✅ Excellent | `winget install Microsoft.CascadiaCode` (may fail if package not indexed) |
| Microsoft JhengHei | ✅ | ❌ Not monospace | Built-in |
| JetBrains Mono | ⚠️ Limited | ✅ Excellent | Download from jetbrains.com |

**Best practice:** Windows Terminal (which is now the default) uses font fallback — it renders ASCII in Consolas and CJK in Microsoft JhengHei automatically. So just setting Windows Terminal as default often fixes the display without installing any new fonts.

### Verification

```powershell
# Check current code page
[System.Console]::OutputEncoding.WebName

# Check font registration
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Console' '65001'

# Verify batch file encoding
$b = [System.IO.File]::ReadAllBytes("C:\path\to\file.bat")
if ($b[0] -eq 0x40) { "No BOM - correct for UTF-8 or ASCII-only files" }
elseif ($b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF) { "Has BOM - correct for files with Chinese/Unicode content" }
```

**Batch file BOM rule of thumb:**
- **Chinese/Unicode content + UTF-8 saved** → MUST have BOM (`EF BB BF`) so cmd.exe reads the file as UTF-8
- **Pure ASCII only** → No BOM needed (and preferred — keeps compatibility with all tools)
- **Git-bash command to add BOM:** `printf '\xef\xbb\xbf' > tmp && cat file >> tmp && cp tmp file`
- **Git-bash command to detect BOM:** `od -A x -t x1 -N 3 file.bat | grep "ef bb bf" || echo "no BOM"`
```

For a detailed session walkthrough with real examples, see `references/windows-cmd-encoding-fix-session.md`.

### 🚨 CRITICAL: PowerShell 5.1 + UTF-8 BOM for .ps1 files

**This is the single most common cause of cryptic errors in zh-TW PowerShell scripts.**

PowerShell 5.1 (Windows PowerShell, not pwsh 7+) determines file encoding by BOM:
- **UTF-8 with BOM** (`EF BB BF`) → reads as UTF-8 ✅
- **No BOM** → reads as system ANSI (CP950/Big5 on zh-TW) ❌

**Symptoms of missing BOM:**
- Chinese characters in string literals become garbled (e.g. `控制台` → `?批?`)
- String boundaries break → `&&` inside string literals is parsed as PowerShell statement separator → `The token '&&' is not a valid statement separator in this version`
- `}` parsing errors, `Unexpected token` errors
- The file looks fine in editors but PowerShell rejects it

**Fix:**
```python
with open(script_path, 'rb') as f:
    raw = f.read()
if raw[:3] != b'\\xef\\xbb\\xbf':
    with open(script_path, 'wb') as f:
        f.write(b'\\xef\\xbb\\xbf')  # UTF-8 BOM
        f.write(raw)
```

**Detection (from git-bash):**
```bash
od -A x -t x1 -N 3 script.ps1 | grep "ef bb bf" || echo "NO BOM"
```

**Rule:** ALL `.ps1` files with Chinese/Unicode content must have UTF-8 BOM when targeting PowerShell 5.x. PowerShell 7+ (pwsh) handles BOM-less UTF-8 correctly but Windows 10 ships with PS 5.1 by default.

**Batch fix script:** `scripts/check-bom.py check <file_or_dir>` scans, `scripts/check-bom.py fix <file_or_dir>` repairs.

### The git-bash (MSYS) Bridge Problem

**This is a different problem from native CMD encoding.** When you run `cmd.exe` commands from within git-bash (MSYS2/MINGW64), TWO independent issues arise that don't exist in native CMD:

#### Issue 1: MSYS Path Translation (`/c` → `C:\`)

MSYS (git-bash) automatically translates POSIX-style paths to Windows paths. A `/c` argument to cmd.exe gets interpreted as drive `C:\`, not as the `/c` (run command) switch:

```bash
# ❌ BROKEN — MSYS converts /c to C:\
cmd.exe /c "echo test"    # → cmd.exe C:\"echo test" → ERROR

# ✅ WORKS — double-slash escapes MSYS translation
cmd.exe //c "echo test"   # → cmd.exe /c "echo test" → OK

# ✅ ALSO WORKS — set MSYS2_ARG_CONV_EXCL to disable translation
MSYS2_ARG_CONV_EXCL="*" cmd.exe /c "echo test"
```

**Rule of thumb:** Always use `//c` (or `//k` for interactive) when running cmd.exe from git-bash. The double-slash tells MSYS to pass the argument literally.

**Detection tip:** If the command outputs only the `Microsoft Windows [Version ...]` banner with no command output, MSYS path translation is likely eating the `/c` switch. Fix it with `//c`.

#### Issue 2: Encoding Mismatch (CP950 → UTF-8)

Even after fixing the `//c` issue, cmd.exe's output is encoded in CP950 (or whatever the system OEM code page is), but git-bash's terminal interprets everything as UTF-8:

```bash
# cmd.exe outputs CP950 bytes, git-bash reads as UTF-8 → garbled
cmd.exe //c "echo 測試"
# → garbled output (亂碼)

# Fix: pipe through iconv to convert CP950 → UTF-8
cmd.exe //c "echo 測試" | iconv -f CP950 -t UTF-8
# → correct output: 測試
```

**Note:** When `cmd.exe //c` is piped (not writing to a real console), it automatically suppresses the banner and prompt — only the actual command output is emitted. This avoids having to strip banner lines.

#### Three-layer Diagnosis

When debugging CMD encoding issues from git-bash, always check ALL three layers:

| Layer | How to check | Common fix |
|-------|-------------|------------|
| **1. System OEM code page** | `reg query HKLM\...\Nls\CodePage /v OEMCP` | Set `HKCU\Console\CodePage = 65001` |
| **2. CMD console code page** | `cmd.exe //c "chcp"` (from PowerShell) | Registry or AutoRun |
| **3. git-bash terminal encoding** | `locale \| grep LANG` | Should be `zh_TW.UTF-8` |

If layers 1 and 2 are fixed (CMD defaults to 65001) but garbled text persists from git-bash, the problem is layer 3 — the pipe bridge. The fix is `iconv` or the helper functions below.

#### .bashrc Helper Functions

Add these to `~/.bashrc` for daily use:

```bash
# ── CMD Encoding Bridge (git-bash → cmd.exe) ─────
# //c bypasses MSYS path translation; iconv fixes encoding

# cmd_utf8: Run cmd.exe with proper Chinese display from git-bash
# Usage: cmd_utf8 "echo 測試"  or  cmd_utf8 dir /b %USERPROFILE%
cmd_utf8() {
  cmd.exe //d //c "chcp 950 >nul & $*" 2>&1 | iconv -f CP950 -t UTF-8//IGNORE
}

# cmd_cp: Run with specific code page
#   cmd_cp 950 "echo 測試"       → Big5 + iconv (default, general use)
#   cmd_cp 65001 "type file.bat"  → UTF-8 mode, no iconv (for BOM files)
cmd_cp() {
  local cp="${1:-950}"; shift
  if [ "$cp" = "65001" ]; then
    cmd.exe //d //c "chcp 65001 >nul & $*" 2>&1
  else
    cmd.exe //d //c "chcp $cp >nul & $*" 2>&1 | iconv -f CP950 -t UTF-8//IGNORE
  fi
}

# cmd2: Shortcut for cmd_utf8
cmd2() { cmd_utf8 "$@"; }
```

**Key design decisions:**
- `/d` disables AutoRun (avoids auto-chcp + preserves clean pipe semantics)
- `chcp 950 >nul` forces CP950 before the command, making output encoding predictable
- `iconv -f CP950 -t UTF-8//IGNORE` converts CP950 output to UTF-8 for git-bash; `//IGNORE` gracefully drops non-CP950 bytes (UTF-8 BOM, stray bytes) instead of erroring out
- `cmd_cp 65001` mode avoids iconv entirely — passes raw bytes through for `type` on BOM-bearing UTF-8 files
- Functions (not aliases) ensure they work in non-interactive bash too

#### When to use each approach

| Scenario | What to use |
|----------|-------------|
| From git-bash, quick CMD command | `cmd2 "echo 測試"` |
| From git-bash, legacy Big5 file | `cmd_cp 950 "type file.txt"` |
| From git-bash, type BOM UTF-8 file | `cmd_cp 65001 "type file.bat"` (skips iconv) |
| Direct CMD window (not git-bash) | Registry fix (see Case A/B above) |
| Batch file with UTF-8 + Chinese | Save as UTF-8 **with BOM** + Registry fix |
| Batch file, pure ASCII only | UTF-8 without BOM (no `chcp` needed) |

### Rule of Thumb: Prefer PowerShell Over CMD

For Chinese-language Windows users, **PowerShell is the correct tool**, not CMD batch files. CMD has unfixable encoding limitations:

| Problem | CMD (.bat/.cmd) | PowerShell (.ps1) |
|---------|----------------|-------------------|
| Chinese in prompts | ❌ `set /p` returns empty under CP 65001 | ✅ `Read-Host` works perfectly |
| `chcp 65001` stability | ❌ Can crash batch files | ✅ Not needed — native Unicode |
| Font fallback | ❌ Single font, no CJK | ✅ Windows Terminal handles it |
| Emoji | ❌ Mostly unsupported | ✅ Full support |
| Error handling | ❌ Basic `errorlevel` | ✅ `try/catch`, `$LASTEXITCODE` |

**Decision:** Always reach for PowerShell first when creating a multi-option launcher, interactive menu, or any tool that displays Chinese text. Reserve `.bat`/`.cmd` for simple one-shot admin commands (service restart, file cleanup) that need no Chinese text.

**Migration path when a CMD-based launcher already exists:**
1. Rewrite the menu/logic as a `.ps1` script with `Write-Host` (colored output) and `Read-Host` (reliable input)
2. Wrap CMD commands that must stay via `cmd /c "..."` inside PowerShell
3. Delete standalone `.bat` utilities once the launcher inlines their logic
4. Run via `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "path\to\launcher.ps1"`
5. Use a `.lnk` shortcut (not a `.cmd` wrapper) on the desktop

### Hermes i18n: Setting Language from the CLI

Hermes Agent has built-in i18n (`agent/i18n.py`). To set Traditional Chinese:

```bash
hermes config set display.language zh-hant
```

**Scope (by design):**
- ✅ Translated: approval prompts, gateway slash command replies, `/help` output, model switching, goal setting, voice commands
- ❌ NOT translated: CLI ASCII art banner, tool listing, welcome message, agent-generated output, error tracebacks

**Verification:**
```python
from agent.i18n import get_language, t
get_language()                    # Returns 'zh-hant'
t('approval.choose_long')         # Returns Chinese text
```

---

## Developer Tool Installation (Python)

One-shot setup for Python developer tooling on Windows:

### Core Tools

| Tool | Purpose | Install Command | Verify |
|------|---------|-----------------|--------|
| **ruff** | Linter + formatter (Rust, fast) | `pip install ruff` | `ruff --version` |
| **mypy** | Static type checker | `pip install mypy` | `mypy --version` |
| **black** | Code formatter | `pip install black` | `black --version` |
| **pre-commit** | Git hook automation | `pip install pre-commit` | `pre-commit --version` |

Always install into the active Python environment (`pip -V` to confirm). On Windows with multiple Python versions, the Hermes venv is at `~/AppData/Local/hermes/hermes-agent/venv/`.

### Usage

```bash
# Lint
ruff check file.py                      # Show errors
ruff check --fix file.py                # Auto-fix
ruff format file.py                     # Auto-format

# Type check
mypy file.py                            # No type annotations? No errors reported

# Format
black file.py

# Git hooks (per project)
pre-commit install                      # Install git hooks
# Then create .pre-commit-config.yaml (see template)
```

### VS Code Configuration

Place in `%APPDATA%\Code\User\settings.json`:

```json
{
    "python.defaultInterpreterPath": "C:\\Users\\<user>\\AppData\\Local\\hermes\\hermes-agent\\venv\\Scripts\\python.exe",
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.autoImportCompletions": true,
    "ruff.enable": true,
    "ruff.format.args": ["--line-length", "100"],
    "ruff.lint.run": "onType",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll": "explicit",
            "source.organizeImports": "explicit"
        }
    },
    "errorLens.enabled": true,
    "errorLens.delay": 500
}
```

Pre-requisite VS Code extensions (already installed in this session): `charliermarsh.ruff`, `usernamehw.errorlens`, `ms-python.python`, `ms-python.vscode-pylance`.

### VS Code Configuration for zh-TW (Traditional Chinese) Users

For Traditional Chinese Windows users running git-bash (MSYS) as their primary shell, add these encoding and terminal settings to `%APPDATA%\Code\User\settings.json`:

```json
{
    "terminal.integrated.defaultProfile.windows": "Git Bash",
    "terminal.integrated.profiles.windows": {
        "Git Bash": {
            "path": "C:\\Program Files\\Git\\bin\\bash.exe",
            "args": ["--login", "-i"]
        }
    },
    "terminal.integrated.env.windows": {
        "CHCP": "65001",
        "LANG": "zh_TW.UTF-8",
        "LC_ALL": "zh_TW.UTF-8"
    },
    "terminal.integrated.windowsEnableConPTY": true,
    "terminal.integrated.fontFamily": "Consolas, 'Microsoft JhengHei', monospace",
    "terminal.integrated.fontSize": 13,

    "files.encoding": "utf8",
    "files.autoGuessEncoding": true,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,

    "editor.fontFamily": "Consolas, 'Microsoft JhengHei', 'Noto Sans CJK TC', monospace",
    "editor.fontSize": 14,
    "editor.fontLigatures": true,
    "editor.wordWrap": "on",
    "editor.wordWrapColumn": 100,

    "workbench.iconTheme": "material-icon-theme",
    "workbench.startupEditor": "none",

    "git.autofetch": true,
    "git.confirmSync": false,
    "git.enableSmartCommit": true
}
```

**Key decisions:**
- `terminal.integrated.defaultProfile.windows: "Git Bash"` — replaces PowerShell as the default terminal (preferred for Hermes Agent work)
- `terminal.integrated.env.windows` — sets `LANG` and `LC_ALL` so UTF-8 encoding propagates through nested shells
- `files.autoGuessEncoding: true` — auto-detects Big5 vs UTF-8 when opening legacy files
- `editor.fontFamily` — Consolas for code (monospace) with Microsoft JhengHei fallback for CJK glyphs
- `workbench.iconTheme: "material-icon-theme"` — requires `pkief.material-icon-theme` extension (already installed in this user's session)

### Pre-commit Template

See `templates/pre-commit-config.yaml` for a ready-to-use `.pre-commit-config.yaml` covering ruff, mypy, and standard hooks.

### Shortcut (.lnk) Repair — Emoji Path Workaround

Windows shortcuts (`*.lnk`) with emoji in the filename or target path (`🚀`, `📁`) can break when recreated via `WScript.Shell.CreateShortcut()` because the COM object uses ANSI (CP950) APIs internally and cannot create files at emoji-containing paths.

**Symptom:** `$lnk.Save()` throws `FileNotFoundException` even though the directory exists and is writable, or `TargetPath` reads as empty, or the stored target path contains `??` where the emoji should be.

#### Root Cause

On zh-TW Windows, the COM ANSI code page is CP950 (Big5), which **cannot represent emoji characters** (surrogate pairs). When `WScript.Shell.CreateShortcut()` processes emoji in filenames or in `Arguments`/`WorkingDirectory` strings, it silently degrades the surrogate pair bytes to `0x3F` (`?`). NTFS supports emoji natively via Unicode APIs, but COM legacy code path goes through ANSI.

#### Method A: ASCII Temp Path + Rename (COM-safe filename)

```powershell
# 1. Create at ASCII temp path
$ws = New-Object -ComObject WScript.Shell
$tempLnk = "$env:USERPROFILE\Desktop\tools_launcher.lnk"
$lnk = $ws.CreateShortcut($tempLnk)
$lnk.TargetPath = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
$lnk.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "...\launcher.ps1"'
$lnk.WorkingDirectory = "...\常用工具"
$lnk.Save()

# 2. Rename to final emoji path (NTFS natively supports Unicode)
Rename-Item $tempLnk "$env:USERPROFILE\Desktop\🚀 工具啟動台.lnk"
```

**⚠️ KNOWN LIMITATION:** Even with this workaround, the **internal** target path stored inside the `.lnk` binary for `Arguments` and `WorkingDirectory` may still have emoji corrupted to `??` (`3f 00 3f 00`). This happens because the COM `CreateShortcut` call passes these string values through ANSI APIs internally, converting surrogate pairs to `?`. The shortcut filename is correct but the path it targets is wrong. **Always verify the internal path after renaming** (see Detection below). If corrupted, apply Method B.

#### Method B: Binary Patching (reliable, fixes internal path emoji)

When the COM approach corrupts the internal emoji path, patch the `.lnk` binary directly. This bypasses all COM encoding issues:

```python
import os

with open(lnk_path, 'rb') as f:
    data = bytearray(f.read())

# The UTF-16LE encoding of the corrupted character and correct emoji
# Example: ?? (U+003F U+003F) → 📁 (U+1F4C1 = D83D DCC1)
# Old: 3f 00 3f 00    New: 3d d8 c1 dc
# Include surrounding context bytes for a unique match so we only
# hit the actual path strings, not random 3f 00 occurrences
old = bytes([0x3f, 0x00, 0x3f, 0x00, 0x20, 0x00, 0x4c, 0x68])  # "?? 桌"
new = bytes([0x3d, 0xd8, 0xc1, 0xdc, 0x20, 0x00, 0x4c, 0x68])  # "📁 桌"

count = 0
pos = 0
while True:
    idx = data.find(old, pos)
    if idx == -1:
        break
    data[idx:idx+len(old)] = new
    count += 1
    print(f"Fixed at offset {idx:#06x}")
    pos = idx + len(new)

if count:
    with open(lnk_path, 'wb') as f:
        f.write(data)
    print(f"✅ {count} emoji replacements made")
```

**Key assumption:** The old/new byte arrays must be the **same length** to preserve all internal offsets. Emoji surrogate pairs are always 4 bytes in UTF-16LE; `??` is also 4 bytes (`3f 00 3f 00`), so the swap is safe.

**Verification:**
```python
with open(lnk_path, 'rb') as f:
    data = f.read()
assert data.find(bytes([0x3d, 0xd8, 0xc1, 0xdc])) >= 0, "Emoji not found"
assert data.find(bytes([0x3f, 0x00, 0x3f, 0x00, 0x20, 0x00, 0x4c, 0x68])) < 0, "Old ? still present"
```

**Detection:** Raw bytes at the `Desktop\` path offset show `3f 00 3f 00` where a surrogate pair should be:
```python
with open(lnk_path, 'rb') as f:
    data = f.read()
# Search for "Desktop\" in UTF-16LE
desktop_utf16 = b'\x44\x00\x65\x00\x73\x00\x6b\x00\x74\x00\x6f\x00\x70\x00\x5c\x00'
idx = data.find(desktop_utf16)
if idx >= 0:
    after = data[idx+len(desktop_utf16):idx+len(desktop_utf16)+20]
    if after[:4] == b'\x3f\x00\x3f\x00':
        print("❌ Emoji corrupted to ??")
    elif after[:4] == b'\x3d\xd8\xc1\xdc':
        print("✅ Emoji is correct (📁)")
```

For a detailed session walkthrough, see `references/windows-shortcut-emoji-path-workaround.md`.

## References

- `references/windows-hermes-venv-notes.md` — Hermes venv quirks on Windows
- `references/windows-claude-code-dual-install.md` — Detecting and diagnosing dual Claude Code installations on Windows
- `references/windows-cmd-encoding-fix-session.md` — Real session walkthrough: garbled Chinese CMD fix, font registry, Windows Terminal default, dev tools installation\n- `references/windows-cmd-gitbash-bridge.md` — Real session walkthrough: MSYS `//c` path translation fix, iconv CP950→UTF-8 bridge, .bashrc helper functions\n- `references/windows-desktop-organization-session.md` — Real session walkthrough: desktop cleanup, tool launcher consolidation, tray icon approach
- `references/windows-disguised-folder-forensics.md` — Investigating calc-icon shortcuts that hide password-protected folders under AppData\Local
- `references/windows-shortcut-emoji-path-workaround.md` — Fixing .lnk files whose emoji-containing paths prevent recreation via COM objects
- `references/windows-launcher-diagnostics-session.md` — Multi-layer diagnostic pipeline for broken shortcuts (binary → script → encoding → paths → system)
- `references/windows-gateway-cmd-flash-on-boot.md` — Hermes gateway service script with hardcoded wrong user path causing CMD flash on startup

## Pitfalls

- **`wmic` doesn't exist in git-bash** — use `powershell.exe -Command` or `/proc/` instead.
- **`pip` is NOT the Hermes pip** — always check `pip -V` to confirm target.
- **`du -sh` on large directories can time out** (30s+) — use targeted subdirectory checks instead.
- **`rm -rf /c/WINDOWS/SoftwareDistribution/Download/*` needs admin** — skip or elevate.
- **`npm update -g` can fail on individual packages** but leave others updated — check results individually if batch fails.
- **Temp dir cleanup may leave locked files** — unavoidable on Windows. Just delete what you can.
- **`npm update -g` batch can fail on one package** (e.g., `@openai/codex` internal temp naming) — fall back to `npm install -g <pkg>@latest` per package.
- **`diff -rq` between large directories may hang or be misleading** under git-bash — use targeted `ls` comparisons instead.
- **Desktop shortcuts that open file paths** (`.lnk` files) should be moved into folders, not deleted.
- **`du -sh` on `~/AppData/Local` can take >30s** — restrict to specific subdirectories.
- **Multiple Python installations (3.10/3.11/3.12)** — track them all; `pip` almost certainly belongs to 3.10, not the Hermes venv.
- **`set /p` + Chinese prompts under CP 65001 is BROKEN** — When the console code page is 65001 (UTF-8), a `set /p` prompt containing Chinese characters silently returns an empty variable. The user types a number, presses Enter, and nothing is captured. **Fix:** Always use ASCII-only prompt text in `set /p` statements. Keep Chinese text in `echo` statements only. Example: `set /p choice=Enter number (0-16):` (not `請輸入選數`).
- **Emoji in folder paths (`📁`) can cause CMD resolution failures** — Windows .lnk shortcuts handle emoji fine (binary format), but `.cmd` files calling `start "" "path\with\emoji\..."` may fail. Use `.lnk` shortcuts for emoji paths.
- **HKCU registry fixes succeed without admin; HKLM needs elevation** — do HKCU fixes first (VirtualTerminalLevel, EnableWindowsTerminalControl) and offer a `Start-Process -Verb RunAs` script for HKLM (font registration).
- **`cmd.exe /c` from git-bash (MSYS) misparses `/c` as drive `C:\`** — Always use `//c` instead of `/c` when running cmd.exe from git-bash. Double-slash tells MSYS to bypass path translation. Detection: only the banner appears, no command output.\n- **git-bash pipe bridge encoding mismatch** — cmd.exe output in CP950 piped through git-bash (UTF-8 terminal) produces garbled text. Always pipe through `iconv -f CP950 -t UTF-8` when running cmd.exe commands from git-bash. The `.bashrc` functions (`cmd_utf8`, `cmd2`) automate this.\n- **Always clean up generated temp files** — scripts written during investigation (LNK parsers, analysis dumps, JSON exports) must be deleted from the desktop and user-facing directories immediately after use. Leaving them is clutter the user has to clean up. Delete via `rm` once the information has been extracted.
- **Verify deliverables BEFORE presenting as done** — The user expects a working artifact backed by real tool output, not a description of one. Before saying "done" or "fixed": (1) run the tool/script to confirm it starts without error, (2) check syntax/encoding of any generated files, (3) verify the user's exact complaint case (e.g. garbled text disappeared, no flash on click). If the tool depends on a specific runtime (PowerShell, Python venv), run it end-to-end with `cmd /c` or `powershell -File` to simulate what double-clicking the desktop icon does. Reporting "it should work" without verifying is the most common source of user frustration. When the user says "你先檢查一次再交付" (check it first before delivering), the regression is already in progress — stop, verify, then present.
- **PowerShell 5.1 + UTF-8 BOM for .ps1 files** — .ps1 files with Chinese characters MUST have UTF-8 BOM (EF BB BF) or PS 5.1 reads them as CP950, corrupting all non-ASCII text. Symptom: `&&` parsing errors, garbled Chinese in error messages. Fix: add BOM. Use scripts/check-bom.py fix dir for batch repair. pwsh 7+ handles BOM-less UTF-8 fine.
- **Hermes gateway CMD flash on boot** — If CMD flashes on startup, check `schtasks /query` for `Hermes_Gateway`, then inspect `$HERMES_HOME\\gateway-service\\Hermes_Gateway.cmd`. The gateway service script sometimes has a hardcoded wrong user path (e.g. `C:\\Users\\Hermes\\...` instead of `C:\\Users\\ysga1\\...`). Fix: replace hardcoded path with `%HERMES_HOME%` variable references. Verify with `read_file` before and after.
- **CMD flash diagnosis extends beyond Hermes** — When investigating CMD flash on boot, always check ALL scheduled tasks for any `.cmd`/`.bat` actions with Logon triggers, not just `Hermes_Gateway`. Also check: (1) `Get-CimInstance Win32_StartupCommand` for registry-based startups, (2) `HKCU\\...\\Run` and `HKLM\\...\\Run` keys, (3) Startup folder (`%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup`), (4) Explorer-spawned children (`Get-CimInstance Win32_Process | Where-Object {$_.ParentProcessName -eq "explorer.exe"}`). The flash may come from third-party apps (AMD drivers, banking software, etc.), not just Hermes.
- **PowerShell from git-bash has quote escaping hell** — When running complex PowerShell from git-bash via `bash -c 'powershell.exe -Command "..."'`, nested quotes always break. ALWAYS use `execute_code` (Python subprocess) instead of `terminal` for PowerShell commands that need quotes, regex, or complex expressions. The Python `subprocess.run(['powershell.exe', '-Command', '...'])` pattern is the reliable bridge.
- **System health check standard procedure** — When asked for a comprehensive system check, follow this sequence: (1) OS info, (2) disk space, (3) RAM/swap, (4) CPU/GPU, (5) running processes, (6) startup programs, (7) services status, (8) Windows Update, (9) event viewer errors, (10) network, (11) dev tools versions, (12) temp files, (13) Hermes status, (14) pagefile, (15) uptime, (16) antivirus. Use `wmic` via PowerShell for hardware, `Get-CimInstance` for processes/services, `Get-WinEvent` for errors. Prioritize actionable findings over raw data.
