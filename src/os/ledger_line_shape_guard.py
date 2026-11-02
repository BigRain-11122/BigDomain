# ledger_line_shape_guard.py - one door that asks the ledger law BEFORE a line
# lands in the state log.
#
# The ledger law lives in ledger_lines.LEDGER_PREFIX_RE = ^R(\d{3,5}) tokens:
# and parse_ledger_line refuses a line that breaks the pinned shape. Nothing
# asked it at the WRITE path: the R2392 closeout wrote
# "2026-11-02 R2392 tokens: ..." with a date prefix, round 2392 then read
# rounds_without_ledger, and four ledger suites plus the census went red on a
# tree nobody had edited. The line was discovered a window later, by a reader.
#
# This module is the door: a candidate line is asked of the shipped law
# (imported at CALL time, so a patched law moves every verdict here) and a
# refusal names the failing token instead of appending and hoping.
#
# Honest scope, stated rather than hidden: the tree carries 231 per-round
# writers that emit ledger lines (closeout_R*.py and friends). None of them
# routes through this door yet - that set difference is the seeded gap row
# ledger_line_shape_writer_sweep, and this window's own line is the first one
# that does.
import io
import json
import os
import re
import sys

LABEL = "os-ledger-line-shape-guard"

# A date prefix is exactly the shape R2392 wrote and exactly the shape the law
# refuses; it is named here so the refusal can quote the prefix itself rather
# than only the law's generic "no leading 'R<n> tokens:' prefix".
DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}\s+)R(\d{3,5})\b")

TAIL_TAIL = "  ]"
INDENT = " " * 16

JSON_KEYS = ("verdict", "code", "token", "round", "local_value", "api",
             "predicted_bytes", "wrote")

_STATE_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "state.json")


def _law():
    """The shipped ledger law, imported at CALL time (AC-LLSG1)."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import ledger_lines
    return ledger_lines


def _refused(code, token, detail=""):
    return {"verdict": "REFUSED", "code": code, "token": token,
            "detail": detail, "round": None, "local_value": None,
            "api": None, "predicted_bytes": None, "wrote": "no"}


def check_candidate(line):
    """Ask the shipped law about one candidate ledger line.

    Verdict is ACCEPTED or REFUSED. Every field that the law validates (round,
    local, api, reason) is taken from the law's own parse, never re-derived
    here (AC-LLSG3).
    """
    text = line if isinstance(line, str) else str(line)
    text = text.strip("\r\n")
    if not text.strip():
        return _refused("E_LLSG_EMPTY", "", "candidate is empty")
    law = _law()
    match = DATE_PREFIX_RE.match(text)
    if match is not None and law.classify(text[match.start(2) - 1:]) == "ledger":
        # The law's own classifier decides that the rest IS a ledger line, so
        # the prefix is the only thing standing between it and the write path.
        # A narrative line that merely QUOTES the token strings is ROUND and
        # passes - measured the hard way in this window own closeout.
        return _refused("E_LLSG_DATE_PREFIX", match.group(1).strip(),
                        "a ledger line may not carry a date prefix; the law "
                        "reads ^R<n> tokens: and round %s would be lost"
                        % match.group(2))
    # A narrative round line (date prefix, no ledger body) is not a ledger
    # line at all: the law classifies it ROUND and it lands untouched.
    if law.classify(text) == "round":
        number = law.NARRATIVE_RE.match(text)
        return {"verdict": "ACCEPTED", "code": "-", "token": "",
                "detail": "narrative round line",
                "round": int(number.group(1)) if number else None,
                "local_value": None, "api": None,
                "predicted_bytes": None, "wrote": "no"}
    try:
        parsed = law.parse_ledger_line(text)
    except law.LedgerLineError as exc:
        return _refused(exc.code, _token_of(exc.detail), exc.detail)
    return {"verdict": "ACCEPTED", "code": "-", "token": "",
            "detail": "", "round": parsed["round"],
            "local_value": parsed["local_value"], "api": parsed["api"],
            "predicted_bytes": None, "wrote": "no"}


def _token_of(detail):
    """The smallest quoted piece of a law detail, so a refusal names a token."""
    match = re.search(r"'([^']+)'", detail)
    return match.group(1) if match else detail[:24]


def predict_append(state_text, line):
    """Return the exact post-append text, or refuse without touching a byte.

    The append transform is the one the round writers already use: the new
    item is spliced in front of the closing bracket of the log array, with the
    file's own EOL, then the payload is parsed back and the last item compared.
    """
    eol = "\r\n" if "\r\n" in state_text else "\n"
    tail = eol + TAIL_TAIL + eol + "}"
    if state_text.count(tail) != 1:
        raise ValueError("E_LLSG_TAIL_NOT_UNIQUE")
    item = line.strip("\r\n")
    splice = "," + eol + INDENT + json.dumps(item, ensure_ascii=True)
    new_text = state_text.replace(tail, splice + tail, 1)
    payload = json.loads(new_text)
    if payload["log"][-1] != item:
        raise ValueError("E_LLSG_READBACK_MISMATCH")
    return new_text


def read_state(state_path):
    with io.open(state_path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def append_ledger_line(state_path, line, execute=False):
    """Refuse or (with execute) land the line through ONE verified write.

    A refusal returns before the file is opened for write, so it writes no
    byte (AC-LLSG4); a dry run reports the exact predicted post size.
    """
    verdict = check_candidate(line)
    if verdict["verdict"] != "ACCEPTED":
        return verdict
    text = read_state(state_path)
    try:
        new_text = predict_append(text, line)
    except ValueError as exc:
        code = str(exc)
        verdict.update({"verdict": "REFUSED", "code": code,
                        "token": TAIL_TAIL.strip(), "detail": code})
        return verdict
    predicted = len(new_text.encode("utf-8"))
    verdict["predicted_bytes"] = predicted
    if not execute:
        return verdict
    with io.open(state_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(new_text)
    landed = read_state(state_path)
    if len(landed.encode("utf-8")) != predicted:
        raise SystemExit("E_LLSG_WRITE_VERIFY")
    verdict["wrote"] = "yes"
    return verdict


def _fail(message, code=5):
    sys.stderr.write(message + "\n")
    return code


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    want_json = False
    path = None
    line = None
    append = False
    execute = False
    state_path = _STATE_DEFAULT

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--json":
            want_json = True
        elif arg == "--check":
            if i + 1 >= len(args):
                return _fail("E_LLSG_BAD_ARGS: --check needs a value")
            line = args[i + 1]
            i += 1
        elif arg == "--file":
            if i + 1 >= len(args):
                return _fail("E_LLSG_BAD_ARGS: --file needs a value")
            path = args[i + 1]
            i += 1
        elif arg == "--state":
            if i + 1 >= len(args):
                return _fail("E_LLSG_BAD_ARGS: --state needs a value")
            state_path = args[i + 1]
            i += 1
        elif arg == "--append":
            append = True
        elif arg == "--execute":
            execute = True
        elif arg in ("-h", "--help"):
            sys.stdout.write(__doc__ or "usage: ledger_line_shape_guard.py "
                             "--check LINE [--json] | --file PATH "
                             "[--append [--execute]] [--state PATH]\n")
            return 0
        else:
            return _fail("E_LLSG_BAD_FLAG: %s" % arg)
        i += 1

    if path is not None:
        try:
            with io.open(path, "r", encoding="utf-8", newline="") as handle:
                line = handle.read()
        except IOError:
            return _fail("E_LLSG_UNREADABLE: %s" % path, 3)
    if line is None:
        return _fail("E_LLSG_BAD_ARGS: --check LINE or --file PATH is required")

    if append:
        if not os.path.exists(state_path):
            return _fail("E_LLSG_UNREADABLE: %s" % state_path, 3)
        verdict = append_ledger_line(state_path, line, execute=execute)
    else:
        verdict = check_candidate(line)

    out = dict((k, verdict.get(k)) for k in JSON_KEYS)
    if want_json:
        sys.stdout.write(json.dumps(out, sort_keys=True, ensure_ascii=True)
                         + "\n")
    else:
        sys.stdout.write("%s code=%s token=%s round=%s local=%s api=%s "
                         "predicted_bytes=%s wrote=%s\n"
                         % (out["verdict"], out["code"], out["token"],
                            out["round"], out["local_value"], out["api"],
                            out["predicted_bytes"], out["wrote"]))
        if out["verdict"] == "REFUSED" and verdict.get("detail"):
            sys.stdout.write("  NOTE %s\n" % verdict["detail"])
    return 0 if out["verdict"] == "ACCEPTED" else 2


if __name__ == "__main__":
    sys.exit(main())