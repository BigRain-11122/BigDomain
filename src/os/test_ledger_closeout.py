"""Closing-station suite (R2154; criteria AC-LGN1..AC-LGN8 were
pre-registered in state/queue/tech.md BEFORE this code existed -
honesty law).

What this proves: the line a round writes as its very last act is
checked at the moment the round is closing, instead of a later window
discovering that it never parsed. One target round, one verdict, five
pinned report keys, the four verdict values, and a CLI that prints
`LEDGER OK <round>` only when the round may actually be shut.

Round numbers in fixtures are three digits or more, the same numeric
domain the real log uses (R586 .. R2154).

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import io
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import ledger_lines as LL  # noqa: E402

EXPECTED_CRITERIA = 8
MODULE = os.path.join(BASE, "ledger_lines.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-ledger-closeout"

PASSES = 0
FAILS = 0

GOOD = ("R2150 tokens: local=~90k api=0 "
        "api_reason=five-silence scan plus one product change")
GOOD_2 = ("R2151 tokens: local=~70k api=0 "
          "api_reason=closing station suite and its evidence logs")


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def write_world(lines, name="state.json"):
    world = tempfile.mkdtemp(prefix="bigdomain-lgn-")
    path = os.path.join(world, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"tick": 1, "log": lines}, ensure_ascii=True))
    return world, path


def drop_world(world):
    for name in os.listdir(world):
        os.unlink(os.path.join(world, name))
    os.rmdir(world)


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    out = proc.stdout.decode("ascii", "replace")
    return proc.returncode, out, proc.stderr.decode("ascii", "replace")


def run():
    # AC-LGN1: fixed report shape, closed verdict set, pure derivation.
    first = LL.check_closeout([GOOD])
    second = LL.check_closeout([GOOD])
    check(tuple(sorted(first.keys())) == tuple(sorted(LL.CLOSEOUT_KEYS))
          and first == second
          and first["verdict"] in LL.CLOSEOUT_VERDICTS
          and first["round"] == 2150
          and first["ledger_line"] == 1
          and first["errors"] == [],
          "AC-LGN1 report keys pinned, deterministic, verdict in closed set")

    # AC-LGN2: the default target is the newest narrative round.
    only_ledger = LL.check_closeout([GOOD])
    only_narrative = LL.check_closeout([GOOD, "2026-10-27 R2150 the round "
                                              "narrative line"])
    both = LL.check_closeout([GOOD, "R2150 narrative", "R2151 narrative"])
    check(only_ledger["round"] == 2150 and only_ledger["verdict"] == "OK"
          and only_narrative["round"] == 2150
          and only_narrative["verdict"] == "OK"
          and both["round"] == 2151 and both["verdict"] == "MISSING"
          and both["ledger_line"] is None,
          "AC-LGN2 default target is the newest narrative round")

    # AC-LGN3: a broken closing line is refused, reason included.
    bad_forms = [
        "R2150 tokens: local=x7 api=0 api_reason=local field is not a "
        "number",
        "R2150 tokens: local=~9k api=zero api_reason=api field is not an "
        "integer",
        "R2150 tokens: local=~9k api=0 api_reason=",
        "R2150 tokens: local=~9k api=0 api_reason=short",
    ]
    codes = []
    for line in bad_forms:
        report = LL.check_closeout([line])
        codes.append((report["verdict"], len(report["errors"])))
    check(all(item == ("BAD_SHAPE", 1) for item in codes),
          "AC-LGN3 four bad closing shapes all BAD_SHAPE with one error")

    # AC-LGN4: ordering against what was already settled; future lines
    # never influence the verdict.
    reordered = LL.check_closeout([GOOD, "R2149 narrative", GOOD.replace(
        "2150", "2149")], 2149)
    future = LL.check_closeout([GOOD, "R2151 narrative", GOOD_2])
    check(reordered["verdict"] == "NOT_MONOTONIC"
          and reordered["previous_round"] == 2150
          and reordered["errors"][0]["code"] == "E_LGN_NOT_MONOTONIC"
          and future["verdict"] == "OK"
          and future["previous_round"] == 2150,
          "AC-LGN4 older round after a settled one is NOT_MONOTONIC")

    # AC-LGN5: a narrative without its ledger line is MISSING (fail
    # closed); a ledger line without a narrative is legal here.
    missing = LL.check_closeout(["R2150 narrative", "some note"])
    lone = LL.check_closeout([GOOD])
    check(missing["verdict"] == "MISSING"
          and missing["errors"][0]["code"] == "E_LGN_MISSING"
          and lone["verdict"] == "OK"
          and lone["previous_round"] is None,
          "AC-LGN5 missing closing line refused, lone ledger line legal")

    # AC-LGN6: CLI contract - one LEDGER OK line on success, none on
    # failure, and the JSON form carries the same verdict.
    world, path = write_world([GOOD, "R2150 narrative"])
    bad_world, bad_path = write_world(["R2150 narrative", "R2150 token: "
                                       "local=~9k api=0 api_reason=typo"])
    try:
        rc_ok, out_ok, _ = run_cli(["--closeout", path])
        rc_bad, out_bad, _ = run_cli(["--closeout", bad_path])
        rc_json, out_json, _ = run_cli(["--closeout", "--json", path])
        try:
            payload = json.loads(out_json)
        except ValueError:
            payload = None
        ok_lines = [line for line in out_ok.splitlines() if line.strip()]
        check(rc_ok == 0 and out_ok.strip() == "LEDGER OK 2150"
              and len(ok_lines) == 1
              and rc_bad == 2 and "LEDGER OK" not in out_bad
              and rc_json == 0 and payload is not None
              and tuple(sorted(payload.keys()))
              == tuple(sorted(LL.CLOSEOUT_KEYS))
              and payload["verdict"] == "OK",
              "AC-LGN6 CLI prints one LEDGER OK on success only")

        # AC-LGN7: read-only and offline.
        with io.open(path, "rb") as handle:
            before = handle.read()
        run_cli(["--closeout", path])
        with io.open(path, "rb") as handle:
            after = handle.read()
        with io.open(MODULE, "r", encoding="ascii", errors="strict") as handle:
            source = handle.read()
        check(before == after and LL.network_imports(source) == [],
              "AC-LGN7 state file untouched by the gate, zero network imports")
    finally:
        drop_world(world)
        drop_world(bad_world)

    # AC-LGN8: the old faces still behave, and the live log closes.
    parsed = LL.parse_ledger_line(GOOD)
    window = LL.audit([GOOD, "R2150 narrative"], None)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner_src = handle.read()
    live_log = LL.load_state_log(os.path.join(BASE, "state.json"))
    live = LL.check_closeout(live_log)
    ledger_rounds = [int(LL.LEDGER_PREFIX_RE.match(line).group(1))
                     for line in live_log
                     if LL.LEDGER_PREFIX_RE.match(line)]
    check(parsed["round"] == 2150 and parsed["api"] == 0
          and window["clean"] is True
          and live["verdict"] == "OK"
          and live["round"] == max(ledger_rounds)
          and LABEL in runner_src
          and EXPECTED_CRITERIA == 8,
          "AC-LGN8 legacy faces unchanged, live log closes clean")


def main():
    print("suite: round closing station (R2154 AC-LGN1..AC-LGN8)")
    run()
    total = PASSES + FAILS
    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAILS == 0 and total == EXPECTED_CRITERIA
             else "FAIL", PASSES, EXPECTED_CRITERIA))
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())