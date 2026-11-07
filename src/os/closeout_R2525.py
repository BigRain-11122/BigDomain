"""Closeout for the R2525 window: append its rows, then fold if due.

Writes the state file the way the file is already written (load, mutate,
dump with a proved byte round-trip) and folds with the SHIPPED laws it can
still ask: state_fold.round_split for the round-block boundary, state_fold.PAT
for the token coverage check and state_fold.append_archive for the block.
Nothing is reformatted.

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
TICK = 2525
FOLD_NO = 787
LAST_ORDER = "2026-11-07 12:2x"
DEC_ROWS = 127
DEC_TOKENS = 91


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
    summary = ("Fold %d (R2525): log lines 1..%d folded verbatim into "
               "logs/state-log-archive-2026-11.md at a true round-block "
               "boundary; window tokens: %s"
               % (FOLD_NO, end, " ".join(sorted(tokens))))
    header = "# --- Fold %d (R2525) - window 1..%d - %d lines" % (
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
    "2026-11-07 R2525 PRODUCT window on the tech head the queue named "
    "(state/queue/tech.md:561 prefix AC-PLAC1 probe_seam_annotated_constant_"
    "scope, criteria AC-PLAC1..AC-PLAC6 pinned in that row at R2523 BEFORE any "
    "code). Five-silence scan at open: git status empty, no index.lock, "
    "content-addressed decisions diff read new=0 over the stored 160-token "
    "baseline (the group canon file still carries 91 tokens, all already "
    "inside the baseline), group orders tail unchanged at 2026-11-07 12:2x and "
    "benchmarks 2026-11-03 inside the seven-day gate. The debt gate read "
    "OPEN-NONE (open=8, first=0) so no battery was owed, and queue_head named "
    "tech line 561 claimable=11. Zero-occupancy was re-checked for all five "
    "pinned anchors before any code: probe_seam_annotated_constant_scope, "
    "AC-PLAC, E_PLAC, os-probe-seam-annotated-constant-scope and "
    "test_probe_seam_annotated_constant_scope appear only in the seed row and "
    "in the writers that produced it, never in an implementation.",
    "2026-11-07 R2525 SHIPPED src/os/probe_seam_annotated_constant_scope.py "
    "plus its suite. MEASURED at R2523 on the shipped local-constant face own "
    "readers and re-measured here before shipping: an annotated assignment "
    "(`NAME: str = \"x\"`), a walrus binding and a for-loop target of one str "
    "literal all read empty from the constant tables, and a container reached "
    "through a nested attribute resolved to None. The face EXTENDS the shipped "
    "tables rather than replacing them - the shipped law answers first and the "
    "extension adds those three shapes in the module body and in function "
    "bodies with the same ambiguity rule, and the shipped resolution law is "
    "asked FIRST with the extended tables so every shape it already answered "
    "keeps its answer; only when it answers None is ONE more attribute hop "
    "taken on a module-level constant tree, gated by the probe own imports, "
    "and the row carries the binding label it followed. An annotation that is "
    "not a plain name is refused rather than guessed; a call, a concatenation, "
    "a comprehension and an arithmetic expression are never evaluated and the "
    "row names the unresolved call instead. The seam CLASSIFIER is still the "
    "shipped registry single `quiets` and the shape detector is still the "
    "shipped dynamic face, so no second classifier exists.",
    "2026-11-07 R2525 PROOF measured, not quoted: AC-PLAC1..AC-PLAC6 SUITE "
    "PASS 6/6 TWICE with an identical digest plus three adjacent probe faces "
    "green (qa/probe-seam-annotated-constant-scope-R2525.log, 8335B, utf-8, "
    "legs=2 identical=True fails=0 adjacent=3), landed through an evidence "
    "callable with an explicit LF newline and a byte read-back. LIVE leg on "
    "the REAL tree through the shipped reading: "
    "verdict=SEAMS-ANNOTATED-COVERED over 1410 probes (3 covered, 172 "
    "out-of-scope, 1235 historical, missing=0) with the real probes now "
    "showing the annotated local bindings they read, one annotated fixture "
    "against a partial helper reads MISSING-SEAM missing=PLRC dynamic="
    "importlib.import_module:plac_live_helper@NAME, a missing root is refused "
    "E_PLAC_NO_ROOT at exit 3, and the module and render digests are unchanged "
    "across the reading (qa/probe-seam-annotated-constant-scope-live-R2525.log,"
    " 1267B, LF only).",
    "2026-11-07 R2525 REGISTRY, MATRIX, BOARD AND DEBT: one runner row "
    "os-probe-seam-annotated-constant-scope(6), so the registry reads 592 "
    "suites / 4528 criteria, recounted by importing reconcile_all.SUITES rather "
    "than trusted. docs/sandbox-suite-matrix.md was regenerated stamp-aligned "
    "from the ELIGIBLE battery leg qa/reconcile-all-R2524-retry.log to 57026 "
    "bytes at 592 suites / 4528 criteria with its green line honestly reading "
    "591/592, and --check then read byte-identical. The claimed row 561 was "
    "closed through its own per-round writer at predicted and measured "
    "1698899B (delta 4308) and ONE row was seeded from this window own MEASURED "
    "limit through the same writer: an annotated alias of an existing constant "
    "reads the table without the alias, a with-as binding reads empty, a "
    "for-loop over two or more literals reads empty, and a two-hop dict chain "
    "resolves to None; queue_floor then read FLOOR-MET 5/5 10/10 10/10 with the "
    "new head at line 563 prefix AC-PCAS1. BIRTH SITE: the R2514 residue block "
    "had expired at until R2524, so the shipped idempotent repin re-read every "
    "live round it carries and re-pinned them through R2535 (300 -> 301 "
    "entries, 83156B -> 83255B, readback PINNED), which also declared R2525 "
    "DELIVERED, after which the batch appender correctly REFUSED the second "
    "declaration as a duplicate and residue_triage --check read R2525 "
    "state=TRIAGED live=DELIVERED at exit 0. DEBT: reconcile-battery-R2525 was "
    "appended first=yes at its predicted 156539B -> 156981B naming this window "
    "own registered target, and product-face-R2525 appended first=no at "
    "156981B -> 157320B, both readback ok; the gate now names that battery "
    "first.",
    "2026-11-07 R2525 honest disclosures: (a) TWO product points on the "
    "Executive Protocol scale - a runnable CLI with its own suite and a live "
    "reading a maintainer can run - but nothing a CEO could open was newly "
    "built and no P-47 business surface moved. (b) The defect was MEASURED at "
    "R2523 in that window own legs and re-measured here before shipping, so "
    "this is a repair of a disclosed gap rather than a new discovery. (c) "
    "DISCLOSED LIMITS measured this window rather than assumed: only literally "
    "constant values are followed, an annotated alias of another constant is "
    "NOT resolved, a with-as binding and a multi-value for-loop target are not "
    "read, and only one extra attribute hop is taken on a module in the same "
    "root - all seeded as the next tech row. (d) The walk shape is written in "
    "this module rather than injected into the shipped face, which is the "
    "third copy of that walk, because parameterising a shipped module would owe "
    "a battery in the same window; the tables and the resolution law are the "
    "shipped ones extended at call time, so no second classifier exists. (e) "
    "The registry moved by one row and a shipped doc moved, so a battery on "
    "this committed tree is owed BEFORE any further product byte. (f) MEASURED "
    "DEFECT STILL OPEN from R2524: the shipped state_fold layout reader no "
    "longer matches the state file that window wrote with json.dump, so this "
    "window appended with a proved load+dump round-trip and folded with the "
    "laws it could still ask instead of reformatting the file. (g) The residue "
    "declaration block had expired one round before this window opened and was "
    "re-pinned rather than hand-edited, which is why a fresh product round was "
    "already declared DELIVERED by the repin writer. (h) Docker is absent on "
    "this host so no containerised bring-up of the sandbox faces is claimed. "
    "(i) The real 19.9 debit and the real msgSecCheck still wait on CEO "
    "physical items (merchant id, mini-program appid/secret). (j) tasks.md was "
    "not touched, it is the P-47 canonical board. (k) The S4U lane "
    "re-registration still needs an ELEVATED shell and D-20261107-14 has "
    "classified it as a ceo-pending physical item with zero chase.",
    "R2525 tokens: local=~24k api=0 api_reason=product window - five-silence "
    "scan, one content-addressed decisions scan reading new=0, one "
    "zero-occupancy anchor check, one pre-registered face shipped with its six "
    "criteria, one suite proved twice with an identical digest plus three "
    "adjacent suites, one live leg on the real tree with a stale fixture "
    "refused and a missing root refused, one registry row recounted by import, "
    "one stamp-aligned matrix regeneration from an eligible battery leg checked "
    "byte-identical, one expired residue declaration re-pinned through its "
    "idempotent writer and a duplicate declaration correctly refused, one queue "
    "row closed and one seeded, two debt rows moved through their shipped "
    "writers, and the state/export/backlog/heartbeat closeout; zero cloud calls "
    "and zero external API touches",
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