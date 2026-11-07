"""R2515 closeout: append this product window's log items and move the tick.

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
    "2026-11-07 R2515 PRODUCT window on the tech head the register named "
    "(product-face-R2514, state/queue/tech.md:552 prefix AC-PSF1 "
    "probe_seam_forwarding_scope, criteria AC-PSF1..AC-PSF6 pinned in that "
    "row at R2513 BEFORE any code). Five-silence scan at open was clean at "
    "HEAD f80b75a9: git status empty, no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, content-addressed decisions diff new=0 over "
    "the stored 90-token baseline at a measured 189 rows (89 distinct tokens "
    "now), group orders tail unchanged at 2026-11-06 23:46 so last_order "
    "stands, benchmarks 2026-11-03 inside the seven-day gate. The debt gate "
    "read CLAIM-FIRST item=reconcile-battery-R2515 opened=R2515 first=1 with "
    "product-face-R2514 carried, and that battery is owed by THIS window, so "
    "the product byte came first per the R2168 mixed-tree rule and the "
    "battery is registered for the next window at the registry the shipped "
    "row moved to.",

    "2026-11-07 R2515 CLAIM AND SHIP: R2513 disclosed and MEASURED that a "
    "probe which quiets the render guard seams through a shared helper names "
    "no seam itself, so probe_seam_registry read it OUT-OF-SCOPE while the "
    "helper read COVERED and the forwarding shape was invisible. SHIPPED "
    "src/os/probe_seam_forwarding_scope.py plus its suite. The hop is DERIVED "
    "at CALL time from the probe own module-level import statements and each "
    "helper own syntax tree: no helper list and no seam name is spelled in "
    "the module, a bare string that merely names a helper is not an import, "
    "and editing ONLY a helper moves the same probe MISSING-SEAM -> COVERED "
    "with no code change. A forwarding probe reads COVERED with the helpers "
    "it was followed through named on its row; a helper that omits a seam "
    "makes the probe MISSING-SEAM naming seam and file and the probe is never "
    "imported or run; a module importing helpers that quiet nothing stays "
    "OUT-OF-SCOPE; an unparseable source or helper reads UNREADABLE rather "
    "than being skipped; a round-token file reads HISTORICAL.",

    "2026-11-07 R2515 ONE REGISTERED HOP WAS NOT ENOUGH, MEASURED BEFORE "
    "SHIPPING: a one-hop reading INVENTS a MISSING-SEAM when a middle helper "
    "names part of the set and re-exports the rest, which is worse than the "
    "gap it closes. The shipped reading therefore follows local imports "
    "transitively (same root only, cycle-guarded, depth 8) and the suite "
    "proves the chain shape reads COVERED with the middle helper named and "
    "the cycle terminates; this is a strict superset of the registered face "
    "and is disclosed rather than hidden. A file whose name carries a round "
    "token is still HISTORICAL, so the one-off scripts of this round are "
    "named in the counts rather than counted against the tree.",

    "2026-11-07 R2515 PROOF measured, not quoted: AC-PSF1..AC-PSF6 SUITE "
    "PASS 6/6 TWICE with an identical digest plus four adjacent readability "
    "suites green (qa/probe-seam-forwarding-scope-R2515.log, 6183B, "
    "legs=2 identical=True fails=0 adjacent=4) captured through the shipped "
    "evidence callable. LIVE LEG on the REAL tree through the shipped single "
    "evidence writer: qa/probe-seam-forwarding-scope-live-R2515.log (1132B, "
    "class=tee) reads verdict=SEAMS-FORWARDED over 3 covered probes, 167 "
    "out-of-scope modules and 1199 historical one-shot scripts with the "
    "render and artifact digests unchanged across the reading, then a "
    "forwarding fixture reads COVERED helpers=quiet_helper quieted=5 and a "
    "stale fixture reads MISSING-SEAM missing=STPT while the fixture tree "
    "reads SEAMS-FORWARD-STALE (exit 2 by the tool). The real-tree audit "
    "costs 1.74s.",

    "2026-11-07 R2515 REGISTRY, MATRIX, BOARD AND DEBT: one runner row "
    "os-probe-seam-forwarding-scope(6), so the registry reads 587 suites / "
    "4498 criteria, recounted by importing reconcile_all.SUITES. The row "
    "moved the artifact, so docs/sandbox-suite-matrix.md was regenerated "
    "stamp-aligned from qa/reconcile-all-R2514-retry.log to 56475B at 587 "
    "suites / 4498 criteria with --check byte-identical, and its green line "
    "honestly reads 586/587 because the battery for this tree has not run "
    "yet. The claimed row 552 was closed through a per-round writer with its "
    "DISCHARGED note (predicted and measured 1674931B, readback ok) and ONE "
    "row was seeded from this window own live measurement: a probe that "
    "imports its quieting helper INSIDE a function body reads OUT-OF-SCOPE "
    "quieted=0 because only module-level imports are followed (lazy fixture "
    "in the live log), seeded as AC-PSL1..AC-PSL6; queue_floor then read "
    "FLOOR-MET 5/5 10/10 10/10 with the new head at line 553. Debt through "
    "the shipped writers: product-face-R2514 closed (line 237, open 4->3, "
    "done 215->216, 148756B -> 148759B, readback ok), reconcile-battery-R2515 "
    "appended first=yes at the pre-registered 587/4498 (148759B -> 149123B), "
    "product-face-R2515 appended first=no naming tech line 553 AC-PSL1 "
    "(149123B -> 149635B); the gate now names reconcile-battery-R2515 first.",

    "2026-11-07 R2515 honest disclosures: (a) ONE product point on the "
    "Executive Protocol scale - a runnable CLI reading that now names a "
    "forwarding probe instead of skipping it - and nothing a CEO could open "
    "was newly built; (b) the defect was MEASURED at R2513 in that window own "
    "live leg and re-measured here, so this is a repair of a disclosed gap "
    "rather than a new discovery; (c) the registered face said ONE hop and "
    "the shipped reading follows local imports transitively because a one-hop "
    "reading could invent a MISSING-SEAM - named here as a superset, not "
    "smuggled in; (d) DISCLOSED LIMITS measured this window: only "
    "module-level imports in the SAME root are followed, at most 8 hops, so a "
    "quieting performed inside a function body (lazy fixture reading "
    "OUT-OF-SCOPE) or from another directory is still invisible and is seeded "
    "as the next tech row; (e) no battery ran this window by design and the "
    "register now owes reconcile-battery-R2515 at the pre-registered 587 "
    "suites / 4498 criteria BEFORE any further product byte; (f) the raw "
    "checkers queue_row --check and queue_done_stamp --check read VIOLATION / "
    "UNSTAMPED on OLD rows (tech 524 and 537, explore 295/614/615/618) that "
    "pre-date this window and were not touched - the battery runs the shipped "
    "SUITES, not these raw readers, and the condition is reported rather than "
    "silently fixed; (g) the real 19.9 debit and the real msgSecCheck still "
    "wait on CEO physical items (merchant id, mini-program appid/secret); "
    "(h) tasks.md was not touched, it is the P-47 canonical board; (i) the "
    "S4U lane reconcile (loop-s4u-reconcile) still needs an ELEVATED shell "
    "and was not attempted, BigDomain-OSLoop still reads InteractiveToken; "
    "(j) Docker is absent on this host so no containerised bring-up of the "
    "sandbox faces is claimed.",

    "R2515 tokens: local=~17k api=0 api_reason=product window - one "
    "pre-registered face shipped with its six criteria, one suite proved "
    "twice with four adjacent suites, one live leg on the real tree with a "
    "forwarding fixture, a stale fixture and a measured lazy gap, one "
    "transitive-following repair made because a one-hop reading could invent "
    "a defect, one registry row recounted by import, one matrix "
    "stamp-aligned regeneration checked byte-identical, one queue row closed "
    "and one seeded through their shipped writers, three debt rows moved "
    "through their shipped writers, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2515
    state["last_decision_rows"] = 189
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
          and back["tick"] == 2515
          and back["last_decision_rows"] == 189
          and back["log"][-1] == LINES[-1])
    print("state %s tick=%s log=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             os.path.getsize(PATH), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())