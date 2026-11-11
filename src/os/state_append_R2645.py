"""state_append_R2645 - the R2645 verification window narrative and tokens.

Every number below was measured off the tree in this window: the evidence file
re-measured on bytes, the registry recounted by import, the matrix byte counts
on both sides of the regeneration, and the debt register byte counts.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import general_writer_dialect_audit as GWDA  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")

LINES = [
    "2026-11-11 R2645 VERIFICATION window on the battery the debt gate named"
    " first (reconcile-battery-R2643, pre-registered 648 suites / 4864"
    " criteria at R2643 because that window moved product src bytes and one"
    " registry row). Five readings at open: git status carried ONE untracked"
    " file, the one-off launcher of an INTERRUPTED ATTEMPT of this same round,"
    " with no index.lock; ZERO unreplied @BigDomain rows in"
    " cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0); the"
    " content-addressed D-/C-/P-/O-/T-/XL- decisions scan read tokens=189"
    " new=0 over 323 rows; the group orders tail still carries the 2026-11-11"
    " 20:15 BigStream mv0001 v727 row already judged knowledge-only for this"
    " company at R2643; benchmarks_refreshed 2026-11-10 one day inside the"
    " seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2643"
    " opened=R2643 carried=2 stale=no first=1 open=43; queue_head named tech"
    " line 661 prefix AC-EDWX1 claimable=15 and queue_floor read FLOOR-MET at"
    " 5/5, 15/10, 10/10.",

    "R2645 THE LEG THE INTERRUPTED ATTEMPT LAUNCHED HAD ALREADY FINISHED AND"
    " WAS ADOPTED, NOT RESTARTED: no reconcile writer was live by command line"
    " match, logs/battery-R2645.pid carried pid 38188, the stream closed on"
    " RUNNER PASS (648/648 suites green, reconcile controls 7/7, 2659.2s) and"
    " BATTERY rc=0 2659.4s, and the single writer had already landed"
    " qa/reconcile-all-R2645.log. The target was re-measured BY IMPORT before"
    " anything was judged: reconcile_all.SUITES read 648 suites / 4864"
    " criteria / 648 unique names / 648 unique paths, byte for byte the"
    " pre-registered number.",

    "R2645 THE EVIDENCE WAS MEASURED ON BYTES AND NOT QUOTED:"
    " qa/reconcile-all-R2645.log is 1096252B, utf-8 with bom=False, crlf=0,"
    " lone_cr=0, nul=0, 8615 lines, ZERO FAIL suite rows, 648 real suite rows"
    " carrying 648 UNIQUE names, and an INDEPENDENT criteria recount over the"
    " per-row fields summing to EXACTLY 4864 against the pre-registered"
    " 648/4864. Two dialect facts are NAMED rather than swept: the 649th line"
    " matching a PASS-suite prefix is the runner own summary row"
    " 'PASS suite suites 648/648' and not a suite, and 28 lines carry a"
    " non-zero exit inside a PASS assertion because they describe expected"
    " refusal exits of fixtures (the member-tamper, census-drift, sentinel and"
    " matrix-refusal probes), which is the known runner dialect and not a"
    " green claim invented here.",

    "R2645 FOLLOW-UP RAN IN THE DESIGNED ORDER: the dry run read VERDICT FAIL"
    " failing=matrix at on-disk=66331B against regenerated=66290B with NO byte"
    " written while fingerprint read CLEAN domains=5, profile read"
    " byte-identical and census read DRIFT-CLEAN; docs/sandbox-suite-matrix.md"
    " was then regenerated stamp-aligned from THIS round own green leg through"
    " src/sandbox/suite_matrix.py --stamp-from to 66290 bytes at 648 suites /"
    " 4864 criteria with its green line honestly reading 648/648"
    " self-describing, and --check read byte-identical at rc=0; the write leg"
    " then read all four sections PASS for VERDICT R2645 PASS failing=none"
    " (APPENDED 1951B eol_ok=True).",

    "R2645 DEBT through the shipped writers: reconcile-battery-R2643 was"
    " closed at its predicted and measured 206693B -> 206696B (line 379,"
    " open 43->42, done 318->319, readback ok) and product-face-R2645 was"
    " opened first=yes at the predicted 206696B -> 207247B (readback ok)"
    " naming the next window a PRODUCT face on the queue head"
    " state/queue/tech.md:661 prefix AC-EDWX1 (export_composed_landed_face BOM"
    " precedence second wave, criteria AC-EDWX1..AC-EDWX6 pinned there at"
    " R2643 BEFORE any code). NO successor battery is owed because this window"
    " moved no product src byte and the registry is unmoved at 648 suites /"
    " 4864 criteria, re-measured by import.",

    "R2645 honest disclosures: (a) ZERO product points on the Executive"
    " Protocol scale - no product byte was written, because the debt gate puts"
    " the owed battery before any further product work and this window spent"
    " its budget adopting and closing that leg; (b) THE LEG WAS AUTHORED BY AN"
    " INTERRUPTED ATTEMPT OF THIS SAME ROUND and is adopted rather than"
    " presented as this window own work - it was re-measured at HEAD before"
    " any judgement, and this window one-off launcher"
    " src/os/launch_battery_R2645.py was DELETED before the commit instead of"
    " being staged; (c) src/os/scan_five_still.py still crashes at its final"
    " [ORD-TOP] print on the GBK console (a BOM in the group orders row), so"
    " this window scan was run under PYTHONIOENCODING=utf-8 - WORKED AROUND,"
    " NOT REPAIRED, and the repair stays carried on the backlog because"
    " touching product src now would owe another battery; (d) Docker is absent"
    " on this host so no containerised bring-up of the sandbox faces is"
    " claimed; (e) the real 19.9 debit and the real msgSecCheck still wait on"
    " CEO physical items (merchant id, mini-program appid/secret); (f)"
    " tasks.md was not touched, it is the P-47 canonical board; (g)"
    " BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED"
    " shell for its S4U re-registration (carried ceo-pending physical item"
    " loop-s4u-reconcile).",

    "R2645 tokens: local=~9k api=0 api_reason=verification window - one"
    " five-silence scan with the content-addressed decisions scan, the group"
    " orders tail and the ledger face actually read, one debt gate read and"
    " one queue head plus floor read, one liveness check of the adopted leg by"
    " command line and stream tail, one byte-level re-measurement of the"
    " evidence on seven axes plus a registry recount by import on four axes,"
    " one designed matrix FAIL with no byte written, one stamp-aligned"
    " regeneration checked byte-identical, one four-section write leg to a"
    " PASS verdict, one debt row closed and one opened through their shipped"
    " writers, one untracked launcher deleted before the commit, and the"
    " state/export closeout; zero cloud calls and zero external API touches",
]


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    if not isinstance(state.get("log"), list):
        print("E_APPEND_NO_LOG")
        return 3
    state["tick"] = int(state.get("tick", 0)) + 1
    for line in LINES:
        state["log"].append(line)
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    before = len(raw.encode("utf-8"))
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        check = fh.read()
    reread = json.loads(check.decode("utf-8"))
    ok = (len(reread["log"]) == len(state["log"])
          and reread["tick"] == state["tick"])
    print("APPEND tick=%d lines=%d bytes %d -> %d readback=%s"
          % (state["tick"], len(LINES), before, len(check),
             "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
