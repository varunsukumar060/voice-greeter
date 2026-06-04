#!/usr/bin/env python3
"""
VoiceGreeter v2 - Kokoro Neural TTS Edition
A lightweight login greeter with a natural, active, feminine AI voice.

Engine priority: Kokoro -> Piper -> espeak-ng (fallback)
Features:
  - Kokoro 82M neural TTS (af_heart / af_sky voices - bright & expressive)
  - Persona-style rotating greeting lines (Friday-inspired, humorous)
  - Time/session-aware greetings
  - Battery, Wi-Fi context add-ons
  - config.json for full customization
  - --diagnose and --preview flags
"""

import subprocess, sys, os, time, json, random
from datetime import datetime
from pathlib import Path

CONFIG_DIR  = Path.home() / ".config" / "voice-greeter"
STATE_FILE  = CONFIG_DIR / "state.json"
LOG_FILE    = CONFIG_DIR / "greeter.log"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "engine":       "kokoro",      # kokoro | piper | espeak
    "kokoro_voice": "af_heart",    # af_heart (warm) | af_sky (bright/bubbly) | af_nova | bf_emma
    "piper_model":  "en_US-jenny-diphone",
    "espeak_voice": "en-us+f3",
    "espeak_speed": 160,
    "espeak_pitch": 62,
    "volume":       90,
    "persona":      "friday",      # friday | calm | anime | watchmojo
    "context_hints": True,
    "silent_after_first": False
}

PERSONAS = {
    "friday": {
        "morning":   [
            "Good morning, sir! Systems are online. Coffee is your problem.",
            "Good morning, sir. Another day, another opportunity to be brilliant.",
            "Rise and shine, sir. Your laptop missed you. I did not, but it did.",
            "Good morning, sir! I ran a full diagnostic while you slept. Everything is fine. You're welcome.",
        ],
        "afternoon": [
            "Good afternoon, sir! Still coding or just pretending?",
            "Good afternoon, sir. The sun is out. Not that it matters in your terminal.",
            "Good afternoon! Hope lunch was worth the compile time.",
        ],
        "evening":   [
            "Good evening, sir. Working late again? Totally normal.",
            "Good evening! The night shift begins. I'll keep the logs warm.",
            "Good evening, sir. The bugs are patient. Are you?",
        ],
        "night":     [
            "It's quite late, sir. Even I have concerns.",
            "Good night, sir. Or good morning. I genuinely cannot tell anymore.",
            "Late night session, sir? The code will still be broken tomorrow. Rest up.",
        ],
        "welcome_back": [
            "Welcome back, sir! I kept everything from exploding.",
            "Welcome back! The terminal missed you. The bugs did too.",
            "Welcome back, sir. I monitored the system in your absence. All clear.",
            "Oh, you're back. The laptop was getting lonely.",
            "Welcome back, sir! No new kernel panics while you were gone. Progress!",
        ],
    },
    "calm": {
        "morning":      ["Good morning, sir."],
        "afternoon":    ["Good afternoon, sir."],
        "evening":      ["Good evening, sir."],
        "night":        ["Good night, sir."],
        "welcome_back": ["Welcome back, sir."],
    },
    "anime": {
        "morning":   [
            "Ohayou, senpai! A new day begins~ Let's make it legendary!",
            "Good morning, sir! The main character has logged in!",
        ],
        "afternoon": [
            "Konnichiwa, sir! Afternoon arc activated!",
            "Good afternoon! The plot thickens, sir~",
        ],
        "evening":   [
            "Konbanwa, sir! Evening mode: unlocked.",
            "Good evening, sir! The night arc begins~",
        ],
        "night":     [
            "Sir, it is way past midnight. Even the protagonist needs sleep.",
            "The final boss can wait, sir. Rest!",
        ],
        "welcome_back": [
            "Welcome back, senpai! I missed you!",
            "You have returned, sir! The adventure continues!",
        ],
    },
    "watchmojo": {
        "morning":   [
            "Good morning, sir! And welcome back to another day of epic productivity!",
            "Good morning! Number one on today's list: you, logging in.",
        ],
        "afternoon": [
            "Good afternoon, sir! Coming in at number one: your afternoon session!",
            "Good afternoon! And that's why this ranks in our top ten greetings!",
        ],
        "evening":   [
            "Good evening, sir! And at number one on our list: this very moment!",
            "Good evening! Before we begin, don't forget to log in. Oh wait, you did!",
        ],
        "night":     [
            "Good night, sir! And that wraps up today's top ten waking hours!",
            "It is late, sir. Number one reason to sleep: tomorrow's list.",
        ],
        "welcome_back": [
            "Welcome back, sir! And at number one: your triumphant return!",
            "Welcome back! Subscribe to your own productivity, sir!",
        ],
    }
}

def log(msg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

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

def get_time_of_day():
    try:
        import urllib.request
        with urllib.request.urlopen("http://worldtimeapi.org/api/ip", timeout=3) as r:
            data = json.loads(r.read().decode())
            hour = int(data.get("datetime", "")[11:13])
            log(f"Internet time hour: {hour}")
            return hour
    except Exception as e:
        log(f"Internet time failed, using local: {e}")
        return datetime.now().hour

def get_period(hour):
    if 5  <= hour < 12: return "morning"
    if 12 <= hour < 17: return "afternoon"
    if 17 <= hour < 21: return "evening"
    return "night"

def get_context_hint():
    hints = []
    try:
        r = subprocess.run(["cat", "/sys/class/power_supply/BAT0/capacity"],
                           capture_output=True, text=True, timeout=2)
        status_r = subprocess.run(["cat", "/sys/class/power_supply/BAT0/status"],
                                  capture_output=True, text=True, timeout=2)
        if r.returncode == 0:
            pct = int(r.stdout.strip())
            status = status_r.stdout.strip() if status_r.returncode == 0 else ""
            if pct <= 20 and "Discharging" in status:
                hints.append(f"Battery is at {pct} percent, sir. Plug in soon.")
            elif pct >= 95 and "Charging" in status:
                hints.append("Battery is fully charged, sir.")
    except Exception:
        pass
    try:
        r = subprocess.run(["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"],
                           capture_output=True, text=True, timeout=3)
        for line in r.stdout.splitlines():
            if line.startswith("yes:"):
                ssid = line.split(":", 1)[1].strip()
                hints.append(f"Connected to {ssid}.")
                break
        else:
            if r.returncode == 0:
                hints.append("No Wi-Fi connection detected, sir.")
    except Exception:
        pass
    return " ".join(hints)

def pick_line(persona_name, key):
    persona = PERSONAS.get(persona_name, PERSONAS["friday"])
    lines   = persona.get(key, PERSONAS["friday"].get(key, ["Hello, sir!"]))
    return random.choice(lines)

def build_message(cfg, state):
    period   = get_period(get_time_of_day())
    returned = state.get("greeted_once", False)
    key      = "welcome_back" if returned else period
    line     = pick_line(cfg["persona"], key)
    if cfg.get("context_hints") and returned:
        hint = get_context_hint()
        if hint:
            line = line.rstrip(".!") + ". " + hint
    return line

def speak_kokoro(text, cfg):
    script = f"""
import sys, io
try:
    from kokoro import KPipeline
    import soundfile as sf
    import numpy as np
    pipeline = KPipeline(lang_code='a')
    gen = pipeline(
        {repr(text)},
        voice={repr(cfg['kokoro_voice'])},
        speed=1.0,
        split_pattern=None
    )
    samples = []
    sr = 24000
    for _, _, audio in gen:
        samples.append(audio)
    if not samples:
        sys.exit(1)
    audio = np.concatenate(samples)
    buf = io.BytesIO()
    with sf.SoundFile(buf, mode='w', samplerate=sr, channels=1, format='WAV', subtype='PCM_16') as f:
        f.write(audio)
    sys.stdout.buffer.write(buf.getvalue())
except Exception as e:
    import traceback; traceback.print_exc(file=sys.stderr); sys.exit(1)
"""
    try:
        p1 = subprocess.Popen(
            [sys.executable, "-c", script],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        wav_data, err = p1.communicate(timeout=30)
        if p1.returncode != 0:
            log(f"Kokoro synthesis error: {err.decode()[:300]}")
            return False
        p2 = subprocess.Popen(
            ["aplay", "-q", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        p2.communicate(input=wav_data, timeout=20)
        log(f"Spoke via Kokoro ({cfg['kokoro_voice']})")
        return True
    except Exception as e:
        log(f"Kokoro speak failed: {e}")
        return False

def speak_piper(text, cfg):
    model_dir  = CONFIG_DIR / "piper"
    model_name = cfg.get("piper_model", "en_US-jenny-diphone")
    onnx_path  = model_dir / f"{model_name}.onnx"
    json_path  = model_dir / f"{model_name}.onnx.json"
    if not onnx_path.exists():
        log(f"Piper model not found: {onnx_path}")
        return False
    try:
        p1 = subprocess.Popen(
            ["piper", "--model", str(onnx_path), "--config", str(json_path), "--output-raw"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        p2 = subprocess.Popen(
            ["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
            stdin=p1.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        p1.stdout.close()
        p1.stdin.write(text.encode())
        p1.stdin.close()
        p2.wait(timeout=20)
        p1.wait()
        log(f"Spoke via Piper ({model_name})")
        return True
    except Exception as e:
        log(f"Piper failed: {e}")
        return False

def speak_espeak(text, cfg):
    try:
        subprocess.run(
            ["espeak-ng", "-v", cfg["espeak_voice"],
             "-s", str(cfg["espeak_speed"]),
             "-p", str(cfg["espeak_pitch"]),
             "-a", "180", text],
            check=True, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=15
        )
        log("Spoke via espeak-ng (fallback)")
        return True
    except Exception as e:
        log(f"espeak-ng failed: {e}")
        return False

def speak(text, cfg):
    log(f"Speaking: '{text}' | engine={cfg['engine']}")
    engine = cfg.get("engine", "kokoro")
    if engine == "kokoro":
        if speak_kokoro(text, cfg): return
        log("Kokoro failed, trying Piper...")
        if speak_piper(text, cfg): return
    elif engine == "piper":
        if speak_piper(text, cfg): return
        log("Piper failed, trying Kokoro...")
        if speak_kokoro(text, cfg): return
    speak_espeak(text, cfg)

def wait_for_audio(max_wait=20):
    for i in range(max_wait):
        for cmd in [["pactl", "info"], ["pw-cli", "info"]]:
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=3)
                if r.returncode == 0:
                    log(f"Audio ready ({cmd[0]}) after {i}s")
                    return True
            except Exception:
                continue
        time.sleep(1)
    log("Warning: audio server not confirmed, proceeding anyway")
    return False

def diagnose():
    print("=== VoiceGreeter v2 Diagnostic ===\n")
    def chk(name, cmd):
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=4)
            ok = r.returncode == 0
        except FileNotFoundError:
            ok = False
        status = "OK" if ok else "NOT FOUND"
        print(f"  {name:<20} {status}")
        return ok
    chk("python3",         ["python3", "--version"])
    has_kokoro = chk("kokoro (pip pkg)",  [sys.executable, "-c", "import kokoro"])
    chk("soundfile",       [sys.executable, "-c", "import soundfile"])
    chk("numpy",           [sys.executable, "-c", "import numpy"])
    has_piper  = chk("piper",             ["piper", "--version"])
    chk("aplay",           ["aplay", "--version"])
    chk("espeak-ng",       ["espeak-ng", "--version"])
    chk("pactl",           ["pactl", "info"])
    cfg = load_config()
    print(f"\n  Config: {CONFIG_FILE}")
    print(f"  Engine: {cfg['engine']}  |  Voice: {cfg['kokoro_voice']}  |  Persona: {cfg['persona']}")
    if not has_kokoro:
        print("\n  Install Kokoro:  pip install kokoro>=0.9.4 soundfile")
    if not has_piper:
        print("  Install Piper:   pip install piper-tts  (+ download model)")
    print("\n  Playing test phrase with current config...")
    speak("Hello sir, voice greeter diagnostics complete. Everything sounds great!", cfg)
    print("  Done.\n")

def preview_voices():
    cfg = load_config()
    print("=== Persona Preview ===\n")
    for pname in PERSONAS:
        line = pick_line(pname, "morning")
        print(f"  [{pname}] {line}")
        c = {**cfg, "persona": pname}
        msg = build_message(c, {})
        speak(msg, cfg)
        time.sleep(0.5)
    print("\n=== Kokoro Voice Preview ===\n")
    voices = ["af_heart", "af_sky", "af_nova", "bf_emma"]
    for v in voices:
        print(f"  Voice: {v}")
        c = {**cfg, "kokoro_voice": v}
        speak(f"Hello sir! This is the {v} voice. How does this sound?", c)
        time.sleep(0.5)

def set_persona(name):
    if name not in PERSONAS:
        print(f"Unknown persona '{name}'. Choose from: {', '.join(PERSONAS.keys())}")
        return
    cfg = load_config()
    cfg["persona"] = name
    save_config(cfg)
    print(f"Persona set to '{name}'. Updated {CONFIG_FILE}")

def set_voice(voice):
    cfg = load_config()
    cfg["kokoro_voice"] = voice
    save_config(cfg)
    print(f"Kokoro voice set to '{voice}'. Updated {CONFIG_FILE}")

def main():
    args = sys.argv[1:]
    if "--diagnose" in args:
        diagnose(); return
    if "--preview" in args:
        preview_voices(); return
    if "--set-persona" in args:
        idx = args.index("--set-persona")
        set_persona(args[idx + 1] if idx + 1 < len(args) else "friday"); return
    if "--set-voice" in args:
        idx = args.index("--set-voice")
        set_voice(args[idx + 1] if idx + 1 < len(args) else "af_heart"); return

    log("--- VoiceGreeter v2 started ---")
    cfg   = load_config()
    state = load_state()

    if cfg.get("silent_after_first") and state.get("greeted_once"):
        log("silent_after_first=True and already greeted. Exiting.")
        return

    wait_for_audio()
    time.sleep(0.4)

    message = build_message(cfg, state)
    speak(message, cfg)

    state["greeted_once"] = True
    state["last_greeted"] = datetime.now().isoformat()
    save_state(state)
    log(f"Done. Said: '{message}'")

if __name__ == "__main__":
    main()
