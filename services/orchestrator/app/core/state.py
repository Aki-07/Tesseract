"""In-memory state shared across battle runners."""

from __future__ import annotations

import asyncio
from typing import Dict

battle_tasks: Dict[str, asyncio.Task] = {}
battle_states: Dict[str, dict] = {}
