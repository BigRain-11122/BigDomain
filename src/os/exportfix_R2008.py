# exportfix_R2008.py - same-round export drift repair: the
# results array accumulated three 'OSLoop tick' pointer rows
# (R2006/R2007 closeouts each appended without removing the
# previous one); the consistency caliber expects exactly one.
# Keep the latest (tick 2008), drop the stale 2006/2007 pointer
# rows, leave every other results row untouched, then the
# driver re-runs the checker for the green terminal run
# (R1673 same-round-fix precedent; drift honestly noted).
# ASCII only.
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
LABEL = "OSLoop " + "\u6267\u884c tick"


def main():
    exp = json.loads(io.open(P_EXPORT, encoding="utf-8").read())
    rows = exp["results"]
    tick_rows = [r for r in rows if r[1] == LABEL]
    assert len(tick_rows) == 3, "expected 3 stale rows, got %d" \
        % len(tick_rows)
    kept = [r for r in rows
            if r[1] != LABEL or r[0] == "2008"]
    assert sum(1 for r in kept if r[1] == LABEL) == 1
    exp["results"] = kept
    with io.open(P_EXPORT, "w", encoding="utf-8",
                 newline="") as fh:
        json.dump(exp, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("export fixed: results rows %d -> %d (kept tick 2008"
          " pointer only)" % (len(rows), len(kept)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
