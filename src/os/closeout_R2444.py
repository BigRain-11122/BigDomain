"""closeout_R2444 - state / backlog / heartbeat closeout for the R2444
product window (comma_binding_identity_face_compare).

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

TICK = 2444
DEC_ROWS = 239

LOG = [
    "2026-11-04 R2444 product window (five-silence scan clean at open: git "
    "status empty at HEAD d43035bb with no .git/index.lock; the evolution "
    "ledger carries zero @BigDomain rows; the content-addressed decisions "
    "diff read 239 rows against the stored 239-row baseline with no new "
    "token; benchmarks were refreshed 2026-11-03 inside the seven-day gate; "
    "the queue gauge read FLOOR-MET main 5/5 tech 10/10 explore 10/10 and "
    "the deliverable-aware reader offered state/queue/tech.md:510 prefix "
    "AC-PICIC1). The debt gate named CLAIM-FIRST item=product-face-R2444 "
    "carried from R2443, so this window is a PRODUCT window on that row.",

    "2026-11-04 R2444 GROUP-LAYER ANOMALY, read-only and reported rather "
    "than repaired: the group orders tail at "
    "C:\\Users\\sjs20\\Desktop\\FluxGroup\\docs\\orders.md carries literal "
    "merge-conflict markers ('<<<<<<< HEAD', '=======', '>>>>>>> "
    "origin/main') in its last lines. The cross-repo write ban forbids this "
    "station from touching the group file, so nothing was edited; the "
    "conflict is named here and in HQ-FEEDBACK.md so the group layer can "
    "resolve it.",

    "2026-11-04 R2444 SHIPPED src/os/comma_binding_identity_face_compare.py: "
    "the sibling reading (R2430) compared the from-import face with the "
    "relative face only, while the identity face reaches the comma-aware "
    "receiver table through a DIFFERENT seam "
    "(comma_binding_consumer_wire.wire_audit_script), so a regression on that "
    "one path could move the identity verdict with both sibling faces still "
    "agreeing. The shipped module asks the three SHIPPED faces at CALL time "
    "and restates no table, and it MEASURES each face's seam instead of "
    "asserting it: both seam providers are wrapped for the duration of that "
    "face's own audit and every call is counted, so the published seam is the "
    "seam that fired. Disagreements are published with the face name, its "
    "verdict and its seam calls, and a face that alone publishes a file is "
    "named as an only-publisher difference.",

    "2026-11-04 R2444 MEASURED LIVE on the real src/os: verdict=FACES-AGREE "
    "with 11 publishers and 33 rows identical in size on all three faces, "
    "differences=0, and the seam reading is the fact this window exists for - "
    "the from-import and relative faces both reach the table through "
    "comma_binding_sibling_faces.receivers_for:33 while the identity face "
    "reads receivers_for:33 AND "
    "comma_binding_consumer_wire.wire_audit_script:33, i.e. the third face "
    "rides a second path the sibling compare never asked "
    "(qa/comma-binding-identity-face-compare-live-R2444.log, 665B, crlf=0)."
    " A fixture probe confirms both directions: one comma-list fixture reads "
    "WIRE on all three faces, a forced identity drift reads FACES-SPLIT "
    "naming the identity face, a foreign fixture reads FOREIGN everywhere, "
    "and a receiver no import binds reads UNRESOLVED everywhere with module "
    "'' rather than being guessed.",

    "2026-11-04 R2444 evidence: SUITE PASS 6/6 twice with an identical digest "
    "6D174EB5708FE9E5 plus three adjacent comma suites green (EVIDENCE "
    "CAPTURE round=R2444 legs=2 identical=True adjacent=3 fails=0, "
    "qa/comma-binding-identity-face-compare-R2444.log), wired "
    "os-comma-binding-identity-face-compare(6) so the registry reads 550 "
    "suites / 4276 criteria. docs/sandbox-suite-matrix.md was regenerated "
    "stamp-aligned through --stamp-from to 55305B at 550 suites / 4276 "
    "criteria and suite_matrix --check reads byte-identical.",

    "2026-11-04 R2444 board and register: row 510 stamped with a DISCHARGED "
    "block and one REAL measured gap row seeded at line 512 from this "
    "window's own limit (comma_binding_face_row_drift, AC-PFRD1..AC-PFRD6 "
    "pre-registered) because the compare reads verdicts and publisher sets "
    "only - MEASURED here, one identity detail row rewritten to "
    "'drifted_wire' under an unchanged WIRE verdict still reads FACES-AGREE "
    "rc=0 differences=0, and the three faces do not even share a row shape "
    "(6/7/8 keys). Debt: product-face-R2444 closed through the shipped "
    "debt_close at 112963B -> 112966B (line=179, open 2->1, done 158->159, "
    "readback=ok) and reconcile-battery-R2445 opened first=yes through "
    "debt_append at 112966B -> 113460B, because this window changed product "
    "src bytes AND moved the registry count, so the R2168 mixed-tree rule "
    "owes the battery next at the pre-registered 550 suites / 4276 criteria.",

    "2026-11-04 R2444 honest disclosures: (a) this window claims two product "
    "points for a runnable artifact-level reading - a CLI whose output is the "
    "three-face verdict with a MEASURED seam - but no CEO-visible business "
    "surface was rebuilt; (b) two assertions in the first suite draft were "
    "invented by this window rather than read off the faces - AC-PICIC3 "
    "demanded the three faces share one row key set (the identity face "
    "publishes 6 keys, the from-import 7 and the relative 8, so that "
    "assertion was wrong, not the code) and AC-PICIC4 demanded exit 2 for a "
    "UNRESOLVED fixture while three faces agreeing on UNRESOLVED is by law "
    "FACES-AGREE at exit 0; both were corrected to the faces' own contract "
    "and no criterion was widened; (c) a third draft defect was mine alone - "
    "the suite's check() did not return its argument, so every criterion "
    "read False while printing PASS, which is exactly the kind of oracle rot "
    "this station keeps catching; (d) AC-PICIC6's first read of 'no clock' "
    "matched the substring 'time.' inside the words 'at call time.' in the "
    "docstring and was narrowed to 'import time'/'time.time', a checker "
    "false positive rather than a source defect; (e) tasks.md was not "
    "touched, it is the P-47 canonical board and carries no row for this "
    "technical window; (f) the doc's provenance line names the evidence log "
    "this round captured, not a borrowed stamp.",

    "2026-11-04 R2444 self-heal check: BigDomain-OSLoop still exists and its "
    "Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 passes an "
    "explicit S4U principal and needs an elevated shell while this session is "
    "unelevated, so the definition was left untouched again "
    "(two-hundred-and-eleventh consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile).",

    "2026-11-04 R2444 push: pending at closeout write; recorded after the "
    "push attempt so the line states what actually happened.",
]

TOKENS = (
    "R2444 tokens: local=~13k api=0 api_reason=product window - one src/os "
    "law that asks all three shipped faces and measures their seams, its "
    "six-criteria suite (two invented-oracle drafts corrected before green), "
    "two-leg evidence capture plus three adjacent suites, one live capture on "
    "the real tree, one real gap row seeded, two debt register writes through "
    "their shipped CLIs, a stamp-aligned matrix regeneration, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches")

BACKLOG_ROW = (
    "- [x] [done 2026-11-04 R2444] R2444 product window on the debt gate "
    "first=yes item (product-face-R2444, tech head state/queue/tech.md:510 "
    "prefix AC-PICIC1, AC-PICIC1..AC-PICIC6 pinned there at R2430 BEFORE any "
    "code): SHIPPED src/os/comma_binding_identity_face_compare.py plus its "
    "six-criteria suite. All three publisher faces are asked at CALL time and "
    "no table is restated, and each face's SEAM is measured by wrapping both "
    "seam providers for that face's own audit - LIVE on the real src/os the "
    "sibling faces read comma_binding_sibling_faces.receivers_for:33 while "
    "the identity face reads receivers_for:33 AND "
    "comma_binding_consumer_wire.wire_audit_script:33, so the second path the "
    "sibling compare never asked is now published as a fact rather than "
    "assumed. SUITE PASS 6/6 twice identical digest 6D174EB5708FE9E5, three "
    "adjacent comma suites green "
    "(qa/comma-binding-identity-face-compare-R2444.log), registry 550 suites "
    "/ 4276 criteria, matrix regenerated stamp-aligned to 55305B with --check "
    "byte-identical. One real gap seeded from this window's own measurement "
    "(verdict-level compare misses per-line module drift; 6/7/8-key row "
    "shapes), product-face-R2444 closed and reconcile-battery-R2445 opened "
    "first=yes at 550/4276. Zero CEO-visible business surface."
)

HEARTBEAT_ROW = (
    "2026-11-04T21:47:00+08:00 tick=2444 R2444 product window - "
    "comma_binding_identity_face_compare asks all three publisher faces on "
    "one tree and measures each face's receiver-table seam instead of "
    "asserting it; LIVE src/os verdict=FACES-AGREE 11 publishers 33 rows with "
    "the identity face reading both seams "
    "(receivers_for:33 + consumer_wire:33) while the siblings read one; SUITE "
    "PASS 6/6 twice identical digest 6D174EB5708FE9E5, three adjacent suites "
    "green, registry 550 suites / 4276 criteria, matrix regenerated "
    "stamp-aligned to 55305B [via BigDomain-OSLoop]")


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
        raise SystemExit("E_R2444_BACK read-back does not match the write")
    return len(back)


def main(execute):
    if TOKENS is None:
        raise SystemExit("E_R2444_TOKENS the token line is not set")
    if not execute:
        print("DRY RUN tick=%d log_lines=%d" % (TICK, len(LOG) + 1))
        for line in LOG:
            print("  LOG %s" % line[:100])
        print("  TOKENS %s" % TOKENS[:100])
        return 0

    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["tick"] != TICK - 1:
        raise SystemExit("E_R2444_TICK state reads %s, expected %d"
                         % (payload["tick"], TICK - 1))
    payload["tick"] = TICK
    payload["last_decision_rows"] = DEC_ROWS
    payload["log"].extend(LOG)
    payload["log"][-1] = payload["log"][-1]
    payload["log"].append(TOKENS)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2444_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2444-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d layout_ok=%s crlf=%d bare_lf=%d"
          % (TICK, size, len(payload["log"]), layout["layout_ok"],
             layout["crlf"], layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if "R2444] R2444 product window" in backlog:
        raise SystemExit("E_R2444_BACKLOG row already present")
    write_bytes_atomic(BACKLOG, (BACKLOG_ROW + "\n" + backlog).encode(
        "utf-8"), ".r2444-backlog-")
    print("BACKLOG row prepended")

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    if "tick=2444 " in beat:
        raise SystemExit("E_R2444_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    write_bytes_atomic(HEARTBEAT, (beat + HEARTBEAT_ROW + "\n").encode(
        "utf-8"), ".r2444-beat-")
    print("HEARTBEAT row appended")
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))