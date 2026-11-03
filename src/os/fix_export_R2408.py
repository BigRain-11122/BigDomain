# fix_export_R2408.py - repair the two export fields this window wrote wrong:
# the live tick row still carried the previous round's number and export_ts
# carried a literal placeholder instead of an ISO8601 instant.
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
p = os.path.join(REPO, "docs", "status-export.json")
patp = os.path.join(REPO, "src", "os", "export_consistency_patterns.json")
d = json.load(io.open(p, encoding="utf-8"))
pat = json.load(io.open(patp, encoding="utf-8"))
label = pat["tick_row_label"]
state = json.load(io.open(os.path.join(REPO, "src", "os", "state.json"),
                          encoding="utf-8"))
tick = str(state["tick"])
hits = 0
for row in d["results"]:
    if isinstance(row, list) and len(row) >= 2 and row[1] == label:
        hits += 1
        old = row[0]
        row[0] = tick
        print("TICK ROW %r -> %r" % (old, tick))
if hits != 1:
    print("E_TICK_ROWS found=%d" % hits)
    sys.exit(2)
d["export_ts"] = pat.get("export_ts_placeholder") or d["export_ts"]
d["export_ts"] = sys.argv[1] if len(sys.argv) > 1 else d["export_ts"]
io.open(p, "w", encoding="utf-8", newline="\n").write(
    json.dumps(d, ensure_ascii=False, indent=2) + "\n")
print("EXPORT bytes=%d export_ts=%s" % (os.path.getsize(p), d["export_ts"]))