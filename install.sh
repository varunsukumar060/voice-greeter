#!/bin/bash
set -e

CYAN="\e[36m"; GREEN="\e[32m"; YELLOW="\e[33m"; RED="\e[31m"; RESET="\e[0m"

echo -e "${CYAN}"
echo "  VoiceGreeter v2 -- Kokoro Neural TTS Edition"
echo -e "${RESET}"

CONFIG_DIR="$HOME/.config/voice-greeter"
mkdir -p "$CONFIG_DIR"

# Step 1: System dependencies
echo -e "${YELLOW}[1/5] Installing system dependencies...${RESET}"
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-venv espeak-ng alsa-utils libsndfile1 network-manager 2>/dev/null || true

# Step 2: Python venv + Kokoro
echo -e "${YELLOW}[2/5] Setting up Python venv + Kokoro TTS...${RESET}"
VENV="$CONFIG_DIR/venv"
python3 -m venv "$VENV" --system-site-packages
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet "kokoro>=0.9.4" soundfile numpy

# Patch greeter.py shebang to use venv python
sed -i "1s|.*|#!$VENV/bin/python3|" greeter.py

# Step 3: Copy files
echo -e "${YELLOW}[3/5] Installing files...${RESET}"
cp greeter.py      "$CONFIG_DIR/greeter.py"
cp reset_state.py  "$CONFIG_DIR/reset_state.py"
chmod +x "$CONFIG_DIR/greeter.py" "$CONFIG_DIR/reset_state.py"

# Write default config.json
cat > "$CONFIG_DIR/config.json" <<EOF
{
  "engine":       "kokoro",
  "kokoro_voice": "af_heart",
  "piper_model":  "en_US-jenny-diphone",
  "espeak_voice": "en-us+f3",
  "espeak_speed": 160,
  "espeak_pitch": 62,
  "volume":       90,
  "persona":      "friday",
  "context_hints": true,
  "silent_after_first": false
}
EOF
echo "Config written to $CONFIG_DIR/config.json"

# Step 4: Systemd user service
echo -e "${YELLOW}[4/5] Setting up systemd user service...${RESET}"
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"
cp voice-greeter.service "$SERVICE_DIR/voice-greeter.service"
systemctl --user daemon-reload
systemctl --user enable voice-greeter.service

AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/voice-greeter.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=VoiceGreeter
Exec=$CONFIG_DIR/greeter.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=Feminine AI voice greeting on login (Kokoro)
EOF

# Step 5: Sleep hook
echo -e "${YELLOW}[5/5] Installing sleep/wake hook...${RESET}"
CURRENT_USER=$(whoami)
sudo cp sleep-hook.sh /lib/systemd/system-sleep/voice-greeter-sleep-hook
sudo sed -i "s/\$SUDO_USER/$CURRENT_USER/g" /lib/systemd/system-sleep/voice-greeter-sleep-hook
sudo chmod +x /lib/systemd/system-sleep/voice-greeter-sleep-hook

echo ""
echo -e "${GREEN}=== VoiceGreeter v2 Installed! ===${RESET}"
echo ""
echo "  Test now:      python3 $CONFIG_DIR/greeter.py --diagnose"
echo "  Preview voices: python3 $CONFIG_DIR/greeter.py --preview"
echo "  Set persona:   python3 $CONFIG_DIR/greeter.py --set-persona watchmojo"
echo "  Set voice:     python3 $CONFIG_DIR/greeter.py --set-voice af_sky"
