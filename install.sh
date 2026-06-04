#!/bin/bash
set -e

CYAN="\e[36m"; GREEN="\e[32m"; YELLOW="\e[33m"; RESET="\e[0m"

echo -e "${CYAN}=== VoiceGreeter Installer ===${RESET}"

# --- Install TTS engine ---
echo -e "${YELLOW}[1/5] Checking TTS engine...${RESET}"
if ! command -v espeak-ng &>/dev/null; then
    echo "Installing espeak-ng..."
    sudo apt-get update -qq && sudo apt-get install -y espeak-ng
else
    echo "espeak-ng already installed."
fi

# --- Copy files ---
echo -e "${YELLOW}[2/5] Installing files...${RESET}"
CONFIG_DIR="$HOME/.config/voice-greeter"
mkdir -p "$CONFIG_DIR"

cp greeter.py    "$CONFIG_DIR/greeter.py"
cp reset_state.py "$CONFIG_DIR/reset_state.py"
chmod +x "$CONFIG_DIR/greeter.py" "$CONFIG_DIR/reset_state.py"
echo "Files copied to $CONFIG_DIR"

# --- Systemd user service ---
echo -e "${YELLOW}[3/5] Setting up systemd user service...${RESET}"
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"
cp voice-greeter.service "$SERVICE_DIR/voice-greeter.service"
systemctl --user daemon-reload
systemctl --user enable voice-greeter.service
echo "Systemd user service enabled."

# --- Sleep hook ---
echo -e "${YELLOW}[4/5] Installing sleep/wake hook...${RESET}"
CURRENT_USER=$(whoami)
sudo cp sleep-hook.sh /lib/systemd/system-sleep/voice-greeter-sleep-hook
sudo sed -i "s/\$SUDO_USER/$CURRENT_USER/g" /lib/systemd/system-sleep/voice-greeter-sleep-hook
sudo chmod +x /lib/systemd/system-sleep/voice-greeter-sleep-hook
echo "Sleep hook installed."

# --- Logout hook (autostart) ---
echo -e "${YELLOW}[5/5] Adding session start autostart...${RESET}"
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/voice-greeter.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=VoiceGreeter
Exec=python3 $CONFIG_DIR/greeter.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=Feminine voice greeting on login
EOF
echo "Autostart .desktop entry created."

echo ""
echo -e "${GREEN}=== Installation Complete! ===${RESET}"
echo "VoiceGreeter will greet you on next login."
echo "Test it now: python3 ~/.config/voice-greeter/greeter.py"
