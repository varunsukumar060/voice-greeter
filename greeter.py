#!/usr/bin/env python3
"""
VoiceGreeter - Lightweight background greeting daemon
Greets Varun with a feminine, human-tone voice on login/boot.
"""

import subprocess
import sys
import os
import time
import json
import socket
from datetime import datetime
from pathlib import Path

STATE_FILE = Path.home() / ".config" / "voice-greeter" / "state.json"
LOG_FILE   = Path.home() / ".config" / "voice-greeter" / "greeter.log"

def log(msg):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

def get_time_of_day():
    """Get current hour from internet time (worldtimeapi), fallback to local."""
    try:
        import urllib.request
        with urllib.request.urlopen("http://worldtimeapi.org/api/ip", timeout=3) as r:
            data = json.loads(r.read().decode())
            dt_str = data.get("datetime", "")
            hour = int(dt_str[11:13])
            log(f"Internet time hour: {hour}")
            return hour
    except Exception as e:
        log(f"Internet time failed, using local: {e}")
        return datetime.now().hour

def get_greeting(hour):
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def is_return_session(state):
    """True if the user logged in before (not first boot of session)."""
    return state.get("greeted_once", False)

def speak(text):
    """
    Speak using espeak-ng with a feminine, warm voice.
    Falls back to festival or spd-say if unavailable.
    """
    log(f"Speaking: {text}")
    engines = [
        ["espeak-ng", "-v", "en-us+f3", "-s", "145", "-p", "60", "-a", "180", text],
        ["spd-say", "-r", "-10", "-p", "10", text],
        ["festival", "--tts"],
    ]
    for cmd in engines:
        try:
            if cmd[0] == "festival":
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                p.communicate(input=text.encode())
            else:
                subprocess.run(cmd, check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=15)
            log(f"Spoke via {cmd[0]}")
            return
        except (FileNotFoundError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired):
            continue
    log("ERROR: No TTS engine found. Install espeak-ng.")

def wait_for_audio(max_wait=20):
    """Wait for PulseAudio/PipeWire to be ready."""
    for _ in range(max_wait):
        result = subprocess.run(
            ["pactl", "info"], capture_output=True, timeout=3
        )
        if result.returncode == 0:
            return True
        time.sleep(1)
    return False

def main():
    log("--- VoiceGreeter started ---")
    state = load_state()

    # Wait for audio system (important on boot)
    wait_for_audio()
    time.sleep(1)  # tiny buffer for DE to fully settle

    hour   = get_time_of_day()
    period = get_greeting(hour)

    if is_return_session(state):
        message = "Welcome back, sir!"
    else:
        message = f"Good {period}, sir!"

    speak(message)

    state["greeted_once"] = True
    state["last_greeted"] = datetime.now().isoformat()
    save_state(state)
    log(f"Done. Message: {message}")

if __name__ == "__main__":
    main()
