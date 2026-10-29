"""Debt-register suite (R2248; criteria AC-DEBT1..AC-DEBT6 were
pre-registered in state/queue/tech.md as the R2240-c seed BEFORE this
code existed - honesty law. AC-DEBT7 and AC-DEBT8 land in the same
window as the code and are disclosed as such.)

What this proves: carried debt is a readable row instead of log prose.
A row is a row only at column 0 with a checkbox; unknown, duplicate or
missing keys are refused rather than silently dropped; at most one open
row may lead the next window; a debt carried three windows or more is an
alarm with its own exit code, and an unaged reading says so instead of
guessing. The register is a pure read.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import debt_register as DR  # noqa: E402

EXPECTED_CRITERIA = 8
MODULE = os.path.join(BASE, "debt_register.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-debt-register"

HEADER = "# debt register\n\nprose that mentions - [ ] a row law\n\n"

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


def make_world(body, present=True):
    world = tempfile.mkdtemp(prefix="bigdomain-dr-")
    state = os.path.join(world, "state")
    os.makedirs(state)
    if present:
        with io.open(os.path.join(state, "debt.md"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def digest_tree(world):
    parts = []
    state = os.path.join(world, "state")
    for leaf in sorted(os.listdir(state)):
        path = os.path.join(state, leaf)
        with open(path, "rb") as handle:
            parts.append((leaf, len(handle.read())))
    return tuple(parts)


def run_cli(args, cwd=REPO):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=cwd)
    return (proc.returncode, proc.stdout.decode("ascii", "replace"),
            proc.stderr.decode("ascii", "replace"))


def row(checkbox, opened, item, extra):
    return "- [%s] opened=%s | item=%s | %s\n" % (
        checkbox, opened, item, extra)


def run():
    # AC-DEBT1: closed report and row shapes, deterministic.
    body = (HEADER
            + row(" ", "R2247", "queue-seeding", "note=floors | first=yes")
            + row("x", "R2244", "battery", "closed=R2247"))
    world = make_world(body)
    try:
        first = DR.register(world, "R2248")
        second = DR.register(world, "R2248")
        keys_ok = sorted(first.keys()) == sorted(DR.REPORT_KEYS)
        row_ok = all(sorted(r.keys()) == sorted(DR.ROW_KEYS)
                     for r in first["rows"])
        shaped = (first["open_count"], first["done_count"]) == (1, 1)
        parsed = first["rows"][0]
        check(keys_ok and row_ok and first == second and shaped
              and parsed["item"] == "queue-seeding"
              and parsed["note"] == "floors"
              and first["verdict"] in DR.VERDICTS,
              "AC-DEBT1 report and row keys pinned, deterministic, "
              "open and done rows parse")
    finally:
        drop_world(world)

    # AC-DEBT2: at most one first item, and it is readable.
    two = make_world(HEADER
                     + row(" ", "R2247", "a", "first=yes")
                     + row(" ", "R2247", "b", "first=yes"))
    one = make_world(HEADER + row(" ", "R2246", "lead-me", "first=yes")
                     + row(" ", "R2247", "later", "first=no"))
    none = make_world(HEADER + row(" ", "R2247", "plain", "first=no"))
    try:
        raised = ""
        try:
            DR.register(two, "R2248")
        except DR.DebtRegisterError as exc:
            raised = exc.code
        lead = DR.first_item(DR.register(one, "R2248"))
        empty_lead = DR.first_item(DR.register(none, "R2248"))
        check(raised == "E_DR_BAD_FIRST" and lead == "lead-me"
              and empty_lead is None,
              "AC-DEBT2 two first flags refused, one reads through, "
              "none reads honestly empty")
    finally:
        drop_world(two)
        drop_world(one)
        drop_world(none)

    # AC-DEBT3: staleness is a window count, unknown without a round.
    aged = make_world(HEADER
                      + row(" ", "R2245", "old", "first=yes")
                      + row(" ", "R2247", "fresh", "first=no"))
    try:
        now = DR.register(aged, "R2248")
        earlier = DR.register(aged, "R2247")
        unaged = DR.register(aged)
        stale_rows = [r["item"] for r in now["rows"] if r["stale"]]
        check(now["verdict"] == "DEBT-STALE" and stale_rows == ["old"]
              and now["oldest_carried"] == 3
              and earlier["verdict"] == "DEBT-OPEN"
              and earlier["stale_count"] == 0
              and unaged["verdict"] == "DEBT-OPEN"
              and unaged["stale_known"] is False
              and unaged["oldest_carried"] is None,
              "AC-DEBT3 a row carried three windows is stale, two is "
              "not, and an unaged reading says stale=unknown")
    finally:
        drop_world(aged)

    # AC-DEBT4: CLI exit codes and a byte-stable JSON face.
    clean = make_world(HEADER)
    openw = make_world(HEADER + row(" ", "R2247", "x", "first=yes"))
    stalew = make_world(HEADER + row(" ", "R2244", "x", "first=yes"))
    gone = make_world(HEADER, present=False)
    malformed = make_world(HEADER + row(" ", "R2247", "x",
                                       "first=yes | wat=1"))
    try:
        clean_code, _, _ = run_cli(["--check", "--root", clean])
        open_code, _, _ = run_cli(["--check", "--root", openw,
                                   "--round", "R2248"])
        stale_code, _, _ = run_cli(["--check", "--root", stalew,
                                    "--round", "R2248"])
        gone_code, _, _ = run_cli(["--check", "--root", gone])
        bad_row_code, _, _ = run_cli(["--check", "--root", malformed])
        bad_flag_code, _, _ = run_cli(["--check", "--root", clean, "--wat"])
        bad_round_code, _, _ = run_cli(["--check", "--root", clean,
                                        "--round", "nope"])
        help_code, help_out, _ = run_cli(["--help"])
        json_code, json_a, _ = run_cli(["--check", "--root", openw,
                                        "--round", "R2248", "--json"])
        _, json_b, _ = run_cli(["--check", "--root", openw,
                                "--round", "R2248", "--json"])
        parsed = json.loads(json_a)
        check(clean_code == 0 and open_code == 2 and stale_code == 4
              and gone_code == 3 and bad_row_code == 3
              and bad_flag_code == 5 and bad_round_code == 3
              and help_code == 0 and "usage: debt_register.py" in help_out
              and json_code == 2
              and sorted(parsed.keys()) == sorted(DR.REPORT_KEYS)
              and json_a == json_b and json_a.endswith("\n"),
              "AC-DEBT4 CLI exits 0/2/4/3/5 on clean/open/stale/"
              "bad-input/bad-flags, JSON parses and is byte-stable")
    finally:
        for world in (clean, openw, stalew, gone, malformed):
            drop_world(world)

    # AC-DEBT5: an empty register is clean, a missing one is not silent.
    empty = make_world(HEADER)
    missing = make_world(HEADER, present=False)
    try:
        body = DR.register(empty, "R2248")
        absent = DR.register(missing, "R2248")
        check(body["open_count"] == 0 and body["verdict"] == "DEBT-CLEAN"
              and body["oldest_carried"] is None
              and absent["present"] is False
              and absent["open_count"] == 0
              and absent["verdict"] == "DEBT-CLEAN",
              "AC-DEBT5 a register with no rows reads clean, a missing "
              "file is reported absent instead of silently clean")
    finally:
        drop_world(empty)
        drop_world(missing)

    # AC-DEBT6: pure read, ASCII source, no network or clock import.
    world = make_world(HEADER + row(" ", "R2245", "x", "first=yes"))
    try:
        before = digest_tree(world)
        DR.register(world, "R2248")
        DR.one_line(DR.register(world, "R2248"))
        DR.to_json(DR.register(world, "R2248"))
        after = digest_tree(world)
    finally:
        drop_world(world)
    with io.open(MODULE, "r", encoding="ascii") as handle:
        source = handle.read()
    net = re.findall(r"^\s*(?:import|from)\s+"
                     r"(socket|ssl|urllib|http|requests|ftplib|time|"
                     r"datetime)\b", source, re.M)
    check(before == after and not net,
          "AC-DEBT6 the register is a pure read, source ASCII with zero "
          "network and zero clock imports")

    # AC-DEBT7: the live register parses and an independent recount agrees.
    live = DR.register(REPO, "R2248")
    independent = independent_counts(REPO)
    live_ok = ((live["open_count"], live["done_count"])
               == independent["counts"])
    if live["present"] and not live_ok:
        live_ok = False
    check(live_ok and (not live["present"]
                       or live["verdict"] in DR.VERDICTS),
          "AC-DEBT7 the live register parses and matches an independent "
          "recount of open and done rows")

    # AC-DEBT8: wired into the battery with the pinned criteria count.
    check(wiring_ok(),
          "AC-DEBT8 wired as os-debt-register(8) in the battery runner")


def independent_counts(root):
    """Recount the live register with different code than the module."""
    path = os.path.join(root, "state", "debt.md")
    counts = [0, 0]
    if not os.path.isfile(path):
        return {"counts": tuple(counts), "present": False}
    with io.open(path, "r", encoding="utf-8") as handle:
        for line in handle.read().splitlines():
            if line.startswith("- [ ]"):
                counts[0] += 1
            elif line.startswith("- [x]") or line.startswith("- [X]"):
                counts[1] += 1
    return {"counts": tuple(counts), "present": True}


def wiring_ok():
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        text = handle.read()
    needle = '"%s"' % LABEL
    if needle not in text:
        return False
    tail = text[text.find(needle):]
    window = tail[:400]
    return ("test_debt_register.py" in window) and (", 8)" in window)


if __name__ == "__main__":
    run()
    print("SUITE %s %d/%d" % (
        "PASS" if FAILS == 0 else "FAIL", PASSES + FAILS, EXPECTED_CRITERIA),
        flush=True)
    sys.exit(0 if FAILS == 0 else 2)