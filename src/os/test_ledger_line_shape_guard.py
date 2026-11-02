"""ledger_line_shape_guard suite (R2401; criteria AC-LLSG1..AC-LLSG6 were
pre-registered inside the R2393 seed row of state/queue/tech.md line 470
BEFORE this code existed).

What this proves: the ledger shape law (LEDGER_PREFIX_RE = ^R(\\d{3,5})
tokens: plus parse_ledger_line) is now asked BEFORE a line lands, so the
shape R2392 actually wrote - "2026-11-02 R2392 tokens: ..." - is refused at
the door with the prefix named, instead of being appended and discovered a
window later by a reader.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import json
import os
import re
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import ledger_line_shape_guard as LLSG  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "ledger_line_shape_guard.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-ledger-line-shape-guard"

GOOD = ("R2401 tokens: local=~24k api=0 api_reason=product window - one "
        "door asks the ledger law before a line lands, and a refusal names "
        "the failing token instead of appending and discovering it later")
DATED = ("2026-11-02 R2392 tokens: local=~38k api=0 api_reason=the exact "
         "shape R2392 wrote and the law refuses")

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


def state_text(items, eol="\n"):
    body = ",\n".join(" " * 16 + json.dumps(i, ensure_ascii=True)
                      for i in items)
    text = ('{\n  "tick": 1,\n  "log": [\n' + body + "\n  ]\n}\n")
    return text if eol == "\n" else text.replace("\n", eol)


def write_state(path, items, eol="\n"):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(state_text(items, eol))
    return os.path.getsize(path)


def ac_llsg1():
    """AC-LLSG1: the acceptance law is the shipped parse, asked at CALL time."""
    original = LLSG._law

    class Fake(object):
        class LedgerLineError(Exception):
            def __init__(self, code, detail):
                Exception.__init__(self, detail)
                self.code = code
                self.detail = detail

        NARRATIVE_RE = None

        @staticmethod
        def classify(line):
            return "other"

        @staticmethod
        def parse_ledger_line(line):
            raise Fake.LedgerLineError("E_LGR_FAKE", "round 0 refused by fake")

    LLSG._law = lambda: Fake
    try:
        patched = LLSG.check_candidate(GOOD)
    finally:
        LLSG._law = original
    real = LLSG.check_candidate(GOOD)
    check(patched["verdict"] == "REFUSED"
          and patched["code"] == "E_LGR_FAKE"
          and real["verdict"] == "ACCEPTED",
          "AC-LLSG1 the verdict follows the shipped law, patched or real")


def ac_llsg2():
    """AC-LLSG2: a date-prefixed candidate is refused naming the prefix."""
    refused = LLSG.check_candidate(DATED)
    accepted = LLSG.check_candidate(GOOD)
    check(refused["verdict"] == "REFUSED"
          and refused["code"] == "E_LLSG_DATE_PREFIX"
          and refused["token"] == "2026-11-02"
          and accepted["verdict"] == "ACCEPTED"
          and accepted["code"] == "-",
          "AC-LLSG2 a date prefix is refused by name, a conforming line "
          "passes")


def ac_llsg3():
    """AC-LLSG3: local and api come from the shipped parse, never re-parsed."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_number_regex = not re.search(r"\\d\+\(\?:\\\\\.\\d\+\)\?", source)
    parsed = LLSG.check_candidate(GOOD)
    bad_api = LLSG.check_candidate(
        "R2401 tokens: local=~24k api=abc api_reason=long enough reason text")
    bad_local = LLSG.check_candidate(
        "R2401 tokens: local=lots api=0 api_reason=long enough reason text")
    check(no_number_regex
          and parsed["local_value"] == 24000
          and parsed["api"] == 0
          and parsed["round"] == 2401
          and bad_api["code"] == "E_LGR_BAD_API"
          and bad_local["code"] == "E_LGR_BAD_LOCAL",
          "AC-LLSG3 local/api verdicts are the law's own codes, no local "
          "number grammar")


def ac_llsg4():
    """AC-LLSG4: a refusal writes no byte; a dry run predicts the post size."""
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "state.json")
    before = write_state(path, ["R2400 an earlier round line"])
    with io.open(path, "rb") as handle:
        before_bytes = handle.read()

    refused = LLSG.append_ledger_line(path, DATED, execute=True)
    with io.open(path, "rb") as handle:
        after_refusal = handle.read()

    dry = LLSG.append_ledger_line(path, GOOD, execute=False)
    with io.open(path, "rb") as handle:
        after_dry = handle.read()

    landed = LLSG.append_ledger_line(path, GOOD, execute=True)
    after = os.path.getsize(path)
    payload = json.loads(io.open(path, "r", encoding="utf-8").read())
    check(refused["verdict"] == "REFUSED"
          and refused["wrote"] == "no"
          and after_refusal == before_bytes
          and after_dry == before_bytes
          and dry["predicted_bytes"] == after
          and dry["wrote"] == "no"
          and landed["wrote"] == "yes"
          and payload["log"][-1] == GOOD
          and after > before,
          "AC-LLSG4 refusal writes nothing, the dry run predicts the exact "
          "post size, the write lands the line")


def ac_llsg5():
    """AC-LLSG5: exits 0/2/3/5 and a byte-stable --json over pinned keys."""
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "state.json")
    write_state(path, ["R2400 an earlier round line"])

    def run(argv):
        import subprocess
        return subprocess.run([sys.executable, MODULE] + argv,
                              capture_output=True, text=True)

    ok = run(["--check", GOOD, "--json"])
    bad = run(["--check", DATED, "--json"])
    missing = run(["--check", GOOD, "--append", "--state",
                   os.path.join(tmp, "nope.json"), "--json"])
    flag = run(["--bogus"])
    again = run(["--check", GOOD, "--json"])
    keys = sorted(LLSG.JSON_KEYS)
    try:
        first_payload = json.loads(ok.stdout)
        second_payload = json.loads(again.stdout)
        bad_payload = json.loads(bad.stdout)
    except ValueError:
        first_payload = second_payload = bad_payload = None
    if not (ok.returncode == 0 and bad.returncode == 2
            and missing.returncode == 3 and flag.returncode == 5
            and ok.stdout == again.stdout
            and first_payload is not None
            and sorted(first_payload.keys()) == keys
            and first_payload == second_payload
            and bad_payload is not None
            and bad_payload.get("code") == "E_LLSG_DATE_PREFIX"):
        print("  measured: rc=%r/%r/%r/%r stable=%r keys_ok=%r bad_code=%r"
              % (ok.returncode, bad.returncode, missing.returncode,
                 flag.returncode, ok.stdout == again.stdout,
                 (first_payload is not None
                  and sorted(first_payload.keys()) == keys),
                 (bad_payload or {}).get("code")), flush=True)
        print("  stderr missing=%r flag=%r"
              % (missing.stderr.strip()[:80], flag.stderr.strip()[:80]),
              flush=True)
        check(False, "AC-LLSG5 CLI exits 0/2/3/5 with a byte-stable --json "
              "over the pinned keys")
        return
    check(True, "AC-LLSG5 CLI exits 0/2/3/5 with a byte-stable --json over "
          "the pinned keys")


def ac_llsg6():
    """AC-LLSG6: pure ASCII, stdlib only, no clock, no network, own label."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(ch) < 128 for ch in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    imports = re.findall(r"^\s*import (\w+)", source, re.MULTILINE)
    stdlib_only = sorted(set(imports)) == ["io", "json", "ledger_lines", "os",
                                          "re", "sys"]
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_ledger_line_shape_guard.py" in runner)
    own_label = source.count('LABEL = "%s"' % LABEL) == 1
    ok = (ascii_only and no_net and no_clock and stdlib_only and wired
          and own_label)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r imports=%r wired=%r "
              "label=%r" % (ascii_only, no_net, no_clock,
                            sorted(set(imports)), wired, own_label),
              flush=True)
    check(ok, "AC-LLSG6 pure, stdlib only, no clock, no net, wired with its "
          "own label")


def main():
    print("ledger_line_shape_guard suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_llsg1()
    ac_llsg2()
    ac_llsg3()
    ac_llsg4()
    ac_llsg5()
    ac_llsg6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())