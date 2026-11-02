# battery_followup_help_wire.py - the follow-up CLI asks the same contract
# the runner does.
# Criteria AC-BFH1..AC-BFH6 were pre-registered in state/queue/tech.md
# (R2365 seed row, line 412) BEFORE this file existed.
#
# Why this exists: battery_followup.py answered a bare `--help` with
# E_BFU_BAD_ARGS at exit 5, while the sibling runner answers `--help` as a
# QUESTION at exit 0 under the R2362 runner_arg_guard contract. One of the two
# CLIs therefore lied to an operator asking how to use it. This module is the
# single place that answers that question for the follow-up tool.
#
# Both halves of the answer are IMPORTED, never retyped (AC-BFH1):
#   - the house half comes from reconcile_all.CLI_CONTRACT, read through
#     runner_arg_guard.load_contract - the same importer the guard uses, so
#     there is no second way to read that contract in this tree;
#   - this tool's own flags come from battery_followup.TAKES and
#     battery_followup.FLAGS, which are the parser's own tables, so the wire
#     cannot drift from the CLI it describes and no second flag table is
#     written here.
#
# Nothing else moves (AC-BFH4): this module parses no value, opens no file and
# runs no section. It answers one question and classifies one refusal.
#
# CLI: battery_followup_help_wire.py [--json] <token...>
#   exit 0 = the question was answered, or every token is recognized
#   exit 2 = an unknown flag, named
#   exit 5 = the wire's own flags are bad, or nothing was asked
#
# Pure read: no write, no clock, no network. ASCII source, stdlib only.

import json
import sys

HELP_FLAGS = ("--help", "-h")

# The keys this module actually reads off the house contract. Checked here
# rather than trusted, so a contract that lost a key refuses instead of
# raising a bare KeyError deep inside a renderer.
RUNNER_KEYS = ("name", "known_flags", "positional_label")

WIRE_KEYS = ("status", "flag", "exit", "name", "runner", "flags")
REPORT_KEYS = WIRE_KEYS

E_BFH_NO_CONTRACT = "E_BFH_NO_CONTRACT"
E_BFH_UNKNOWN_FLAG = "E_BFH_UNKNOWN_FLAG"
E_BFH_BAD_ARGS = "E_BFH_BAD_ARGS"

STATUS_HELP = "HELP"
STATUS_RECOGNIZED = "RECOGNIZED"
STATUS_UNKNOWN = "UNKNOWN_FLAG"
STATUS_NO_ARGS = "NO_ARGS"

EXIT_OK = 0
EXIT_REFUSED = 2
EXIT_BAD_ARGS = 5


class HelpWireError(Exception):
    """Raised when the contract cannot be read honestly."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def load_runner_contract(path=None):
    """The house CLI contract, through the guard's own importer (AC-BFH1)."""
    import runner_arg_guard
    try:
        contract = runner_arg_guard.load_contract(path)
    except Exception as exc:
        raise HelpWireError(E_BFH_NO_CONTRACT, str(exc) or "unreadable")
    if not isinstance(contract, dict):
        raise HelpWireError(E_BFH_NO_CONTRACT, "contract is not a mapping")
    for key in RUNNER_KEYS:
        if key not in contract:
            raise HelpWireError(E_BFH_NO_CONTRACT, "missing key " + key)
    return contract


def own_contract(module=None):
    """This tool's own flags, taken from the parser's tables (AC-BFH1)."""
    if module is None:
        import battery_followup as module
    takes = getattr(module, "TAKES", None)
    flags = getattr(module, "FLAGS", None)
    if not isinstance(takes, dict) or not isinstance(flags, dict):
        raise HelpWireError(E_BFH_NO_CONTRACT, "battery_followup tables")
    return {"name": "battery_followup.py",
            "takes": dict(takes),
            "flags": dict(flags)}


def known_flags(own):
    """Every token this tool accepts, including the question itself."""
    tokens = list(own["flags"]) + list(own["takes"]) + list(HELP_FLAGS)
    return tuple(sorted(tokens))


def house_line(runner):
    """The house half of the block, rendered by the guard's own renderer.

    R2373: the formatting moved to contract_usage_renderer, which the guard
    exports as usage_text (two-line) and contract_line (one-line). This wire
    asks the guard for the one-line form instead of writing a second format
    string, so a change in that module moves BOTH CLIs (AC-CUR1) while this
    line stays byte-identical to what R2366 published (AC-CUR2).
    """
    import runner_arg_guard
    try:
        return runner_arg_guard.contract_line(runner)
    except Exception as exc:
        code = getattr(exc, "code", None) or str(exc) or "unrenderable"
        raise HelpWireError(E_BFH_NO_CONTRACT, code)


def usage_text(module=None, path=None):
    """The usage block, derived from both contracts rather than hand-written."""
    own = own_contract(module)
    runner = load_runner_contract(path)
    # The value flags carry a metavar derived from their own option key, so the
    # placeholder cannot drift from the table either.
    takes = " ".join("%s %s" % (flag, own["takes"][flag].upper())
                     for flag in sorted(own["takes"]))
    flags = " ".join(sorted(own["flags"]))
    lines = [
        "usage: %s %s %s [--help]" % (own["name"], takes, flags),
        "  --help  print this usage and run no section (exit 0)",
        "  exit 0 = every section PASS, or this question answered",
        "  exit 2 = a section FAILED",
        "  exit 3 = the evidence file is missing",
        "  exit 5 = bad flags",
        house_line(runner),
    ]
    return "\n".join(lines) + "\n"


def answer(tokens, module=None):
    """One pinned verdict for a token list; never parses a value (AC-BFH4)."""
    own = own_contract(module)
    known = known_flags(own)
    tokens = list(tokens)
    if not tokens:
        return {"status": STATUS_NO_ARGS, "flag": None, "exit": EXIT_BAD_ARGS}
    for token in tokens:
        if token in HELP_FLAGS:
            return {"status": STATUS_HELP, "flag": None, "exit": EXIT_OK}
    for token in tokens:
        if token.startswith("-") and token not in known:
            return {"status": STATUS_UNKNOWN, "flag": token,
                    "exit": EXIT_REFUSED}
    return {"status": STATUS_RECOGNIZED, "flag": None, "exit": EXIT_OK}


def classify(tokens, module=None, path=None):
    """The wire report: the answer plus the two contract names it came from."""
    verdict = answer(tokens, module)
    own = own_contract(module)
    runner = load_runner_contract(path)
    return {"status": verdict["status"],
            "flag": verdict["flag"],
            "exit": verdict["exit"],
            "name": own["name"],
            "runner": runner["name"],
            "flags": list(known_flags(own))}


def render(report, text=None):
    """One line per pinned key, in order, so a reading is comparable."""
    lines = ["ANSWER %s exit=%d flag=%s"
             % (report["status"], report["exit"], report["flag"] or "-"),
             "HOUSE %s flags=%s"
             % (report["runner"], ",".join(report["flags"]))]
    if text:
        lines.append(text.rstrip("\n"))
    return "\n".join(lines) + "\n"


def parse_wire_args(argv):
    """The wire's own flags: --json only. Everything else is a token to read."""
    opts = {"json": False}
    tokens = []
    for arg in argv:
        if arg == "--json":
            opts["json"] = True
        elif arg == "--":
            continue
        else:
            tokens.append(arg)
    return opts, tokens


def main(argv):
    opts, tokens = parse_wire_args(argv)
    try:
        report = classify(tokens)
    except HelpWireError as exc:
        print(str(exc))
        return EXIT_BAD_ARGS
    text = usage_text() if report["status"] == STATUS_HELP else None
    print(render(report, text), end="")
    if opts["json"]:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    return report["exit"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))