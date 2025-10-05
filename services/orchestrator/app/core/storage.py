import os
import json
import logging
from pathlib import Path
from .state import battle_states

logger = logging.getLogger("tesseract.storage")

# ------------------------------------------------------------------------------
# Use absolute path /data by default (matches docker-compose volume)
# ------------------------------------------------------------------------------

DEFAULT_DATA_DIR = "/data"  # always volume-mounted in docker-compose
DATA_DIR = os.getenv("DATA_DIR", DEFAULT_DATA_DIR)
BATTLES_DIR = Path(DATA_DIR) / "battles"
BATTLES_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"[storage] Using BATTLES_DIR={BATTLES_DIR}")

# ------------------------------------------------------------------------------
# Save battle state
# ------------------------------------------------------------------------------
def save_battle_state(run_id: str):
    """Persist current in-memory battle_states[run_id] to /data/battles/{run_id}.json."""
    try:
        state = battle_states.get(run_id)
        if state is None:
            logger.warning("save_battle_state: no state for run_id %s", run_id)
            return

        path = BATTLES_DIR / f"{run_id}.json"
        path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
        logger.info("Saved battle state %s -> %s", run_id, path)
    except Exception as e:
        logger.exception("Failed to save battle state %s: %s", run_id, e)


# ------------------------------------------------------------------------------
# Load battle state
# ------------------------------------------------------------------------------
def load_battle_state(run_id: str):
    """Load persisted state if present."""
    path = BATTLES_DIR / f"{run_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.exception("Failed to load battle state %s: %s", run_id, e)
        return None
