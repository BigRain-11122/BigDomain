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

    state step  (state_append.run)   <- HARD PRECONDITION, and it is verified
    face step   (export_round.write) <- only reachable when state really moved

It owns no serialisation and no write path of its own. Both writes stay in the
two vehicles that already carry their suites, their shape gates and their
grader. This file only decides WHEN each one runs and what a failure is called.

Criteria AC-COUT1..AC-COUT7 were pinned in src/os/backlog.md at R2835 BEFORE
this file existed.

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
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import export_round as ER  # noqa: E402
import state_append as SA  # noqa: E402
import state_io  # noqa: E402


def state_path(root):
    return os.path.join(root, "src", "os", "state.json")


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


def run(args):
    """Return (rc, message lines). One command, two writes, named steps."""
    root = os.path.abspath(args.root)
    lines = []

    # ---- step 1: state. A refusal here costs the face zero bytes. ----------
    result = SA.run(_state_args(args, root))
    if not result.get("ok"):
        code = result.get("code") or "E_CO_NO_STATE"
        detail = result.get("detail") or ""
        if code == "E_RSA_DUPLICATE":
            # The window's line is already on disk: the state did not move, so
            # the face has nothing new to publish. Refreshing it here would be
            # a write that claims a change which never happened.
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
        return 0, ["CLOSEOUT CHECK step=state tick=%d log=%d bytes=%d "
                   "fold_margin=%d %s face=NOT-MEASURED"
                   % (result["tick"], result["log"], result["bytes"],
                      result["fold_margin"], result.get("detail") or "")]

    unproven = _confirm_state_moved(state_path(root), result)
    if unproven:
        return 2, ["CLOSEOUT FAIL %s step=state face=NOT-WRITTEN" % unproven]

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

    lines.append("CLOSEOUT OK tick=%d state=WRITTEN face=WRITTEN "
                 "log=%d bytes=%d fold_margin=%d queue=%s queue_bytes=%s "
                 "latest=%s"
                 % (result["tick"], result["log"], result["bytes"],
                    result["fold_margin"], proof.get("gate"),
                    proof.get("bytes"), derived.get("latest")))
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
