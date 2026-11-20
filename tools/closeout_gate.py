"""Closeout precondition gate (R2932, criteria AC-CLG1..AC-CLG5).

WHY: the R2926 commit hook refuses STAGED evidence bytes only. A round that
writes a shell-captured file and never stages it still leaves the file on disk,
where every later reader meets it and no gate has refused it yet. The board
carried this as "decide whether the closeout runs qa_writer_census --check as a
HARD precondition, and pin WHICH of its two faces gates".

THE DECISION, and why it is not a preference:

  * `flags` GATES. It is the census's own drift face - a new non-tee file, or a
    baselined file whose class moved. That is exactly "this round let a
    non-healthy write reach the tree", i.e. the thing a closeout precondition
    exists to refuse.
  * `reader_refused` does NOT gate. It counts BASELINED files that no writer
    family decodes. Those were baselined by name at freeze time, so a refusal
    there would make every closeout red for history the round did not create,
    and the only exit would be a re-freeze that also masks unrelated drift. It
    stays PUBLISHED on the gate line so the debt is visible on every closeout.

  A change to a baselined file's bytes that breaks the dialect moves its class,
  so it already lands on `flags`. Honest boundary: a rewrite that stays inside
  the same class is invisible to both faces (the census has no hashes).

R3093 - the two faces a round could still slip past (AC-CLG6):

Two laws already ship as SUITES but were never asked at closeout, so a round
could read PASS while both were red. Measured at R3092: R3091 closed a round
whose newest block carried no dated labelled main line, and entered the tree
with a registry row that had never been re-pinned; each law was asked only by
its own suite, and the closeout gate asked none of them.

  * round-main - `ledger_lines --round-main` (E_RMS_NO_ROUND / NO_DATE /
    NO_LABEL). The CEO face is composed from the newest dated labelled line;
    a round without one publishes the PREVIOUS round while every check passes.
  * registry census - `registry_counter_census --check`. A registry row that
    was edited without re-pinning moves the census, and nothing at closeout
    refused it.

Both are READ-ONLY and both are cheap (one state read, one registry read).
Both are opt-in through `root`: with `root=None` the gate answers exactly the
question it shipped with, byte for byte, so the eleven shipped call sites and
the five shipped criteria keep their meaning. The CLI passes `root=ROOT`, so a
human closeout asks all three faces in one command.

Ordering is part of the law: `flags` is asked FIRST, because it is the cheapest
face and the only one about bytes this round wrote; a drifted tree is refused
before either root face is read.

Shape: a published line, never a silent pass.

    CLOSEOUT-GATE PASS files=<n> flags=0 reader_refused=<n> gating=flags
    CLOSEOUT-GATE PASS ... gating=flags round_main=OK census=PASS
    CLOSEOUT-GATE REFUSED reason=<E_CLG_*> flags=<n> ... [flag] lines

Exit codes: 0 PASS; 2 REFUSED. Read-only: the gate never writes the tree, the
baseline, or any qa/ file. Stdlib only (plus the shipped census module), no
network, no shell.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))          # .../tools
ROOT = os.path.dirname(BASE)                                # repo root
sys.path.insert(0, os.path.join(ROOT, "src", "os"))

import qa_writer_census as CENSUS                           # noqa: E402

GATING_FACE = "flags"
INFORMATIONAL_FACES = ("reader_refused", "plain_unusable",
                       "reader_rescued", "flags")


class GateRowError(Exception):
    """The census row did not carry a field the gate needs."""


def _token(lines, name):
    """Read `name=<digits>` through the census's OWN scanner (R2933).

    The token scanner moved into the census module because the commit-side
    tree face reads the same row: two private scanners could drift and let
    one gate accept a row the other refuses. Absent or malformed ->
    GateRowError (a gate that cannot read its own input must refuse).
    """
    try:
        return CENSUS.published_int(lines, name)
    except ValueError as exc:
        raise GateRowError(str(exc))


def _src_os(root):
    """The repo's src/os on sys.path, importing lazily (R3093).

    Imported inside the root faces so that `root=None` keeps the gate's
    import surface at exactly what R2932 shipped: a closeout that does not
    ask the two new questions does not load their modules either.
    """
    path = os.path.join(root, "src", "os")
    if path not in sys.path:
        sys.path.insert(0, path)
    return path


def check_round_main(root):
    """Ask the round-main shape law of the live log. Returns (ok, line)."""
    path = _src_os(root)
    import ledger_lines as LEDGER
    log = LEDGER.load_state_log(os.path.join(path, "state.json"))
    report = LEDGER.check_round_main_shape(log)
    return bool(report["ok"]), LEDGER.format_round_main(report)


def check_census(root, registry=None, pin=None):
    """Ask the registry counter census against its own pin. (ok, line).

    `registry`/`pin` exist so a fixture world can inject its own frozen
    registry and pin; the live call passes neither and reads the shipped
    constants of the census module itself.
    """
    _src_os(root)
    import registry_counter_census as RC
    registry = registry or RC.REGISTRY
    pin = pin or RC.PIN
    try:
        report = RC.census(registry=registry)
    except RC.CensusError as exc:
        return False, "%s %s" % (exc.code, exc.detail)
    try:
        with io.open(pin, encoding="utf-8") as fh:
            pinned = json.load(fh)
    except (IOError, OSError, ValueError) as exc:
        return False, "E_RCC_NO_PIN %s" % exc
    fails = RC.compare(report, pinned)
    if fails:
        return False, "VERDICT FAIL %s" % " ".join(fails)
    return True, "VERDICT PASS pinned=%d" % sum(
        len(v) for v in pinned.values())


def evaluate(target, baseline, root=None, registry=None, census_pin=None):
    """Run the census check and return (lines, exit_code, verdict dict).

    `root=None` -> the pre-R3093 question, byte for byte.
    `root` given -> after a green `flags` face, also ask round-main and the
    registry census; either red refuses the closeout by name.
    """
    census_lines, census_rc = CENSUS.check_against_baseline(target, baseline)
    out = []
    if census_lines and census_lines[0].startswith("baseline file missing"):
        out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_NO_BASELINE "
                   "baseline=%s" % os.path.basename(baseline))
        out.extend(census_lines)
        return out, 2, {"verdict": "REFUSED",
                        "reason": "E_CLG_NO_BASELINE"}
    if census_rc == 3:
        out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_EMPTY target=%s"
                   % os.path.abspath(target))
        out.extend(census_lines)
        return out, 2, {"verdict": "REFUSED", "reason": "E_CLG_EMPTY"}
    try:
        flags = _token(census_lines, GATING_FACE)
        refused = _token(census_lines, "reader_refused")
        count = 0
        for line in census_lines:
            if line.startswith("census: files="):
                count = _token([line], "files")
                break
        if count == 0:
            raise GateRowError("census did not publish its file count")
    except GateRowError as exc:
        out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_ROW detail=%s" % exc)
        out.extend(census_lines)
        return out, 2, {"verdict": "REFUSED", "reason": "E_CLG_ROW"}

    if flags == 0:
        verdict = {"verdict": "PASS", "files": count, "flags": flags,
                   "reader_refused": refused, "gating": GATING_FACE}
        tail = ""
        if root is not None:
            # R3093: the two laws a round could slip past. Read-only, cheap,
            # and asked only after the byte-drift face is green.
            try:
                rm_ok, rm_line = check_round_main(root)
            except (IOError, OSError, ValueError) as exc:
                out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_ROUND_MAIN "
                           "files=%d flags=%d round_main=UNREADABLE"
                           % (count, flags))
                out.append("E_RMS_UNREADABLE %s" % exc)
                verdict = {"verdict": "REFUSED",
                           "reason": "E_CLG_ROUND_MAIN", "files": count,
                           "flags": flags, "round_main": "UNREADABLE"}
                return out, 2, verdict
            if not rm_ok:
                out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_ROUND_MAIN "
                           "files=%d flags=%d round_main=FAIL" % (count, flags))
                out.append(rm_line)
                verdict = {"verdict": "REFUSED",
                           "reason": "E_CLG_ROUND_MAIN", "files": count,
                           "flags": flags, "round_main": "FAIL"}
                return out, 2, verdict
            try:
                cen_ok, cen_line = check_census(root, registry=registry,
                                                pin=census_pin)
            except (IOError, OSError, ValueError) as exc:
                out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_CENSUS "
                           "files=%d flags=%d census=UNREADABLE"
                           % (count, flags))
                out.append("E_RCC_UNREADABLE %s" % exc)
                verdict = {"verdict": "REFUSED", "reason": "E_CLG_CENSUS",
                           "files": count, "flags": flags,
                           "round_main": "OK", "census": "UNREADABLE"}
                return out, 2, verdict
            if not cen_ok:
                out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_CENSUS "
                           "files=%d flags=%d round_main=OK census=FAIL"
                           % (count, flags))
                out.append(cen_line)
                verdict = {"verdict": "REFUSED", "reason": "E_CLG_CENSUS",
                           "files": count, "flags": flags,
                           "round_main": "OK", "census": "FAIL"}
                return out, 2, verdict
            verdict["round_main"] = "OK"
            verdict["census"] = "PASS"
            tail = " round_main=OK census=PASS"
        out.append("CLOSEOUT-GATE PASS files=%d flags=%d "
                   "reader_refused=%d gating=%s%s"
                   % (count, flags, refused, GATING_FACE, tail))
        # The informational debt is never silent: a baselined file no family
        # decodes is still named on every closeout, it just does not refuse.
        out.extend(line for line in census_lines
                   if line.startswith("[refuse-read]"))
        return out, 0, verdict

    out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_DRIFT files=%d flags=%d "
               "reader_refused=%d gating=%s"
               % (count, flags, refused, GATING_FACE))
    for line in census_lines:
        if line.startswith("[flag]") or line.startswith("[refuse-read]"):
            out.append(line)
    return out, 2, {"verdict": "REFUSED", "reason": "E_CLG_DRIFT",
                    "files": count, "flags": flags,
                    "reader_refused": refused, "gating": GATING_FACE}


def main(argv=None):
    target = os.path.join(ROOT, "qa")
    lines, code, _verdict = evaluate(
        target, os.path.join(target, CENSUS.BASELINE_NAME), root=ROOT)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
