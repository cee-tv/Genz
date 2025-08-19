#!/usr/bin/env python3
import argparse
import base64
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
from pathlib import Path
import csv

PHT = ZoneInfo("Asia/Manila")

VALID_UNITS = {"days", "weeks", "months", "years"}

def make_key() -> str:
    # 16 random bytes, URL-safe base64 (no padding), prefixed for readability
    raw = secrets.token_bytes(16)
    b64 = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    return f"KEY-{b64}"

def compute_expiry(now_pht: datetime, unit: str, amount: int) -> datetime:
    unit = unit.lower()
    if unit not in VALID_UNITS:
        raise ValueError(f"unit must be one of {sorted(VALID_UNITS)}")
    if amount <= 0:
        raise ValueError("amount must be a positive integer")

    if unit == "days":
        return now_pht + relativedelta(days=+amount)
    if unit == "weeks":
        return now_pht + relativedelta(weeks=+amount)
    if unit == "months":
        return now_pht + relativedelta(months=+amount)
    if unit == "years":
        return now_pht + relativedelta(years=+amount)

    # Fallback (should never hit)
    return now_pht

def to_rfc3339(dt: datetime) -> str:
    return dt.isoformat()

def write_outputs(output_dir: Path, payload: dict):
    # per-run folder
    stamp = datetime.now(PHT).strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"run_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = run_dir / "keys.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # CSV
    csv_path = run_dir / "keys.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key", "generated_at_pht", "expires_at_pht", "expires_at_unix", "unit", "amount", "tag"])
        for k in payload["keys"]:
            w.writerow([
                k,
                payload["generated_at_pht"],
                payload["expires_at_pht"],
                payload["expires_at_unix"],
                payload["unit"],
                payload["amount"],
                payload.get("tag","")
            ])

    # latest.json (for the website to fetch easily)
    latest_path = output_dir / "latest.json"
    with latest_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # optional index of runs (append-only list of summaries)
    index_path = output_dir / "index.json"
    index = []
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except Exception:
            index = []
    index.append({
        "run": run_dir.name,
        "unit": payload["unit"],
        "amount": payload["amount"],
        "count": len(payload["keys"]),
        "generated_at_pht": payload["generated_at_pht"],
        "expires_at_pht": payload["expires_at_pht"],
        "tag": payload.get("tag","")
    })
    with index_path.open("w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"Wrote: {json_path}, {csv_path}, and updated {latest_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate time-limited keys (Asia/Manila).")
    parser.add_argument("--unit", required=True, choices=sorted(VALID_UNITS),
                        help="Validity unit (days|weeks|months|years)")
    parser.add_argument("--amount", required=True, type=int, help="How many units")
    parser.add_argument("--count", required=True, type=int, help="How many keys to generate")
    parser.add_argument("--tag", default="", help="Optional tag/label")
    parser.add_argument("--output-dir", default="keys", help="Output directory (default: keys)")
    args = parser.parse_args()

    now_pht = datetime.now(PHT)
    expires_pht = compute_expiry(now_pht, args.unit, args.amount)

    keys = [make_key() for _ in range(args.count)]

    payload = {
        "generated_at_pht": to_rfc3339(now_pht),
        "generated_at_utc": to_rfc3339(now_pht.astimezone(timezone.utc)),
        "unit": args.unit,
        "amount": args.amount,
        "count": args.count,
        "tag": args.tag,
        "expires_at_pht": to_rfc3339(expires_pht),
        "expires_at_utc": to_rfc3339(expires_pht.astimezone(timezone.utc)),
        "expires_at_unix": int(expires_pht.timestamp()),
        "timezone": "Asia/Manila (GMT+8)",
        "keys": keys,
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_outputs(out_dir, payload)

if __name__ == "__main__":
    sys.exit(main())
