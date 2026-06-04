#!/usr/bin/env python3
"""Reset greeter state on logout or sleep so next login gives welcome-back."""
import json
from pathlib import Path

STATE_FILE = Path.home() / ".config" / "voice-greeter" / "state.json"
try:
    with open(STATE_FILE) as f:
        state = json.load(f)
    state["greeted_once"] = True   # marks that a session existed
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("State reset: next greeting will say 'Welcome back'.")
except Exception as e:
    print(f"Note: {e}")
