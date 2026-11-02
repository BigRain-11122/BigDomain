"""runner_arg_guard (R2362; criteria AC-RAG1..AC-RAG6 were pinned inside
the R2348 tech seed row of state/queue/tech.md:404 BEFORE this code).

Why this exists: reconcile_all.py has no argument parser. It treats argv[1]
as an evidence path, so any token handed to it - `--help` included - becomes
a FILE NAME and a real battery starts. R2344/R2346/R2347/R2348 each measured
the same trap (a stray `--help` file in the repo root, a truncated run). This
module is the guard that reads the runner argv and refuses an unknown flag
BEFORE any suite starts.

The known-flag set is IMPORTED from the runner itself (reconcile_all.CLI_CONTRACT),
never a second hand-written list - so the guard cannot drift from the tool it
guards.

Guard CLI (this module, not the runner):

    python runner_arg_guard.py [--json] [--] <runner argv ...>
    python runner_arg_guard.py --guard-help

Exit codes: 0 allowed or asked, 2 refused, 3 runner unreadable / no contract,
5 bad guard flags.

Stdlib only, ASCII source, zero network, no clock, read-only: this module
never starts the runner and never creates a file.
"""

import importlib.util
import json
import os
import sys

import contract_usage_renderer as CUR
import own_usage_block_renderer as OUB

GUARD_LABEL = "runner-arg-guard"
GUARD_FLAGS = ("--json",)
GUARD_POSITIONAL = "<runner argv ...>"
GUARD_EXTRA = ("runner_arg_guard.py --guard-help",)
GUARD_PROSE = (
    "answers whether reconcile_all.py would accept that argv; "
    "exit 0 allowed/asked, 2 refused, 3 unreadable runner, "
    "5 bad guard flags. A bare --help is forwarded to the runner "
    "as a QUESTION (exit 0), never swallowed by the guard.")
RUNNER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))), "sandbox", "reconcile_all.py")
CONTRACT_KEYS = ("name", "known_flags", "max_positional", "positional_label")
JSON_KEYS = ("allowed", "created_path", "reason", "refused", "runner", "status")

E_OK = 0
E_REFUSED = 2
E_UNREADABLE = 3
E_BAD_GUARD_FLAG = 5


class ContractError(Exception):
    """The runner could not be imported or carries no CLI contract."""


def load_contract(path=None):
    """Import the runner module and hand back its CLI_CONTRACT dict."""
    target = RUNNER if path is None else path
    spec = importlib.util.spec_from_file_location("_rag_runner", target)
    if spec is None or spec.loader is None:
        raise ContractError("E_RAG_UNREADABLE_RUNNER")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        raise ContractError("E_RAG_UNREADABLE_RUNNER")
    contract = getattr(module, "CLI_CONTRACT", None)
    if not isinstance(contract, dict):
        raise ContractError("E_RAG_NO_CONTRACT")
    for key in CONTRACT_KEYS:
        if key not in contract:
            raise ContractError("E_RAG_CONTRACT_MISSING_" + key.upper())
    return contract


def usage_text(contract):
    """Runner usage, derived from the contract (never hand-written).

    R2373: the formatting lives in contract_usage_renderer, which is the ONE
    owner of the contract-block vocabulary - the wire renders its house line
    through the same module, so a change there moves both CLIs (AC-CUR1).
    The text this function returns is byte-identical to what R2362 shipped.
    """
    return CUR.block(contract)


def contract_line(contract):
    """The one-line form of the same contract; the wire asks for this."""
    return CUR.inline(contract)


def classify(runner_argv, contract, cwd):
    """Decide what the runner would do with this argv, without running it.

    Returns a pinned dict: status is allowed | refused | asked, allowed is the
    raw argv as it would pass through (order preserved), refused names any
    token that would have become a file, created_path is that absolute path.
    """
    argv = list(runner_argv)
    known = tuple(contract["known_flags"])
    max_positional = int(contract["max_positional"])
    result = {"runner": contract["name"], "allowed": [], "refused": [],
              "created_path": "", "reason": "", "status": "allowed"}
    if argv == ["--help"]:
        result["reason"] = "asked"
        result["status"] = "asked"
        return result
    positional = 0
    for token in argv:
        if token in known:
            result["allowed"].append(token)
            continue
        if token.startswith("-"):
            created = os.path.abspath(os.path.join(cwd, token))
            result["refused"] = ["%s -> %s" % (token, created)]
            result["created_path"] = created
            result["reason"] = "E_RAG_UNKNOWN_FLAG"
            result["status"] = "refused"
            return result
        positional += 1
        if positional > max_positional:
            result["refused"] = ["%s" % token]
            result["reason"] = "E_RAG_TOO_MANY_POSITIONAL"
            result["status"] = "refused"
            return result
        result["allowed"].append(token)
    return result


def render(result, as_json):
    """One stable line, or byte-stable JSON over the pinned keys."""
    if as_json:
        payload = dict((key, result[key]) for key in JSON_KEYS)
        return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True)
    if result["status"] == "refused":
        return "%s REFUSED %s %s" % (GUARD_LABEL, result["reason"],
                                     " ".join(result["refused"]))
    if result["status"] == "asked":
        return "%s ASKED %s" % (GUARD_LABEL, result["runner"])
    return "%s ALLOWED %s" % (GUARD_LABEL, " ".join(result["allowed"]))


def guard_usage():
    """This tool's OWN block, rendered by the one own-block owner (AC-OUB1).

    R2383: the literal that used to live here was the second of two shapes a
    third tool could have copied. Every line now comes from
    own_usage_block_renderer, so a change there moves this block too, while
    the published text stays byte-identical to R2366 (AC-OUB2).
    """
    return OUB.block({"name": "runner_arg_guard.py",
                      "flags": GUARD_FLAGS,
                      "brackets": True,
                      "positional": GUARD_POSITIONAL,
                      "extra": GUARD_EXTRA,
                      "prose": (GUARD_PROSE,)})


def main(argv):
    args = list(argv[1:])
    as_json = False
    runner_argv = []
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--":
            runner_argv = args[index + 1:]
            break
        if token == "--guard-help":
            print(guard_usage(), flush=True)
            return E_OK
        if token.startswith("--guard"):
            print("%s BAD_GUARD_FLAG %s" % (GUARD_LABEL, token), flush=True)
            return E_BAD_GUARD_FLAG
        if token == "--json":
            as_json = True
            index += 1
            continue
        runner_argv = args[index:]
        break
    try:
        contract = load_contract()
    except ContractError as exc:
        print("%s %s" % (GUARD_LABEL, exc), flush=True)
        return E_UNREADABLE
    result = classify(runner_argv, contract, os.getcwd())
    print(render(result, as_json), flush=True)
    if result["status"] == "asked":
        try:
            print(usage_text(contract), flush=True)
        except CUR.ContractUsageError as exc:
            print("%s %s" % (GUARD_LABEL, exc.code), flush=True)
            return E_UNREADABLE
        return E_OK
    return E_OK if result["status"] == "allowed" else E_REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv))