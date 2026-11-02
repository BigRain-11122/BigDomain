"""review_window_guard_parity_blind_agreement - agreement on ignorance is not agreement.

Criteria AC-RWGB1..AC-RWGB6 were pinned inside the R2381 seed row of
state/queue/tech.md BEFORE this file existed. Anchor check at HEAD
2026-11-02: review_window_guard_parity_blind_agreement, AC-RWGB and E_RWGB
hit only prose and state files (that seed row, src/os/closeout_R2381.py,
src/os/state.json) with zero executable occupancy under src/.

Why this exists: review_window_guard_parity answers ONE question - do the two
review-window faces agree about a rewind - and it answers it by comparing two
rewind booleans. Measured at R2381 on a declaration NEITHER face can read
(state/review_window.json containing `{not json`): declared E_RWW_UNREADABLE,
argument ARGUMENT-UNKNOWN carrying E_RWAG_UNREADABLE, and the parity reads
verdict=PARITY-AGREES agrees=yes. The one reading whose whole purpose is to
catch a split therefore reports a green over exactly the file that would break
both paths, and the law it guards is invisible there.

This face adds the distinction and NOTHING else:

  * the parity is IMPORTED and asked at call time (AC-RWGB6), so patching
    review_window_guard_parity.check moves this reading - no third rewind
    comparison, no second declarations reader, no row parser lives here;
  * a side that answered "I could not judge" is named as an ignorance, and a
    pair that agrees only because nobody could judge reads PARITY-UNKNOWN with
    both codes carried (AC-RWGB1) - never AGREES;
  * a genuine two-sided rewind and a genuine two-sided clean (or merely moved,
    or deliberately UNPINNED) list keep the parity's own verdict and keep its
    eight fields byte for byte (AC-RWGB2, AC-RWGB3);
  * a real split is still PARITY-DISAGREES naming both codes, and a split
    outranks an ignorance instead of being swallowed by it (AC-RWGB4);
  * the CLI adds exactly one exit code - 1 for UNKNOWN - to the parity's own
    0/2/3/5, and the JSON adds exactly one key, `ignorance`, after the eight
    pinned ones (AC-RWGB5).

Read-only: it writes nothing, reads no clock, imports no network. Pure ASCII
source, stdlib only.
"""

import json
import os
import sys

import review_window_guard_parity as RWGP
import review_window_wire_argument_guard as RWAG

BLIND_PREFIX = "E_RWGB"

# AC-RWGB5: the parity's eight keys, in its own order, plus one new key.
REPORT_KEYS = RWGP.PARITY_KEYS + ("ignorance",)

VERDICT_AGREES = RWGP.VERDICTS[0]
VERDICT_DISAGREES = RWGP.VERDICTS[1]
VERDICT_UNKNOWN = "PARITY-UNKNOWN"
VERDICTS = (VERDICT_AGREES, VERDICT_DISAGREES, VERDICT_UNKNOWN)

IGNORANCE_NONE = "none"
IGNORANCE_DECLARED = "declared"
IGNORANCE_ARGUMENT = "argument"
IGNORANCE_BOTH = "both"

# A refusal that says the list could not be JUDGED, as opposed to a refusal
# that reports a state of the list the caller can act on (UNPINNED, DRIFT).
IGNORANCE_SUFFIXES = ("_UNREADABLE", "_BAD_SHAPE", "_BROKEN")


class ReviewWindowGuardParityBlindError(Exception):
    """Raised only when the reading cannot be taken at all."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def unknown_word():
    """The argument face's own word for 'this list could not be judged'.

    Taken from that face's vocabulary at call time rather than restated, so
    renaming the word there moves this reading instead of splitting it.
    """
    for word in RWAG.VERDICTS:
        if isinstance(word, str) and word.endswith("-UNKNOWN"):
            return word
    return None


def ignorant_code(code):
    """Is this refusal an 'I could not judge' one?"""
    if not isinstance(code, str):
        return False
    for suffix in IGNORANCE_SUFFIXES:
        if code.endswith(suffix):
            return True
    return False


def ignorance(report):
    """Which sides answered 'I could not judge', named as a word."""
    declared = ignorant_code(report.get("declared_code"))
    word = unknown_word()
    argument = word is not None and report.get("argument") == word
    if declared and argument:
        return IGNORANCE_BOTH
    if declared:
        return IGNORANCE_DECLARED
    if argument:
        return IGNORANCE_ARGUMENT
    return IGNORANCE_NONE


def check(root, round_text=None):
    """Ask the parity, then name whether its agreement was informed."""
    if not os.path.isdir(root):
        raise ReviewWindowGuardParityBlindError(
            BLIND_PREFIX + "_ROOT", "no such root: %s" % root)

    base = RWGP.check(root, round_text)
    found = dict(base)
    found["ignorance"] = ignorance(base)

    if base.get("agrees") is False:
        verdict = VERDICT_DISAGREES
    elif found["ignorance"] != IGNORANCE_NONE:
        verdict = VERDICT_UNKNOWN
    else:
        verdict = VERDICT_AGREES
    found["verdict"] = verdict
    # One invariant for every verdict: agrees is true exactly when the two
    # faces agreed AND that agreement was informed.
    found["agrees"] = verdict == VERDICT_AGREES
    return found


def one_line(found):
    """The single line an operator reads."""
    window = "-" if found["declared_window"] is None else \
        "%d" % found["declared_window"]
    return ("REVIEW WINDOW GUARD PARITY BLIND verdict=%s rewind=%s window=%s "
            "declared=%s argument=%s agrees=%s ignorance=%s"
            % (found["verdict"],
               "yes" if found["rewind"] else "no",
               window,
               found["declared_code"] or found["declared"],
               found["argument_code"] or found["argument"],
               "yes" if found["agrees"] else "no",
               found["ignorance"]))


def render(found):
    """The one line, then the two codes side by side."""
    out = [one_line(found)]
    out.append("  DECLARED %s%s"
               % (found["declared"],
                  "" if not found["declared_code"]
                  else " " + found["declared_code"]))
    out.append("  ARGUMENT %s%s"
               % (found["argument"],
                  "" if not found["argument_code"]
                  else " " + found["argument_code"]))
    out.append("  IGNORANCE %s" % found["ignorance"])
    return "\n".join(out)


def to_json(found):
    """Serialise in the pinned key order only (AC-RWGB5)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = found.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: review_window_guard_parity_blind_agreement.py --check "
         "[--root PATH] [--round RN] [--json]\n"
         "  exit 0 = the two faces agree and both could judge the list\n"
         "  exit 1 = UNKNOWN: the pair agreed only because a side could not\n"
         "           judge it, so the agreement proves nothing\n"
         "  exit 2 = the two faces disagree about the declarations list\n"
         "  exit 3 = the root is missing or unreadable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    check_flag = False
    as_json = False
    round_text = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check_flag = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--round"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RWGB_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            if arg == "--root":
                root = argv[index]
            else:
                round_text = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RWGB_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check_flag:
        sys.stdout.write("E_RWGB_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        found = check(root, round_text)
    except ReviewWindowGuardParityBlindError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        return 3
    if as_json:
        sys.stdout.write(to_json(found))
    else:
        sys.stdout.write(render(found) + "\n")
    if found["verdict"] == VERDICT_AGREES:
        return 0
    if found["verdict"] == VERDICT_UNKNOWN:
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))