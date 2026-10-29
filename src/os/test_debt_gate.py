"""debt_gate suite (R2267; criteria AC-DGT1..AC-DGT5 were pinned in
state/queue/tech.md as the R2248 f seed row BEFORE this code existed).

What this proves: the register names a `first=yes` row for the next window,
but nothing forced a window to read it. This suite pins the gate that asks
that one question - verdict, the named row, absence as OPEN-NONE, the CLI
codes and the module's purity plus its live reading.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import hashlib
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

import debt_gate as DG  # noqa: E402

EXPECTED_CRITERIA = 5
MODULE = os.path.join(BASE, "debt_gate.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-debt-gate"
WIRED_EXPECT = '"test_debt_gate.py"), 5),'

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


FIRST_ROW = ("- [ ] opened=R2266 | item=product-face-R2267 | "
             "note=verification then product | first=yes")
SECOND_ROW = ("- [ ] opened=R2231 | item=loop-s4u-reconcile | "
              "note=needs elevation | first=no")
DONE_ROW = "- [x] opened=R2260 | item=product-face-R2261 | closed=R2261"


def make_world(rows, raw=None):
    """Build a temp root carrying state/debt.md."""
    world = tempfile.mkdtemp(prefix="bigdomain-dgt-")
    inner = os.path.join(world, "state")
    os.makedirs(inner)
    body = raw if raw is not None else "\n".join(rows) + "\n"
    with io.open(os.path.join(inner, "debt.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return world


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def refusal(world, round_label="R2267"):
    """The gate own code, or NONE when the reading was not refused."""
    try:
        DG.gate(world, round_label)
    except DG.DebtGateError as exc:
        return exc.code
    return "NONE"


# AC-DGT1: the verdict is the register own reading, counts included.
world = make_world([FIRST_ROW, SECOND_ROW, DONE_ROW])
report = DG.gate(world, "R2267")
done_only = DG.gate(make_world([DONE_ROW]), "R2267")
check(report["verdict"] == "CLAIM-FIRST"
      and report["open_count"] == 2
      and report["first_count"] == 1
      and report["present"] is True
      and done_only["verdict"] == "OPEN-NONE"
      and done_only["open_count"] == 0,
      "AC-DGT1 CLAIM-FIRST verdict with the register own counts")

# AC-DGT2: the named row is fully named, and its age is honest or unknown.
aged_row = "- [ ] opened=R2200 | item=product-face-X | first=yes"
no_round = DG.gate(world)
aged = DG.gate(make_world([aged_row]), "R2267")
check(report["item"] == "product-face-R2267"
      and report["opened"] == "R2266"
      and report["note"] == "verification then product"
      and report["carried"] == 1
      and report["stale"] is False
      and no_round["carried"] is None
      and no_round["stale"] is False
      and no_round["current_round"] is None
      and aged["carried"] == 67
      and aged["stale"] is True,
      "AC-DGT2 names item, opened, note and a carried age that is never faked")

# AC-DGT3: absence reads OPEN-NONE; a lost or broken register refuses.
none_flagged = DG.gate(make_world([SECOND_ROW, DONE_ROW]), "R2267")
empty = DG.gate(make_world([]), "R2267")
missing_world = tempfile.mkdtemp(prefix="bigdomain-dgt-miss-")
bad_world = make_world(["- [ ] opened=R2266 | item=x | first=maybe"])
two_first = make_world([FIRST_ROW,
                        "- [ ] opened=R2200 | item=second | first=yes"])
check(none_flagged["verdict"] == "OPEN-NONE"
      and none_flagged["item"] is None
      and none_flagged["open_count"] == 1
      and empty["verdict"] == "OPEN-NONE"
      and empty["open_count"] == 0
      and refusal(missing_world) == "E_DGT_NO_REGISTER"
      and refusal(bad_world) == "E_DGT_BAD_FIRST"
      and refusal(two_first) == "E_DGT_BAD_FIRST",
      "AC-DGT3 absence reads OPEN-NONE while a lost or broken register refuses")

# AC-DGT4: CLI codes, byte-stable JSON, zero writes.
code_zero, out_zero = run_cli(["--check", "--root", world, "--round", "R2267"])
code_two, out_two = run_cli(["--check", "--root", make_world([SECOND_ROW]),
                            "--round", "R2267"])
code_three, out_three = run_cli(["--check", "--root", missing_world])
code_five, _ = run_cli(["--check", "--bogus"])
before = digest(os.path.join(world, "state", "debt.md"))
json_a = run_cli(["--check", "--root", world, "--round", "R2267", "--json"])
json_b = run_cli(["--check", "--root", world, "--round", "R2267", "--json"])
after = digest(os.path.join(world, "state", "debt.md"))
payload = json.loads(json_a[1])
check(code_zero == 0 and "verdict=CLAIM-FIRST" in out_zero
      and code_two == 2 and "verdict=OPEN-NONE" in out_two
      and code_three == 3 and "E_DGT_NO_REGISTER" in out_three
      and code_five == 5
      and json_a[1] == json_b[1]
      and before == after
      and list(payload.keys()) == list(DG.REPORT_KEYS),
      "AC-DGT4 CLI 0/2/3/5, byte-stable JSON with every key, zero writes")

# AC-DGT5: purity, wiring and the live reading.
with io.open(MODULE, "r", encoding="utf-8") as handle:
    source = handle.read()
non_ascii = [ch for ch in source if ord(ch) > 127]
imports = [line.strip() for line in source.splitlines()
           if line.strip().startswith("import ")
           or line.strip().startswith("from ")]
banned = ("socket", "urllib", "requests", "http", "time", "datetime",
          "subprocess")
net_hits = [line for line in imports
            if any(word in line for word in banned)]
with io.open(RUNNER, "r", encoding="utf-8") as handle:
    runner = handle.read()
live = DG.gate(REPO, "R2267")
check(not non_ascii and not net_hits
      and WIRED_EXPECT in runner and LABEL in runner
      and live["verdict"] in DG.VERDICTS
      and (live["verdict"] != "CLAIM-FIRST"
           or (live["item"] and live["opened"])),
      "AC-DGT5 pure ASCII, no network or clock, wired, live reading closed")

print("LIVE %s" % DG.one_line(live), flush=True)
print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL",
                          PASSES, EXPECTED_CRITERIA), flush=True)
sys.exit(0 if FAILS == 0 else 1)