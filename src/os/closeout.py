#!/usr/bin/env python3
"""closeout - the ONE command that closes a round (R2835).

Why this exists
---------------
The close of a round used to be two commands in two processes:

    python src/os/state_append.py ...      # write state.json
    python src/os/export_round.py          # write docs/status-export.json

Two commands mean a window can run only the second one, or run them in the
wrong order, or have the first fail while the second still publishes. R2831
shipped a CEO face that narrated a round whose log line had lost its date
anchor; the shape law (R2832), its state call site (R2833) and its face call
site (R2834) all make that particular line impossible, but the ORDER was still
nobody's job. A face is derived FROM state, so a face written while the state
write failed describes a round the state never got.

This module makes the order a law instead of a habit:

    step 0 one-off law (one_off_round_scripts.audit) <- REFUSES a new one-off
    state step  (state_append.run)   <- HARD PRECONDITION, and it is verified
    face step   (export_round.write) <- only reachable when state really moved

It owns no serialisation and no write path of its own. Both writes stay in the
two vehicles that already carry their suites, their shape gates and their
grader. This file only decides WHEN each one runs and what a failure is called.

R3095 adds the third reader of this order: the closeout gate's TREE faces, asked
between the two writes. Measured at R3095, the ROUND face of that gate needs no
help from here - the state door already refuses a newest round with no dated
line (`E_RSA_NO_DATE`) and one with no uppercase label - while the census drift
face and the derived document are tree-wide laws that no per-round vehicle was
asking, which is how "state written, face written, gate red" happened. A world
that builds no tree reads `gate=NOT-ASKED` with its reason on its own line; one
that builds a drifted tree is refused by name and the face keeps its bytes.
Criteria AC-COUT8 were pinned in src/os/backlog.md at R3095 BEFORE this change.

Criteria AC-COUT1..AC-COUT7 were pinned in src/os/backlog.md at R2835 BEFORE
this file existed.

R2836 adds the one hole R2835 disclosed: a crash BETWEEN the two writes leaves
the state written and the face narrating the previous round, and a duplicate
replay of the same closeout deliberately does not rewrite the face - so the
half-close used to exit 0. `E_CO_FACE_BEHIND` now names it, from a measurement
of the two files on disk (state tick vs the round in ceo_face.current), both in
--check and on the duplicate path. Criteria AC-COUTB1..AC-COUTB5 were pinned in
src/os/backlog.md at R2836 BEFORE this change.

Usage
-----
    python src/os/closeout.py --round 2835 \
        --line "2026-11-16 R2835 PRODUCT: what this window shipped" \
        --tokens "local=~20k api=0 api_reason=..." --tick

    python src/os/closeout.py --round 2835 --line "..." --check   # zero writes
    python src/os/closeout.py --round 9100 --line "..." --root DIR

Exit codes
----------
    0  both writes landed (or --check read a passing dry run, or a replay was
       refused as a duplicate with the face deliberately not written)
    2  refused by a named law, and the refusal names WHICH step
    3  unusable input (no state file, nothing to append)

Stdlib only, ASCII source, zero network.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import export_round as ER  # noqa: E402
import one_off_round_scripts as OOR  # noqa: E402
import state_append as SA  # noqa: E402
import state_io  # noqa: E402

# The shape export_round writes into ceo_face.current, and nothing else: an
# optional date anchor, then the round. A face string that does not match this
# is NOT graded by the detector below - it is another named defect's business.
FACE_ROUND_RE = re.compile(r"^\s*(?:\d{4}-\d{2}-\d{2}\s+)?R(\d+)\b")


def state_path(root):
    return os.path.join(root, "src", "os", "state.json")


def face_path(root):
    return os.path.join(root, "docs", "status-export.json")


def measure_face(root):
    """(state tick, face round) read from the two files, or None if unreadable.

    The half-close disclosed last round is a state that moved while the face
    did not. It is a MEASUREMENT, so it is taken from disk every time and never
    inferred from an argument. None means "not measurable", which is not the
    same as "behind" - an unreadable face or a `current` that carries no round
    keeps whatever verdict its own gate gives it.
    """
    try:
        data = state_io.parse(state_io.decode(state_io.read_raw(
            state_path(root))))
        tick = int(data.get("tick"))
    except (OSError, state_io.StateIOError, TypeError, ValueError):
        return None
    try:
        with io.open(face_path(root), "r", encoding="utf-8") as handle:
            face = json.loads(handle.read())
    except (OSError, ValueError):
        return None
    current = str(((face.get("ceo_face") or {}).get("current")) or "")
    match = FACE_ROUND_RE.match(current)
    if not match:
        return None
    return tick, int(match.group(1))


def face_behind(root, state_word):
    """The named half-close, or "" when the face is level with the state."""
    measured = measure_face(root)
    if not measured:
        return ""
    tick, face_round = measured
    if face_round >= tick:
        return ""
    return ("E_CO_FACE_BEHIND step=face state=%s state_tick=%d face=R%d "
            "behind_by=%d repair=\"python src/os/export_round.py\""
            % (state_word, tick, face_round, tick - face_round))


def _state_args(args, root):
    """The state_append call, built from this window's closeout arguments."""
    return argparse.Namespace(
        round=args.round,
        line=list(args.line),
        tokens=args.tokens,
        tick=args.tick,
        check=args.check,
        state=state_path(root),
    )


def _confirm_state_moved(path, result):
    """Read the state back: the append must be ON DISK, not merely reported.

    A vehicle that reports a write it did not perform is the same class of
    defect as a face narrating a round the log never got, so this is a real
    post-condition rather than trust in a return value.
    """
    try:
        data = state_io.parse(state_io.decode(state_io.read_raw(path)))
    except (OSError, state_io.StateIOError) as exc:
        return "E_CO_STATE_UNPROVEN unreadable: %s: %s" % (
            type(exc).__name__, exc)
    log = data.get("log") or []
    if int(data.get("tick", -1)) != int(result["tick"]):
        return ("E_CO_STATE_UNPROVEN tick on disk %r != reported %r"
                % (data.get("tick"), result["tick"]))
    if len(log) != int(result["log"]):
        return ("E_CO_STATE_UNPROVEN log length on disk %d != reported %d"
                % (len(log), int(result["log"])))
    return ""


def one_off_refusal(root):
    """The freeze-round law, asked at the one place every round must pass.

    R2838 shipped the law as a reading and nothing called it, so a new
    `foo_R2839.py` could still be written and committed; only a later battery
    leg would find it. The closeout vehicle runs before the state step, so a
    one-off is now refused in the window that creates it, with the state and
    the CEO face untouched.

    The law is not re-implemented here: the walk, the name shape and the
    freeze round all come from one_off_round_scripts.audit(), and the numbers
    printed below are that report's numbers (AC-OOSW5).
    """
    try:
        report, code = OOR.audit(root, OOR.DEFAULT_SCOPE, OOR.FREEZE_ROUND)
    except OOR.OneOffRoundScriptsError as exc:
        return ("E_CO_ONE_OFF_SCOPE %s scope=%s (the one-off law could not "
                "read its scope; nothing was written)"
                % (exc.code, OOR.DEFAULT_SCOPE.replace(os.sep, "/")))
    if code == 2:
        names = " ".join(row["path"] for row in report["detail"])
        return ("E_CO_ONE_OFF refused=%d freeze=%d scanned=%d one_offs=%d "
                "max_round=%d files=[%s]"
                % (len(report["refused"]), report["freeze"], report["scanned"],
                   report["one_offs"], report["max_round"], names))
    return ""


def tree_refusal(root):
    """The closeout gate's TREE faces, asked before the CEO face is published.

    Returns (word, line): "PASS", "NOT-ASKED" or "RED".

    R3095 measured that the round's own shape does not need this: the state
    door refuses a newest round with no dated line (`E_RSA_NO_DATE`) and one
    with no uppercase label long before the face is written, so the round-main
    face of the gate is already enforced ahead of this vehicle. What is NOT
    enforced here is the TREE: the census drift face and the derived document,
    which is exactly how "state written, face written, gate red" was reachable.

    Those faces need the tree's own inputs, so a world that builds none reads
    NOT-ASKED - printed with its reason, never a silent skip. A world that
    builds them and has drifted is refused by name, and the face keeps its
    bytes.
    """
    tools = os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        import closeout_gate as CG
    except (ImportError, ValueError) as exc:
        return "RED", ("E_CO_GATE_UNAVAILABLE %s: %s"
                       % (type(exc).__name__, exc))
    qa = os.path.join(root, "qa")
    baseline = os.path.join(qa, CG.CENSUS.BASELINE_NAME)
    doc = os.path.join(root, "docs", "sandbox-suite-matrix.md")
    if not (os.path.isfile(baseline) and os.path.isfile(doc)):
        return "NOT-ASKED", ("E_CO_GATE_NO_INPUTS qa=%d doc=%d (this world "
                             "builds no tree for the gate to read)"
                             % (int(os.path.isdir(qa)),
                                int(os.path.isfile(doc))))
    try:
        lines, code, _verdict = CG.evaluate(qa, baseline, root=root)
    except (IOError, OSError, ValueError) as exc:
        return "RED", ("E_CO_GATE_UNREADABLE %s: %s"
                       % (type(exc).__name__, exc))
    if code == 0:
        return "PASS", lines[0]
    return "RED", lines[0]


def run(args):
    """Return (rc, message lines). One command, two writes, named steps."""
    root = os.path.abspath(args.root)
    lines = []

    # ---- step 0: the one-off law. A refused name costs zero bytes. --------
    one_off = one_off_refusal(root)
    if one_off:
        return 2, ["CLOSEOUT FAIL %s step=one-off state=NOT-WRITTEN "
                   "face=NOT-WRITTEN" % one_off]

    # ---- step 1: state. A refusal here costs the face zero bytes. ---------
    result = SA.run(_state_args(args, root))
    if not result.get("ok"):
        code = result.get("code") or "E_CO_NO_STATE"
        detail = result.get("detail") or ""
        if code == "E_RSA_DUPLICATE":
            # The window's line is already on disk: the state did not move, so
            # the face has nothing new to publish. Refreshing it here would be
            # a write that claims a change which never happened.
            #
            # R2836: "nothing new to publish" is only true when the face is
            # ALREADY level with the state. If it lags, this replay is a
            # half-close - an earlier attempt wrote state and died before the
            # face - and exiting 0 would hide it. Name it instead.
            behind = face_behind(root, "WRITTEN")
            if behind:
                return 2, ["CLOSEOUT FAIL %s face_lagging=1 "
                           "(state moved in an earlier attempt; the face was "
                           "NOT rewritten here by design)" % behind]
            return 0, ["CLOSEOUT NOOP E_CO_DUPLICATE %s face=NOT-WRITTEN "
                       "(state did not move, so the face was left alone)"
                       % detail]
        return result.get("rc", 2) or 2, [
            "CLOSEOUT FAIL E_CO_NO_STATE step=state %s %s "
            "face=NOT-WRITTEN" % (code, detail)]

    if args.check:
        # A face verdict can only be asked AFTER the state write, so --check
        # measures the state step and says so instead of inventing a face
        # verdict from a state that has not moved.
        #
        # R2836: the one face verdict that IS available without writing is the
        # comparison of the state already on disk with the face already on
        # disk. When the face lags, that is the half-close and it is named here
        # at the moment it is visible - read-only, no bytes, no mtime.
        behind = face_behind(root, "HELD")
        if behind:
            return 2, ["CLOSEOUT FAIL %s face_lagging=1 "
                       "(step 1 left the state untouched; the face cannot "
                       "describe a round it never got)" % behind]
        # The tree faces are round-independent, so a dry run can and does ask
        # them - that is the one verdict a --check can give without waiting for
        # a write. A red tree is reported here, not invented.
        gate_word, gate_line = tree_refusal(root)
        if gate_word == "RED":
            return 2, ["CLOSEOUT CHECK RED step=tree %s face=NOT-MEASURED"
                       % gate_line]
        return 0, ["CLOSEOUT CHECK step=state tick=%d log=%d bytes=%d "
                   "fold_margin=%d %s face=NOT-MEASURED gate=%s"
                   % (result["tick"], result["log"], result["bytes"],
                      result["fold_margin"], result.get("detail") or "",
                      gate_word)]

    unproven = _confirm_state_moved(state_path(root), result)
    if unproven:
        return 2, ["CLOSEOUT FAIL %s step=state face=NOT-WRITTEN" % unproven]

    # ---- step 1.5: the TREE this face is about to speak for. ---------------
    # Asked after the state write (a refusal costs that write, which is the
    # cheaper of the two and the one an operator can replay) and before the
    # face (so a red tree never reaches the CEO face).
    gate_word, gate_line = tree_refusal(root)
    if gate_word == "RED":
        return 2, ["CLOSEOUT FAIL E_CO_TREE_RED step=tree "
                   "state=WRITTEN face=NOT-WRITTEN tick=%d %s "
                   "repair=\"fix the tree, then python src/os/export_round.py\""
                   % (result["tick"], gate_line)]

    # ---- step 2: the face. Reachable only when the state really moved. -----
    stamp = ER.datetime.datetime.now(ER.TZ).replace(microsecond=0).isoformat()
    try:
        ok, derived, proof = ER.write(root, stamp)
    except ValueError as exc:
        return 2, ["CLOSEOUT FAIL E_CO_NO_FACE step=face state=WRITTEN "
                   "tick=%d %s" % (result["tick"], exc)]
    except (IOError, OSError) as exc:
        return 2, ["CLOSEOUT FAIL E_CO_NO_FACE step=face state=WRITTEN "
                   "tick=%d %s: %s"
                   % (result["tick"], type(exc).__name__, exc)]

    if not ok or proof.get("gate") != "CURRENT":
        return 2, ["CLOSEOUT FAIL E_CO_FACE_UNPROVEN step=face state=WRITTEN "
                   "ok=%s queue=%s bytes=%s latest=%s"
                   % (ok, proof.get("gate"), proof.get("bytes"),
                      derived.get("latest"))]

    lines = ["CLOSEOUT OK tick=%d state=WRITTEN face=WRITTEN "
             "log=%d bytes=%d fold_margin=%d queue=%s queue_bytes=%s "
             "latest=%s gate=%s"
             % (result["tick"], result["log"], result["bytes"],
                result["fold_margin"], proof.get("gate"),
                proof.get("bytes"), derived.get("latest"), gate_word)]
    if gate_word == "NOT-ASKED":
        # Printed, not silent: a round closed in a world that carries no tree
        # says so on its own line, with the reason the gate was not asked.
        lines.append("CLOSEOUT GATE NOT-ASKED %s" % gate_line)
    return 0, lines


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="closeout.py",
        description="Close a round: state first (hard precondition), then the "
                    "CEO face, in one command with two named steps.")
    parser.add_argument("--round", type=int, default=None,
                        help="the round this window is closing")
    parser.add_argument("--line", action="append", default=[],
                        help="a log line to append (repeatable)")
    parser.add_argument("--tokens", default=None,
                        help="render 'R<n> tokens: <text>' and append it")
    parser.add_argument("--tick", nargs="?", const="auto", default=None,
                        help="no value = increment; a number = set forward")
    parser.add_argument("--check", action="store_true",
                        help="measure the state step without writing anything")
    parser.add_argument("--root", default=ER.REPO,
                        help="the repo root to close (a private world is fine)")
    args = parser.parse_args(argv)

    rc, lines = run(args)
    for line in lines:
        print(line, flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
