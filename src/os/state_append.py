#!/usr/bin/env python3
"""The one vehicle that appends to state.json (R2833).

Why this exists
---------------
223 one-off scripts named state_append_R<n>.py had accumulated in this
folder, each of them carrying its own JSON serialisation and its own write
path. That is exactly why the round-main shape law landed at R2832 with NO
production call site: there was no single place to put it, so a round line
that forgot its date prefix was caught only later - by an exporter crash
(R2831) or by a battery leg (R2829).

This module is that single place:

    read (state_io) -> append -> shape gate (ledger_lines)
                    -> atomic write -> size report vs the fold waterline

The shape gate runs BEFORE any byte is written, so a forgotten date prefix
is refused at the write site instead of being discovered downstream.

R3309 added the neighbouring law at the same station: a log item is ONE
line, so a `--line` or `--tokens` payload carrying `\n` or `\r` is refused
as E_RSA_NEWLINE before the bytes land. Measured on the shipped face before
the gate: `--line "a\nsecond."` and a break inside `--tokens` both wrote an
item the fold could not carry; the R3308 stream proof then had to be the
one to notice. The earliest station is cheaper than the proof.

Usage
-----
    python src/os/state_append.py --round 2833 --line "2026-11-16 R2833 ..."
    python src/os/state_append.py --round 2833 --tokens "local=~1k api=0 ..."
    python src/os/state_append.py --tick --round 2833 --line "..."
    python src/os/state_append.py --check --round 2833 --line "..."

Exit codes
----------
    0  written, or --check read PASS (a refused duplicate still reads 0)
    2  refused by a named law (shape, tick direction)
    3  unusable input (no state, no log array, nothing to append)

Stdlib only, ASCII source, zero network, no clock.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import heartbeat  # noqa: E402
import ledger_lines  # noqa: E402
import logs_toolkit  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(HERE, "state.json")
FOLD_WATERLINE = 78500
TOKENS_FMT = "R%d tokens: %s"
FOLD_HINT = ("hint: python src/os/logs_toolkit.py eol --fix-indent --execute")


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()[:16]


def _refuse(code, rc, detail):
    return {"rc": rc, "ok": False, "code": code, "detail": detail}


def atomic_write(path, text):
    """Replace the state file in one step; a failure leaves nothing behind."""
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_append_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(text.encode("utf-8"))
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, path)
        temp = None
    finally:
        if temp is not None and os.path.exists(temp):
            os.remove(temp)


def _ledger_dated(text):
    """A budget line the live shape law cannot read (R3517, AC-RSA13).

    LEDGER_PREFIX_RE is anchored at the round marker and refuses a date
    prefix, while LEDGER_PRESENCE_RE tolerates one. A line that reads as
    presence but not as prefix is therefore stored bytes no live reader
    counts as a ledger line: measured at R3514, where a dated 'tokens:' line
    left its round reported as having no budget line at all. The gate asks
    the shipped regexes rather than a copy of them, so the two laws cannot
    drift apart.
    """
    text = (text or "").strip()
    return (ledger_lines.LEDGER_PRESENCE_RE.match(text) is not None
            and ledger_lines.LEDGER_PREFIX_RE.match(text) is None)


def _break_at(text):
    """Index of the first line break in text, or -1 (R3309).
    One log item is one line: the archive is appended with
    `"\\n".join(window)`, so an item that carries a break cannot be found
    again as one line, and a terminal break is silently trimmed by the
    `.strip()` below - the writer's bytes and the stored bytes stop being
    the same thing, which is the R3308 disease read from the other side.
    Measured at R3309 on the shipped face: `--line "a\\nsecond."` and
    `--tokens` carrying a break both landed with the break stored.
    """
    for index, char in enumerate(text):
        if char in ("\n", "\r"):
            return index
    return -1


def _collect(data, args):
    """Return (new_lines, added) or a refusal."""
    log = data.get("log")
    if not isinstance(log, list):
        return None, _refuse("E_RSA_NO_LOG", 3, "state.json holds no log array")
    existing = set(str(item) for item in log)
    added = []
    for raw in args.line:
        at = _break_at(raw)
        if at >= 0:
            return None, _refuse(
                "E_RSA_NEWLINE", 2,
                "a log item is one line; this append carries a line break at "
                "char %d (%r)" % (at, raw[max(0, at - 20):at + 20]))
        text = raw.strip()
        if not text:
            return None, _refuse("E_RSA_EMPTY_LINE", 3, "an empty --line")
        if _ledger_dated(text):
            return None, _refuse(
                "E_RSA_LEDGER_DATE", 2,
                "a budget line may not carry a date prefix; write it as "
                "'R<n> tokens: ...' or pass --tokens with --round "
                "(hint: python src/os/repair_tokens_prefix_R2597.py --apply "
                "heals one already stored this way)")
        if text in existing:
            return None, {"rc": 0, "ok": False, "code": "E_RSA_DUPLICATE",
                          "detail": text[:60]}
        added.append(text)
        existing.add(text)
    if args.tokens is not None:
        if args.round is None:
            return None, _refuse("E_RSA_NO_ROUND", 3,
                                 "--tokens needs --round")
        at = _break_at(args.tokens)
        if at >= 0:
            return None, _refuse(
                "E_RSA_NEWLINE", 2,
                "a tokens line is one line; --tokens carries a line break at "
                "char %d (%r)" % (at, args.tokens[max(0, at - 20):at + 20]))
        text = TOKENS_FMT % (args.round, args.tokens.strip())
        if text in existing:
            return None, {"rc": 0, "ok": False, "code": "E_RSA_DUPLICATE",
                          "detail": text[:60]}
        added.append(text)
        existing.add(text)
    if not added:
        return None, _refuse("E_RSA_NO_INPUT", 3, "nothing to append")
    return list(log) + added, None


def _settle_tick(data, args):
    """Return (new_tick, refusal). Tick may only move forward."""
    current = int(data.get("tick", 0))
    if args.tick is None:
        return current, None
    if args.tick == "auto":
        return current + 1, None
    try:
        want = int(args.tick)
    except (TypeError, ValueError):
        return None, _refuse("E_RSA_BAD_TICK", 3,
                             "--tick takes a number or no value")
    if want < current:
        return None, _refuse("E_RSA_TICK_BACK", 2,
                             "%d < %d (tick never goes backwards)"
                             % (want, current))
    return want, None


def _layout_refusal(text, log_len):
    """Ask the FOLD's own reader about the document about to be written (R2915).

    Why: the R2913 closeout left 4-space log items - the shape a bare
    json.dump(indent=2) produces - and the next window had to repair the
    file through `eol --fix-indent --execute` before it could fold. A
    layout a fold cannot read must be refused HERE, on the text that
    would have been written, instead of being discovered a round later.
    The question is asked of logs_toolkit.split_ps_layout, i.e. the very
    reader the fold uses, so the two modules cannot drift apart.
    """
    if logs_toolkit.split_ps_layout(text, log_len) is None:
        return _refuse("E_RSA_LAYOUT", 2,
                       "the fold reader cannot read the document this append "
                       "would write (%s)" % FOLD_HINT)
    return None


def _shipped_root(state_path):
    """The repo root a state file belongs to, or None for a private world.

    Only `<root>/src/os/state.json` has a heartbeat neighbour: a world built
    by a suite holds one state file and must keep holding exactly one.
    """
    state_dir = os.path.dirname(os.path.abspath(state_path))
    if os.path.basename(state_dir) != "os":
        return None
    src_dir = os.path.dirname(state_dir)
    if os.path.basename(src_dir) != "src":
        return None
    return os.path.dirname(src_dir)


def _heartbeat_notice(state_path, tick):
    """Publish the heartbeat row's distance from this tick (read only, R3320).

    WHY THE WRITE IS NOT HERE (measured, not preferred): `closeout.py` step
    1.6 lands the row through `heartbeat.write_tick` AFTER the state write is
    proven, and AC-COUT13 arm (d) pins that order - a world whose heartbeat
    name is occupied must advance the tick and only then refuse the face. A
    second write inside this vehicle would move that refusal ahead of the
    state write and change the tick the arm expects. So the write keeps its
    one station and this one only SAYS what it sees, which is the reading a
    round that advanced the tick directly had never been given: R3317..R3319
    each opened with the row two ticks behind the state.
    """
    root = _shipped_root(state_path)
    if root is None:
        return "skipped"
    try:
        row = heartbeat.read_tick(root)
    except (IOError, OSError):
        return "unreadable"
    if row is None:
        return "none"
    if row == tick:
        return "tick=%d" % tick
    if row > tick:
        # A row ahead of the tick is not a negative lag: it means someone
        # stamped the heartbeat past this state (a hand ran
        # `heartbeat.py --write N`). Naming it keeps every printed number
        # non-negative, so a reader never has to decode a sign.
        return "ahead=%d" % (row - tick)
    return "lag=%d" % (tick - row)


def run(args):
    try:
        raw_before = state_io.read_raw(args.state)
    except (OSError, state_io.StateIOError) as exc:
        return _refuse("E_RSA_NO_STATE", 3, "%s: %s" % (type(exc).__name__, exc))
    try:
        data = state_io.parse(state_io.decode(raw_before))
    except state_io.StateIOError as exc:
        return _refuse("E_RSA_BAD_STATE", 3, "%s: %s" % (exc.code, exc))
    if not isinstance(data, dict):
        return _refuse("E_RSA_BAD_STATE", 3, "state document is not an object")

    log_before = len(data.get("log") or [])
    new_lines, refusal = _collect(data, args)
    if refusal is not None:
        return refusal

    # The shape gate asks the law of the window that WOULD exist. Nothing
    # has been written yet, so a refusal costs the tree zero bytes.
    report = ledger_lines.check_round_main_shape(new_lines)
    if not report["ok"]:
        code = ("E_RSA_NO_DATE" if report["code"] == "E_RMS_NO_DATE"
                else report["code"])
        return _refuse(code, 2, "round=%s %s" % (report.get("round"),
                                                 report.get("detail")))

    new_tick, refusal = _settle_tick(data, args)
    if refusal is not None:
        return refusal

    before_rest = dict((k, v) for k, v in data.items() if k not in ("log", "tick"))
    data["log"] = new_lines
    data["tick"] = new_tick
    new_text = state_io.dump_canon(data)

    # The layout gate runs on the FINISHED text and before any byte lands,
    # so a writer that drifts off a readable caliber costs the tree nothing.
    refusal = _layout_refusal(new_text, len(new_lines))
    if refusal is not None:
        return refusal

    # Payload proof: exactly the appended lines and the tick can differ.
    try:
        after = state_io.parse(new_text)
    except state_io.StateIOError as exc:
        return _refuse("E_RSA_BAD_STATE", 3, "written text does not parse: %s"
                       % exc.code)
    after_rest = dict((k, v) for k, v in after.items() if k not in ("log", "tick"))
    moved = (len(after.get("log", [])) != len(new_lines)
             or after.get("tick") != new_tick
             or after_rest != before_rest)
    if moved:
        return _refuse("E_RSA_PAYLOAD", 3,
                       "the rebuilt document moved a key it may not move")

    size = len(new_text.encode("utf-8"))
    margin = FOLD_WATERLINE - size
    result = {"rc": 0, "ok": True, "tick": new_tick,
              "log": len(new_lines), "bytes": size, "fold_margin": margin,
              "code": "APPEND",
              "hb": _heartbeat_notice(args.state, new_tick),
              "detail": "+%d line(s)" % (len(new_lines) - log_before)}
    if args.check:
        return result
    atomic_write(args.state, new_text)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="state_append.py",
        description="Append to state.json through the one shape-gated vehicle.")
    parser.add_argument("--round", type=int, default=None,
                        help="the round this window is closing")
    parser.add_argument("--line", action="append", default=[],
                        help="a log line to append (repeatable)")
    parser.add_argument("--tokens", default=None,
                        help="render 'R<n> tokens: <text>' and append it")
    parser.add_argument("--tick", nargs="?", const="auto", default=None,
                        help="no value = increment; a number = set forward")
    parser.add_argument("--check", action="store_true",
                        help="measure the append without writing")
    parser.add_argument("--state", default=STATE, help="state file to touch")
    args = parser.parse_args(argv)

    result = run(args)
    if result["ok"]:
        print("APPEND %s tick=%d log=%d bytes=%d fold_margin=%d hb=%s %s"
              % ("CHECK" if args.check else "OK", result["tick"],
                 result["log"], result["bytes"], result["fold_margin"],
                 result["hb"], result["detail"]), flush=True)
    else:
        print("APPEND FAIL %s %s" % (result["code"], result["detail"]),
              flush=True)
    return result["rc"]


if __name__ == "__main__":
    sys.exit(main())
