# VoiceGreeter v2 — Kokoro Neural TTS Edition

A **lightweight Linux login greeter** that speaks in a natural, active, feminine AI voice using the **Kokoro 82M** neural TTS model.

> *"Good morning, sir! I ran a full diagnostic while you slept. Everything is fine. You're welcome."*

---

## What's New in v2

| Feature | v1 (espeak) | v2 (Kokoro) |
|---------|------------|-------------|
| Voice quality | Robotic, monotone | Natural neural AI voice |
| Voice model | espeak-ng | **Kokoro 82M** (open-weight) |
| Fallback | spd-say | Piper → espeak-ng |
| Greeting style | Static phrases | **Rotating persona lines** |
| Personas | none | Friday / Calm / Anime / WatchMojo |
| Context hints | none | Battery & Wi-Fi announcements |
| CLI tools | `--diagnose` | `--diagnose` `--preview` `--set-persona` `--set-voice` |

---

## Voice Engine — Kokoro 82M

[Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) is an open-weight 82M parameter TTS model that produces quality comparable to much larger models and runs fully offline on CPU.

Available voices (American English):

| Voice ID | Character |
|----------|-----------|
| `af_heart` | Warm, friendly *(default)* |
| `af_sky` | Bright, bubbly, energetic |
| `af_nova` | Confident, clear |
| `bf_emma` | British feminine |

---

## Personas

| Persona | Style | Sample line |
|---------|-------|-------------|
| `friday` | Iron Man's FRIDAY — witty, professional | *"Good morning, sir! Systems online. Coffee is your problem."* |
| `calm` | Minimal, clean | *"Good morning, sir."* |
| `anime` | Energetic, playful | *"Ohayou, senpai! The main character has logged in!"* |
| `watchmojo` | Narrator energy | *"Good morning! Number one on today's list: you, logging in."* |

---

## Installation

```bash
git clone https://github.com/varunsukumar060/voice-greeter.git
cd voice-greeter
chmod +x install.sh
./install.sh
```

The installer creates a Python venv, installs Kokoro, and sets up systemd + autostart.

---

## CLI Commands

```bash
# Full audio + engine diagnostic
python3 ~/.config/voice-greeter/greeter.py --diagnose

# Preview all personas AND all Kokoro voices
python3 ~/.config/voice-greeter/greeter.py --preview

# Switch persona
python3 ~/.config/voice-greeter/greeter.py --set-persona anime

# Switch Kokoro voice
python3 ~/.config/voice-greeter/greeter.py --set-voice af_sky

# Trigger greeting manually
python3 ~/.config/voice-greeter/greeter.py
```

---

## config.json

Located at `~/.config/voice-greeter/config.json`:

```json
{
  "engine":       "kokoro",
  "kokoro_voice": "af_heart",
  "persona":      "friday",
  "context_hints": true,
  "silent_after_first": false
}
```

| Key | Options | Description |
|-----|---------|-------------|
| `engine` | `kokoro` `piper` `espeak` | Primary TTS engine |
| `kokoro_voice` | `af_heart` `af_sky` `af_nova` `bf_emma` | Kokoro voice character |
| `persona` | `friday` `calm` `anime` `watchmojo` | Greeting line style |
| `context_hints` | `true`/`false` | Announce battery/Wi-Fi |
| `silent_after_first` | `true`/`false` | Only greet once per power-on |

---

## Engine Fallback Chain

```
Kokoro 82M → Piper TTS → espeak-ng
```

---

## Uninstall

```bash
./uninstall.sh
```

---

## License

MIT — do whatever you want with it!
