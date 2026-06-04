#!/bin/bash
echo "Removing VoiceGreeter..."
systemctl --user disable --now voice-greeter.service 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/voice-greeter.service"
rm -f "$HOME/.config/autostart/voice-greeter.desktop"
sudo rm -f /lib/systemd/system-sleep/voice-greeter-sleep-hook
rm -rf "$HOME/.config/voice-greeter"
systemctl --user daemon-reload
echo "VoiceGreeter removed."
