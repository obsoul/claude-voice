#!/bin/bash
# claude-voice installer for macOS
# Run with: bash install.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="$HOME/.claude-voice"
SKILL_DIR="$HOME/.claude/skills/voice"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/com.claude-voice.plist"

echo ""
echo "  claude-voice installer for macOS"
echo "  ================================="
echo ""

# 1. Check Python
if ! command -v python3 &>/dev/null; then
    echo "  [ERROR] Python 3 not found."
    echo "  Install it from https://python.org or run: brew install python"
    exit 1
fi

PYVER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  [OK] Python $PYVER found"

# 2. Install dependencies
echo ""
echo "  Installing Python dependencies..."
pip3 install -r "$REPO_DIR/requirements.txt" --quiet
echo "  [OK] Dependencies installed"

# 3. Create config
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    cp "$REPO_DIR/config.yaml" "$CONFIG_DIR/config.yaml"
    echo "  [OK] Config created at $CONFIG_DIR/config.yaml"
else
    echo "  [OK] Config already exists (not overwritten)"
fi

# 4. Install Claude Code skill
mkdir -p "$SKILL_DIR"
sed "s|<path-to-claude-voice>|$REPO_DIR|g" "$REPO_DIR/SKILL.md" > "$SKILL_DIR/SKILL.md"
echo "  [OK] Claude Code skill installed at $SKILL_DIR/SKILL.md"

# 5. Pre-download Whisper model
echo ""
echo "  Pre-downloading Whisper 'tiny' model (~39 MB)..."
python3 -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu', compute_type='int8')" 2>/dev/null
echo "  [OK] Model ready"

# 6. Grant Accessibility permission reminder
echo ""
echo "  [IMPORTANT] macOS Accessibility Permission"
echo "  The hotkey listener needs Accessibility access to detect global key presses."
echo "  When prompted, go to:"
echo "  System Settings -> Privacy & Security -> Accessibility"
echo "  and enable your Terminal (or iTerm2)."
echo ""

# 7. Install launchd startup agent
echo "  Installing startup agent (auto-launch at login)..."
mkdir -p "$PLIST_DIR"
PYTHON_PATH=$(which python3)

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude-voice</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$REPO_DIR/main.py</string>
        <string>hotkey</string>
        <string>--autostart</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$CONFIG_DIR/claude-voice.log</string>
    <key>StandardErrorPath</key>
    <string>$CONFIG_DIR/claude-voice.log</string>
</dict>
</plist>
EOF

launchctl load "$PLIST_PATH" 2>/dev/null || true
echo "  [OK] Startup agent installed — claude-voice will launch at every login"

echo ""
echo "  Installation complete!"
echo ""
echo "  How to use:"
echo ""
echo "    Hold Ctrl+Shift+Space anywhere to record"
echo "    Release to transcribe and paste"
echo ""
echo "    Or type /voice inside Claude Code"
echo ""
echo "    Edit config: open $CONFIG_DIR/config.yaml"
echo "    View logs:   tail -f $CONFIG_DIR/claude-voice.log"
echo ""
