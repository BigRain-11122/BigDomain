"""R2436 closeout: state append through the shipped canon writer, plus the
heartbeat face.

Usage: python src/os/closeout_R2436.py [--execute]
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import state_io  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

ITEMS = [
    "2026-11-04 R2436 product window (five-silence scan clean at open: git status empty with no .git/index.lock; zero unreplied @BigDomain ledger rows; the content-addressed decisions diff read 111 tokens against the stored baseline with new=0 and two baseline tokens that no longer appear in the document; the group orders tail max_ts is 2026-11-04 00:46, equal to the stored last_order, so nothing dispatches this company; benchmarks refreshed 2026-11-03 inside the seven-day gate; the queue gauge read FLOOR-MET). The debt gate named CLAIM-FIRST item=product-face-R2436, the tech head state/queue/tech.md:500 prefix AC-OTST1 (owner_table_split_triage), whose AC-OTST1..AC-OTST6 were pinned in that row at R2412 BEFORE any code, so no criterion was written this window.",
    "2026-11-04 R2436 SHIPPED src/os/owner_table_split_triage.py plus src/os/test_owner_table_split_triage.py and the shipped declaration state/owner_table_triage.json. The split face publishes every disagreement between the two table readers, but it re-reported the same known law false positives every round with no way to say reviewed and accepted, so the debt count could never reach zero. The new face asks owner_table_reader_parity.audit at CALL time and ages a declaration against that live payload, so no verdict and no count is stored: a declaration row shaped exactly {tool, reason, since_round} that matches a live row on tool AND reason moves it to TRIAGED while the row is still printed with both verdicts and the law own flags; an entry that matches nothing reads STALE with why=no-live-disagreement (the tool is gone from the read tree, or now reads PARITY-AGREES on both sides) or why=reason-differs (the tool is still live but its reason changed), and in that case the row stays in the split.",
    "2026-11-04 R2436 proofs, measured rather than asserted: SUITE PASS 6/6 on the first run with no repair, then twice with an identical criterion digest (qa/owner-table-split-triage-R2436-a.log / -b.log, 689B each, sha16 023a446b91304ce9), three adjacent suites green (owner_table_parity 6/6, owner_table_usage_wire 6/6, owner_table_reader_parity 6/6), and the runner wired os-owner-table-split-triage(6) so the registry reads 546 suites / 4252 criteria. LIVE on the REAL src/os (qa/owner-table-split-triage-live-R2436.log): scanned=1068 rows=41 superseded=35 split=0 triaged=6 stale=0 verdict=TRIAGE-CLEAN, and the six triaged rows are the six MEASURED live law-only-table rows - battery_followup_help_wire, evidence_R2372, matrix_stamp_compare, r2140_fold, retry_naming, run_identity - each disposition read by opening the file (a help-flag tuple, a canned command tuple, a key map, internal vocabularies), never assumed.",
    "2026-11-04 R2436 honest disclosures: (a) TRIAGE-CLEAN is a TRIAGE verdict, not a parity proof - all six acceptances are law false positives the law keeps reporting, and the shipped declaration carries that sentence in its own note; (b) the seed row prose said five known false positives, this window MEASURED six live rows and triaged all six rather than dropping one to match the prose; (c) docs/sandbox-suite-matrix.md was regenerated through the shipped generator to 52596B at 546 suites / 4252 criteria and its own line reads green=545/546 because this window suite has no line in the R2435 evidence yet; (d) no battery ran and reconcile-battery-R2436 is owed next at the pre-registered 546 suites / 4252 criteria.",
    "R2436 tokens: local=~13k api=0 api_reason=product window - one new reader plus its six-criteria suite, two evidence legs, one live reading on the real src/os, one matrix regeneration and the state/declaration/backlog/tech/debt/export closeout; zero product cloud calls and zero external API touches",
    "2026-11-04 R2436 self-heal check: BigDomain-OSLoop still exists and its Principal.LogonType reads Interactive (InteractiveToken), which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 passes an explicit S4U principal and needs an elevated shell while this session is unelevated, so the definition was left untouched again (two-hundred-and-third consecutive disclosure, carried as the stale row loop-s4u-reconcile).",
]

HB_2436 = ("2026-11-04T10:20:00+08:00 tick=2436 R2436 product window - "
           "owner_table_split_triage shipped against AC-OTST1..AC-OTST6 pinned "
           "at R2412: a dated {tool, reason, since_round} declaration moves a "
           "reviewed live row to TRIAGED while it stays printed with both "
           "verdicts and the law flags, and an entry that no longer matches "
           "reads STALE with its why; suite 6/6 twice identical, live "
           "TRIAGE-CLEAN on the real src/os (split=0 triaged=6 stale=0), "
           "registry 546 suites / 4252 criteria, product-face-R2436 closed "
           "and reconcile-battery-R2436 opened first=yes")


def main():
    raw = state_io.read_raw(STATE)
    state = json.loads(state_io.decode(raw))
    tick = int(state.get("tick", 0)) + 1
    state["tick"] = tick
    state.setdefault("log", []).extend(ITEMS)
    payload = json.dumps(state, ensure_ascii=False, indent=2)
    post = state_io.canon(payload)

    hb_raw = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    lines = hb_raw.split("\n")
    lines.append(HB_2436)
    hb_post = "\n".join(lines)

    print("tick=%d items=%d before=%dB after=%dB hb_before=%dB hb_after=%dB"
          % (tick, len(ITEMS), len(raw), len(post.encode("utf-8")),
             len(hb_raw.encode("utf-8")), len(hb_post.encode("utf-8"))))
    if "--execute" not in sys.argv:
        print("dry run, wrote nothing")
        return 0

    body = post.encode("utf-8")
    tmp = STATE + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(body)
    os.replace(tmp, STATE)
    back = state_io.decode(state_io.read_raw(STATE))
    assert back == post, "E_R2436_READBACK"

    hb_tmp = HEARTBEAT + ".tmp"
    with io.open(hb_tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(hb_post)
    os.replace(hb_tmp, HEARTBEAT)
    hb_back = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    assert hb_back == hb_post, "E_R2436_HB_READBACK"

    print("readback state=%dB eol_ok=%s heartbeat=%dB"
          % (len(back.encode("utf-8")), state_io.layout(back)["eol_ok"],
             len(hb_back.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())