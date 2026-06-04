# 🎤 VoiceGreeter

A **lightweight background daemon** for Linux that greets you in a warm, feminine voice every time you log in or wake your laptop.

> *"Good morning, sir!"* / *"Welcome back, sir!"*

---

## ✨ Features

- 🌅 **Time-aware greeting** — morning / afternoon / evening / night using **internet time** (worldtimeapi.org), with local time as fallback
- 🔁 **Session-aware** — says *"Welcome back, sir!"* on re-login or wake-from-sleep
- 💜 **Feminine, human-tone voice** — uses `espeak-ng` with tuned pitch/speed for natural sound
- 🪶 **Ultra-lightweight** — runs as a one-shot systemd user service, zero background CPU/RAM usage
- 😴 **Sleep/wake support** — detects laptop suspend and greets appropriately on resume
- 🔌 **Auto-start on boot** — systemd user service + XFCE autostart `.desktop` entry

---

## 🛠️ Requirements

- Linux with systemd (Ubuntu/Mint/Debian based)
- Python 3.8+
- `espeak-ng` (auto-installed by installer)
- PulseAudio or PipeWire (standard on most desktops)

---

## 📦 Installation

```bash
git clone https://github.com/varunsukumar060/voice-greeter.git
cd voice-greeter
chmod +x install.sh
./install.sh
```

> **Note:** The installer will ask for `sudo` only for installing `espeak-ng` and the sleep hook.

---

## 🧪 Test It

```bash
python3 ~/.config/voice-greeter/greeter.py
```

---

## 🗂️ File Structure

```
~/.config/voice-greeter/
├── greeter.py        ← Main greeting script
├── reset_state.py    ← Resets session state (called on sleep)
├── state.json        ← Tracks greeting state (auto-created)
└── greeter.log       ← Log file (auto-created)
```

---

## ⚙️ How It Works

| Event | Trigger | Greeting |
|-------|---------|----------|
| First login after boot | systemd user service | *"Good [time], sir!"* |
| Re-login / unlock | `.desktop` autostart | *"Welcome back, sir!"* |
| Wake from sleep | `/lib/systemd/system-sleep/` hook | *"Welcome back, sir!"* |

---

## 🎨 Customization

Edit `~/.config/voice-greeter/greeter.py` to change:

- **Voice**: Change `-v en-us+f3` to another espeak-ng voice variant
- **Speed**: `-s 145` (words per minute)
- **Pitch**: `-p 60` (0-99)
- **Messages**: Edit the `message` strings in `main()`

List available voices: `espeak-ng --voices | grep en`

---

## 🗑️ Uninstall

```bash
./uninstall.sh
```

---

## 📄 License

MIT License — do whatever you want with it!
