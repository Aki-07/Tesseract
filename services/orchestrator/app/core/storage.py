import os
import json
import logging
from .state import battle_states

logger = logging.getLogger("tesseract.storage")

DEFAULT_DATA_DIR = os.path.join(os.getcwd(), "data")
DATA_DIR = os.path.abspath(os.getenv("DATA_DIR", DEFAULT_DATA_DIR))
BATTLES_DIR = os.path.join(DATA_DIR, "battles")
os.makedirs(BATTLES_DIR, exist_ok=True)


def save_battle_state(run_id: str):
    """Persist current in-memory battle_states[run_id] to /data/battles/{run_id}.json."""
    try:
        state = battle_states.get(run_id)
        if state is None:
            logger.warning("save_battle_state: no state for run_id %s", run_id)
            return
        path = os.path.join(BATTLES_DIR, f"{run_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
        logger.debug("Saved battle state %s -> %s", run_id, path)
    except Exception as e:
        logger.exception("Failed to save battle state %s: %s", run_id, e)


def load_battle_state(run_id: str):
    """Load persisted state if present."""
    path = os.path.join(BATTLES_DIR, f"{run_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.exception("Failed to load battle state %s: %s", run_id, e)
        return None
