import json
from pathlib import Path

STATE_FILE = Path(".prompt_state.json")

def save_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def clear_state():
    if STATE_FILE.exists():
        STATE_FILE.unlink()
