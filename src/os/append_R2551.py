"""R2551 closeout append: the product window on the AC-PNDP1 head.

The shipped state_fold layout reader still refuses this file and state_fold.py
offers ONLY a --check face, so the append is a PROVED load+dump round-trip:
the bytes are read, decoded, re-encoded and compared byte for byte BEFORE any
mutation, and only then are the tick and the log rows written.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

ROUND = (
    "2026-11-08 R2551 PRODUCT window on the tech head the register named "
    "(product-face-R2550, state/queue/tech.md:587 prefix AC-PNDP1 "
    "probe_seam_name_binding_nested_arm_mixed_scope, criteria AC-PNDP1.."
    "AC-PNDP6 pinned in that row at R2549 BEFORE any code). Five-silence at "
    "open: git status EMPTY with no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed decisions diff read new=0 "
    "over the stored 182-token baseline at a measured 70 rows, the group orders "
    "tail unchanged at 2026-11-08 00:04 (OB-20261108-000400-425, already judged "
    "knowledge-only), benchmarks 2026-11-03 inside the seven-day gate. The debt "
    "gate read CLAIM-FIRST item=product-face-R2550 first=1 with no battery owed "
    "because R2550 moved no product byte, queue_head named tech line 587 "
    "claimable=12 with the floor MET, and all five pinned anchors were "
    "re-checked at zero occupancy at HEAD before any code: every hit was a seed "
    "row, a bookkeeping writer, state prose or the export face, never an "
    "implementation. "
    "SHIPPED src/os/probe_seam_name_binding_nested_arm_mixed_scope.py plus its "
    "six-criteria suite. MEASURED at R2549 on the nested face own reader and "
    "re-measured here before shipping: (1) an arm that binds KEY DIRECTLY and "
    "also contains a nested guard read mixed:body and resolved nothing even "
    "though all four leaves bound the same literal; (2) a try whose else "
    "rebinds the same literal read incomplete:try:2; (3) a with-as arm read "
    "non-literal:body, hiding the reason. The shipped face folds a direct arm "
    "binding together with the nested tree under it and resolves ONLY when "
    "every leaf binds the same single literal, publishes BOTH values by full "
    "path when they disagree, treats a try else as a coverage arm while an "
    "empty else stays partial:else, and NAMES a with-as arm with-as:<arm>; a "
    "finally is still refused as incomplete and says so. "
    "PROOF measured, not quoted: AC-PNDP1..AC-PNDP6 SUITE PASS 6/6 TWICE with "
    "identical output plus five adjacent probe suites green "
    "(qa/probe-seam-name-binding-nested-arm-mixed-scope-R2551.log, 20653B, "
    "legs=2 identical=True fails=0 adjacent=5, landed through the shipped "
    "capture callable), and a BOUNDED live leg on the real probe family reads "
    "SEAMS-ARM-MIXED-COVERED over 20 probe_seam modules with 571 arm loop rows "
    "and the SAME fixture measured on BOTH readers: THIS face reads ok/b while "
    "the R2549 face reads refused mixed:body "
    "(qa/probe-seam-name-binding-nested-arm-mixed-scope-live-R2551.log). "
    "REGISTRY, MATRIX, BOARD AND DEBT: one runner row "
    "os-probe-seam-name-binding-nested-arm-mixed-scope(6), so the registry reads "
    "605 suites / 4606 criteria, recounted by importing reconcile_all.SUITES "
    "rather than trusted; docs/sandbox-suite-matrix.md was regenerated "
    "stamp-aligned from the ELIGIBLE battery leg qa/reconcile-all-R2550.log to "
    "58666 bytes at 605 suites / 4606 criteria with its green line honestly "
    "reading 604/605, and --check then read byte-identical at rc=0. The claimed "
    "row 587 was closed through src/os/queue_close_R2551.py at its predicted "
    "and measured 1757384B and ONE row was seeded from this window own MEASURED "
    "limits (a module-level with-as refusal carries reason None, two sequential "
    "nested groups under one arm read grouped:<arm>, and a direct binding "
    "through a module-level constant NAME reads non-literal:<arm>) as "
    "AC-PNDQ1..AC-PNDQ6 with its five anchors re-checked at zero occupancy "
    "before the write; queue_head then read the new head at line 589 prefix "
    "AC-PNDQ1 and queue_floor read FLOOR-MET main=5/5 tech=12/10 explore=10/10. "
    "DEBT through the shipped writers: product-face-R2550 closed (line 288, "
    "open 21->20, done 249->250, 171254B -> 171257B, readback ok) and "
    "reconcile-battery-R2551 appended first=yes at the pre-registered 605/4606 "
    "(171257B -> 171580B, readback ok), so the gate now names that battery "
    "first."
)


def honest_line(size):
    return (
        "2026-11-08 R2551 honest disclosures: (a) TWO product points on the "
        "Executive Protocol scale - a runnable CLI with its own suite and a "
        "live reading a maintainer can run - but nothing a CEO could newly "
        "open and no P-47 business surface moved; (b) THE WHOLE-TREE LIVE LEG "
        "WAS ATTEMPTED AND STOPPED on budget after several minutes of an audit "
        "that walks every module in src/os, so the leg actually shipped is "
        "BOUNDED to the 20 real probe_seam modules and ZERO of those probes "
        "were COVERED (all twenty read OUT-OF-SCOPE), which makes the verdict "
        "honest but weak and is stated rather than dressed up; (c) a REAL "
        "DEFECT IN A SHIPPED FACE was measured this window: a module-level "
        "with-as binding comes back from the nested face as a refusal whose "
        "reason is None - the caller is told nothing - and it is seeded as "
        "AC-PNDQ1 rather than silently repaired inside this window; (d) the "
        "round was declared through the shipped queue writers at their "
        "predicted byte counts (row 587 predicted 1757384B = measured "
        "1757384B), and ONE of my own first-pass defects in the closeout "
        "reader (a log line carrying three counters was parsed as one value) "
        "was corrected BEFORE the writer ran, so no byte was written twice; "
        "(e) state.json reads %dB against the 78500B waterline so state_fold "
        "--check reads FOLD-DUE, the shipped tool still ships only a --check "
        "face, and the fold remains an OWED obligation; (f) two further arm "
        "shapes stay refused and are seeded rather than smoothed - two "
        "sequential nested groups under one arm read grouped:body even when "
        "every leaf agrees, and a direct binding through a module-level "
        "constant name reads non-literal:body; (g) Docker is absent on this "
        "host so no containerised bring-up of the sandbox faces is claimed; "
        "(h) the real 19.9 debit and the real msgSecCheck still wait on CEO "
        "physical items (merchant id, mini-program appid/secret); (i) tasks.md "
        "was not touched, it is the P-47 canonical board; (j) the S4U lane "
        "re-registration still needs an ELEVATED shell and remains a "
        "ceo-pending physical item with zero chase; (k) the round overshot its "
        "25-minute budget on the stopped whole-tree leg and the bounded rerun "
        "and says so." % (size,)
    )


TOKENS = (
    "R2551 tokens: local=~15k api=0 api_reason=product window - five-silence "
    "scan, one content-addressed decisions scan reading new=0, one "
    "zero-occupancy anchor check on five anchors, one pre-registered face "
    "shipped with its six criteria and its suite, one two-leg evidence capture "
    "with five adjacent suites, one whole-tree live attempt STOPPED on budget, "
    "one bounded live leg with the same fixture on both readers, one real "
    "defect measured and seeded, one registry row recounted by import, one "
    "stamp-aligned matrix regeneration checked byte-identical, one board row "
    "closed and one seeded through their shipped writers, two debt rows moved "
    "through their shipped writers, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches"
)


def main():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    replay = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    if replay.encode("utf-8") != raw:
        print("REFUSED E_APP_ROUNDTRIP: dump does not reproduce the file")
        return 3
    state["tick"] = 2551
    state["last_decision_rows"] = 70
    state["log"].extend([ROUND, honest_line(len(raw)), TOKENS])
    out = (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    tmp = STATE + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(out)
    os.replace(tmp, STATE)
    back = open(STATE, "rb").read()
    print("APPENDED before=%dB after=%dB tick=%d log=%d readback=%s"
          % (len(raw), len(back), state["tick"], len(state["log"]),
             "ok" if back == out else "MISMATCH"))
    return 0


if __name__ == "__main__":
    sys.exit(main())