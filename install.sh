#!/bin/bash
# claude-voice installer for macOS and Linux
# Run with: bash install.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="$HOME/.claude-voice"
SKILL_DIR="$HOME/.claude/skills/voice"
OS=$(uname -s)

echo ""
echo "  claude-voice installer"
echo "  ======================"
echo "  Platform: $OS"
echo ""

# ------------------------------------------------------------------
# 1. Check Python
# ------------------------------------------------------------------
if ! command -v python3 &>/dev/null; then
    echo "  [ERROR] Python 3 not found."
    if [ "$OS" = "Darwin" ]; then
        echo "  Install from https://python.org or run: brew install python"
    else
        echo "  Install with: sudo apt install python3 python3-pip"
    fi
    exit 1
fi
PYVER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  [OK] Python $PYVER found"

# ------------------------------------------------------------------
# 2. Install system dependencies
# ------------------------------------------------------------------
if [ "$OS" = "Linux" ]; then
    echo ""
    echo "  Installing system dependencies..."

    if command -v apt &>/dev/null; then
        sudo apt install -y xdotool xclip python3-pip python3-dev 2>/dev/null
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y xdotool xclip python3-pip 2>/dev/null
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm xdotool xclip python-pip 2>/dev/null
    else
        echo "  [!] Could not detect package manager. Please install xdotool and xclip manually."
    fi
    echo "  [OK] System dependencies installed"
fi

# ------------------------------------------------------------------
# 3. Install Python packages
# ------------------------------------------------------------------
echo ""
echo "  Installing Python dependencies..."
pip3 install -r "$REPO_DIR/requirements.txt" --quiet

# pynput needs python-xlib on Linux for X11
if [ "$OS" = "Linux" ]; then
    pip3 install python-xlib --quiet 2>/dev/null || true
fi

echo "  [OK] Dependencies installed"

# ------------------------------------------------------------------
# 4. Create config
# ------------------------------------------------------------------
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    cp "$REPO_DIR/config.yaml" "$CONFIG_DIR/config.yaml"
    echo "  [OK] Config created at $CONFIG_DIR/config.yaml"
else
    echo "  [OK] Config already exists (not overwritten)"
fi

# ------------------------------------------------------------------
# 5. Install Claude Code skill
# ------------------------------------------------------------------
mkdir -p "$SKILL_DIR"
sed "s|<path-to-claude-voice>|$REPO_DIR|g" "$REPO_DIR/SKILL.md" > "$SKILL_DIR/SKILL.md"
echo "  [OK] Claude Code skill installed at $SKILL_DIR/SKILL.md"

# ------------------------------------------------------------------
# 6. Pre-download Whisper model
# ------------------------------------------------------------------
echo ""
echo "  Pre-downloading Whisper 'tiny' model (~39 MB)..."
python3 -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu', compute_type='int8')" 2>/dev/null
echo "  [OK] Model ready"

# ------------------------------------------------------------------
# 7. Auto-start at login
# ------------------------------------------------------------------
PYTHON_PATH=$(which python3)

if [ "$OS" = "Darwin" ]; then
    # macOS — launchd agent
    PLIST_DIR="$HOME/Library/LaunchAgents"
    PLIST_PATH="$PLIST_DIR/com.claude-voice.plist"
    mkdir -p "$PLIST_DIR"

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
    echo "  [OK] Startup agent installed (launchd)"

    # Accessibility permission reminder
    echo ""
    echo "  [IMPORTANT] macOS Accessibility Permission"
    echo "  Go to: System Settings -> Privacy & Security -> Accessibility"
    echo "  Add your Terminal app to grant hotkey access."

elif [ "$OS" = "Linux" ]; then
    # Linux — XDG autostart desktop file
    AUTOSTART_DIR="$HOME/.config/autostart"
    mkdir -p "$AUTOSTART_DIR"

    cat > "$AUTOSTART_DIR/claude-voice.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Claude Voice
Comment=Local Whisper voice dictation — push to talk
Exec=$PYTHON_PATH $REPO_DIR/main.py hotkey --autostart
Icon=$REPO_DIR/assets/tray_idle.png
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
    echo "  [OK] Startup entry installed (~/.config/autostart/claude-voice.desktop)"

    # Optional systemd user service
    SYSTEMD_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SYSTEMD_DIR"
    cat > "$SYSTEMD_DIR/claude-voice.service" << EOF
[Unit]
Description=Claude Voice Push-to-Talk
After=graphical-session.target

[Service]
Type=simple
ExecStart=$PYTHON_PATH $REPO_DIR/main.py hotkey --autostart
Restart=on-failure
RestartSec=5s
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
EOF
    systemctl --user enable claude-voice.service 2>/dev/null || true
    systemctl --user start claude-voice.service 2>/dev/null || true
    echo "  [OK] systemd user service installed (claude-voice.service)"

    # Wayland note
    echo ""
    echo "  [NOTE] Wayland users: global hotkeys require the compositor to allow"
    echo "  accessibility access. If the hotkey doesn't work, try running under X11."
fi

# ------------------------------------------------------------------
# Done
# ------------------------------------------------------------------
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
echo "    Edit config:  open $CONFIG_DIR/config.yaml"
echo "    View logs:    tail -f $CONFIG_DIR/claude-voice.log"
echo ""
