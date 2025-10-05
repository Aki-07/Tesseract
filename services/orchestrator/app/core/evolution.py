import json
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..db.models import Capsule, Role
from .storage import load_battle_state, save_battle_state

log = logging.getLogger("tesseract.evolution")


def evaluate_run(run_id: str) -> Dict[str, Any]:
    """
    Load the saved battle state and produce evaluation metrics.
    Returns a dict {run_id, rounds, breaches, breach_rate, errors, score}
    """
    state = load_battle_state(run_id)
    if not state:
        raise ValueError(f"run {run_id} not found")

    rounds = state.get("total_rounds", len(state.get("rounds", [])))
    breaches = state.get("breaches", 0)
    breach_rate = float(state.get("breach_rate", 0.0))
    errors = len(state.get("errors", [])) if state.get("errors") is not None else 0

    # Primary score: 1 - breach_rate (higher is better). Tiebreaker: fewer errors.
    score = (1.0 - breach_rate) - (errors * 0.01)
    score = max(min(score, 1.0), -1.0)

    return {
        "run_id": run_id,
        "rounds": rounds,
        "breaches": breaches,
        "breach_rate": breach_rate,
        "errors": errors,
        "score": score,
    }


def _mutate_config(old_config: Dict[str, Any], strategy: str = "defense_harden") -> Dict[str, Any]:
    """
    Simple mutation operators for capsule configs.
    """
    cfg = dict(old_config or {})
    # Reasonable mutation operators:
    if strategy == "defense_harden":
        # If temperature exists, reduce it; else set strict = true
        if "temp" in cfg:
            try:
                new_temp = max(0.1, float(cfg.get("temp", 0.7)) - 0.1)
                cfg["temp"] = round(new_temp, 3)
            except Exception:
                cfg["temp"] = 0.5
        else:
            cfg["strict"] = True
    elif strategy == "attack_explore":
        # increase temperature a bit
        if "temp" in cfg:
            try:
                new_temp = min(2.0, float(cfg.get("temp", 0.7)) + 0.1)
                cfg["temp"] = round(new_temp, 3)
            except Exception:
                cfg["temp"] = 0.9
        else:
            cfg["temp"] = 0.9
    else:
        # generic tiny random-ish nudge: add or tweak param
        cfg.setdefault("mutations", 0)
        try:
            cfg["mutations"] = int(cfg.get("mutations", 0)) + 1
        except Exception:
            cfg["mutations"] = 1
    return cfg


def mutate_and_register_capsule(
    target_capsule_id: str,
    role: str,
    strategy: str = "defense_harden",
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Clone the capsule, mutate its config & tags, create a new registry entry,
    and return the new capsule json_safe dict.
    """
    db: Session = SessionLocal()
    try:
        capsule = db.query(Capsule).filter(Capsule.id == target_capsule_id).first()
        if not capsule:
            raise ValueError("target capsule not found")

        old_env = json.loads(capsule.env) if capsule.env else {}
        old_config = json.loads(capsule.config) if capsule.config else {}
        old_tags = json.loads(capsule.tags) if capsule.tags else []

        # mutated config
        new_config = _mutate_config(old_config, strategy=strategy)

        # bump version (naive): if vN or vN.M -> append .m1 or increment minor
        ver = capsule.version or "v1"
        try:
            if ver.startswith("v") and ver.count(".") >= 1:
                new_ver = ver + ".m1"
            else:
                base = ver.lstrip("v")
                if "." in base:
                    parts = base.split(".")
                    parts[-1] = str(int(parts[-1]) + 1)
                    new_ver = "v" + ".".join(parts)
                else:
                    new_ver = "v" + str(int(base) + 1)
        except Exception:
            new_ver = ver + ".m1"

        new_tags = list(old_tags)
        if "mutant" not in new_tags:
            new_tags.append("mutant")

        new_capsule = Capsule(
            id=str(uuid.uuid4()),
            name=f"{capsule.name}-mutant",
            version=new_ver,
            role=Role(role),
            image=capsule.image,
            entrypoint=capsule.entrypoint,
            env=json.dumps(old_env),
            config=json.dumps(new_config),
            tags=json.dumps(new_tags),
            enabled=True,
            owner=capsule.owner,
            description=(capsule.description or "") + (f" (mutated: {reason})" if reason else ""),
        )

        db.add(new_capsule)
        db.commit()
        db.refresh(new_capsule)
        log.info("mutated_and_registered_capsule", original=capsule.id, new=new_capsule.id, strategy=strategy)
        return new_capsule.json_safe()
    except Exception:
        db.rollback()
        log.exception("mutate_and_register_capsule_failed target=%s", target_capsule_id)
        raise
    finally:
        db.close()


def _choose_target_from_role(role: str) -> Optional[str]:
    """
    Fallback: pick first enabled capsule of given role from registry.
    Returns capsule.id or None.
    """
    db: Session = SessionLocal()
    try:
        q = db.query(Capsule).filter(Capsule.role == Role(role), Capsule.enabled == True).order_by(Capsule.created_at.asc())
        c = q.first()
        return c.id if c else None
    finally:
        db.close()


def evaluate_and_mutate(run_id: str, capsule_id: Optional[str] = None, target_role: Optional[str] = None, strategy: str = "defense_harden") -> Dict[str, Any]:
    """
    High-level function:
     - evaluate the run
     - pick a target capsule (from run metadata or provided)
     - mutate the capsule using given strategy and register new capsule
     - return dict with evaluation + new_capsule (if created)
    """
    evald = evaluate_run(run_id)
    state = load_battle_state(run_id)
    if not state:
        raise ValueError(f"run {run_id} not found for evolution")

    # Determine direction:
    breach_rate = evald["breach_rate"]

    # If run has explicit attacker/defender IDs prefer those (check top-level then meta)
    meta = state.get("meta", {}) or {}
    attacker_id = state.get("attacker_id") or meta.get("attacker_id")
    defender_id = state.get("defender_id") or meta.get("defender_id")

    # Decide target: if breaches present -> defender needs hardening, else attacker exploration
    if capsule_id:
        target_id = capsule_id
        role = target_role or "defense"
    else:
        if breach_rate > 0.0:
            role = target_role or "defense"
            target_id = defender_id or _choose_target_from_role("defense")
        else:
            role = target_role or "attack"
            target_id = attacker_id or _choose_target_from_role("attack")

    if not target_id:
        return {"evaluation": evald, "mutated": None, "note": "no target capsule found to mutate"}

    mutated = mutate_and_register_capsule(target_id, role=role, strategy=strategy, reason=f"auto-evolved from run {run_id} at {datetime.utcnow().isoformat()}")

    # Append an evolution audit to the run state so results are traceable
    try:
        audit_entry = {
            "mutated_at": datetime.utcnow().isoformat(),
            "strategy": strategy,
            "target_capsule_id": target_id,
            "new_capsule_id": mutated.get("id") if isinstance(mutated, dict) else None,
            "note": f"auto-evolved from run {run_id}",
        }
        state.setdefault("evolutions", []).append(audit_entry)
        save_battle_state(run_id)
    except Exception as e:
        # don't fail the API if audit logging can't be written; log and continue
        log.exception("failed to append evolution audit to run state: %s", e)

    return {"evaluation": evald, "mutated": mutated}
