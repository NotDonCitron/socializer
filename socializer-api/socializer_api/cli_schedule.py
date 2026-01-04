"""
CLI entrypoints for scheduling without HTTP.
"""
from __future__ import annotations

import argparse
import json
import random
from typing import Optional

from . import db
from .scheduler.schedule import schedule_approved_content


def cmd_tick(platform: str, dry_run: bool, limit: int) -> None:
    jobs = schedule_approved_content(platform=platform, limit=limit, dry_run=dry_run, rng=random.Random(0))
    print(json.dumps(jobs, indent=2))


def cmd_policy(show: bool, set_values: Optional[dict]) -> None:
    if set_values:
        db.upsert_schedule_policy(**{k: v for k, v in set_values.items() if v is not None})
    policy = db.get_schedule_policy()
    print(json.dumps(policy, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Scheduler CLI")
    sub = parser.add_subparsers(dest="cmd")

    tick = sub.add_parser("tick", help="Schedule approved content")
    tick.add_argument("--platform", required=True, choices=["tiktok", "instagram_reels", "youtube_shorts"])
    tick.add_argument("--dry-run", action="store_true", default=False)
    tick.add_argument("--limit", type=int, default=1)

    policy = sub.add_parser("policy", help="Show or update scheduling policy")
    policy.add_argument("--show", action="store_true", default=False)
    policy.add_argument("--bootstrap-weeks", type=int)
    policy.add_argument("--epsilon", type=float)
    policy.add_argument("--jitter-min", type=int)
    policy.add_argument("--jitter-max", type=int)
    policy.add_argument("--min-gap-hours", type=int)
    policy.add_argument("--slots", type=str, help='Comma-separated slots, e.g., "13:00,19:00"')
    policy.add_argument("--enable-optional-slot", action="store_true")

    args = parser.parse_args()
    db.init_db()

    if args.cmd == "tick":
        cmd_tick(args.platform, args.dry_run, args.limit)
    elif args.cmd == "policy":
        slots = args.slots.split(",") if args.slots else None
        set_values = {
            "bootstrap_weeks": args.bootstrap_weeks,
            "epsilon": args.epsilon,
            "jitter_min": args.jitter_min,
            "jitter_max": args.jitter_max,
            "min_gap_hours": args.min_gap_hours,
            "slots": slots,
            "enable_optional_slot": args.enable_optional_slot if args.enable_optional_slot else None,
        }
        cmd_policy(args.show, set_values if any(v is not None for v in set_values.values()) else None)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
