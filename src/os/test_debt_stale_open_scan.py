"""debt_stale_open_scan suite (R3162; criteria AC-DSRC1..AC-DSRC6 were pinned
in state/queue/tech.md as the R2524 seed row BEFORE the code existed, and
AC-DSRC2 was JUDGED-CHANGED on the board at R3162 with the measured reason).
AC-DSRC7 was pinned on the board at R3163 BEFORE the three-way split landed,
and AC-DSRC3 was re-pinned (JUDGED-CHANGED, narrower) to the new state names.

What this proves: an OPEN debt row is judged by its OWN item round against the
two shipped evidence faces, a missing measurement can never read STALE, the
discharge bracket is named rather than merged, the reading writes nothing, and
the CLI keeps its pinned codes.

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

import debt_register  # noqa: E402
import debt_stale_open_scan as DSOS  # noqa: E402

EXPECTED_CRITERIA = 7
MODULE = os.path.join(BASE, "debt_stale_open_scan.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-debt-stale-open"
WIRED_EXPECT = '"test_debt_stale_open_scan.py"), 7),'

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


LIVE_LABEL = "2026-11-21 R3001 PRODUCT: shipped a face, SUITE PASS 6/6"
QUIET_LABEL = "2026-11-21 R3002 narration: a labelled round with no file"
ARCHIVE_LABEL = "2026-11-01 R3000 PRODUCT: folded block, SUITE PASS 5/5"

ROWS = [
    "- [ ] opened=R3001 | item=product-face-R3001 | note=shipped | first=no",
    "- [ ] opened=R3000 | item=product-face-R3000 | note=folded | first=no",
    "- [ ] opened=R2999 | item=loop-s4u-reconcile | "
    "note=repair needs elevation (34th disclosure at R3001) | first=no",
    "- [ ] opened=R3999 | item=product-face-R3999 | note=never logged | "
    "first=no",
    "- [ ] opened=R3002 | item=product-face-R3002 | note=no evidence file | "
    "first=no",
    "- [ ] opened=R3003 | item=product-face-R3003b | note=not a round | "
    "first=no",
    "- [x] opened=R2990 | item=product-face-R2991 | closed=R2991 | "
    "note=discharged",
]


def write(path, text, newline="\n"):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with io.open(path, "w", encoding="utf-8", newline=newline) as handle:
        handle.write(text)


def make_world():
    """A temp root with a register, a live log, a fold archive and qa files."""
    world = tempfile.mkdtemp(prefix="bigdomain-dsos-")
    write(os.path.join(world, "state", "debt.md"), "\n".join(ROWS) + "\n")
    write(os.path.join(world, "src", "os", "state.json"),
          json.dumps({"tick": 3002, "log": [LIVE_LABEL, QUIET_LABEL]}) + "\n")
    write(os.path.join(world, "logs", "state-log-archive-2026-11.md"),
          "# archive\n\n" + ARCHIVE_LABEL + "\n")
    write(os.path.join(world, "qa", "suite-face-R3001.log"), "SUITE PASS 6/6\n")
    write(os.path.join(world, "qa", "suite-face-R3000.log"), "SUITE PASS 5/5\n")
    return world


def digest_tree(root):
    rows = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(dirnames)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace("\\", "/")
            with io.open(full, "rb") as handle:
                rows.append("%s %s" % (rel, hashlib.sha256(
                    handle.read()).hexdigest()))
    return "\n".join(rows)


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def by_item(report):
    return dict((row["item"], row) for row in report["rows"])


def ac_dsrc1(world):
    """The register is read through the SHIPPED row law, asked at call time."""
    report = DSOS.scan(world)
    moved = 0
    original = debt_register.register
    try:
        def doctored(root, current_round=None):
            out = original(root, current_round)
            out["rows"] = [row for row in out["rows"]
                           if row["item"] != "product-face-R3001"]
            return out
        debt_register.register = doctored
        patched = DSOS.scan(world)
        moved = report["open_count"] - patched["open_count"]
    finally:
        debt_register.register = original
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    no_parser = ("OPEN_RE" not in source and "DONE_RE" not in source
                 and "^- \\[ \\]" not in source)
    check(moved == 1 and no_parser,
          "AC-DSRC1 the register is read through the shipped debt row law "
          "asked at call time, and this module carries no second parser")


def ac_dsrc2(world):
    """The item round decides; note rounds are published, never decisive."""
    report = DSOS.scan(world)
    rows = by_item(report)
    live = rows["product-face-R3001"]
    folded = rows["product-face-R3000"]
    disclosure = rows["loop-s4u-reconcile"]
    ok = (live["state"] == "STALE-OPEN" and live["deciding"] == 3001
          and folded["state"] == "STALE-OPEN" and folded["deciding"] == 3000
          and disclosure["state"] == "OPEN-UNNAMED"
          and disclosure["note_rounds"] == [3001]
          and disclosure["deciding"] is None)
    check(ok, "AC-DSRC2 the item round decides, a live or folded round both "
          "count, and a discharged NOTE round never promotes a row whose "
          "item names no round (the false-positive guard)")


def ac_dsrc3(world):
    """Missing measurement can never reach STALE; refusals carry their code."""
    report = DSOS.scan(world)
    rows = by_item(report)
    unknown = rows["product-face-R3999"]
    no_file = rows["product-face-R3002"]
    not_round = rows["product-face-R3003b"]
    refused = []
    for world2 in (None, "empty"):
        if world2 is None:
            missing = tempfile.mkdtemp(prefix="bigdomain-dsos-none-")
        else:
            missing = tempfile.mkdtemp(prefix="bigdomain-dsos-bad-")
            write(os.path.join(missing, "state", "debt.md"),
                  "- [ ] opened=not-a-round | item=x | first=no\n")
        code = None
        try:
            DSOS.scan(missing)
        except DSOS.DebtStaleOpenError as exc:
            code = exc.code
        refused.append(code)
    zeros = 0
    ok = (unknown["state"] == "UNKNOWN"
          and no_file["state"] == "LANDED-NO-EVIDENCE"
          and not_round["state"] == "OPEN-UNNAMED"
          and report["stale_count"] == 2
          and refused[0] == "E_DSRC_NO_REGISTER"
          and refused[1] == "E_DSRC_REGISTER"
          and zeros == 0)
    check(ok, "AC-DSRC3 a round that is never labelled reads UNKNOWN, a "
          "labelled round with no evidence file reads LANDED-NO-EVIDENCE, a "
          "token that is not a round stays OPEN-UNNAMED, and a missing or "
          "malformed register refuses by name")


def ac_dsrc4(world):
    """The reading is read-only and says so."""
    before = digest_tree(world)
    report = DSOS.scan(world)
    after = digest_tree(world)
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    no_write = (all(token not in source for token in (
        'os.remove', 'os.rename', 'os.unlink', 'shutil', 'open(path, "w"'))
        and '"w",' not in source)
    ok = (before == after and report["action"] == "CLOSE-BY-HAND"
          and no_write and "CLOSE-BY-HAND" in DSOS.render(report))
    check(ok, "AC-DSRC4 the reading closes nothing: the world digest is "
          "identical before and after, the module holds no write primitive, "
          "and the report says CLOSE-BY-HAND")


def ac_dsrc5(world):
    """The CLI keeps its pinned codes and a byte-stable JSON face."""
    clean = tempfile.mkdtemp(prefix="bigdomain-dsos-clean-")
    write(os.path.join(clean, "state", "debt.md"),
          "- [ ] opened=R2999 | item=loop-only | note=owed | first=no\n")
    write(os.path.join(clean, "src", "os", "state.json"),
          json.dumps({"tick": 2999, "log": []}) + "\n")
    code_clean, out_clean = run_cli(["--check", "--root", clean])
    code_stale, _ = run_cli(["--check", "--root", world])
    code_gate, _ = run_cli(["--check", "--gate", "--root", world])
    code_missing, out_missing = run_cli(
        ["--check", "--root", os.path.join(clean, "absent")])
    code_bad, _ = run_cli(["--check", "--root", world, "--nope"])
    first, text_first = run_cli(["--check", "--json", "--root", world])
    second, text_second = run_cli(["--check", "--json", "--root", world])
    keys_ok = json.loads(text_first) and list(json.loads(text_first)) == list(
        DSOS.REPORT_KEYS)
    ok = (code_clean == 0 and "NO-STALE" in out_clean
          and code_stale == 0 and code_gate == 2
          and code_missing == 3 and "E_DSRC_NO_REGISTER" in out_missing
          and code_bad == 5
          and first == 0 and second == 0 and text_first == text_second
          and text_first.endswith("\n") and not text_first.endswith("\n\n")
          and keys_ok)
    check(ok, "AC-DSRC5 the CLI exits 0 on a clean or reported reading, 2 "
          "only when --gate finds stale, 3 on a missing register, 5 on bad "
          "flags, and --json is byte-stable over the pinned keys")


def ac_dsrc6(world):
    """Hygiene, registration and the live reading taken this window."""
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_ok = all(byte < 128 for byte in raw)
    text = raw.decode("ascii")
    no_clock = not any(token in text for token in (
        "import time", "import datetime", "time.time", "socket", "urllib",
        "http.client", "subprocess"))
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner = handle.read()
    wired = WIRED_EXPECT in runner and ('("%s",' % LABEL) in runner
    live = DSOS.scan(REPO)
    summed = (live["stale_count"] + live["unnamed_count"]
              + live["landed_no_evidence_count"] + live["unknown_count"])
    ok = (ascii_ok and no_clock and wired
          and summed == live["open_count"] and live["open_count"] > 0
          and isinstance(live["stale_count"], int)
          and len(live["rows"]) == live["open_count"])
    print("LIVE %s" % DSOS.one_line(live), flush=True)
    check(ok, "AC-DSRC6 pure ASCII stdlib with no clock and no network, wired "
          "as %s(7), and the live register reading sums and prints its stale "
          "count as a number" % LABEL)


def ac_dsrc7(world):
    """The discharge bracket is named, never merged (R3163)."""
    report = DSOS.scan(world)
    rows = by_item(report)
    live = rows["product-face-R3001"]
    no_file = rows["product-face-R3002"]
    never = rows["product-face-R3999"]
    arm_a = (live["state"] == "STALE-OPEN"
             and live["evidence"] == "DISCHARGED"
             and live["deciding"] == 3001
             and no_file["state"] == "LANDED-NO-EVIDENCE"
             and no_file["evidence"] == "LANDED-NO-EVIDENCE"
             and no_file["deciding"] == 3002
             and never["state"] == "UNKNOWN"
             and never["evidence"] == "UNKNOWN"
             and never["deciding"] == 3999)
    tallies = {
        "STALE-OPEN": 0, "OPEN-UNNAMED": 0,
        "LANDED-NO-EVIDENCE": 0, "UNKNOWN": 0,
    }
    for row in report["rows"]:
        tallies[row["state"]] += 1
    live_report = DSOS.scan(REPO)
    live_tallies = {
        "STALE-OPEN": 0, "OPEN-UNNAMED": 0,
        "LANDED-NO-EVIDENCE": 0, "UNKNOWN": 0,
    }
    for row in live_report["rows"]:
        live_tallies[row["state"]] += 1
    arm_b = (
        report["stale_count"] == tallies["STALE-OPEN"]
        and report["unnamed_count"] == tallies["OPEN-UNNAMED"]
        and report["landed_no_evidence_count"] == tallies["LANDED-NO-EVIDENCE"]
        and report["unknown_count"] == tallies["UNKNOWN"]
        and sum(tallies.values()) == report["open_count"]
        and live_report["stale_count"] == live_tallies["STALE-OPEN"]
        and live_report["unnamed_count"] == live_tallies["OPEN-UNNAMED"]
        and (live_report["landed_no_evidence_count"]
             == live_tallies["LANDED-NO-EVIDENCE"])
        and live_report["unknown_count"] == live_tallies["UNKNOWN"]
        and sum(live_tallies.values()) == live_report["open_count"])
    measuring = tempfile.mkdtemp(prefix="bigdomain-dsos-measuring-")
    write(os.path.join(measuring, "state", "debt.md"),
          "- [ ] opened=R3002 | item=landed-no-file-R3002 | note=x | first=no\n"
          "- [ ] opened=R3999 | item=never-labelled-R3999 | note=y | first=no\n")
    write(os.path.join(measuring, "src", "os", "state.json"),
          json.dumps({"tick": 3002, "log": [QUIET_LABEL]}) + "\n")
    code_gate, out_gate = run_cli(
        ["--check", "--gate", "--root", measuring])
    arm_c = (code_gate == 0 and "NO-STALE" in out_gate
             and "landed_no_evidence=1" in out_gate
             and "unknown=1" in out_gate and "stale=0" in out_gate)
    first, text_first = run_cli(["--check", "--json", "--root", world])
    second, text_second = run_cli(["--check", "--json", "--root", world])
    parsed = json.loads(text_first)
    row_keys = list(parsed["rows"][0])
    line = DSOS.one_line(report)
    arm_d = (row_keys == list(DSOS.ROW_KEYS) and "evidence" in row_keys
             and list(parsed) == list(DSOS.REPORT_KEYS)
             and text_first == text_second
             and "landed_no_evidence=%d" % report["landed_no_evidence_count"]
             in line
             and "unknown=%d" % report["unknown_count"] in line
             and "undischarged=" not in line)
    arm_e = (report["stale_count"] == 2
             and rows["loop-s4u-reconcile"]["state"] == "OPEN-UNNAMED"
             and rows["product-face-R3003b"]["state"] == "OPEN-UNNAMED"
             and rows["product-face-R3000"]["state"] == "STALE-OPEN"
             and rows["product-face-R3000"]["evidence"] == "DISCHARGED")
    with io.open(MODULE, "r", encoding="utf-8") as handle:
        source = handle.read()
    seen = set(row["evidence"] for row in report["rows"])
    arm_f = ("OPEN-UNDISCHARGED" not in source
             and DSOS.EVIDENCE_STATES == (
                 "DISCHARGED", "LANDED-NO-EVIDENCE", "UNKNOWN")
             and seen == set(DSOS.EVIDENCE_STATES)
             and isinstance(live_report["landed_no_evidence_count"], int)
             and isinstance(live_report["unknown_count"], int))
    ok = (arm_a and arm_b and arm_c and arm_d and arm_e and arm_f)
    check(ok, "AC-DSRC7 the discharge bracket is named not merged: the three "
          "states are separately reachable with their own evidence word, each "
          "count equals its row tally and sums to open, a world holding only "
          "the two unproven brackets is NO-STALE and gates clean, the keys and "
          "the one line carry both new counts, and the retired word is gone")


def main():
    world = make_world()
    ac_dsrc1(world)
    ac_dsrc2(world)
    ac_dsrc3(world)
    ac_dsrc4(world)
    ac_dsrc5(world)
    ac_dsrc6(world)
    ac_dsrc7(world)
    print("SUITE %s %d/%d"
          % ("PASS" if FAILS == 0 else "FAIL", PASSES,
             PASSES + FAILS), flush=True)
    if PASSES + FAILS != EXPECTED_CRITERIA or FAILS:
        print("EXPECTED %d criteria" % EXPECTED_CRITERIA, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
