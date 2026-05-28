import json
from pathlib import Path
from datetime import datetime, timezone as tz

q = Path("tmp/polycop_queue.json")
queue = json.loads(q.read_text()) if q.exists() else []
addr = "0x594edb9112f526fa6a80b8f858a6379c8a2c1c11"
if any(i.get("address") == addr for i in queue):
    print("deja en queue")
else:
    queue.append({
        "address": addr,
        "label": "thread-extract-2",
        "confidence": 66.7,
        "risk_badge": "🟡 YELLOW",
        "edge_type": "category_specialist:weather",
        "size_pct": 1.0,
        "n_resolved": 491,
        "total_pnl_usd": 96724,
        "queued_at": datetime.now(tz.utc).isoformat(),
        "status": "pending",
        "tier": "standard",
    })
    q.parent.mkdir(exist_ok=True)
    q.write_text(json.dumps(queue, indent=2))
    print("thread-extract-2 ajouté à la queue PolyCop")
