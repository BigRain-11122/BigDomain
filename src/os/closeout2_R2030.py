# closeout2_R2030.py - R2030 closeout continuation: explore
# flip/done note/reseed, backlog P1 registration, heartbeat
# line, export refresh. State surgery lands via
# state_append_R2030.py; this driver must NOT touch
# state.json. ASCII logic; CJK lives in
# closeout_payload_R2030.json (closeout2_R2029 pattern).
import io
import json
import os
import sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_PAYLOAD = os.path.join(HERE, "closeout_payload_R2030.json")
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

CLAIM_MARKER = "test_datasub_coveragemonthroll"
BACKLOG_ANCHOR = "- [x] pycrdt"

PAY = json.loads(io.open(P_PAYLOAD, encoding="utf-8").read())


def main():
    # guard: state must already carry the R2030 pair post-fold
    st = json.loads(io.open(
        os.path.join(ROOT, "src", "os", "state.json"),
        encoding="utf-8").read())
    assert st["tick"] == 2030 and st["log"][-1].startswith(
        "R2030 tokens:"), "state not at post-closeout shape"

    # -- explore.md claim flip + done note + reseed --------------
    text = io.open(P_EXPLORE, encoding="utf-8").read()
    hits = [ln for ln in text.splitlines()
            if ln.startswith("- [ ] ") and CLAIM_MARKER in ln]
    assert len(hits) == 1, "claim rows found=%d" % len(hits)
    claim = hits[0]
    flipped = claim.replace("- [ ] ", "- [x] ", 1)
    flipped = flipped + PAY["explore_done_note"]
    assert text.count(claim) == 1, "claim not unique"
    text = text.replace(claim, flipped, 1)
    assert text.count(PAY["reseed_row"]) == 0, "reseed exists"
    if not text.endswith("\n"):
        text += "\n"
    text += PAY["reseed_row"] + "\n"
    with io.open(P_EXPLORE, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    print("explore ok: row flipped, done note, reseed appended")

    # -- backlog.md P1 registration (insert before first item) ---
    btext = io.open(P_BACKLOG, encoding="utf-8").read()
    assert text.count(PAY["backlog_p1_row"]) == 0
    blines = btext.splitlines()
    anchor_idx = [i for i, ln in enumerate(blines)
                  if ln.startswith(BACKLOG_ANCHOR)]
    assert len(anchor_idx) == 1, "backlog anchor count=%d" % len(
        anchor_idx)
    i = anchor_idx[0]
    blines.insert(i, PAY["backlog_p1_row"])
    btext = "\n".join(blines)
    if not btext.endswith("\n"):
        btext += "\n"
    with io.open(P_BACKLOG, "w", encoding="utf-8", newline="") as fh:
        fh.write(btext)
    print("backlog ok: P1 row inserted at top")

    # -- heartbeat line -------------------------------------------
    now = datetime.now(timezone(timedelta(hours=8)))
    stamp = now.strftime("%Y-%m-%d %H:%M") + " +08:00"
    hb_line = (stamp + " | BigDomain OSLoop alive | tick 2030 | "
               + PAY["heartbeat_line"] + "\n")
    with io.open(P_HEART, "a", encoding="utf-8", newline="") as fh:
        fh.write(hb_line)
    print("heartbeat ok tick=2030")

    # -- export refresh --------------------------------------------
    import check_export_consistency as CEC
    derived, _state, exp, _pat = CEC.recompute()
    exp["export_ts"] = now.isoformat(timespec="seconds")
    exp["ceo_face"]["current"] = PAY["ceo_current"]
    exp["ceo_face"]["latest_artifact"] = PAY["ceo_artifact"]
    exp["ceo_face"]["next_milestone"] = PAY["ceo_milestone"]
    exp["results"].insert(0, [PAY["results_row_tick"],
                              PAY["results_row_label"]])
    with io.open(os.path.join(HERE,
                 "export_consistency_patterns.json"), "r",
                 encoding="utf-8-sig") as f:
        tick_label = json.load(f)["tick_row_label"]
    hit = 0
    for row in exp["results"]:
        if len(row) >= 2 and row[1] == tick_label:
            row[0] = "2030"
            hit += 1
    if hit != 1:
        raise SystemExit("FATAL: tick row count=%d" % hit)
    derived["method"] = ("machine-derived from state.json log"
                        " per BD-PROP-001 caliber"
                        " (check_export_consistency.recompute)")
    exp["self_drive"] = derived
    with io.open(P_EXPORT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(exp, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("export ok ts=%s window=%s W=%d sub=%d explore=%d"
          % (exp["export_ts"], derived["window"],
             derived["log_lines_in_window"],
             derived["substantive_non_idle_mention_lines"],
             derived.get("queue_explore_open", -1)))

    report, n_pass, n_fail = CEC.check()
    print("\n".join(report[-4:]))
    print("CHECK n_pass=%d n_fail=%d" % (n_pass, n_fail))
    if n_fail:
        raise SystemExit(2)
    print("EXPORT-FLUSH-OK tick=2030")
    return 0


if __name__ == "__main__":
    sys.exit(main())
