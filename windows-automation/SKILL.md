---
name: windows-automation
description: "PowerShell automation on Windows: tool launchers, encoding handling, replacing CMD batch files."
status: stable
---
# windows-automation

## 📖 Description

PowerShell automation on Windows: tool launchers, encoding handling, replacing CMD batch files.

---

# Windows Automation (PowerShell)

## Overview

Windows CMD batch files (.bat/.cmd) are a legacy technology with fundamental limitations. For any interactive tool, menu-driven script, or Chinese-language UI on Windows, **use PowerShell (.ps1) instead**.

PowerShell handles UTF-8 natively, has proper input handling (`Read-Host`), structured error handling, and works with Windows Terminal for full Unicode/emoji support.

## When to Use

- Building tool launchers or menu-driven scripts on Windows
- Any script that needs Chinese/Traditional Chinese text display
- Replacing legacy CMD batch files that have encoding or input issues
- System administration tasks (service management, registry edits)
- Wrapping WSL commands for Windows desktop access

## When NOT to Use

- One-shot commands (use a direct command or shortcut)
- Cross-platform scripts (use Python or shell script)
- The task is already handled by the PowerShell launcher

## Core Principles

### 1. PowerShell Over CMD Batch

| Feature | CMD (.bat/.cmd) | PowerShell (.ps1) |
|---------|----------------|-------------------|
| UTF-8/Chinese | Requires `chcp 65001` which breaks `set /p` | Native — no workarounds needed |
| User input | `set /p` — breaks with non-ASCII prompts | `Read-Host` — works with any characters |
| Menu/flow | `goto` labels — fragile | `switch` + functions — structured |
| Error handling | `if errorlevel` — manual | `try/catch` + `$LASTEXITCODE` |
| Emoji display | ❌ | ✅ |
| Calling WSL | `wsl command` via CMD | `cmd /c "wsl command"` or direct |

**Default choice:** PowerShell. Only fall back to CMD for trivial single-command wrappers.

### 2. Launching from Desktop

Create a Windows shortcut (.lnk) that runs:
```
Target: powershell.exe
Args: -NoProfile -ExecutionPolicy Bypass -File "path\to\script.ps1"
```

Use PowerShell to create the shortcut:
```powershell
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("$env:USERPROFILE\Desktop\🚀 Launcher.lnk")
$s.TargetPath = "powershell.exe"
$s.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "C:\path\to\launcher.ps1"'
$s.WorkingDirectory = "C:\path\to"
$s.WindowStyle = 1
$s.Save()
```

**⚠️ Emoji limitation:** The COM `CreateShortcut` uses ANSI (CP950) APIs internally. Emoji in the shortcut filename or in `Arguments`/`WorkingDirectory` paths will be silently degraded to `??` (`3f 00 3f 00` in the LNK binary). For emoji paths, use either:
- **Create at ASCII temp path, rename afterward** (for the filename)
- **Binary patch** the LNK file to restore surrogate pairs (for internal paths)
See `windows-env-diagnostics` skill → "Shortcut (.lnk) Repair — Emoji Path Workaround".

### 3. Encoding on zh-TW Windows

On Traditional Chinese Windows:
- System OEM code page = **950 (Big5)**
- If "Beta: Use Unicode UTF-8" is enabled (common on Win11 builds): OEM = **65001 (UTF-8)**
- PowerShell uses .NET strings (UTF-16 internally) — encoding is handled transparently
- Always save .ps1 files as **UTF-8 with BOM** (PowerShell default) or **UTF-8 without BOM** (works)

### 4. Registry Fixes for Terminal

For reliable UTF-8 display in the console:
```powershell
# Register Consolas for CP 65001 (HKLM — needs admin)
New-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Console' -Name '65001' -Value 'Consolas' -PropertyType String -Force

# Enable ANSI escape codes
New-ItemProperty -Path 'HKCU:\Console' -Name 'VirtualTerminalLevel' -Value 1 -PropertyType DWord -Force

# Set Windows Terminal as default
New-ItemProperty -Path 'HKCU:\Console' -Name 'EnableWindowsTerminalControl' -Value 1 -PropertyType DWord -Force

# Per-user CMD defaults
$cmdKey = 'HKCU:\Console\%SystemRoot%_system32_cmd.exe'
New-Item -Path $cmdKey -Force | Out-Null
New-ItemProperty -Path $cmdKey -Name 'CodePage' -Value 65001 -PropertyType DWord -Force
New-ItemProperty -Path $cmdKey -Name 'FaceName' -Value 'Consolas' -PropertyType String -Force
New-ItemProperty -Path $cmdKey -Name 'FontFamily' -Value 54 -PropertyType DWord -Force
```

## PowerShell Menu-Driven Launcher Template

See `templates/launcher.ps1` for a complete template.

Key structure:
```powershell
function Show-Menu {
    Clear-Host
    Write-Host "═" * 50 -ForegroundColor Cyan
    Write-Host "     Title" -ForegroundColor Yellow
    Write-Host "═" * 50 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [Section]" -ForegroundColor Green
    Write-Host "    1.  Option"
    Write-Host ""
    Write-Host "  [Other]"
    Write-Host "    0.  Exit"
    Write-Host ""
    Write-Host "═" * 50 -ForegroundColor Cyan
}

function Start-Option1 {
    Write-Host "`nStarting..." -ForegroundColor Yellow
    # Execute action
    Write-Host "[OK] Done" -ForegroundColor Green
}

while ($true) {
    Show-Menu
    $choice = Read-Host "`nEnter number"
    switch ($choice) {
        "1"  { Start-Option1 }
        "0"  { exit 0 }
        default { Write-Host "Invalid" -ForegroundColor Red; Start-Sleep 2 }
    }
}
```

## Pitfalls

### ❌ DO NOT use CMD for interactive tools
- `chcp 65001` has a known bug that breaks `set /p` input
- Batch files cannot properly display Chinese/emoji
- `goto`-based menus are fragile and hard to debug

### ❌ DO NOT put Chinese text in `set /p` prompts
Even if `chcp 65001` works, the prompt text can corrupt the input buffer.

### ❌ DO NOT use `start ""` in CMD shortcuts
Creates a second window; the original flashes and closes. Use `call` + `pause` or switch to PowerShell.

### ❌ DO NOT skip testing
After writing any automation script, test it by running it once in a non-interactive mode to verify it starts, displays correctly, and processes input.

## PowerShell Patterns for Reliable Scripts

### "Press Any Key" — PowerShell native (no cmd /c pause)

```powershell
# Instead of: cmd /c "pause"
Write-Host "`n按任意鍵繼續..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
```

This stays entirely in PowerShell, avoids the `cmd /c` overhead, and works with any character encoding.

### Checking if a CLI tool is available

```powershell
$tool = Get-Command "toolname" -ErrorAction SilentlyContinue
if ($tool) {
    # Tool exists, use it
    cmd /c "toolname"
} else {
    Write-Host "❌ [錯誤] 找不到 toolname 指令" -ForegroundColor Red
}
```

### Syntax-checking a PowerShell script

```powershell
$path = "C:\path\to\script.ps1"
$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile($path, [ref] $tokens, [ref] $errors)
if ($errors.Count -eq 0) {
    Write-Host "[OK] Syntax: NO ERRORS ($($tokens.Count) tokens)" -ForegroundColor Green
}
```

Always run this before delivering a PowerShell script.

### Multi-level submenu structure

```powershell
function Start-SubSection {
    while ($true) {
        Clear-Host
        Write-Host "  a.  Option A"
        Write-Host "  b.  Option B"
        Write-Host "  q.  Back"
        $s = Read-Host "Choice"
        switch ($s) {
            "a" { # action + "press any key"
                  $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
            "b" { # action + "press any key" }
            "q" { break }
            default { Write-Host "❌ Invalid" -ForegroundColor Red; Start-Sleep 1 }
        }
    }
}
```

### Launching a CMD tool from PowerShell

```powershell
# For tools that need to run interactively in a new window:
Start-Process cmd -ArgumentList "/k title MyTool && cd /d C:\path && call tool.bat"

# For tools that run and return (blocking):
cmd /c "tool command"
```

### Cleaning up after yourself

Always remove temporary `.ps1` helper files created during the session. The user's desktop should not be littered with intermediate scripts.

## Verification (User Expectation)

This user DEMANDS real verification. Follow this checklist before presenting any work as done:

1. **Check syntax** using PowerShell parser API (for .ps1 files)
2. **Run the script briefly** to confirm it starts and displays correctly — show actual output
3. **Test at least one function path** — menu → select item → confirm action executes
4. **Test exit behavior** — confirm the script exits cleanly
5. **Show the user real terminal output**, not a description
6. **If it fails**, report the actual error — never fabricate successful output

> ⚠️ The user will call you out if you claim something works without proving it. 'I will test' is not acceptable — test now, in this turn, and show the result.

## Templates

- `templates/launcher.ps1` — Complete PowerShell tool launcher template with multi-level submenus, Chinese/English text, Read-Host input, switch routing, error handling, press-any-key pattern, syntax-checked.

## References

- `references/cmd-encoding-research.md` — Research findings on CMD encoding bugs, chcp 65001 issues, and font configuration
