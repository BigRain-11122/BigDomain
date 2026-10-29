# fix_R2252.py - repair the three export fields the closeout left stale.
# The tick row is matched by its exact body text, never by a loose label
# match (the R2248 lesson: a loose 'tick' match overwrote three
# historical round labels).
import io
import json

PATH = "docs/status-export.json"

TICK_BODY = "OSLoop 执行 tick"

NEW_ROW = [
    "R2252",
    "verification window on the debt register first item: full reconcile "
    "battery RUNNER PASS 430/430 suites plus controls 7/7 in 798.1s, tmp "
    "reclaim 932/932 worlds 326.57 MiB, four follow-up sections all PASS "
    "(matrix 430 suites / 3558 criteria byte-identical, fingerprint CLEAN 5 "
    "domains, profile PASS, census DRIFT-CLEAN files=2188 flags=0), VERDICT "
    "PASS; the +2 suites and +12 criteria against R2249 are exactly the R2250 "
    "export-freshness and R2251 debt-append suites joining the registry; zero "
    "product code changed on the committed tree (the R2168 mixed-tree rule)",
]


def main():
    data = json.load(io.open(PATH, encoding="utf-8"))
    data["export_ts"] = "2026-10-29T12:26:00+08:00"
    sd = data["self_drive"]
    sd["log_lines_in_window"] = 10
    sd["substantive_non_idle_mention_lines"] = 10

    rows = data["results"]
    hits = [i for i, r in enumerate(rows)
            if len(r) > 1 and r[1] == TICK_BODY]
    if len(hits) != 1:
        raise SystemExit("E_FIX_TICK matches=%d" % len(hits))
    tick_index = hits[0]
    old = rows[tick_index][0]
    rows[tick_index][0] = "2252"

    if rows[0][0] == NEW_ROW[0]:
        raise SystemExit("E_FIX_DUP top row is already R2252")
    rows.insert(0, NEW_ROW)

    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("tick_row %s -> 2252 (index %d), rows %d -> %d"
          % (old, tick_index, len(rows) - 1, len(rows)))


if __name__ == "__main__":
    main()