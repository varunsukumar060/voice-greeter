#!/usr/bin/env python3
"""
VoiceGreeter - Lightweight background greeting daemon
Greets Varun with a feminine, human-tone voice on login/boot.

v1.1 - Speed/lag fix:
  - espeak-ng now pipes audio to sox for real-time speed/pitch correction
  - Added config.json for easy tuning without editing code
  - Added --diagnose flag for audio self-test
  - Smarter audio wait (pipewire + pulseaudio)
"""

import subprocess
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "voice-greeter"
STATE_FILE = CONFIG_DIR / "state.json"
LOG_FILE   = CONFIG_DIR / "greeter.log"
CONFIG_FILE = CONFIG_DIR / "config.json"

# --- Default voice config (edit config.json to override) ---
DEFAULT_CONFIG = {
    "voice":   "en-us+f3",  # espeak-ng voice variant
    "speed":   160,          # words per minute (default espeak is 175; lower = slower)
    "pitch":   62,           # 0-99, higher = more feminine
    "volume":  180,          # 0-200
    "tempo":   1.25,         # sox speed multiplier (1.0 = normal, 1.25 = fix 0.8x lag)
    "use_sox": True          # pipe through sox for speed correction
}

def log(msg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        return {**DEFAULT_CONFIG, **cfg}
    except Exception:
        return DEFAULT_CONFIG.copy()

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
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def is_return_session(state):
    return state.get("greeted_once", False)

def has_sox():
    try:
        subprocess.run(["sox", "--version"], capture_output=True, timeout=3)
        return True
    except FileNotFoundError:
        return False

def speak_with_sox(text, cfg):
    """
    espeak-ng -> raw WAV on stdout -> sox speed correction -> aplay
    This fixes the 0.7x/0.8x playback speed issue caused by PulseAudio
    sample rate mismatch with espeak-ng's default 22050Hz output.
    """
    espeak_cmd = [
        "espeak-ng",
        "-v", cfg["voice"],
        "-s", str(cfg["speed"]),
        "-p", str(cfg["pitch"]),
        "-a", str(cfg["volume"]),
        "--stdout",   # output raw WAV to stdout
        text
    ]
    # sox: read stdin WAV, apply tempo (no pitch shift), output to stdout
    # then pipe to aplay
    sox_cmd = [
        "sox",
        "-t", "wav", "-",          # input: wav from stdin
        "-t", "wav", "-",          # output: wav to stdout
        "tempo", str(cfg["tempo"]) # speed up without pitch change
    ]
    aplay_cmd = ["aplay", "-q", "-"]

    try:
        p1 = subprocess.Popen(espeak_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        p2 = subprocess.Popen(sox_cmd, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        p1.stdout.close()
        p3 = subprocess.Popen(aplay_cmd, stdin=p2.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p2.stdout.close()
        p3.wait(timeout=15)
        p1.wait()
        p2.wait()
        log(f"Spoke via espeak-ng|sox|aplay (tempo={cfg['tempo']})")
        return True
    except Exception as e:
        log(f"sox pipe failed: {e}")
        # Kill any lingering processes
        for p in [p1, p2, p3]:
            try: p.kill()
            except Exception: pass
        return False

def speak_direct(text, cfg):
    """Direct espeak-ng without sox (fallback)."""
    cmd = [
        "espeak-ng",
        "-v", cfg["voice"],
        "-s", str(cfg["speed"]),
        "-p", str(cfg["pitch"]),
        "-a", str(cfg["volume"]),
        text
    ]
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=15)
        log("Spoke via espeak-ng direct")
        return True
    except Exception as e:
        log(f"espeak-ng direct failed: {e}")
        return False

def speak_spd(text):
    try:
        subprocess.run(["spd-say", "-r", "-5", "-p", "20", text],
                       check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=15)
        log("Spoke via spd-say")
        return True
    except Exception:
        return False

def speak(text, cfg):
    log(f"Speaking: '{text}'")
    if cfg.get("use_sox") and has_sox():
        if speak_with_sox(text, cfg):
            return
        log("sox pipe failed, falling back to direct espeak-ng")
    if speak_direct(text, cfg):
        return
    if speak_spd(text):
        return
    log("ERROR: All TTS engines failed. Install espeak-ng + sox + aplay (alsa-utils).")

def wait_for_audio(max_wait=20):
    """Wait for PipeWire or PulseAudio to be ready."""
    for i in range(max_wait):
        for cmd in [["pactl", "info"], ["pw-cli", "info"]]:
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=3)
                if r.returncode == 0:
                    log(f"Audio ready via {cmd[0]} after {i}s")
                    return True
            except Exception:
                continue
        time.sleep(1)
    log("Warning: audio server not detected after waiting, proceeding anyway")
    return False

def diagnose():
    """Run a quick audio/TTS self-diagnostic. Call with: python3 greeter.py --diagnose"""
    print("=== VoiceGreeter Diagnostic ===")
    # Check espeak-ng
    r = subprocess.run(["espeak-ng", "--version"], capture_output=True)
    print(f"espeak-ng: {'OK' if r.returncode == 0 else 'NOT FOUND'}")
    # Check sox
    r = subprocess.run(["sox", "--version"], capture_output=True)
    print(f"sox:       {'OK' if r.returncode == 0 else 'NOT FOUND — install: sudo apt install sox'}")
    # Check aplay
    r = subprocess.run(["aplay", "--version"], capture_output=True)
    print(f"aplay:     {'OK' if r.returncode == 0 else 'NOT FOUND — install: sudo apt install alsa-utils'}")
    # Check pactl
    r = subprocess.run(["pactl", "info"], capture_output=True)
    print(f"pactl:     {'OK — audio server running' if r.returncode == 0 else 'NOT running'}")
    # Load config
    cfg = load_config()
    print(f"\nConfig: {json.dumps(cfg, indent=2)}")
    print("\nPlaying test phrase...")
    speak("Good morning, sir!", cfg)
    print("Done. If it sounded slow, increase tempo in config.json")
    print(f"Config file: {CONFIG_FILE}")

def main():
    if "--diagnose" in sys.argv:
        diagnose()
        return

    log("--- VoiceGreeter v1.1 started ---")
    cfg   = load_config()
    state = load_state()

    wait_for_audio()
    time.sleep(0.5)

    hour   = get_time_of_day()
    period = get_greeting(hour)

    if is_return_session(state):
        message = "Welcome back, sir!"
    else:
        message = f"Good {period}, sir!"

    speak(message, cfg)

    state["greeted_once"] = True
    state["last_greeted"] = datetime.now().isoformat()
    save_state(state)
    log(f"Done. Message: '{message}'")

if __name__ == "__main__":
    main()
