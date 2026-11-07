import json
import os

PATH = "state/residue_triage.json"
with open(PATH, encoding="utf-8") as handle:
    data = json.load(handle)
print("bytes", os.path.getsize(PATH))
print("top keys", list(data)[:8] if isinstance(data, dict) else type(data))
if isinstance(data, dict):
    for key in list(data)[:4]:
        value = data[key]
        print("field", key, type(value).__name__,
              len(value) if hasattr(value, "__len__") else value)
    entries = data.get("entries")
    if isinstance(entries, list):
        print("entries", len(entries))
        rounds = [str(item.get("round")) for item in entries
                  if isinstance(item, dict)]
        for probe in ("R1755", "R2519", "R2524", "R2525"):
            hit = [item for item in entries
                   if isinstance(item, dict) and str(item.get("round")) == probe]
            print(probe, hit[:1])
        print("declared_by", sorted(set(
            str(item.get("declared_by")) for item in entries
            if isinstance(item, dict)))[-4:])