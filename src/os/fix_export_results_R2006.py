# fix_export_results_R2006.py - results 'OSLoop 执行 tick' row is
# a single rolling slot (exactly-one law per the consistency
# checker): replace the ["2005", ...] row with ["2006", ...]
# instead of appending a duplicate. ASCII logic; label comes
# from the payload (CJK data file law).
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PAY = json.loads(io.open(os.path.join(
    HERE, "closeout_payload_R2006.json"),
    encoding="utf-8").read())
P = os.path.join(ROOT, "docs", "status-export.json")

exp = json.loads(io.open(P, encoding="utf-8").read())
label = PAY["results_row_label"]
rows = exp["results"]
hits = [i for i, r in enumerate(rows)
        if isinstance(r, list) and len(r) == 2 and r[1] == label]
assert len(hits) == 2, "expected 2 rows (2005 + appended 2006)"
rows[hits[0]][0] = PAY["results_row_tick"]
rows.pop(hits[1])
assert sum(1 for r in rows
           if isinstance(r, list) and len(r) == 2
           and r[1] == label) == 1, "exactly-one law"
with io.open(P, "w", encoding="utf-8", newline="") as fh:
    json.dump(exp, fh, ensure_ascii=False, indent=1)
    fh.write("\n")
print("results fixed: rolling row tick=%s total=%d"
      % (rows[hits[0]][0], len(rows)))
sys.exit(0)
