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

Shape: a published line, never a silent pass.

    CLOSEOUT-GATE PASS files=<n> flags=0 reader_refused=<n> gating=flags
    CLOSEOUT-GATE REFUSED reason=<E_CLG_*> flags=<n> ... [flag] lines

Exit codes: 0 PASS; 2 REFUSED. Read-only: the gate never writes the tree, the
baseline, or any qa/ file. Stdlib only (plus the shipped census module), no
network, no shell.
"""

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


def evaluate(target, baseline):
    """Run the census check and return (lines, exit_code, verdict dict)."""
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
        out.append("CLOSEOUT-GATE PASS files=%d flags=%d "
                   "reader_refused=%d gating=%s"
                   % (count, flags, refused, GATING_FACE))
        # The informational debt is never silent: a baselined file no family
        # decodes is still named on every closeout, it just does not refuse.
        out.extend(line for line in census_lines
                   if line.startswith("[refuse-read]"))
        return out, 0, {"verdict": "PASS", "files": count, "flags": flags,
                        "reader_refused": refused, "gating": GATING_FACE}

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
        target, os.path.join(target, CENSUS.BASELINE_NAME))
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
