import json
import os
from pathlib import Path

class AppState:
    def __init__(self):
        self.data = {}
        self.load_state()

    def load_state(self):
        # We load the precomputed data JSON which acts as our in-memory engine state cache.
        # When refit is called, this JSON gets rebuilt.
        root = Path(__file__).resolve().parent.parent
        json_path = root / "simulator" / "aeriva_sim_data.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {}

state = AppState()
