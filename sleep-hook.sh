#!/bin/bash
# /lib/systemd/system-sleep/voice-greeter-sleep-hook
# Resets greeting state on sleep so wake-up says "Welcome back"
case "$1" in
  pre)
    # Going to sleep — mark state so wake sounds welcoming
    su - "$SUDO_USER" -c "python3 ~/.config/voice-greeter/reset_state.py" 2>/dev/null || true
    ;;
  post)
    # Waking from sleep — trigger greeting
    uid=$(id -u "$SUDO_USER" 2>/dev/null || echo "1000")
    DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" \
    XDG_RUNTIME_DIR="/run/user/${uid}" \
    sudo -u "$SUDO_USER" \
      DISPLAY=:0 \
      DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" \
      XDG_RUNTIME_DIR="/run/user/${uid}" \
      python3 "/home/$SUDO_USER/.config/voice-greeter/greeter.py" &
    ;;
esac
