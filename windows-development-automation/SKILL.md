---
name: windows-development-automation
description: "Windows CMD/PowerShell automation for zh-TW systems: encoding, terminal config, scripting best practices"
status: stable
---
# windows-development-automation

## 📖 Description

Windows CMD/PowerShell automation for zh-TW systems: encoding, terminal config, scripting best practices

**Tags**: windows, cmd, powershell, encoding, terminal, automation, batch

---

# Windows Development Automation

## Overview

Windows command-line automation on Traditional Chinese (zh-TW) systems has well-known encoding pitfalls. CMD batch files use the OEM code page (CP 950 = Big5 by default), but modern tools output UTF-8. This mismatch causes garbled text, broken input prompts, and flashing terminal windows.

**Core principle:** Use the RIGHT tool for the job. PowerShell is the correct choice for any Windows automation involving non-ASCII text.

## The CMD Encoding Trap

### Known Bug: `chcp 65001` + `set /p`

On Windows (confirmed on 10/11), calling `chcp 65001` to switch the console to UTF-8 and then using `set /p` with Chinese characters in the prompt string causes **input to be silently dropped**. The variable remains empty.

**References:**
- [Stack Overflow: chcp 65001 and a .bat file](https://stackoverflow.com/questions/32182619/chcp-65001-and-a-bat-file)
- [Super User: Batch file fails with chcp 65001](https://superuser.com/questions/1306152/batch-file-fails-with-chcp-65001)
- [Microsoft Dev Blog: Diagnosing batch file encoding (Raymond Chen)](https://devblogs.microsoft.com/oldnewthing/20210726-00/?p=105483)

### What DOES NOT work reliably on zh-TW Windows

| Approach | Problem |
|----------|---------|
| CMD batch file saved as UTF-8, no `chcp` | CMD reads as CP 950 → garbled Chinese |
| CMD batch + `chcp 65001` + Chinese `set /p` | `set /p` silently drops input |
| CMD batch + `chcp 65001` + ASCII `set /p` | Works but fragile; other commands may fail under 65001 |
| Using `start ""` to launch a batch | Opens new window, original window flashes closed |

### What DOES work

| Approach | How |
|----------|-----|
| **PowerShell script (.ps1)** | Native UTF-8/UTF-16, `Read-Host` works correctly with Chinese |
| **Windows Terminal as default** | Handles UTF-8 natively with font fallback for CJK |
| **CMD batch + ANSI encoding** | Save as CP 950 (system default on zh-TW). No `chcp` needed. But `set /p` with Chinese still risky. |

## The PowerShell Solution

### Why PowerShell

| Feature | CMD | PowerShell |
|---------|-----|------------|
| Unicode handling | ⚠️ Limited (depends on code page) | ✅ Native UTF-16, auto-detect |
| Input prompts | ⚠️ `set /p` breaks with Chinese under 65001 | ✅ `Read-Host` works perfectly |
| Error handling | ⚠️ `errorlevel` is fragile | ✅ `try/catch`, `$LASTEXITCODE` |
| Script structure | ⚠️ GOTO spaghetti | ✅ Functions, switch, modules |
| Emoji support | ❌ None | ✅ Full support |
| Color output | ⚠️ Limited (color codes) | ✅ `Write-Host -ForegroundColor` |

### Running a PowerShell script from a shortcut

```powershell
# Target (in .lnk shortcut properties):
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\path\to\script.ps1"
```

### What NOT to do in PowerShell scripts for Chinese Windows

- ❌ `chcp 65001` — PowerShell handles encoding natively; this is unnecessary and can conflict
- ❌ Encoding batch files as UTF-8 with BOM — PowerShell reads .ps1 files as UTF-8 with BOM correctly, but CMD reads .bat/.cmd as OEM code page
- ❌ Using `cmd /c` internally when not needed — stay in PowerShell

## Windows Terminal Configuration

### Setting Windows Terminal as the default terminal app

```powershell
# Registry: Use Windows Terminal as default terminal host
New-ItemProperty -Path 'HKCU:\Console' -Name 'EnableWindowsTerminalControl' -Value 1 -PropertyType DWord -Force
```

### Enabling ANSI escape codes in legacy CMD

```powershell
New-ItemProperty -Path 'HKCU:\Console' -Name 'VirtualTerminalLevel' -Value 1 -PropertyType DWord -Force
```

### Setting CMD defaults for current user

```powershell
# Per-user CMD console settings
$cmdKey = 'HKCU:\Console\%SystemRoot%_system32_cmd.exe'
New-Item -Path $cmdKey -Force | Out-Null
New-ItemProperty -Path $cmdKey -Name 'CodePage' -Value 65001 -PropertyType DWord -Force
New-ItemProperty -Path $cmdKey -Name 'FaceName' -Value 'Consolas' -PropertyType String -Force
New-ItemProperty -Path $cmdKey -Name 'FontFamily' -Value 54 -PropertyType DWord -Force
New-ItemProperty -Path $cmdKey -Name 'FontSize' -Value 0x100000 -PropertyType DWord -Force
```

### Font registration for CP 65001

On zh-TW Windows, CP 65001 (UTF-8) may not have a registered font. To register one:

```powershell
# Requires admin rights (HKLM)
New-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Console' -Name '65001' -Value 'Consolas' -PropertyType String -Force
```

### Checking current code pages

```powershell
# Check current console encoding
[System.Console]::OutputEncoding.CodePage
[System.Console]::InputEncoding.CodePage

# Check system OEM/ANSI code pages
[System.Globalization.CultureInfo]::CurrentCulture.TextInfo.OEMCodePage
[System.Globalization.CultureInfo]::CurrentCulture.TextInfo.ANSICodePage
```

## File Encoding — Saving Batch Files Correctly

### To save a file as UTF-8 without BOM (best for PowerShell scripts)

```powershell
[System.IO.File]::WriteAllText("C:\path\to\file.ps1", $content, [System.Text.UTF8Encoding]::new($false))
```

### To save a file as ANSI/System Default (for CMD batch files)

```powershell
# On zh-TW Windows, this = CP 950 (Big5)
[System.IO.File]::WriteAllText("C:\path\to\file.bat", $content, [System.Text.Encoding]::Default)
```

### To read an existing file's encoding

```powershell
$b = [System.IO.File]::ReadAllBytes("C:\path\to\file")
if ($b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF) { "UTF-8 with BOM" }
elseif ($b[0] -eq 0xFF -and $b[1] -eq 0xFE) { "UTF-16 LE" }
else { "UTF-8 without BOM or ANSI" }
```

## Creating Windows Shortcuts Programmatically

```powershell
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut([Environment]::GetFolderPath("Desktop") + "\MyApp.lnk")
$s.TargetPath = "powershell.exe"
$s.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"C:\path\to\script.ps1`""
$s.WorkingDirectory = "C:\path\to\workdir"
$s.WindowStyle = 1  # 1=Normal, 3=Maximized, 7=Minimized
$s.Description = "My App Launcher"
$s.Save()
```

## The PowerShell Menu Launcher Pattern

For tool launchers and control panels, prefer a structured PowerShell script over CMD batch files:

```powershell
# Structure: functions for each action + main loop with switch

function Show-Menu {
    Clear-Host
    Write-Host "═" * 50 -ForegroundColor Cyan
    Write-Host "  Title" -ForegroundColor Yellow
    Write-Host "═" * 50 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1.  Action label" -ForegroundColor Green
    Write-Host "  0.  Exit" -ForegroundColor Red
    Write-Host ""
    Write-Host "═" * 50 -ForegroundColor Cyan
}

function Start-ActionOne {
    Write-Host "⏳ Starting..." -ForegroundColor Yellow
    # External command
    cmd /c "some_command"
    # Key reader (not `pause` which is CMD-only)
    Write-Host "`nPress any key to continue..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Main loop
while ($true) {
    Show-Menu
    $choice = Read-Host "`nEnter number (0-16)"

    switch ($choice) {
        "1"  { Start-ActionOne }
        "0"  {
            Clear-Host
            Write-Host "Goodbye!" -ForegroundColor Yellow
            exit 0
        }
        default {
            Write-Host "Invalid choice" -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
}
```

### Key design decisions

| Decision | Why |
|----------|-----|
| `Read-Host` with ASCII prompt | Avoids `set /p` encoding bugs. Language text goes in `Write-Host` output only. |
| Functions per action | Keeps the switch statement readable. Each function is independently testable. |
| `$Host.UI.RawUI.ReadKey(...)` | PowerShell equivalent of `pause`. Works on all Windows versions. |
| `cmd /c` for external commands | Bridges to WSL, legacy .bat tools. Use full paths to avoid working-directory issues. |
| `Start-Process` for new windows | Opens browser, new terminal, or external apps without blocking the menu loop. |

## Creating Windows Shortcuts Programmatically

PowerShell can create proper `.lnk` files via COM — avoids the "flash" bug of CMD wrappers:

```powershell
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut([Environment]::GetFolderPath("Desktop") + "\AppName.lnk")
$s.TargetPath = "powershell.exe"
$s.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"C:\path\to\script.ps1`""
$s.WorkingDirectory = "C:\path\to\workdir"
$s.WindowStyle = 1
$s.Description = "Description"
$s.Save()
```

To verify an existing shortcut:
```powershell
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("C:\path\to\shortcut.lnk")
$s.TargetPath   # what it launches
$s.Arguments    # arguments passed
$s.WorkingDirectory  # working dir
```

## Verification Checklist

**CRITICAL: Always verify before presenting as done.** The user will immediately notice if it doesn't work.

Before presenting a Windows automation fix as done:

- [ ] Run the script/tool yourself and confirm it starts without errors
- [ ] Verify Chinese characters display correctly (not garbled)
- [ ] Verify user input (`Read-Host` / `set /p`) captures input correctly
- [ ] Test at least one function/tool launch option — confirm it actually runs, not just shows a message
- [ ] Confirm the window stays open until user action (no flash)
- [ ] Test the exit/close behavior
- [ ] **Show actual output to the user** (screenshot, copy-paste of terminal output) — don't just say "it works"
- [ ] For shortcut-based tools: verify the shortcut's TargetPath and Arguments point to the correct locations

## Pitfalls

- **`cmd /c` from git-bash (MSYS) translates to `C:\`** — MSYS automatically converts POSIX-style arguments. `cmd.exe /c "command"` becomes `cmd.exe C:\ "command"`. Always use `//c` instead: `cmd.exe //c "command"`. Alternatively, set `MSYS2_ARG_CONV_EXCL="*"` before the command.\n- **Encoding mismatch in git-bash pipes** — When running `cmd.exe` from git-bash, output is in CP950 (Big5) but git-bash reads UTF-8. Pipe through `iconv -f CP950 -t UTF-8` to fix. See `windows-env-diagnostics` skill for complete .bashrc helper functions (`cmd_utf8`, `cmd2`, `cmd_cp`).\n- **`start ""` launches a new window** — the original window flashes closed. Use `call` or a Windows .lnk shortcut instead.
- **`cmd /c` from PowerShell** returns control to PowerShell. Use `cmd /k` to keep the CMD window open for interactive tools.
- **Emoji in file paths** work on Windows 10/11 with UTF-8 but may cause issues in some CMD commands. PowerShell handles them correctly.
- **`WriteAllText` with `Encoding::Default`** on newer Windows 11 builds may return UTF-8 (65001) if the "Beta: Use Unicode UTF-8" feature is enabled. Always check with `[System.Text.Encoding]::Default.EncodingName`.
