"""R2549 closeout append: a product window.

The shipped state_fold layout reader still refuses this file and the shipped
state_fold.py offers ONLY a --check face, so the append is a PROVED
load+dump round-trip: the bytes are read, decoded, re-encoded and compared
byte for byte BEFORE any mutation, and only then are the tick and the log
rows written.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-08 R2549 PRODUCT window on the tech head the register named "
    "(product-face-R2548, state/queue/tech.md:585 prefix AC-PNCD1 "
    "probe_seam_name_binding_nested_exhaustive_path, criteria AC-PNCD1..AC-PNCD6 "
    "pinned in that row at R2547 BEFORE any code). Five-silence scan at open: git status "
    "EMPTY with no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the "
    "content-addressed decisions diff read new=0 over the stored baseline at a measured "
    "42 rows / 47 file tokens, the group orders tail unchanged at 2026-11-08 00:04 "
    "(OB-20261108-000400-425, already judged knowledge-only at R2543), benchmarks "
    "2026-11-03 inside the seven-day gate. The debt gate read CLAIM-FIRST "
    "item=product-face-R2548 first=1 with no battery owed because R2548 moved no product "
    "byte, queue_head named tech line 585 claimable=12 with the floor MET, and all five "
    "pinned anchors were re-checked at zero occupancy at HEAD before any code: every hit "
    "was a seed row, a bookkeeping writer or state/debt prose, never an implementation.",

    "2026-11-08 R2549 SHIPPED src/os/probe_seam_name_binding_nested_exhaustive_path.py "
    "plus its six-criteria suite. MEASURED at R2547 on the shipped exhaustive face own "
    "reader and re-measured here before shipping: `if a: (if b: KEY=\"b\" else: KEY=\"b\") "
    "else: KEY=\"b\"` agrees on EVERY path yet read as TWO groups (if:3 exhaustive, if:2 "
    "covering only its else arm) and resolved nothing. The face folds a nested guard tree "
    "to its ROOT group and resolves ONLY when every group on it covers every path AND "
    "every LEAF binds the same single literal, publishing every leaf by its full path "
    "(if:2/body>if:3/else); an arm that binds nothing is NAMED partial:<arm> and a loop "
    "standing on the path is NAMED loop:<line>, neither folded into coverage. The shipped "
    "exhaustive face is asked FIRST and its answer is carried verbatim on every row as "
    "base_* beside the shipped guard answer, and the seam CLASSIFIER is still the shipped "
    "registry single `quiets`.",

    "2026-11-08 R2549 PROOF measured, not quoted: AC-PNCD1..AC-PNCD6 SUITE PASS 6/6 "
    "TWICE with identical output plus five adjacent probe suites green "
    "(qa/probe-seam-name-binding-nested-exhaustive-path-R2549.log, 27885B, legs=2 "
    "identical=True fails=0 adjacent=5, landed through the shipped capture callable). A "
    "LIVE leg on the REAL tree reads SEAMS-NESTED-COVERED over 1499 probes (3 covered, "
    "184 out-of-scope, 1312 historical, missing=0) with the module, the base face and the "
    "render digests unchanged across the reading, and the SAME fixtures are measured on "
    "BOTH readers: the agreeing tree reads ok/b here while the exhaustive face reads "
    "refused/guarded:if:2>if:3, and the partial tree reads partial:else here while the "
    "exhaustive face RESOLVES b (qa/probe-seam-name-binding-nested-exhaustive-path-live"
    "-R2549.log, 557B, utf-8 LF, crlf=0, bom=False).",

    "2026-11-08 R2549 REGISTRY, MATRIX, BOARD AND DEBT: one runner row "
    "os-probe-seam-name-binding-nested-exhaustive-path(6), so the registry reads 604 "
    "suites / 4600 criteria, recounted by importing reconcile_all.SUITES rather than "
    "trusted. docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the ELIGIBLE "
    "battery leg qa/reconcile-all-R2548.log to 58526 bytes at 604 suites / 4600 criteria "
    "with its green line honestly reading 603/604, and --check then read byte-identical at "
    "rc=0. The claimed row 585 was closed through src/os/queue_close_R2549.py at its "
    "predicted and measured 1753380B and ONE row was seeded from this window own MEASURED "
    "limits (a direct arm binding plus an agreeing nested tree reads mixed:<arm>, a try "
    "with an else or a finally keeps incomplete:<group>, and a with-as binding reads "
    "non-literal:<arm>) as AC-PNDP1..AC-PNDP6 with its five anchors re-checked at zero "
    "occupancy before the write; queue_head then read the new head at line 587 prefix "
    "AC-PNDP1 and queue_floor read FLOOR-MET main=5/5 tech=12/10 explore=10/10. DEBT "
    "through the shipped writers: product-face-R2548 closed (line 286, open 21->20, done "
    "247->248, 170488B -> 170491B, readback ok) and reconcile-battery-R2549 appended "
    "first=yes at the pre-registered 604/4600 (170491B -> 170770B, readback ok), so the "
    "gate now names that battery first. The round was declared through the shipped batch "
    "writer at its predicted 301 -> 302 entries / 83288B -> 83471B until R2559, after "
    "which residue_triage --check read TRIAGED.",

    "2026-11-08 R2549 honest disclosures: (a) TWO product points on the Executive Protocol "
    "scale - a runnable CLI with its own suite and a live reading a maintainer can run - "
    "but nothing a CEO could newly open and no P-47 business surface moved; (b) the defect "
    "was MEASURED at R2547 in that window own legs and re-measured here before shipping, "
    "so this is a repair of a disclosed gap rather than a new discovery; (c) A REAL "
    "OVER-RESOLUTION IN A SHIPPED FACE was measured this window and is disclosed rather "
    "than smoothed: on the partial fixture (an outer else binding nothing) and on the "
    "loop-under-an-arm fixture the exhaustive face RESOLVED b, which the tree does not "
    "prove, and this face refuses both while carrying the shipped answer on the row; (d) "
    "TWO of my own first-pass defects were fixed in the suite rather than the code "
    "loosened - an arm list read as a dict and a fold that dropped a nested disagreement "
    "by only looking at OK results (the fold now aggregates leaf values at every level); "
    "(e) DISCLOSED LIMITS measured and seeded as the next tech row: a direct binding plus "
    "an agreeing nested tree is refused as mixed, a try carrying an else or a finally is "
    "refused as incomplete even when every leaf agrees, and a with-as binding is never "
    "counted as coverage; (f) the registry moved by one row and a shipped doc moved, so a "
    "battery on this committed tree is owed BEFORE any further product byte; (g) MEASURED "
    "DEFECT STILL OPEN from R2522: state.json stands at 198443B against the 78500B "
    "waterline so state_fold --check reads FOLD-DUE and the shipped tool still ships only "
    "a --check face, so this append used a PROVED load+dump round-trip and the fold stays "
    "an owed obligation; (h) Docker is absent on this host so no containerised bring-up "
    "of the sandbox faces is claimed; (i) the real 19.9 debit and the real msgSecCheck "
    "still wait on CEO physical items (merchant id, mini-program appid/secret); (j) "
    "tasks.md was not touched, it is the P-47 canonical board; (k) the S4U lane "
    "re-registration still needs an ELEVATED shell and remains a ceo-pending physical "
    "item with zero chase.",

    "R2549 tokens: local=~13k api=0 api_reason=product window - five-silence scan, one "
    "content-addressed decisions scan reading new=0, one zero-occupancy anchor check on "
    "five anchors, one pre-registered face shipped with its six criteria, one suite proved "
    "twice through the shipped capture callable plus five adjacent suites, one live leg on "
    "the real tree with the same fixtures measured on BOTH readers, one measured "
    "over-resolution in a shipped face disclosed rather than hidden, one registry row "
    "recounted by import, one stamp-aligned matrix regeneration checked byte-identical, "
    "one board row closed and one seeded through their shipped writers, two debt rows "
    "moved and one residue declaration appended through their shipped writers, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero external API "
    "touches",
]


def main():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    replay = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    if replay.encode("utf-8") != raw:
        print("REFUSED E_APP_ROUNDTRIP: dump does not reproduce the file")
        return 3
    state["tick"] = 2549
    state["last_decision_rows"] = 42
    state["log"].extend(LINES)
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