"""
CLI for local review of content packs without hitting the HTTP API.
"""
from __future__ import annotations

import argparse
import json
from typing import Optional

from . import db


def list_packs(status: Optional[str]) -> None:
    packs = db.list_content_packs(status=status, limit=200)
    for p in packs:
        print(json.dumps({"id": p["id"], "lane": p.get("lane"), "status": p.get("status")}, indent=2))


def approve(pack_id: str, status: str) -> None:
    ok = db.set_content_pack_status(pack_id, status)
    if not ok:
        print(f"Content pack {pack_id} not found")
    else:
        print(f"{status} -> {pack_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Review content packs locally")
    sub = parser.add_subparsers(dest="cmd")

    list_cmd = sub.add_parser("list", help="List content packs")
    list_cmd.add_argument("--status", choices=["draft", "approved", "rejected"], default=None)

    approve_cmd = sub.add_parser("approve", help="Approve a content pack")
    approve_cmd.add_argument("content_pack_id")

    reject_cmd = sub.add_parser("reject", help="Reject a content pack")
    reject_cmd.add_argument("content_pack_id")

    args = parser.parse_args()
    db.init_db()

    if args.cmd == "list":
        list_packs(args.status)
    elif args.cmd == "approve":
        approve(args.content_pack_id, "approved")
    elif args.cmd == "reject":
        approve(args.content_pack_id, "rejected")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
