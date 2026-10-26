"""Round ledger line suite (R2152; criteria AC-LGR1..AC-LGR8 were
pre-registered in state/queue/tech.md BEFORE this code existed -
honesty law).

What this proves: the ledger-line shape that the F3 law and the
status-export self_drive face derive from is machine-checked instead of
merely assumed - the pinned parse, the bad-shape family with its gate
order, the narrative/ledger coverage law, the tail window, zero false
positives on the other line families, the api discipline, the CLI
contract, and a live gate over the real state.json log.

Round numbers in fixtures are three digits or more, the same numeric
domain the real log uses (R586 .. R2152).

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
LABEL = "os-ledger-lines"

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def raises(line):
    """Return the error code parse_ledger_line raises, or 'NONE'."""
    try:
        LL.parse_ledger_line(line)
    except LL.LedgerLineError as exc:
        return exc.code
    return "NONE"


def run_cli(args):
    proc = subprocess.Popen(
        [sys.executable, MODULE] + args,
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return (proc.returncode,
            out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


def write_state(path, log):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"tick": 1, "log": log}, sort_keys=True))


def run():
    # AC-LGR1: the canonical shape parses, units and the approx marker
    # are resolved, and api stays a pure integer.
    good = "R2099 tokens: local=~120k api=0 api_reason=clean window " \
           "with one suite"
    rec = LL.parse_ledger_line(good)
    rec2 = LL.parse_ledger_line(
        "R2098 tokens: local=95000 api=12 api_reason=cloud audit batch one")
    rec3 = LL.parse_ledger_line(
        "R2097 tokens: local=~1.2m api=0 api_reason=heavy window with "
        "three suites")
    check(rec["round"] == 2099 and rec["local_raw"] == "~120k"
          and rec["local_value"] == 120000 and rec["local_approx"] is True
          and rec["api"] == 0 and rec["api_approx"] is False
          and rec["api_reason"].startswith("clean window")
          and rec2["local_value"] == 95000
          and rec2["local_approx"] is False and rec2["api"] == 12
          and rec3["local_value"] == 1200000 and rec3["local_approx"] is True,
          "AC-LGR1 canonical parse, units and approx marker resolved")

    # AC-LGR2: nine bad forms, each named, plus the pinned gate order
    # round -> local -> api -> reason.
    bad = {
        "tokens: local=1k api=0 api_reason=long enough reason":
            "E_LGR_NO_ROUND",
        "R101 tokens: api=0 api_reason=long enough reason": "E_LGR_NO_LOCAL",
        "R101 tokens: local=1k api_reason=long enough reason": "E_LGR_NO_API",
        "R101 tokens: local=1k api=0": "E_LGR_NO_REASON",
        "R101 tokens: local=abc api=0 api_reason=long enough reason":
            "E_LGR_BAD_LOCAL",
        "R101 tokens: local=1k api=1k api_reason=long enough reason":
            "E_LGR_BAD_API",
        "R101 tokens: local=1k api=0 api_reason=   ": "E_LGR_NO_REASON",
        "R101 tokens: local=1k api=0 api_reason=too short":
            "E_LGR_SHORT_REASON",
        "R101 tokens: local=1k api=0 api_reason=first line\nsecond part "
        "long enough": "E_LGR_MULTILINE",
    }
    codes_ok = all(raises(line) == want for line, want in bad.items())
    order_ok = (raises("R101 tokens: local=abc api=zz api_reason=x")
                == "E_LGR_BAD_LOCAL"
                and raises("R101 tokens: local=1k api=zz api_reason=x")
                == "E_LGR_BAD_API"
                and raises("R101 tokens: local=1k api=0 api_reason=short")
                == "E_LGR_SHORT_REASON")
    check(codes_ok and order_ok,
          "AC-LGR2 nine bad forms named, gate order round/local/api/reason")

    # AC-LGR3: coverage law over narrative rounds vs ledger rounds.
    cover = [
        "R101 (first round narrative) product change",
        "R101 tokens: local=1k api=0 api_reason=round one ledger line",
        "R102 (second round narrative) product change",
        "R103 (third round narrative) product change",
        "R103 tokens: local=2k api=0 api_reason=round three ledger line",
        "R109 tokens: local=3k api=0 api_reason=orphan ledger for nine",
    ]
    rep = LL.audit(cover)
    check(rep["rounds_without_ledger"] == [102]
          and rep["ledger_without_round"] == [109]
          and rep["ledger_lines"] == 3 and rep["round_lines"] == 3
          and rep["other_lines"] == 0 and rep["errors"] == []
          and rep["clean"] is False,
          "AC-LGR3 coverage law derives missing and orphan rounds")

    # AC-LGR4: tail window inspects only the last N lines and echoes the
    # arithmetic; a bad line outside the window is not judged.
    window = [
        "R201 note about the round",
        "R201 tokens: local=1k api=0 api_reason=round twenty-one clean",
        "R202 tokens: local=zz api=0 api_reason=round twenty-two is bad",
        "R203 note about another round",
        "R203 tokens: local=2k api=0 api_reason=round twenty-three clean",
    ]
    full = LL.audit(window)
    tail = LL.audit(window, tail=2)
    check(full["total_lines"] == 5 and full["window_lines"] == 5
          and full["tail"] is None
          and full["ledger_lines"] == 3 and full["round_lines"] == 2
          and len(full["errors"]) == 1
          and full["errors"][0]["line"] == 3
          and full["errors"][0]["code"] == "E_LGR_BAD_LOCAL"
          and full["rounds_without_ledger"] == []
          and full["ledger_without_round"] == []
          and tail["total_lines"] == 5 and tail["window_lines"] == 2
          and tail["tail"] == 2 and tail["errors"] == []
          and tail["ledger_lines"] == 1 and tail["round_lines"] == 1
          and tail["clean"] is True,
          "AC-LGR4 tail window scopes the audit and echoes its arithmetic")

    # AC-LGR5: the other line families are never judged as ledger, and a
    # typo prefix is caught by the coverage law instead.
    mixed = [
        "R301 (product change narrative) something happened",
        "R2151 battery outcome: RUNNER PASS 352/353 suites green",
        "R2151 tokens: local=120k api=0 api_reason=battery ledger line",
        "carry-forward rolling line R586: folded the rounds",
        "receipt 2026-10-27 R2152: acknowledged D-20261027-01",
        "R302 token: local=1k api=0 api_reason=typo prefix round",
        "R301 tokens: local=1k api=0 api_reason=round thirty-one clean",
    ]
    mixed_rep = LL.audit(mixed)
    check(mixed_rep["ledger_lines"] == 2 and mixed_rep["round_lines"] == 3
          and mixed_rep["other_lines"] == 2
          and mixed_rep["errors"] == []
          and mixed_rep["rounds_without_ledger"] == [302]
          and mixed_rep["clean"] is False,
          "AC-LGR5 zero false positives, typo caught by coverage law")

    # AC-LGR6: api discipline - pure integer only, reason always present.
    api_codes = [
        raises("R101 tokens: local=1k api=1k api_reason=long enough reason"),
        raises("R101 tokens: local=1k api=-1 api_reason=long enough reason"),
        raises("R101 tokens: local=1k api=120 api_reason="),
        raises("R101 tokens: local=1k api=120 api_reason=short"),
    ]
    api_ok = LL.parse_ledger_line(
        "R101 tokens: local=1k api=150000 api_reason=big cloud batch with "
        "attribution")
    check(api_codes == ["E_LGR_BAD_API", "E_LGR_BAD_API",
                        "E_LGR_NO_REASON", "E_LGR_SHORT_REASON"]
          and api_ok["api"] == 150000,
          "AC-LGR6 api is a pure integer and always carries a reason")

    # AC-LGR7: CLI contract - exit codes, JSON stability, no writes.
    world = tempfile.mkdtemp(prefix="lgr-cli-")
    try:
        clean_path = os.path.join(world, "clean.json")
        dirty_path = os.path.join(world, "dirty.json")
        write_state(clean_path, [
            "R401 note",
            "R401 tokens: local=1k api=0 api_reason=round forty-one clean",
        ])
        write_state(dirty_path, [
            "R402 note",
            "R402 tokens: local=zz api=0 api_reason=round forty-two is bad",
        ])
        with io.open(clean_path, "rb") as handle:
            before = handle.read()
        clean_rc, clean_out, _ = run_cli(["--check", clean_path])
        dirty_rc, dirty_out, _ = run_cli(["--check", dirty_path])
        miss_rc, _, miss_err = run_cli(
            ["--check", os.path.join(world, "no-such.json")])
        flag_rc, flag_out, flag_err = run_cli(["--nope"])
        j1_rc, j1_out, _ = run_cli(["--check", dirty_path, "--json"])
        j2_rc, j2_out, _ = run_cli(["--check", dirty_path, "--json"])
        with io.open(clean_path, "rb") as handle:
            after = handle.read()
        payload = json.loads(j1_out)
        required = {"clean", "errors", "ledger_lines", "ledger_without_round",
                    "other_lines", "round_lines", "rounds_without_ledger",
                    "tail", "total_lines", "window_lines"}
        check(clean_rc == 0 and "VERDICT CLEAN" in clean_out
              and dirty_rc == 2 and "VERDICT DIRTY" in dirty_out
              and miss_rc == 3 and "E_LGR_NO_STATE" in miss_err
              and flag_rc == 2 and flag_out == ""
              and "E_LGR_BAD_ARGS" in flag_err
              and j1_rc == 2 and j2_rc == 2 and j1_out == j2_out
              and required.issubset(set(payload.keys()))
              and "new_missing" in payload and "baseline_missing" in payload
              and before == after,
              "AC-LGR7 CLI exit 0/2/3, stable JSON, zero file writes")
    finally:
        for name in ("clean.json", "dirty.json"):
            path = os.path.join(world, name)
            if os.path.exists(path):
                os.unlink(path)
        os.rmdir(world)

    # AC-LGR8: live gate over the real state.json log plus hygiene.
    with io.open(MODULE, "r", encoding="ascii", errors="strict") as handle:
        source = handle.read()
    net = LL.network_imports(source)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner_src = handle.read()
    live_log = LL.load_state_log(os.path.join(BASE, "state.json"))
    live = LL.audit(live_log)
    base_path = LL.default_baseline_path()
    baseline = LL.load_baseline(base_path)
    gated = LL.apply_baseline(live, baseline)
    with io.open(base_path, "r", encoding="utf-8") as handle:
        shipped = json.load(handle)
    check(live["errors"] == []
          and live["ledger_lines"] >= 30 and live["round_lines"] >= 30
          and live["rounds_without_ledger"] == [2090, 2095]
          and live["ledger_without_round"] == []
          and gated["new_missing"] == [] and gated["new_orphan"] == []
          and gated["clean"] is True
          and shipped["missing"] == [2090, 2095]
          and shipped["orphan"] == []
          and not net and LABEL in runner_src
          and EXPECTED_CRITERIA == 8,
          "AC-LGR8 live gate clean, two historical gaps baselined, hygiene")


def main():
    print("suite: round ledger line checker (R2152 AC-LGR1..AC-LGR8)")
    run()
    total = PASSES + FAILS
    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAILS == 0 and total == EXPECTED_CRITERIA
             else "FAIL", PASSES, EXPECTED_CRITERIA))
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())