"""review_window_wire - exempt_review reads its window from the declaration.

`review_window_decl` pins and dates the window a review is judged against, but
until this file nothing consumed it: `exempt_review` still took `--window` as a
per-call argument with its own CLI default, so the declaration could read
PINNED while every actual age reading used another number and the divergence
was invisible. This module is the one place that translates the declaration
into the number a reviewer ages against, and it never derives that number
itself:

  * the window comes from `review_window_decl.resolve` (caller window left
    unset) and is read off the report it hands back - no second join over the
    declarations rows, no default, no arithmetic in this file;
  * an UNPINNED, DRIFT or consistency-refused declaration is a refusal here
    too, with its own E_RWW_* code, so a caller that asked for the declared
    window never silently falls back to a literal;
  * the resolver's own codes are carried through rather than collapsed: the
    suffix after E_RWD_ becomes the suffix after E_RWW_ (UNPINNED, DRIFT,
    REFUSED, DECL_FUTURE, UNREADABLE, BAD_SHAPE), so an operator reading the
    refusal can tell which law refused.

Read-only, no clock, no network. Criteria AC-RWW1..AC-RWW6 were pinned inside
the R2305 seed row of state/queue/tech.md BEFORE this file existed.
Pure ASCII source, stdlib only.
"""

import review_window_decl

REFUSAL_PREFIX = "E_RWW"
RESOLVER_PREFIX = "E_RWD_"

SOURCE_DECLARATION = "declaration"
SOURCE_ARGUMENT = "argument"


class ReviewWindowWireError(Exception):
    """Raised when the declaration cannot hand back an honest window."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def carry_code(code):
    """E_RWD_X -> E_RWW_X; anything unexpected is an unreadable refusal."""
    if isinstance(code, str) and code.startswith(RESOLVER_PREFIX):
        return REFUSAL_PREFIX + "_" + code[len(RESOLVER_PREFIX):]
    return REFUSAL_PREFIX + "_UNREADABLE"


def declared_window(root, round_text):
    """The pinned window through the resolver, or a named refusal (AC-RWW1)."""
    try:
        report = review_window_decl.resolve(root, None, round_text)
    except review_window_decl.ReviewWindowError as exc:
        raise ReviewWindowWireError(carry_code(exc.code), exc.detail)
    except Exception as exc:  # noqa: BLE001 - a broken resolver is not a pass
        raise ReviewWindowWireError(
            REFUSAL_PREFIX + "_UNREADABLE",
            "%s (%s)" % (type(exc).__name__, exc))
    if not isinstance(report, dict):
        raise ReviewWindowWireError(
            REFUSAL_PREFIX + "_UNREADABLE",
            "resolver returned %r" % (type(report).__name__,))
    window = report.get("window")
    if isinstance(window, bool) or not isinstance(window, int) or window < 1:
        raise ReviewWindowWireError(
            REFUSAL_PREFIX + "_BAD_WINDOW",
            "resolver window is not a positive int: %r" % (window,))
    return window