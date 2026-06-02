# claude-voice installer for Windows
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"
$InstallDir = "$env:USERPROFILE\.claude-voice"
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host ""
Write-Host "  claude-voice installer" -ForegroundColor Cyan
Write-Host "  ======================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
try {
    $pyver = python --version 2>&1
    Write-Host "  [OK] Python found: $pyver" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python not found. Install Python 3.10+ from https://python.org" -ForegroundColor Red
    exit 1
}

# 2. Install dependencies
Write-Host ""
Write-Host "  Installing Python dependencies..." -ForegroundColor Yellow
pip install -r "$RepoDir\requirements.txt" --quiet
Write-Host "  [OK] Dependencies installed" -ForegroundColor Green

# 3. Create config directory and copy default config
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}
if (-not (Test-Path "$InstallDir\config.yaml")) {
    Copy-Item "$RepoDir\config.yaml" "$InstallDir\config.yaml"
    Write-Host "  [OK] Default config created at $InstallDir\config.yaml" -ForegroundColor Green
} else {
    Write-Host "  [OK] Config already exists at $InstallDir\config.yaml (not overwritten)" -ForegroundColor Green
}

# 4. Install the Claude Code skill
$SkillDir = "$env:USERPROFILE\.claude\skills\voice"
if (-not (Test-Path $SkillDir)) {
    New-Item -ItemType Directory -Path $SkillDir | Out-Null
}
$SkillContent = Get-Content "$RepoDir\SKILL.md" -Raw
# Patch the path into the skill
$SkillContent = $SkillContent -replace "<path-to-claude-voice>", $RepoDir
Set-Content -Path "$SkillDir\SKILL.md" -Value $SkillContent
Write-Host "  [OK] Claude Code skill installed at $SkillDir\SKILL.md" -ForegroundColor Green

# 5. Pre-download the Whisper model
Write-Host ""
Write-Host "  Pre-downloading Whisper 'base' model (~74 MB)..." -ForegroundColor Yellow
python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')" 2>&1
Write-Host "  [OK] Model ready" -ForegroundColor Green

Write-Host ""
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  How to use:" -ForegroundColor Cyan
Write-Host "    Tray app (system-wide hotkey):"
Write-Host "      python $RepoDir\main.py"
Write-Host ""
Write-Host "    Claude Code skill:"
Write-Host "      Type /voice in any Claude Code session"
Write-Host ""
Write-Host "    Edit config:"
Write-Host "      notepad $InstallDir\config.yaml"
Write-Host ""
