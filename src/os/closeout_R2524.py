"""Closeout for the R2524 window: append its rows, then fold if due.

Writes the state file the way the file is already written (load, mutate,
dump with a proved byte round-trip) and folds with the SHIPPED laws it can
still ask: state_fold.round_split for the round-block boundary, state_fold.PAT
for the token coverage check and state_fold.append_archive for the block.
Nothing is reformatted.

ASCII, stdlib only, zero network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
ARCHIVE = os.path.join(ROOT, "logs", "state-log-archive-2026-11.md")

sys.path.insert(0, BASE)
import state_fold  # noqa: E402

KEEP_LIVE = 24
TICK = 2524
FOLD_NO = 786
LAST_ORDER = "2026-11-07 12:2x"
DEC_ROWS = 127


def raw_state():
    with io.open(STATE, "rb") as handle:
        raw = handle.read()
    return raw, json.loads(raw.decode("utf-8"))


def dump(state):
    return json.dumps(state, indent=4, ensure_ascii=False) + "\n"


def append(rows, tick, execute):
    raw, state = raw_state()
    if tick <= state["tick"]:
        raise SystemExit("REFUSE: tick %d is not above %d"
                         % (tick, state["tick"]))
    if dump(state).encode("utf-8").rstrip(b"\n") != raw.rstrip(b"\n"):
        raise SystemExit("REFUSE: the file does not round-trip through "
                         "load+dump; the writer law is not known here")
    state["tick"] = tick
    state["last_order"] = LAST_ORDER
    state["last_decision_rows"] = DEC_ROWS
    state["log"] = list(state["log"]) + list(rows)
    data = dump(state).encode("utf-8")
    if not execute:
        return {"would_bytes": len(data), "before": len(raw)}
    with io.open(STATE, "wb") as handle:
        handle.write(data)
    with io.open(STATE, "rb") as handle:
        back = handle.read()
    if back != data:
        raise SystemExit("REFUSE: read-back differs")
    check = json.loads(back.decode("utf-8"))
    if (check["log"] != state["log"] or check["tick"] != tick
            or check["last_order"] != LAST_ORDER):
        raise SystemExit("REFUSE: payload does not round-trip")
    return {"post_bytes": len(data), "before": len(raw),
            "log": len(check["log"]), "tick": check["tick"]}


def fold(execute):
    raw, state = raw_state()
    log = list(state["log"])
    count = len(log)
    end = count - KEEP_LIVE
    if end < 1:
        return {"verdict": "NOOP", "detail": "nothing to fold"}
    while end >= 1:
        window = log[0:end]
        kept = log[end:]
        split = state_fold.round_split(window, kept)
        if split is None:
            break
        end -= 1
    window = log[0:end]
    kept = log[end:]
    tokens = set()
    for line in window:
        tokens |= set(state_fold.PAT.findall(line))
    summary = ("Fold %d (R2524): log lines 1..%d folded verbatim into "
               "logs/state-log-archive-2026-11.md at a true round-block "
               "boundary; window tokens: %s"
               % (FOLD_NO, end, " ".join(sorted(tokens))))
    header = "# --- Fold %d (R2524) - window 1..%d - %d lines" % (
        FOLD_NO, end, end)
    plan = {"window_start": 1, "window_end": end, "window_lines": end,
            "tokens_total": len(tokens), "summary_head": summary[:60],
            "round_split": state_fold.round_split(window, kept)}
    if not execute:
        plan["verdict"] = "PLANNED"
        return plan
    archived = state_fold.append_archive(ARCHIVE, header, window)
    state["log"] = kept
    data = dump(state).encode("utf-8")
    with io.open(STATE, "wb") as handle:
        handle.write(data)
    with io.open(STATE, "rb") as handle:
        back = handle.read()
    if back != data:
        raise SystemExit("REFUSE: fold read-back differs")
    check = json.loads(back.decode("utf-8"))
    if check["log"] != kept:
        raise SystemExit("REFUSE: folded log does not match")
    plan.update({"verdict": "FOLDED", "archive": archived,
                 "post_bytes": len(data), "kept": len(kept)})
    return plan


ROWS = [
    "2026-11-07 R2524 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2523, pre-registered 591 suites / 4522 criteria). "
    "Five-silence scan at open: one untracked file was already on disk - "
    "qa/reconcile-all-R2524.log, a battery leg this round had started before "
    "the window was opened - with no index.lock and no python reconcile "
    "process alive, so it was read rather than restarted. Content-addressed "
    "decisions diff read new=0 over the stored 160-token baseline, and "
    "DISCLOSED rather than smoothed: the group canon file now carries 91 "
    "tokens in 127 lines against the 211 rows measured at R2523, which means "
    "a group-level fold shrank it, and every token it still carries is "
    "already inside the baseline. Group orders tail still reads 2026-11-07 "
    "12:2x, the row the previous window judged knowledge-only, so no new "
    "order arrived; benchmarks 2026-11-03 inside the seven-day gate. The "
    "debt gate read CLAIM-FIRST item=reconcile-battery-R2523 opened=R2523 "
    "carried=1 stale=no open=8 first=1, and the target was RE-MEASURED by "
    "importing reconcile_all.SUITES before anything ran: 591 suites and 4522 "
    "criteria, byte for byte the registered number.",
    "2026-11-07 R2524 LEG 1 RED AND THE RED LEG KEPT (qa/reconcile-all-"
    "R2524.log, 911059B, utf-8, bom=False, crlf=0): 590/591 suites green "
    "with exactly ONE failed suite, os-residue-triage 5/6 on AC-RTR6, "
    "reproduced alone in 3.4s. THE CAUSE WAS READ, NOT GUESSED: the shipped "
    "reader reported residue 300 with triaged 296 and untriaged 4, and the "
    "set difference named FOUR product rounds that shipped and were committed "
    "without a declaration row - R2513, R2515, R2517 and R2519. This is the "
    "same birth site R2506 and R2514 hit, so the repair went through the "
    "shipped batch writer rather than a hand edit: residue_triage_append_batch "
    "dry run first (296 -> 300 entries, 82268B -> 83156B, delta 888, verdict "
    "DRY-RUN wrote=no), then --execute which hit that prediction exactly with "
    "verdict TRIAGED wrote=yes, after which the reader read every one of the "
    "four rounds TRIAGED and the suite alone read SUITE PASS 6/6. The repair "
    "and the red leg were committed ALONE as b8da165e so the retry ran on a "
    "committed tree with an empty git status.",
    "2026-11-07 R2524 LEG 2 GREEN ON THE COMMITTED REPAIR TREE, measured not "
    "quoted: qa/reconcile-all-R2524-retry.log is 910866B, utf-8, bom=False, "
    "crlf=0, lone_cr=0, zero FAIL suite rows, closing RUNNER PASS (591/591 "
    "suites green, reconcile controls 7/7, 1145.9s), and an independent "
    "recount over the 591 PASS rows sums to EXACTLY 4522 criteria - the "
    "pre-registered total matched by measurement. Launched detached and "
    "unfiltered through src/os/battery_stream.py (pid in "
    "logs/battery-R2524-retry.pid). FOUR FOLLOW-UP SECTIONS in the designed "
    "order: the dry run read SECTION matrix FAIL at on-disk 56905B against "
    "regenerated 56903B with NO byte written while fingerprint read CLEAN "
    "domains=5, profile byte-identical and census DRIFT-CLEAN; "
    "docs/sandbox-suite-matrix.md was then regenerated stamp-aligned from "
    "THIS round own green evidence through src/sandbox/suite_matrix.py "
    "--stamp-from to 56903 bytes at 591 suites / 4522 criteria with its green "
    "line honestly reading 591/591, --check read byte-identical, and the "
    "re-run read all four PASS for VERDICT R2524 PASS failing=none (APPENDED "
    "1950B eol_ok=True).",
    "2026-11-07 R2524 DEBT, BOARD AND ONE SEED: reconcile-battery-R2523 was "
    "closed through the shipped debtor at its predicted 155526B -> 155529B "
    "(line 249, open 8->7, done 224->225, readback ok) and product-face-R2524 "
    "was appended first=no through the shipped appender at its predicted "
    "155529B -> 156539B (readback ok). The first=yes append was NOT attempted "
    "because product-face-R2523 still holds that slot and this window shipped "
    "no product byte. NO successor battery is owed: the registry is unmoved at "
    "591 suites / 4522 criteria, re-read by import rather than trusted. ONE "
    "row was seeded from this window own MEASURED limit through "
    "src/os/seed_queue_R2524.py (state/queue/tech.md 565 -> 566 lines, "
    "once=True, lf_only=True) naming AC-DSRC1..AC-DSRC6 for a reading of debt "
    "rows whose named work already shipped; queue_floor then read FLOOR-MET "
    "main=5/5 tech=11/10 explore=10/10 with the head unmoved at line 561.",
    "2026-11-07 R2524 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - nothing a CEO could open was built this window "
    "and none is claimed; the deliverable is a green 591/4522 battery and a "
    "birth-site repair. (b) The red cause was born in FOUR earlier product "
    "windows, not this one: R2513, R2515, R2517 and R2519 each shipped and "
    "committed a product face without a declaration row, and R2506 and R2514 "
    "had repaired the same class twice before - so the batch writer exists and "
    "still is not wired into the product closeout, which is a named "
    "limitation rather than a closed loop. (c) MEASURED AND NOT HAND-FIXED: "
    "the debt register reads open=7 while FOUR of those rows - "
    "product-face-R2511, product-face-R2513, product-face-R2515 and "
    "product-face-R2517 - name product windows whose suites demonstrably "
    "shipped in R2513, R2515, R2517 and R2519, and no shipped reader names "
    "them because the gate ranks only the first=yes row; this window declined "
    "to mass-close them by hand and seeded the reading instead, so the "
    "register still overstates outstanding work by four rows and says so "
    "here. (d) A battery leg was already on disk when this window opened and "
    "its cause was not known then; it was read first rather than restarted, "
    "and it happened to be red, which is stated rather than dressed as a "
    "prediction. (e) Docker is absent on this host so no containerised "
    "bring-up of the sandbox faces is claimed. (f) The real 19.9 debit and the "
    "real msgSecCheck still wait on CEO physical items (merchant id, "
    "mini-program appid/secret). (g) tasks.md was not touched, it is the P-47 "
    "canonical board. (h) The S4U lane re-registration needs an ELEVATED "
    "shell and D-20261107-14 has classified it as a ceo-pending physical item "
    "with zero chase. (i) The window overshot its 25-minute budget on a "
    "1145.9s battery plus a follow-up pass and says so.",
    "R2524 tokens: local=~9k api=0 api_reason=verification window - "
    "five-silence scan, one pre-existing battery leg read rather than "
    "restarted, one content-addressed decisions scan reading new=0, one "
    "registry target re-measured by import, one batch-writer repair at the "
    "birth site with a dry run then an execution at the prediction, one "
    "committed-alone repair holding the red leg, one full 591-suite retry "
    "green at the pre-registered 4522 criteria, four follow-up sections plus "
    "one stamp-aligned matrix regeneration checked byte-identical, one debt "
    "row closed and one opened through their shipped writers, one queue row "
    "seeded with its criteria pre-registered, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]


def main():
    result = append(ROWS, TICK, execute=True)
    print("append before=%dB post=%dB log=%d tick=%d"
          % (result["before"], result["post_bytes"], result["log"],
             result["tick"]))
    check = state_fold.check(ROOT)
    print("gate bytes=%d margin=%d verdict=%s"
          % (check["bytes"], check["gate"] - check["bytes"],
             check["verdict"]))
    if check["verdict"] != "FOLD-CLEAR":
        plan = fold(execute=False)
        print("fold plan %s" % (plan,))
        done = fold(execute=True)
        print("fold %s post=%dB kept=%d archive_before=%dB archive_after=%dB"
              % (done.get("verdict"), done.get("post_bytes", 0),
                 done.get("kept", 0),
                 done.get("archive", {}).get("before_bytes", 0),
                 done.get("archive", {}).get("after_bytes", 0)))
        check = state_fold.check(ROOT)
        print("gate after bytes=%d margin=%d verdict=%s"
              % (check["bytes"], check["gate"] - check["bytes"],
                 check["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())