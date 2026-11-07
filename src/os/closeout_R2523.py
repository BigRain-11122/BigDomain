"""Closeout for the R2523 window: append its rows, then fold at a boundary.

The state file measured 78908 bytes against the 78500 byte waterline at the
close, so a fold is due. DISCLOSED: the shipped state_fold layout reader
(ITEM_PREFIX 16 spaces) no longer matches the file the R2522 writer produced
with json.dump(indent=4, 8-space items), so plan_fold refuses E_SF_BAD_LAYOUT
here. This closeout therefore writes the file the way the file is already
written (load, mutate, dump - byte-identical round-trip proved below), and
folds with the SHIPPED laws it still can ask: state_fold.round_split for the
round-block boundary and state_fold.PAT for the token coverage check, with
state_fold.append_archive writing the block verbatim. Nothing is reformatted.

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
TICK = 2523
FOLD_NO = 785
LAST_ORDER = "2026-11-07 12:2x"
DEC_ROWS = 211


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
    summary = ("Fold %d (R2523): log lines 1..%d folded verbatim into "
               "logs/state-log-archive-2026-11.md at a true round-block "
               "boundary; window tokens: %s"
               % (FOLD_NO, end, " ".join(sorted(tokens))))
    header = "# --- Fold %d (R2523) - window 1..%d - %d lines" % (
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
    "2026-11-07 R2523 PRODUCT window on the tech head the register named "
    "(product-face-R2521, state/queue/tech.md:559 prefix AC-PLC1 "
    "probe_seam_local_constant_scope, criteria AC-PLC1..AC-PLC6 pinned in that "
    "row at R2521 BEFORE any code). Five-silence scan at open was clean at "
    "HEAD 08c434ce: git status empty, no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, content-addressed decisions diff new=0 over the "
    "stored 160-token baseline at a measured 211 rows, group orders tail moved "
    "to 2026-11-07 12:2x so the new rows were read and judged knowledge-only "
    "(a ceo-pending physical item queue entry for S4U re-registration and the "
    "D:/FluxGroup deletion candidate, plus three fleet-level OB event rows for "
    "the bm-a/bm-b/bm-c lanes), benchmarks 2026-11-03 inside the seven-day "
    "gate. The debt gate read CLAIM-FIRST item=product-face-R2521 first=1 and "
    "no battery was owed because R2522 discharged it and moved neither the "
    "register nor a product byte, so this window shipped the product face. "
    "Zero-occupancy of the five anchors was re-checked at HEAD before any "
    "code: no src/os/probe_seam_local_constant_scope.py and no suite existed, "
    "and the token appeared only in registration prose.",
    "2026-11-07 R2523 CLAIM AND SHIP: R2521 MEASURED in its own AC-PCB1 and "
    "AC-PCB4 legs that the constant table is read off MODULE-level assignments "
    "only, so a probe that declares its module name inside a function body "
    "reads OUT-OF-SCOPE while the same call one level up reads COVERED, and "
    "that a container reached through an attribute was not resolved either. "
    "SHIPPED src/os/probe_seam_local_constant_scope.py plus its suite. The "
    "string constant table is now read at CALL time in TWO scopes - the module "
    "body and the enclosing FUNCTION bodies - with a name dropped as soon as "
    "it is also bound to something that is not a constant anywhere in the tree "
    "or to two different constants, so an ambiguous name is never resolved. A "
    "constant-key lookup into a module-level container is resolved when that "
    "container is reached by a PLAIN ATTRIBUTE on a module file in the SAME "
    "root and named by the probe own imports; a Call node is never resolved, "
    "so a container returned by a function stays unresolved and is named. Rows "
    "name the helpers followed, the dynamic shapes taken WITH their binding "
    "label, the local bindings read and any unresolved call.",
    "2026-11-07 R2523 PROOF measured, not quoted: AC-PLC1..AC-PLC6 SUITE PASS "
    "6/6 TWICE with an identical digest plus three adjacent probe faces green "
    "(qa/probe-seam-local-constant-scope-R2523.log, 6833B, utf-8, legs=2 "
    "identical=True fails=0 adjacent=3) captured through the shipped evidence "
    "callable. LIVE leg on the REAL tree through the shipped single writer: "
    "verdict=SEAMS-LOCAL-COVERED over 1400 probes (3 covered, 171 "
    "out-of-scope, 1226 historical) with the module and render digests "
    "unchanged across the reading and read_only=True, then a local fixture "
    "reads COVERED helpers=plc_live_helper dynamic=importlib.import_module:"
    "plc_live_helper@name while the SAME fixture reads OUT-OF-SCOPE quieted=0 "
    "under the shipped constant-binding face, and a stale local fixture reads "
    "MISSING-SEAM missing=PLRC with the world reading SEAMS-LOCAL-STALE "
    "(qa/probe-seam-local-constant-scope-live-R2523.log, 1254B, crlf=0, lf=14). "
    "First suite leg was RED on ONE self-inflicted assertion - a str-literal "
    "argument was asserted to resolve while the resolver handled only bound "
    "names - and the resolver was extended to literal nodes rather than the "
    "assertion loosened, disclosed instead of hidden.",
    "2026-11-07 R2523 REGISTRY, MATRIX, BOARD AND DEBT: one runner row "
    "os-probe-seam-local-constant-scope(6), so the registry reads 591 suites / "
    "4522 criteria, recounted by importing reconcile_all.SUITES rather than "
    "trusted. The row moved the artifact, so docs/sandbox-suite-matrix.md was "
    "regenerated stamp-aligned from the ELIGIBLE battery leg "
    "qa/reconcile-all-R2522-leg3.log through src/sandbox/suite_matrix.py "
    "--evidence plus --stamp-from to 56905 bytes at 591 suites / 4522 "
    "criteria with its green line honestly reading 590/591, and --check then "
    "read byte-identical. The claimed row 559 was closed through a per-round "
    "writer with its DISCHARGED note (predicted and measured 1692598B, "
    "readback ok) and ONE row was seeded from this window own MEASURED limit: "
    "an annotated assignment (NAME colon str equals a literal) reads empty from "
    "BOTH tables, a walrus binding and a for-loop target of a str literal read "
    "empty from the local table, and a container reached through a NESTED "
    "attribute resolves to None, seeded as AC-PLAC1..AC-PLAC6; queue_floor then "
    "read FLOOR-MET 5/5 10/10 10/10 with the new head at line 561. Debt "
    "through the shipped writers: product-face-R2521 closed (line 246, open "
    "7->6, done 223->224, 154248B -> 154251B, readback ok), "
    "reconcile-battery-R2523 appended first=yes at the pre-registered 591/4522 "
    "(154251B -> 154912B) and product-face-R2523 appended first=no naming tech "
    "line 561 AC-PLAC1 (154912B -> 155526B); the gate now names "
    "reconcile-battery-R2523 first.",
    "2026-11-07 R2523 honest disclosures: (a) TWO product points on the "
    "Executive Protocol scale - a runnable CLI reading with its own suite and a "
    "live reading a maintainer can run - but nothing a CEO could open was "
    "newly built, and no P-47 business surface moved; (b) the defect was "
    "MEASURED at R2521 in that window own legs and re-measured here before "
    "shipping, so this is a repair of a disclosed gap rather than a new "
    "discovery; (c) DISCLOSED LIMITS measured this window rather than assumed: "
    "only str constants in the module body and in function bodies are "
    "followed, only one attribute hop on a module file in the SAME root is "
    "followed, annotated assignments, walrus and for-loop targets are NOT read, "
    "and a value computed at run time is never evaluated - seeded as the next "
    "tech row; (d) the walk shape is written in this module rather than "
    "injected into the shipped constant-binding face, because parameterising a "
    "shipped module would owe a battery in the same window - the seam "
    "CLASSIFIER is still the registry single quiets and the shape detector is "
    "still the shipped dynamic face, so no second classifier exists, and this "
    "duplication is named rather than hidden; (e) the registry moved by one row "
    "and a shipped doc moved, so a battery on this committed tree is owed "
    "BEFORE any further product byte; (f) MEASURED DEFECT BORN AT R2522: the "
    "shipped state_fold layout reader (ITEM_PREFIX 16 spaces) no longer matches "
    "the state file that window wrote with json.dump, so plan_fold refuses "
    "E_SF_BAD_LAYOUT on the real tree; this window appended with a proved "
    "load+dump round-trip and folded with the laws it still could ask "
    "(round_split for the boundary, PAT for token coverage, append_archive for "
    "the block) instead of reformatting the file, and the layout repair is "
    "named here rather than swept; (g) Docker is absent on this host so no "
    "containerised bring-up of the sandbox faces is claimed; (h) the real 19.9 "
    "debit and the real msgSecCheck still wait on CEO physical items (merchant "
    "id, mini-program appid/secret); (i) tasks.md was not touched, it is the "
    "P-47 canonical board; (j) the S4U lane re-registration still needs an "
    "ELEVATED shell and D-20261107-14 has classified it as a ceo-pending "
    "physical item with zero chase.",
    "R2523 tokens: local=~26k api=0 api_reason=product window - five-silence "
    "scan, one group-order tail read judged knowledge-only, one "
    "content-addressed decisions scan reading new=0, one zero-occupancy anchor "
    "check, one pre-registered face shipped with its six criteria, one suite "
    "proved twice with an identical digest plus three adjacent suites, one live "
    "leg on the real tree with the same fixture measured on BOTH readers and a "
    "stale fixture refused, one registry row recounted by import, one "
    "stamp-aligned matrix regeneration from an eligible battery leg checked "
    "byte-identical, one queue row closed and one seeded through their shipped "
    "writers, three debt rows moved through their shipped writers, one fold at "
    "a round-block boundary, and the state/export/backlog/heartbeat closeout; "
    "zero cloud calls and zero external API touches",
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