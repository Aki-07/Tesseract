from typing import Dict
import asyncio


battle_tasks:Dict[str,asyncio.Task] = {}
battle_states: Dict[str, dict] = {}