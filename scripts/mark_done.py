import json
from pathlib import Path

q = Path("tmp/polycop_queue.json")
data = json.loads(q.read_text())
for i in data:
    if i.get("address") == "0x594edb9112f526fa6a80b8f858a6379c8a2c1c11":
        i["status"] = "done"
        i["note"] = "created via fix_queue.py"
q.write_text(json.dumps(data, indent=2))
print("done")
