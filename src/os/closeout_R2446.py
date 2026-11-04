"""closeout_R2446 - state / backlog / heartbeat closeout for the R2446 product
window (product-face-R2446, comma_binding_face_row_drift).

Writes the state log through state_io.canon with a byte read-back, prepends
the backlog row, appends the heartbeat row, and refuses any drift. Run with
--execute to write; the default is a dry run.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
BACKLOG = os.path.join(BASE, "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

TICK = 2446
DEC_ROWS = 239
ORDER_TS = "2026-11-04 23:32"

LOG = [
    "2026-11-04 R2446 product window (five-silence scan at open: git status "
    "empty at HEAD 624fd3fa with no .git/index.lock; the evolution ledger "
    "carries zero @BigDomain rows; the content-addressed decisions diff read "
    "118 rows and 118 tokens with new=0 and gone=0 against the stored "
    "baseline; benchmarks were refreshed 2026-11-03 inside the seven-day "
    "gate; the queue gauge read FLOOR-MET main 5/5 tech 10/10 explore 10/10 "
    "and the deliverable-aware reader offered state/queue/tech.md:512 prefix "
    "AC-PFRD1). Three NEW group order rows landed after the stored baseline "
    "and each was judged against this company's execution face: "
    "OB-20261104-230606-701 (fleet-wide self-dispatch law, lanes "
    "bm-a/bm-b/bm-c/bm-m), OB-20261104-2251-DATASET-EXPAND (bm-c character "
    "and voice dataset sourcing) and OB-20261104-233257-908 (fleet board and "
    "need-work duty, lanes bm-a/bm-b/bm-c/bm-m) - none carries a BigDomain "
    "action, so all three are ACKNOWLEDGED-NO-ACTION and the baseline was "
    "advanced to 2026-11-04 23:32. The debt gate named CLAIM-FIRST "
    "item=product-face-R2446 carried from R2445, so this window is a PRODUCT "
    "window on that row.",

    "2026-11-04 R2446 board first, before any code: AC-PFRD1..AC-PFRD6 were "
    "re-read from the R2444 seed row at state/queue/tech.md:512 and used as "
    "written, and the five anchors were re-checked at HEAD - E_PFRD, "
    "os-comma-binding-face-row-drift and test_comma_binding_face_row_drift "
    "read zero occupancy (git grep -F rc=1) while comma_binding_face_row_drift "
    "and AC-PFRD hit only prose and state files (docs/status-export.json, "
    "closeout_R2444.py, closeout_R2445.py, export_R2444.py, export_R2445.py, "
    "stamp_queue_R2444.py, src/os/backlog.md, src/os/state.json), i.e. zero "
    "executable occupancy.",

    "2026-11-04 R2446 SHIPPED src/os/comma_binding_face_row_drift.py plus "
    "src/os/test_comma_binding_face_row_drift.py: the R2444 compare reads "
    "each face VERDICT and publisher SET, so a per-line disagreement under an "
    "agreeing verdict was invisible. The new reader asks the SHIPPED compare "
    "at CALL time and keeps its report unchanged, then compares the values "
    "the three faces actually share on every published (path, line): the "
    "compared keys are the intersection of the published key sets minus the "
    "row identity, derived per run and never listed. A disagreement is "
    "published as ROWS-SPLIT naming the file, the line, the key and every "
    "face's own module, label and measured seam; a face that publishes "
    "nothing on a line the others publish is named ROWS-SILENT instead of "
    "being counted as agreement. When every row agrees the printed report is "
    "the shipped compare's own text byte for byte.",

    "2026-11-04 R2446 evidence, measured rather than asserted: SUITE PASS 6/6 "
    "with the two legs' criterion digest identical plus three adjacent comma "
    "suites green (EVIDENCE CAPTURE round=R2446 legs=2 identical=True "
    "adjacent=3 fails=0, qa/comma-binding-face-row-drift-R2446.log, 2633B, "
    "single writer utf-8 LF through the shipped capture callable), wired "
    "os-comma-binding-face-row-drift(6) so the registry reads 551 suites / "
    "4282 criteria. The AC-PFRD2 probe is proved both ways in the same run - "
    "the identity detail row rewritten from closeout_export_parity_wire to "
    "drifted_wire STILL reads FACES-AGREE rc=0 differences=0 at the verdict "
    "level, and the new reading names it ROWS-SPLIT at that line with both "
    "modules. docs/sandbox-suite-matrix.md was regenerated stamp-aligned from "
    "the only ELIGIBLE evidence face (qa/reconcile-all-R2445-final.log, the "
    "R2445 law) to 53223B at 551 suites / 4282 criteria with --check reading "
    "byte-identical; its own green line honestly reads 550/551 because this "
    "window's suite has no line in that battery log.",

    "2026-11-04 R2446 LIVE, not a plan: qa/comma-binding-face-row-drift-live-"
    "R2446.log (948B, crlf=0, read-back proved equal) reads the REAL src/os as "
    "verdict=FACES-AGREE rc=0 cells=11 compared=module,receiver,state,text "
    "splits=0 silent=0 over 11 publishers, and the stdout on that tree is the "
    "shipped compare's own text byte for byte. The real tree carries no row "
    "drift, so ROWS-SPLIT and ROWS-SILENT are proved on fixtures only and are "
    "NOT claimed as live catches.",

    "2026-11-04 R2446 board and register: row 512 stamped with a DISCHARGED "
    "block and one REAL measured gap row seeded from this window's own limit "
    "(row_key_carrier_scope, AC-PFKC1..AC-PFKC6 pre-registered) because the "
    "comparison only reads keys EVERY face carries - MEASURED here, `kind` is "
    "carried by the from-import and relative faces over 22 rows and `relative` "
    "by the relative face over 11 rows, and both sit outside the intersection, "
    "so a from-import/relative disagreement on `kind` is published by nothing "
    "(no live disagreement measured today, so it is a latent blind spot proved "
    "on fixtures). The gauge closed FLOOR-MET main 5/5 tech 10/10 explore "
    "10/10 with the head advanced to state/queue/tech.md:514 prefix AC-PDR1, "
    "and the board guards re-read clean around the edit: stamp_exempt_review "
    "--round R2446 read NO-DRIFT entries=383 violations=383 matched=383 "
    "exempt=381 expired=2 missing=0 undeclared=0. Debt: product-face-R2446 "
    "closed through the shipped debt_close at its predicted 114246B -> "
    "114249B (measured exactly, line=182, open 3->2, done 160->161, "
    "readback=ok) and reconcile-battery-R2447 opened first=yes through "
    "debt_append at 114249B -> 114707B (readback=ok), because this window "
    "changed product src bytes AND moved the registry count, so the R2168 "
    "mixed-tree rule owes the battery next.",

    "2026-11-04 R2446 honest disclosures: (a) this window claims two product "
    "points for a runnable reading, but no CEO-visible business surface was "
    "rebuilt - the artifact it protects is the internal three-face compare; "
    "(b) the first suite draft compared the carrier MODULE list without "
    "deduplicating, so a two-face agreement read as three modules and AC-PFRD2 "
    "went red on my own test bug rather than on the module, and AC-PFRD5 "
    "patched the identity face, which by construction suppresses that face's "
    "own seam calls - the patch moved to the from-import face so the other two "
    "run for real and the seam genuinely fires; no criterion was widened and "
    "no checker relaxed in either case; (c) the first evidence capture was "
    "refused E_EVC_RED twice for the SAME trap disclosed at R2444 - --root "
    "src/os with a root-relative suite path - and the capture was re-run with "
    "--root . ; (d) the matrix could not be rendered from this round's own "
    "evidence because no battery ran, so it names the last eligible battery "
    "log and says so in its own green line; (e) tasks.md was not touched, it "
    "is the P-47 canonical board and carries no row for this technical window; "
    "(f) src/os/state.json stood at 54564B against the 78500B waterline before "
    "this closeout (margin 23936B), so no fold was due; (g) queue_row still "
    "reports GATE-DEBT violations=11 over 25 claimable rows - that debt is "
    "pre-existing and named, and neither row this window touched appears in "
    "the violation list.",

    "2026-11-04 R2446 self-heal check: BigDomain-OSLoop still exists and its "
    "Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 passes an "
    "explicit S4U principal and needs an elevated shell while this session is "
    "unelevated, so the definition was left untouched again "
    "(two-hundred-and-thirteenth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile).",

    "2026-11-04 R2446 push: pending at closeout write; recorded after the "
    "push attempt so the line states what actually happened.",
]

TOKENS = (
    "R2446 tokens: local=~16k api=0 api_reason=product window - one src/os "
    "reader that keeps the shipped report unchanged and adds a per-line "
    "comparison whose compared keys are derived per run, its six-criteria "
    "suite (two first-draft test bugs found and fixed in the test, no "
    "criterion widened), two evidence legs with an identical digest plus three "
    "adjacent comma suites green, one live capture on the real tree, one "
    "stamp-aligned matrix regeneration from an eligible evidence face, one "
    "real measured gap row seeded, one board row stamped, two debt register "
    "writes through their shipped CLIs, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches")

BACKLOG_ROW = (
    "- [x] [done 2026-11-04 R2446] R2446 product window on the debt gate "
    "first=yes item (product-face-R2446, tech head state/queue/tech.md:512 "
    "prefix AC-PFRD1 comma_binding_face_row_drift, whose AC-PFRD1..AC-PFRD6 "
    "were pinned in that row at R2444 BEFORE any code): SHIPPED "
    "src/os/comma_binding_face_row_drift.py plus its six-criteria suite. It "
    "asks the SHIPPED compare at CALL time and keeps its report unchanged, "
    "then compares the values the three faces actually share on every "
    "published (path, line) - the compared keys are the intersection of the "
    "published key sets minus the row identity, derived per run and never "
    "listed - so the exact probe this row was seeded from is proved both ways: "
    "the identity detail row rewritten from closeout_export_parity_wire to "
    "drifted_wire still reads FACES-AGREE rc=0 differences=0 at the verdict "
    "level and the new reading names it ROWS-SPLIT at that line with both "
    "modules, while a face that publishes nothing on a line the others publish "
    "reads ROWS-SILENT naming that face. SUITE PASS 6/6 twice with an "
    "identical digest plus three adjacent comma suites green (EVIDENCE CAPTURE "
    "round=R2446 legs=2 identical=True adjacent=3 fails=0, "
    "qa/comma-binding-face-row-drift-R2446.log 2633B); LIVE on the real src/os "
    "FACES-AGREE rc=0 cells=11 compared=module,receiver,state,text splits=0 "
    "silent=0 over 11 publishers (qa/comma-binding-face-row-drift-live-"
    "R2446.log 948B, crlf=0), and the agreeing stdout is the shipped compare's "
    "own text byte for byte. The real tree has no row drift, so the split and "
    "silent cases are proved on fixtures only and are not claimed as live "
    "catches. Wired os-comma-binding-face-row-drift(6) so the registry reads "
    "551 suites / 4282 criteria; docs/sandbox-suite-matrix.md regenerated "
    "stamp-aligned from the only eligible evidence face to 53223B with --check "
    "byte-identical (its green line honestly reads 550/551). Board: row 512 "
    "stamped, one real measured gap row seeded (row_key_carrier_scope "
    "AC-PFKC1..AC-PFKC6: `kind` carried by two faces over 22 rows and "
    "`relative` by one face over 11 rows both sit outside the intersection, so "
    "a two-of-three disagreement is currently dropped), floor FLOOR-MET 5/5 "
    "10/10 10/10, head now state/queue/tech.md:514 AC-PDR1, stamp_exempt_review "
    "NO-DRIFT 383/383. Debt: product-face-R2446 closed (114246B -> 114249B, "
    "readback ok) and reconcile-battery-R2447 opened first=yes at 114249B -> "
    "114707B because product src bytes changed and the registry count moved. "
    "Zero CEO-visible business surface; two product points for a runnable "
    "reading."
)

HEARTBEAT_ROW = (
    "2026-11-04T23:58:00+08:00 tick=2446 R2446 product window - "
    "comma_binding_face_row_drift compares the publisher faces PER LINE on the "
    "keys they actually share, so a module rewritten under an unchanged "
    "verdict now reads ROWS-SPLIT naming the file, the line, the key and every "
    "face's own module and measured seam, while a face publishing nothing on a "
    "line the others publish reads ROWS-SILENT instead of counting as "
    "agreement; the agreeing report stays the shipped compare's own text byte "
    "for byte. SUITE PASS 6/6 twice identical plus three adjacent comma suites "
    "green, LIVE FACES-AGREE rc=0 cells=11 0 splits 0 silent on the real "
    "src/os, registry 551 suites / 4282 criteria, matrix regenerated "
    "stamp-aligned to 53223B [via BigDomain-OSLoop]")


def write_bytes_atomic(path, data, prefix):
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=prefix)
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = open(path, "rb").read()
    if back != data:
        raise SystemExit("E_R2446_BACK read-back does not match the write")
    return len(back)


def main(execute):
    if not execute:
        print("DRY RUN tick=%d log_lines=%d" % (TICK, len(LOG) + 1))
        for line in LOG:
            print("  LOG %s" % line[:100])
        print("  TOKENS %s" % TOKENS[:100])
        return 0

    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["tick"] != TICK - 1:
        raise SystemExit("E_R2446_TICK state reads %s, expected %d"
                         % (payload["tick"], TICK - 1))
    payload["tick"] = TICK
    payload["last_decision_rows"] = DEC_ROWS
    payload["last_order"] = ORDER_TS
    payload["log"].extend(LOG)
    payload["log"].append(TOKENS)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2446_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2446-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d layout_ok=%s crlf=%d bare_lf=%d"
          % (TICK, size, len(payload["log"]), layout["layout_ok"],
             layout["crlf"], layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if "R2446] R2446 product window" in backlog:
        raise SystemExit("E_R2446_BACKLOG row already present")
    write_bytes_atomic(BACKLOG, (BACKLOG_ROW + "\n" + backlog).encode(
        "utf-8"), ".r2446-backlog-")
    print("BACKLOG row prepended")

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    if "tick=2446 " in beat:
        raise SystemExit("E_R2446_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    write_bytes_atomic(HEARTBEAT, (beat + HEARTBEAT_ROW + "\n").encode(
        "utf-8"), ".r2446-beat-")
    print("HEARTBEAT row appended")
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))