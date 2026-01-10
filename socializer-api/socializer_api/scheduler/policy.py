"""
Slot selection policy: bootstrap rotation then epsilon-greedy bandit.
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional

MIN_SAMPLES_PER_SLOT = 5


def _with_optional_slot(slots: List[str], enable_optional: bool) -> List[str]:
    if enable_optional and "02:00" not in slots:
        return slots + ["02:00"]
    return slots


def select_slot(
    platform: str,
    now_utc,
    policy: Dict,
    slot_stats: Dict[str, Dict],
    slot_counts: Dict[str, int],
    rng: Optional[random.Random] = None,
) -> str:
    """
    Pick a slot using rotation during bootstrap, then epsilon-greedy bandit.
    """
    rng = rng or random.Random()
    slots = _with_optional_slot(list(policy.get("slots", [])), policy.get("enable_optional_slot", False))
    if not slots:
        slots = ["13:00", "19:00"]

    total_jobs = sum(slot_counts.values())
    bootstrap_threshold = max(1, policy.get("bootstrap_weeks", 2) * 10)
    insufficient_samples = any(
        slot_stats.get(s, {}).get("samples", 0) < MIN_SAMPLES_PER_SLOT for s in slots
    )
    if total_jobs < bootstrap_threshold or insufficient_samples:
        least = min(slots, key=lambda s: slot_counts.get(s, 0))
        return least

    if rng.random() < policy.get("epsilon", 0.2):
        return rng.choice(slots)

    best_slot = slots[0]
    best_mean = -1e9
    for s in slots:
        mean = slot_stats.get(s, {}).get("reward_mean", 0.0)
        if mean > best_mean:
            best_mean = mean
            best_slot = s
    return best_slot
