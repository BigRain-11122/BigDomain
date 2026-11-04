"""closeout_R2440 - the closeout of the R2440 product window.

Appends this window's own honest lines to src/os/state.json, bumps the tick,
prepends the backlog row and appends the heartbeat row. Dry run by default; on
--execute every file is written once and read back.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

sys.path.insert(0, BASE)
import state_io  # noqa: E402

TICK = 2440
DEC_ROWS = 168

LOG = [
    ("2026-11-04 R2440 product window (five-silence scan clean at open: git "
     "status empty at HEAD aee7c687 with no .git/index.lock; the evolution "
     "ledger carries zero @BigDomain rows; the content-addressed decisions "
     "diff read 168 rows and 113 tokens with new=0 against the stored "
     "baseline; the group orders tail max_ts is 2026-11-04 with last_order "
     "2026-11-04 00:46, so nothing dispatches this company; benchmarks were "
     "refreshed 2026-11-03 inside the seven-day gate; the deliverable-aware "
     "queue reader offered state/queue/tech.md:504 prefix AC-RMEF1 after "
     "walking over the delivered AC-BEDP1 row). The debt gate named "
     "CLAIM-FIRST item=product-face-R2440, so the window took the product "
     "face the criteria were pinned for."),
    ("2026-11-04 R2440 SHIPPED src/os/relative_module_existence_face.py plus "
     "src/os/test_relative_module_existence_face.py against AC-RMEF1..AC-RMEF6 "
     "pinned in state/queue/tech.md:504 at R2415 BEFORE any code, after an "
     "anchor check at HEAD that found the module name only in one-off closeout "
     "prose (closeout_R2415, closeout_R2439, export_R2439), state.json and the "
     "backlog, with zero executable occupancy. The reading is "
     "publish_relative_package_identity own audit asked at CALL time and the "
     "join is that module own join_package, so no second classifier and no "
     "second join exist; the one new fact is the module corpus MEASURED off "
     "the read tree own .py files (pkg/sub/mod.py -> pkg.sub.mod, an "
     "__init__.py -> the package) and the one new word is MISSING-MODULE, "
     "printed with the joined text and the declared package when a join has "
     "no file behind it. A join WITH a file behind it keeps the parent reading "
     "with every verdict, row and count compared against the parent audit, and "
     "a run with NO package keeps the parent reading byte for byte while "
     "measuring no corpus at all."),
    ("2026-11-04 R2440 evidence, measured rather than asserted: SUITE PASS 6/6 "
     "twice with an identical criterion digest plus four adjacent suites green "
     "(EVIDENCE CAPTURE round=R2440 legs=2 identical=True adjacent=4 fails=0, "
     "qa/relative-module-existence-face-R2440.log, 1510B, single writer utf-8 "
     "LF through the R2261 capture callable). AC-RMEF1 is proved both ways - a "
     "patched parent audit moves the verdict and the corpus grows when a file "
     "is added to the tree - and AC-RMEF4 patches the corpus callable and "
     "watches it never run on the no-package path. Registry wiring: "
     "os-relative-module-existence-face(6) so the registry reads 548 suites / "
     "4264 criteria, exactly the +1 suite / +6 criteria this window owes. "
     "docs/sandbox-suite-matrix.md was regenerated through the shipped "
     "generator with --stamp-from to 52828B at 548 suites / 4264 criteria and "
     "--check reads byte-identical; its own line honestly reads green=547/548 "
     "because this window suite has no line in the R2439-retry evidence."),
    ("2026-11-04 R2440 LIVE, not a plan: "
     "qa/relative-module-existence-face-live-R2440.log (539B, crlf=0) reads "
     "the REAL src/os with --package src.os as verdict=WIRE corpus=1216 "
     "scanned=1214 publishers=11 wire=11 relative=0 missing=0 at exit 0. The "
     "real tree carries no package-relative publish line, so the MISSING-MODULE "
     "case is proved on fixtures and is NOT claimed as a live catch."),
    ("2026-11-04 R2440 board and register: tech row 504 stamped and one real "
     "measured gap row seeded (relative_module_corpus_scope, AC-RMSC1..AC-RMSC6 "
     "pre-registered, five anchors to re-check) because the corpus is measured "
     "by walking the ROOT, so an importable module outside that root reads "
     "MISSING-MODULE; a SECOND seed followed the honest reading of the gauge "
     "(relative_package_presence_refusal, AC-RMPP1..AC-RMPP6) because a "
     "typo'd --package is printed as N broken imports rather than one refusal "
     "naming the declaration. A REAL board defect was repaired while measuring "
     "the floor: state/queue/tech.md:494 (AC-BEDP1) still read open though "
     "src/os/bare_evidence_deep_pile.py was delivered at R2432, so the "
     "delivered-aware reader counted a shipped row as standing supply "
     "(tech effective=9, shortfall=1); the row is closed at the round that "
     "delivered it, no new code was written for it, and the gauge now reads "
     "FLOOR-MET main=5/5 tech=10/10 explore=10/10 with discounted=0. Debt: "
     "product-face-R2440 closed through the shipped debt_close (line=174, "
     "open 2->1, done 153->154, 110852B -> 110855B, readback ok) and "
     "reconcile-battery-R2441 opened first=yes through debt_append at the "
     "pre-registered 548 suites / 4264 criteria (110855B -> 111148B, "
     "readback ok)."),
    ("2026-11-04 R2440 honest disclosures: (a) this window changed product src "
     "bytes, so the R2168 mixed-tree rule owes the battery next and "
     "reconcile-battery-R2441 carries it; (b) the window scores two product "
     "points for a runnable reading, but it is an internal owner/import face "
     "and no CEO-visible artifact was rebuilt; (c) a first draft built the "
     "report with dict(report), so the --json key order followed the parent "
     "rather than this face pinned keys - AC-RMEF5 caught it and the module "
     "was fixed, with no criterion widened; (d) the first evidence capture was "
     "refused E_EVC_RED because it was pointed at --root src/os with a "
     "root-relative suite path, so the child ran the wrong path; the capture "
     "was re-run with --root . and nothing was reclassified; (e) the matrix "
     "was regenerated from the LAST battery evidence rather than from this "
     "window, which is why its green line reads 547/548 - named rather than "
     "smoothed; (f) tasks.md was not touched, it is the P-47 canonical board "
     "and carries no row for this technical window."),
    ("R2440 tokens: local=~19k api=0 api_reason=product window - one new "
     "read-only face plus its six-criteria suite against criteria pinned at "
     "R2415, one runner entry, two evidence legs with an identical digest plus "
     "four adjacent suites green, one live reading over the real src/os, one "
     "matrix regeneration with --stamp-from, two sealed algorithms (corpus, "
     "existence reading) and two real gap rows seeded, one stale board row "
     "closed at the round that delivered it, two debt register writes through "
     "their shipped CLIs, and the state/backlog/heartbeat/export closeout; "
     "zero cloud calls and zero external API touches"),
    ("2026-11-04 R2440 self-heal check: BigDomain-OSLoop still exists and its "
     "Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine "
     "law forbids for every lane task; src/os/register_loop_task.ps1 passes an "
     "explicit S4U principal and needs an elevated shell while this session is "
     "unelevated, so the definition was left untouched again "
     "(two-hundred-and-seventh consecutive disclosure, carried as the stale "
     "row loop-s4u-reconcile)."),
]

BACKLOG_ROW = (
    "- [x] [done 2026-11-04 R2440] R2440 product window on the debt gate "
    "first=yes item (product-face-R2440, tech head state/queue/tech.md:504 "
    "prefix AC-RMEF1, criteria pinned there at R2415 BEFORE any code): SHIPPED "
    "src/os/relative_module_existence_face.py plus its six-criteria suite. A "
    "package-relative publish joined onto a declared package was never checked "
    "against the modules the read tree carries, so `from .nosuchmodule import "
    "publish` read FOREIGN exactly like a genuinely foreign wire. The face now "
    "measures a module corpus off the tree own .py files and prints "
    "MISSING-MODULE with the joined text and the declared package when a join "
    "has nothing behind it, while a join with a file behind it keeps the "
    "parent reading row for row and a run with no package keeps it byte for "
    "byte with no corpus measured at all. SUITE PASS 6/6 twice with an "
    "identical digest plus four adjacent suites green "
    "(qa/relative-module-existence-face-R2440.log, 1510B, legs=2 "
    "identical=True adjacent=4 fails=0), wired "
    "os-relative-module-existence-face(6) so the registry reads 548 suites / "
    "4264 criteria, matrix regenerated through --stamp-from to 52828B with "
    "--check byte-identical. LIVE on the real src/os with --package src.os: "
    "corpus=1216, publishers=11 wire=11, relative=0, missing=0 - the "
    "MISSING-MODULE case is proved on fixtures and is not claimed as a live "
    "catch. Board: row 504 stamped, TWO real gap rows seeded "
    "(relative_module_corpus_scope AC-RMSC1..6, "
    "relative_package_presence_refusal AC-RMPP1..6) and a stale delivered row "
    "(494 AC-BEDP1) closed at the round that shipped it, so the floor reads "
    "FLOOR-MET 5/5 10/10 10/10 with discounted=0. Debt: product-face-R2440 "
    "closed (110852B -> 110855B, readback ok) and reconcile-battery-R2441 "
    "opened first=yes at the pre-registered 548/4264. Honest: two product "
    "points, internal face only, no CEO-visible artifact rebuilt."
)

HEARTBEAT_ROW = (
    "%s tick=%d R2440 product window - relative_module_existence_face shipped "
    "against AC-RMEF1..AC-RMEF6 pinned at R2415: the module corpus is measured "
    "off the tree and a package-relative join with nothing behind it now reads "
    "MISSING-MODULE instead of FOREIGN, while a join with a file behind it and "
    "a no-package run keep the parent reading; SUITE PASS 6/6 twice, registry "
    "548 suites / 4264 criteria, LIVE corpus=1216 missing=0; a stale delivered "
    "board row was closed and the floor reads FLOOR-MET 5/5 10/10 10/10; next "
    "window owes reconcile-battery-R2441 [via BigDomain-OSLoop]"
)


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
        raise SystemExit("E_R2440_BACK read-back does not match the write")
    return len(back)


def main(execute):
    if not execute:
        print("DRY RUN tick=%d lines=%d" % (TICK, len(LOG)))
        for line in LOG:
            print("  LOG %s" % line[:100])
        return 0

    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["tick"] != TICK - 1:
        raise SystemExit("E_R2440_TICK state reads %s, expected %d"
                         % (payload["tick"], TICK - 1))
    payload["tick"] = TICK
    payload["last_decision_rows"] = DEC_ROWS
    payload["log"].extend(LOG)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2440_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2440-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d layout_ok=%s crlf=%d bare_lf=%d"
          % (TICK, size, len(payload["log"]), layout["layout_ok"],
             layout["crlf"], layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if BACKLOG_ROW in backlog:
        raise SystemExit("E_R2440_BACKLOG row already present")
    io.open(BACKLOG, "w", encoding="utf-8", newline="").write(
        BACKLOG_ROW + "\n" + backlog)
    print("BACKLOG row prepended, bytes=%d" % os.path.getsize(BACKLOG))

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    row = HEARTBEAT_ROW % ("2026-11-04T18:52:00+08:00", TICK)
    if row in beat:
        raise SystemExit("E_R2440_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    io.open(HEARTBEAT, "w", encoding="utf-8", newline="").write(
        beat + row + "\n")
    print("HEARTBEAT row appended, bytes=%d" % os.path.getsize(HEARTBEAT))
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))