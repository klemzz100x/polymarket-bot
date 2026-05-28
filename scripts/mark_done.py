import json
from pathlib import Path

addr = "0x594edb9112f526fa6a80b8f858a6379c8a2c1c11"

# Mark queue as done
q = Path("tmp/polycop_queue.json")
data = json.loads(q.read_text())
for i in data:
    if i.get("address") == addr:
        i["status"] = "done"
        i["note"] = "created via fix_queue.py"
q.write_text(json.dumps(data, indent=2))
print("queue: done")

# Add to seen.json as autocopy_queued so re-check loop won't re-process
seen_file = Path("tmp/watchdog_seen.json")
seen = json.loads(seen_file.read_text()) if seen_file.exists() else {}
seen[addr] = "autocopy_queued"
seen_file.write_text(json.dumps(seen, indent=2))
print("seen.json: autocopy_queued")
