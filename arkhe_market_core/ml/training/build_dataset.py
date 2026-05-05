import json
import csv
from pathlib import Path

SRC = Path("ml/data/market_log.jsonl")
OUT = Path("ml/data/training_dataset.csv")

def flatten(prefix, value, row):
    if isinstance(value, dict):
        for k, v in value.items():
            flatten(f"{prefix}_{k}" if prefix else str(k), v, row)
    else:
        row[prefix] = value

def flatten_record(r):
    row = {
        "timestamp": r.get("timestamp"),
        "symbol": r.get("symbol"),
        "asset_class": r.get("asset_class"),
        "action": r.get("action"),
    }
    flatten("feature", r.get("features") or {}, row)
    flatten("agent", r.get("agents") or {}, row)
    return row

rows = []
if SRC.exists():
    with SRC.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(flatten_record(json.loads(line)))
            except Exception:
                pass

if not rows:
    print("No records found")
    raise SystemExit(0)

fields = sorted({k for row in rows for k in row.keys()})
with OUT.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {OUT}")
