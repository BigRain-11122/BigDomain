"""debt_item_unique suite (R2290; criteria AC-DIU1..AC-DIU6 were pinned in
state/queue/tech.md as the R2274 seed row BEFORE this code existed).

What this proves: debt_register checks each row's shape and allows at most
one open first=yes, but it never checks that an ITEM appears once. The live
register carries reconcile-battery-and-matrix on two done rows, so "what does
the register say about this item" depends on which duplicate a reader takes,
and debt_close's own ALREADY-DONE and AMBIGUOUS refusals can both fire for
one name. This suite pins the read-only reader that makes that a reading.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import glob
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

import debt_item_unique as DU  # noqa: E402
import debt_register as DR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "debt_item_unique.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-debt-item-unique"
WIRED_EXPECT = '"test_debt_item_unique.py"), 6),'

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


OPEN_A = "- [ ] opened=R2270 | item=item-a | note=live debt | first=yes"
DONE_A = "- [x] opened=R2268 | item=item-a | closed=R2270"
DONE_B1 = "- [x] opened=R2248 | item=item-b | closed=R2249"
DONE_B2 = "- [x] opened=R2250 | item=item-b | closed=R2252"
OPEN_C = "- [ ] opened=R2231 | item=item-c | note=unique | first=no"
DONE_D = "- [x] opened=R2200 | item=item-d | closed=R2201"


def make_world(rows, raw=None):
    """Build a temp root carrying state/debt.md."""
    world = tempfile.mkdtemp(prefix="bigdomain-diu-")
    inner = os.path.join(world, "state")
    os.makedirs(inner)
    body = raw if raw is not None else "\n".join(rows) + "\n"
    with io.open(os.path.join(inner, "debt.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    world_handle = world
    return world_handle


def register_path(world):
    return os.path.join(world, "state", "debt.md")


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def code_of(world):
    """The module's own error code, or NONE when the reading succeeded."""
    try:
        DU.audit(world)
    except DU.DebtItemUniqueError as exc:
        return exc.code
    return "NONE"


# AC-DIU1: the row law is debt_register's, asked at call time - a patched
# parse flows straight through and the module carries no second parser.
mixed_world = make_world([OPEN_A, DONE_A, OPEN_C, DONE_D])
plain = DU.audit(mixed_world)
real_parse = DR.parse


def renamed_parse(text):
    """Same row count, one item renamed so a fresh duplicate appears."""
    rows = real_parse(text)
    for row in rows:
        if row["item"] == "item-c":
            row["item"] = "item-a"
    return rows


DR.parse = renamed_parse
patched = DU.audit(mixed_world)
DR.parse = real_parse
with io.open(MODULE, "r", encoding="utf-8") as handle:
    module_source = handle.read()
patched_a = [entry for entry in patched["duplicates"]
             if entry["item"] == "item-a"]
check(plain["duplicate_count"] == 1
      and plain["duplicates"][0]["row_count"] == 2
      and len(patched_a) == 1 and patched_a[0]["row_count"] == 3
      and not any(entry["item"] == "item-c"
                  for entry in patched["duplicates"])
      and "def parse(" not in module_source
      and "DR.parse(" in module_source,
      "AC-DIU1 row law imported from debt_register, patched parse flows through")

# AC-DIU2: every duplicate is reported with every one of its rows, and the
# reported total equals the same grouping recomputed from the raw parse.
dup_world = make_world([OPEN_A, DONE_A, DONE_B1, DONE_B2, OPEN_C])
report = DU.audit(dup_world)
raw_rows = DR.parse(read_text(register_path(dup_world)))
recount = {}
for row in raw_rows:
    recount[row["item"]] = recount.get(row["item"], 0) + 1
expected_repeats = {name: count for name, count in recount.items()
                    if count > 1}
reported_repeats = {entry["item"]: entry["row_count"]
                    for entry in report["duplicates"]}
rows_complete = all(len(entry["rows"]) == entry["row_count"]
                    and all(set(row) == {"state", "opened", "closed", "line"}
                            for row in entry["rows"])
                    for entry in report["duplicates"])
lines_ok = True
dup_lines = read_text(register_path(dup_world)).split("\n")
for entry in report["duplicates"]:
    for row in entry["rows"]:
        line_text = dup_lines[row["line"] - 1]
        lines_ok = lines_ok and entry["item"] in line_text
check(report["rows_scanned"] == len(raw_rows)
      and reported_repeats == expected_repeats
      and report["duplicate_count"] == len(expected_repeats)
      and rows_complete and lines_ok,
      "AC-DIU2 every duplicate with all its rows, total matches recount")

# AC-DIU3: the two classes are separated and the verdict never merges them.
open_plus_done = DU.audit(make_world([OPEN_A, DONE_A, OPEN_C]))
done_only = DU.audit(make_world([DONE_B1, DONE_B2, OPEN_C]))
kind_open = [entry["kind"] for entry in open_plus_done["duplicates"]]
kind_done = [entry["kind"] for entry in done_only["duplicates"]]
check(report["verdict"] == "DUPLICATES"
      and report["dup_open_count"] == 1 and report["dup_done_count"] == 1
      and kind_open == ["DUP-OPEN"] and open_plus_done["dup_done_count"] == 0
      and kind_done == ["DUP-DONE"] and done_only["dup_open_count"] == 0,
      "AC-DIU3 DUP-OPEN and DUP-DONE separated, never merged")

# AC-DIU4: honest UNIQUE, honest EMPTY, and both unreadable faces fail
# closed with their own codes instead of reading UNIQUE.
unique_world = make_world([OPEN_A, DONE_D, OPEN_C])
unique = DU.audit(unique_world)
empty_world = make_world([], raw="# debt register\n\n## Open\n\n## Closed\n")
empty = DU.audit(empty_world)
absent_world = tempfile.mkdtemp(prefix="bigdomain-diu-absent-")
os.makedirs(os.path.join(absent_world, "state"))
code_absent = code_of(absent_world)
bad_world = make_world(["- [ ] opened=R2266 | item=x | first=maybe"])
code_bad = code_of(bad_world)
unique_cli, unique_out = run_cli(["--check", "--root", unique_world])
empty_cli, empty_out = run_cli(["--check", "--root", empty_world])
absent_cli, absent_out = run_cli(["--check", "--root", absent_world])
bad_cli, bad_out = run_cli(["--check", "--root", bad_world])
check(unique["verdict"] == "UNIQUE" and unique["duplicate_count"] == 0
      and empty["verdict"] == "EMPTY" and empty["rows_scanned"] == 0
      and code_absent == "E_DIU_MISSING"
      and code_bad == "E_DIU_BAD_REGISTER"
      and unique_cli == 0 and "UNIQUE" in unique_out
      and empty_cli == 0 and "EMPTY" in empty_out
      and absent_cli == 3 and "E_DIU_MISSING" in absent_out
      and bad_cli == 3 and "E_DIU_BAD_REGISTER" in bad_out,
      "AC-DIU4 honest UNIQUE and EMPTY, absent and malformed fail closed")

# AC-DIU5: the reader writes nothing and reads no clock; the CLI codes are
# 0/2/3/5 and --json is byte-stable over the pinned keys in order.
dup_cli, dup_out = run_cli(["--check", "--root", dup_world])
before = digest(register_path(dup_world))
DU.audit(dup_world)
run_cli(["--check", "--root", dup_world])
after = digest(register_path(dup_world))
json_one, json_out_one = run_cli(["--check", "--root", dup_world, "--json"])
json_two, json_out_two = run_cli(["--check", "--root", dup_world, "--json"])
parsed = json.loads(json_out_one)
bad_flag, _ = run_cli(["--bogus"])
no_check, _ = run_cli(["--root", dup_world])
residue = glob.glob(os.path.join(dup_world, "state", "*.diu-tmp"))
check(before == after and not residue
      and dup_cli == 2 and "DUP-OPEN" in dup_out and "DUP-DONE" in dup_out
      and unique_cli == 0
      and absent_cli == 3
      and bad_flag == 5 and no_check == 5
      and json_one == 2 and json_two == 2
      and json_out_one == json_out_two
      and list(parsed.keys()) == list(DU.REPORT_KEYS)
      and parsed["verdict"] == "DUPLICATES"
      and parsed["duplicate_count"] == 2,
      "AC-DIU5 zero writes, zero clock, CLI 0/2/3/5, byte-stable JSON")

# AC-DIU6: purity, wiring, and a live read-only reading of the real
# register (the duplicate this seed was found from must be visible).
non_ascii = [ch for ch in module_source if ord(ch) > 127]
imports = [line.strip() for line in module_source.splitlines()
           if line.strip().startswith("import ")
           or line.strip().startswith("from ")]
banned = ("socket", "urllib", "requests", "http", "time", "datetime",
          "subprocess")
net_hits = [line for line in imports if any(word in line for word in banned)]
with io.open(RUNNER, "r", encoding="utf-8") as handle:
    runner = handle.read()
live_before = digest(os.path.join(REPO, "state", "debt.md"))
live = DU.audit(REPO)
live_after = digest(os.path.join(REPO, "state", "debt.md"))
live_carries_seed = any(entry["item"] == "reconcile-battery-and-matrix"
                        for entry in live["duplicates"])
check(not non_ascii and not net_hits
      and WIRED_EXPECT in runner and LABEL in runner
      and live_before == live_after
      and live_carries_seed
      and live["duplicate_count"] == len(live["duplicates"]),
      "AC-DIU6 pure ASCII, stdlib only, wired, live reading names the seed case")

print("LIVE %s" % DU.one_line(live), flush=True)
print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL",
                          PASSES, EXPECTED_CRITERIA), flush=True)
sys.exit(0 if FAILS == 0 else 1)