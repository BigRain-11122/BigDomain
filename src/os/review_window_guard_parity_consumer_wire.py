"""review_window_guard_parity_consumer_wire - the acting path asks the parity.

Criteria AC-RWPC1..AC-RWPC6 were pinned inside the R2387 seed row of
state/queue/tech.md BEFORE this file existed. Anchor check at HEAD 2026-11-02:
the five names hit only prose and state files (that seed row,
src/os/board_R2387.py, src/os/closeout_R2396.py, src/os/state.json,
docs/status-export.json) with zero executable occupancy under src/.

Why this exists: R2387 shipped review_window_guard_parity_blind_agreement,
which can tell an INFORMED agreement from one that only exists because
neither face could judge the declarations list - a blind green over exactly
the file that would break both paths. Measured at R2387 with git grep, `RWGP.`
had ZERO non-test hits under src/: nothing an operator walks ever asked it, so
a split and an ignorance refused nothing. This module is the one place that
asks, on the path that actually ages entries.

It carries no law of its own:

  * the reading is review_window_guard_parity_blind_agreement.check, asked at
    CALL time (AC-RWPC1), so patching that reading moves what this guard does
    and no second rewind comparison lives here - this file never looks at a
    declared_by, never parses the declarations list, never resolves a window;
  * a split refuses with E_RWPC_SPLIT naming BOTH faces' codes (AC-RWPC2);
  * a blind agreement refuses with E_RWPC_UNKNOWN, a different word from the
    split's, naming the ignorant side(s) it measured (AC-RWPC3);
  * an informed agreement refuses nothing and changes nothing, so the acting
    path's reading stays byte for byte what it was (AC-RWPC4);
  * the shipped words are not renamed: the guard's verdicts are its own, the
    parity's three verdict words and the wire's refusal codes are read from
    their owners, and the CLI keeps the 0/2/3/5 shape every sibling uses
    (AC-RWPC5).

Scope is deliberately narrow, the same shape review_window_wire_argument_guard
uses on the argument path: ONLY a provable split and a provable ignorance
refuse. UNPINNED, DRIFT, a mere move and an unreadable file are the resolver's
and the history's business and are reported by them, not re-judged here.

This module writes nothing, reads no clock, imports no network. Pure ASCII
source, stdlib only.
"""

import json
import os
import sys

import review_window_guard_parity_blind_agreement as RWGB

GUARD_PREFIX = "E_RWPC"

SPLIT_CODE = GUARD_PREFIX + "_SPLIT"
UNKNOWN_CODE = GUARD_PREFIX + "_UNKNOWN"
UNREADABLE_CODE = GUARD_PREFIX + "_UNREADABLE"
ROOT_CODE = GUARD_PREFIX + "_ROOT"

# AC-RWPC5: this face's own key order. The parity's words are copied from the
# parity's vocabulary at call time rather than restated as literals.
REPORT_KEYS = (
    "verdict",
    "code",
    "parity",
    "ignorance",
    "declared",
    "declared_code",
    "argument",
    "argument_code",
    "window",
    "detail",
)

VERDICT_CLEAN = "WINDOW-CLEAN"
VERDICT_SPLIT = "WINDOW-SPLIT"
VERDICT_UNKNOWN = "WINDOW-UNKNOWN"
VERDICTS = (VERDICT_CLEAN, VERDICT_SPLIT, VERDICT_UNKNOWN)


class ReviewWindowParityConsumerError(Exception):
    """Raised only when the pair provably splits or provably agrees blind."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _blank(verdict, code, detail, found=None):
    found = found or {}
    return {
        "verdict": verdict,
        "code": code,
        "parity": found.get("verdict"),
        "ignorance": found.get("ignorance"),
        "declared": found.get("declared"),
        "declared_code": found.get("declared_code"),
        "argument": found.get("argument"),
        "argument_code": found.get("argument_code"),
        "window": found.get("declared_window"),
        "detail": detail,
    }


def reading(root, round_text=None):
    """Ask the blind-agreement reading, and answer in THIS face's words.

    AC-RWPC1: the parity is imported and asked at call time, so a patched
    reading flows straight through this file.
    """
    try:
        found = RWGB.check(root, round_text)
    except Exception as exc:  # noqa: BLE001 - a broken reader is not a pass
        code = getattr(exc, "code", None)
        if isinstance(code, str) and code == RWGB.BLIND_PREFIX + "_ROOT":
            return _blank(VERDICT_UNKNOWN, ROOT_CODE,
                          "%s (%s)" % (type(exc).__name__, exc))
        return _blank(VERDICT_UNKNOWN, UNREADABLE_CODE,
                      "%s (%s)" % (type(exc).__name__, exc))
    if not isinstance(found, dict):
        return _blank(VERDICT_UNKNOWN, UNREADABLE_CODE,
                      "parity returned %r" % (type(found).__name__,))

    verdict = found.get("verdict")
    if verdict == RWGB.VERDICT_DISAGREES:
        return _blank(
            VERDICT_SPLIT, SPLIT_CODE,
            "declared=%s argument=%s"
            % (found.get("declared_code") or found.get("declared") or "-",
               found.get("argument_code") or found.get("argument") or "-"),
            found)
    if verdict == RWGB.VERDICT_UNKNOWN:
        return _blank(
            VERDICT_UNKNOWN, UNKNOWN_CODE,
            "ignorance=%s declared=%s argument=%s"
            % (found.get("ignorance"),
               found.get("declared_code") or found.get("declared") or "-",
               found.get("argument_code") or found.get("argument") or "-"),
            found)
    if verdict == RWGB.VERDICT_AGREES:
        return _blank(VERDICT_CLEAN, None, "", found)
    return _blank(VERDICT_UNKNOWN, UNREADABLE_CODE,
                  "parity verdict is not a known word: %r" % (verdict,),
                  found)


def guard(root, round_text=None):
    """Refuse a split or a blind agreement; hand every other reading back.

    AC-RWPC4: a clean reading returns here and the caller continues with
    exactly the bytes it produced before this guard existed.
    """
    found = reading(root, round_text)
    if found["verdict"] in (VERDICT_SPLIT, VERDICT_UNKNOWN):
        raise ReviewWindowParityConsumerError(found["code"], found["detail"])
    return found


def one_line(found):
    """The single line an operator reads."""
    window = "-" if found["window"] is None else "%d" % found["window"]
    return ("REVIEW WINDOW PARITY CONSUMER verdict=%s code=%s parity=%s "
            "window=%s declared=%s argument=%s ignorance=%s"
            % (found["verdict"], found["code"] or "-", found["parity"], window,
               found["declared_code"] or found["declared"] or "-",
               found["argument_code"] or found["argument"] or "-",
               found["ignorance"] or "-"))


def to_json(found):
    """Serialise in the pinned key order only (AC-RWPC5)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = found.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: review_window_guard_parity_consumer_wire.py --check "
         "[--root PATH] [--round RN] [--json]\n"
         "  exit 0 = the pair agrees and both could judge the list\n"
         "  exit 2 = refused: the pair splits (E_RWPC_SPLIT), a side could\n"
         "           not judge it (E_RWPC_UNKNOWN), or the reading is broken\n"
         "  exit 3 = the root is missing\n"
         "  exit 5 = bad flags\n")


def main(argv):
    check = False
    as_json = False
    round_text = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--round"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("%s_BAD_ARGS: %s needs a value\n"
                                 % (GUARD_PREFIX, arg))
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
            sys.stdout.write("%s_BAD_ARGS: unknown flag %s\n"
                             % (GUARD_PREFIX, arg))
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("%s_BAD_ARGS: --check is required\n" % GUARD_PREFIX)
        sys.stdout.write(USAGE)
        return 5
    found = reading(root, round_text)
    if as_json:
        sys.stdout.write(to_json(found))
    else:
        sys.stdout.write(one_line(found) + "\n")
        if found["code"]:
            sys.stdout.write("  %s\n" % found["code"])
        if found["detail"]:
            sys.stdout.write("  %s\n" % found["detail"])
    if found["verdict"] == VERDICT_CLEAN:
        return 0
    if found["code"] == ROOT_CODE:
        return 3
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))