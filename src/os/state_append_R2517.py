"""R2517 closeout: append this product window's log items and move the tick.

The write is one atomic replace in the state canon through the shipped
state_io.canon, proved by a read-back.
"""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

LINES = [
    "2026-11-07 R2517 PRODUCT window on the tech head the register named "
    "(product-face-R2516, state/queue/tech.md:553 prefix AC-PSL1 "
    "probe_seam_lazy_scope, criteria AC-PSL1..AC-PSL6 pinned in that row at "
    "R2515 BEFORE any code). Five-silence scan at open was clean at HEAD "
    "3c3a4e5f: git status empty, no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, content-addressed decisions diff new=0 over "
    "the stored 90-token baseline, group orders tail unchanged at 2026-11-06 "
    "23:46 so last_order stands, benchmarks 2026-11-03 inside the seven-day "
    "gate. The debt gate read CLAIM-FIRST item=product-face-R2516 "
    "opened=R2516 carried=1 stale=no open=5 first=1, and NO successor battery "
    "was owed because R2516 moved no product src byte. Zero-occupancy of the "
    "five anchors was re-checked at HEAD before any code: no "
    "src/os/probe_seam_lazy_scope.py and no suite existed, and the token "
    "appeared only in registration files.",

    "2026-11-07 R2517 CLAIM AND SHIP: R2515 MEASURED in its own live leg that "
    "a probe importing its quieting helper INSIDE a function body reads "
    "OUT-OF-SCOPE with zero quieted seams, because the forwarding face reads "
    "only module-level import statements, so a lazy forwarding probe was "
    "invisible again. SHIPPED src/os/probe_seam_lazy_scope.py plus its suite. "
    "Import resolution is DERIVED at CALL time from the probe own syntax tree "
    "at ANY nesting level on the same cycle-guarded same-root walk, so no "
    "helper list and no seam name is spelled in the module, and a bare string "
    "that merely names a helper is not an import. A lazy forwarding probe "
    "reads COVERED with the helpers it was followed through and the lazy "
    "imports it took named on its row; a lazy helper that omits a seam makes "
    "the probe MISSING-SEAM naming seam and file and the probe is never "
    "imported or run; a module whose lazy imports quiet nothing stays "
    "OUT-OF-SCOPE; a lazily chained helper is followed so a partial middle "
    "helper cannot invent a missing seam; a lazy import cycle terminates; an "
    "unparseable source or helper reads UNREADABLE; a round-token file reads "
    "HISTORICAL.",

    "2026-11-07 R2517 PROOF measured, not quoted: AC-PSL1..AC-PSL6 SUITE PASS "
    "6/6 TWICE with an identical digest plus two adjacent probe faces green "
    "(qa/probe-seam-lazy-scope-R2517.log, 6504B, legs=2 identical=True "
    "fails=0 adjacent=2) captured through the shipped single evidence writer. "
    "LIVE LEG on the REAL tree through the same writer: "
    "qa/probe-seam-lazy-scope-live-R2517.log (625B, class=tee) reads "
    "verdict=SEAMS-LAZY-COVERED over 3 covered probes, 168 out-of-scope "
    "modules and 1208 historical one-shot scripts, then a lazy fixture reads "
    "COVERED helpers=quiet_helper quieted=5 while the SAME fixture reads "
    "OUT-OF-SCOPE quieted=0 under the module-level forwarding face, and a "
    "stale lazy fixture reads MISSING-SEAM missing=STPT with the fixture tree "
    "reading SEAMS-LAZY-STALE; render and artifact digests were unchanged "
    "across the reading.",

    "2026-11-07 R2517 REGISTRY, MATRIX, BOARD AND DEBT: one runner row "
    "os-probe-seam-lazy-scope(6), so the registry reads 588 suites / 4504 "
    "criteria, recounted by importing reconcile_all.SUITES. The row moved the "
    "artifact, so docs/sandbox-suite-matrix.md was regenerated stamp-aligned "
    "from qa/reconcile-all-R2516.log to 56544B at 588 suites / 4504 criteria "
    "with --check byte-identical, and its green line honestly reads 587/588 "
    "because the battery for this tree has not run yet. The claimed row 553 "
    "was closed through a per-round writer with its DISCHARGED note "
    "(predicted and measured 1679440B, readback ok) and ONE row was seeded "
    "from this window own live measurement: a probe that builds its import at "
    "RUN time (importlib.import_module with a literal, or __import__) reads "
    "OUT-OF-SCOPE quieted=0 in both shipped readers, seeded as AC-PDI1..AC-PDI6; "
    "queue_floor then read FLOOR-MET 5/5 10/10 10/10 with the new head at "
    "line 555. Debt through the shipped writers: product-face-R2516 closed "
    "(line 240, open 5->4, done 217->218, 150420B -> 150423B, readback ok), "
    "reconcile-battery-R2517 appended first=yes at the pre-registered 588/4504 "
    "(150423B -> 150786B), product-face-R2517 appended first=no naming tech "
    "line 555 AC-PDI1 (150786B -> 151161B) after ONE refusal "
    "E_DEBTA_BAD_FIELD for an equals sign in the note, obeyed and rewritten in "
    "words; the gate now names reconcile-battery-R2517 first.",

    "2026-11-07 R2517 honest disclosures: (a) ONE product point on the "
    "Executive Protocol scale - a runnable CLI reading that now names a lazy "
    "forwarding probe instead of skipping it - and nothing a CEO could open "
    "was newly built; (b) the defect was MEASURED at R2515 in that window own "
    "live leg and re-measured here, so this is a repair of a disclosed gap "
    "rather than a new discovery; (c) DISCLOSED LIMITS measured this window: "
    "only import STATEMENTS with local modules in the SAME root are followed, "
    "at most 8 hops, so a module name built at run time (importlib with a "
    "computed name, __import__ with a computed name) or resolved from another "
    "directory is still invisible and is seeded as the next tech row; (d) no "
    "battery ran this window by design because none was owed, and the "
    "register now owes reconcile-battery-R2517 at the pre-registered 588 "
    "suites / 4504 criteria BEFORE any further product byte; (e) the group "
    "decisions file was READ at 116 rows while the stored baseline recorded "
    "189 rows, its token set is unchanged at 90 and the scanner reads new=0, "
    "so no new decision arrived and the row figure is recorded honestly "
    "rather than silently carried; (f) the raw checkers queue_row --check and "
    "queue_done_stamp --check still read VIOLATION / UNSTAMPED on OLD rows "
    "that pre-date this window and were not touched - the battery runs the "
    "shipped SUITES, not these raw readers, and the condition is reported "
    "rather than silently fixed; (g) the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items (merchant id, mini-program "
    "appid/secret); (h) tasks.md was not touched, it is the P-47 canonical "
    "board; (i) the S4U lane reconcile (loop-s4u-reconcile) still needs an "
    "ELEVATED shell and was not attempted, BigDomain-OSLoop still reads "
    "InteractiveToken; (j) Docker is absent on this host so no containerised "
    "bring-up of the sandbox faces is claimed.",

    "R2517 tokens: local=~15k api=0 api_reason=product window - five-silence "
    "scan, one zero-occupancy anchor check, one pre-registered face shipped "
    "with its six criteria, one suite proved twice with an identical digest "
    "plus two adjacent suites, one live leg on the real tree with a lazy "
    "fixture measured on BOTH readers, one registry row recounted by import, "
    "one stamp-aligned matrix regeneration checked byte-identical, one queue "
    "row closed and one seeded through their shipped writers, three debt rows "
    "moved through their shipped writers, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2517
    state["last_decision_rows"] = 116
    state["log"].extend(LINES)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"])
          and back["tick"] == 2517
          and back["last_decision_rows"] == 116
          and back["log"][-1] == LINES[-1])
    print("state %s tick=%s log=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             os.path.getsize(PATH), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())