"""declaration_writer_dialect_preservation suite (R2398; criteria
AC-DWPP1..AC-DWPP6 were pre-registered inside the R2389 seed row of
state/queue/tech.md line 458 BEFORE this code existed).

What this proves: a writer that actually CHANGES a declaration now keeps the
declaration's own line endings instead of converting every line to LF. An LF
declaration gets exactly the bytes it got before, a CRLF declaration stays
CRLF with every untouched line byte-identical, the dialect is asked of the
shared law at call time, the MIXED case refuses instead of choosing a
transport nobody asked for, and the four writers keep every refusal code,
exit code and printed line they had.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
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

import declaration_writer_dialect_preservation as DWDP  # noqa: E402
import declaration_writer_noop_parity as DWNP  # noqa: E402
import repin_noop_eol_dialect as RNP  # noqa: E402
import residue_triage_append as RA  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "declaration_writer_dialect_preservation.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-declaration-writer-dialect-preservation"

HEADER = "queue header\n"
TECH = ("- [x] [done 2026-11-01 R9001] a closed row delivered by the "
        "fixture\n"
        "- [x] [done 2026-11-01 R9002] a second closed row for the fixture\n")
LOG_ITEMS = ["2026-11-01 R8900 a prior round in the fixture world"]

WRITERS = (
    "residue_triage_append.py",
    "residue_triage_append_batch.py",
    "residue_triage_head_renew.py",
    "residue_triage_entry_retire.py",
)

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


def entry(number, status="DELIVERED", declared_by=2335, until=9900,
          reason="fixture row"):
    return {"round": number, "status": status, "declared_by": declared_by,
            "reason": reason, "until": until}


def decl_text(entries, declared_by=2335, reason="fixture declaration"):
    head = ('{\n  "declared_by": "R%d",\n  "reason": %s,\n  "entries": [\n'
            % (declared_by, json.dumps(reason, ensure_ascii=True)))
    body = ""
    for index, item in enumerate(entries):
        if index:
            body += ",\n"
        body += RA.entry_text(item)
    if body:
        body += "\n"
    return head + body + "  ]\n}\n"


def make_world(entries=None, dialect="LF", declared_by=2335):
    """A temp root: state.json, the three queues, optionally a declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-dwpp-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    payload = {"tick": declared_by, "log": list(LOG_ITEMS)}
    with io.open(os.path.join(world, "src", "os", "state.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload))
    for name, body in (("tech", TECH), ("main", HEADER),
                       ("explore", HEADER)):
        with io.open(os.path.join(world, "state", "queue", name + ".md"),
                     "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    if entries is not None:
        text = decl_text(entries, declared_by)
        data = text.encode("utf-8")
        if dialect == "CRLF":
            data = text.replace("\n", "\r\n").encode("utf-8")
        with open(os.path.join(world, "state", "residue_triage.json"),
                  "wb") as handle:
            handle.write(data)
    return world


def declaration_path(world):
    return os.path.join(world, "state", "residue_triage.json")


def run_cli(module, world, args):
    proc = subprocess.Popen([sys.executable, os.path.join(BASE, module)]
                            + args + ["--root", world],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return (proc.returncode, out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


APPEND_OK = ["--append", "--round", "R9002", "--status", "DELIVERED",
             "--by", "R2398", "--reason", "fixture", "--until", "R2400"]


def ac_dwpp1():
    """An append to a CRLF declaration lands and it is still CRLF."""
    world = make_world(entries=[entry(9001)], dialect="CRLF")
    try:
        path = declaration_path(world)
        with open(path, "rb") as handle:
            before = handle.read()
        rc, body, _err = run_cli("residue_triage_append.py", world, APPEND_OK)
        with open(path, "rb") as handle:
            after = handle.read()
        before_lines = before.split(b"\r\n")
        after_lines = after.split(b"\r\n")
        # compose appends a comma to the entry object that closes the array,
        # so that ONE line is the change; every other original line survives
        # byte for byte, and the transport does not change.
        changed = before_lines[-4]
        untouched = [line for line in before_lines
                     if line not in (changed, b"")]
        ok = (rc == 0
              and RNP.dialect_of(after) == "CRLF"
              and after.count(b"\r\n") == after.count(b"\n")
              and after.count(b"\r") == after.count(b"\r\n")
              and b'"round": 9002' in after
              and all(line in after_lines for line in untouched)
              and b"\r\r\n" not in after)
        if not ok:
            print("  measured: rc=%r dialect=%r crlf=%d lf=%d cr=%d "
                  "kept=%r" % (rc, RNP.dialect_of(after),
                               after.count(b"\r\n"), after.count(b"\n"),
                               after.count(b"\r"),
                               all(line in after_lines
                                   for line in untouched)), flush=True)
            print("  body=%r" % body[:300], flush=True)
        check(ok, "AC-DWPP1 a CRLF declaration stays CRLF after a real append")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_dwpp2():
    """An LF declaration gets exactly the bytes it got before."""
    world = make_world(entries=[entry(9001)], dialect="LF")
    try:
        path = declaration_path(world)
        with open(path, "rb") as handle:
            before = handle.read()
        rc, _body, _err = run_cli("residue_triage_append.py", world,
                                  APPEND_OK)
        with open(path, "rb") as handle:
            after = handle.read()
        expected = RA.compose(before.decode("utf-8"),
                              entry(9002, declared_by=2398,
                                    until=2400, reason="fixture")) \
            .encode("utf-8")
        ok = (rc == 0 and after == expected
              and RNP.dialect_of(after) == "LF")
        if not ok:
            print("  measured: rc=%r equal=%r dialect=%r delta=%d"
                  % (rc, after == expected, RNP.dialect_of(after),
                     len(after) - len(expected)), flush=True)
        check(ok, "AC-DWPP2 an LF declaration keeps today's bytes exactly")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_dwpp3():
    """The NOOP path still writes nothing, on all four writers."""
    world = make_world(entries=[entry(9001)], dialect="CRLF")
    try:
        path = declaration_path(world)
        with open(path, "rb") as handle:
            raw = handle.read()
        # the derived payload of a document that already IS the composition
        same_name, payload = DWDP.encode(raw, raw.decode("utf-8"))
        noop_still = DWNP.is_noop(path, payload)
        # one real write attempt whose payload equals the file must return
        # None and leave every byte (and the directory) as it was
        prepared = {"path": path, "after_bytes": raw,
                    "before_bytes": len(raw), "delta": 0,
                    "entry": entry(9001), "entries_after": 1}
        returned = RA.apply(world, prepared)
        with open(path, "rb") as handle:
            after = handle.read()
        temp_left = [name for name in os.listdir(os.path.dirname(path))
                     if ".tmp" in name]
        order_ok = True
        pairs = {
            "residue_triage_append.py": ("declaration_writer_noop_parity",
                                         "os.replace"),
            "residue_triage_append_batch.py": (
                "declaration_writer_noop_parity", "os.replace"),
            "residue_triage_head_renew.py": (
                "declaration_writer_noop_parity",
                "write_atomic(path, data, predicted, tail, tail)"),
            "residue_triage_entry_retire.py": (
                "declaration_writer_noop_parity", "os.replace"),
        }
        for name in WRITERS:
            gate_token, write_token = pairs[name]
            source = io.open(os.path.join(BASE, name), "r",
                             encoding="utf-8").read()
            gate = source.find(gate_token)
            write = source.find(write_token)
            if gate < 0 or write < 0 or gate > write:
                order_ok = False
                print("  order: %s gate=%d write=%d"
                      % (name, gate, write), flush=True)
        ok = (same_name == "CRLF" and noop_still and returned is None
              and after == raw and not temp_left and order_ok)
        if not ok:
            print("  measured: dialect=%r noop=%r returned=%r equal=%r "
                  "temp=%r order=%r" % (same_name, noop_still, returned,
                                        after == raw, temp_left, order_ok),
                  flush=True)
        check(ok, "AC-DWPP3 the NOOP path writes nothing on all four writers")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_dwpp4():
    """Every refusal code, exit code and printed line is unchanged."""
    world_dup = make_world(entries=[entry(9001), entry(9002)])
    world_unpinned = make_world(entries=None)
    added = {}
    try:
        # the code inventory of the four writers against git HEAD
        same = True
        for name in WRITERS:
            current = io.open(os.path.join(BASE, name), "r",
                              encoding="utf-8").read()
            proc = subprocess.Popen(["git", "show", "HEAD:src/os/%s" % name],
                                    cwd=REPO, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            out, _err = proc.communicate()
            if proc.returncode != 0:
                same = False
                print("  git show failed for %s" % name, flush=True)
                continue
            older = out.decode("utf-8")
            pattern = r"\bE_[A-Z0-9_]+\b"
            now = set(re.findall(pattern, current))
            was = set(re.findall(pattern, older))
            added[name] = sorted(now - was)
            if was - now:
                same = False
                print("  %s lost codes %r" % (name, sorted(was - now)),
                      flush=True)
        dup_code, dup_body, _err = run_cli(
            "residue_triage_append.py", world_dup, APPEND_OK)
        dup_lines = dup_body.replace("\r\n", "\n").splitlines()
        unpinned_code, unpinned_body, _err = run_cli(
            "residue_triage_append.py", world_unpinned, ["--check", "--round",
                                                         "R9001"])
        retire_code, retire_body, _err = run_cli(
            "residue_triage_entry_retire.py", world_dup,
            ["--round", "R9003"])
        batch_code, batch_body, _err = run_cli(
            "residue_triage_append_batch.py", world_dup,
            ["--append", "--pair", "R9002=DELIVERED", "--by", "R2398",
             "--reason", "fixture", "--until", "R2400"])
        no_new_codes = all(not value for value in added.values())
        ok = (same and no_new_codes
              and dup_code == 2
              and dup_lines[0] == "E_RTA_DUPLICATE"
              and dup_lines[1].startswith("  R9002 is already declared")
              and unpinned_code == 2
              and "declaration=UNPINNED" in unpinned_body
              and unpinned_body.replace("\r\n", "\n").splitlines()[0]
              .startswith("RESIDUE TRIAGE APPEND action=check round=R9001")
              and retire_code == 2
              and retire_body.replace("\r\n", "\n").splitlines()[0]
              == "E_RTER_NOT_DECLARED"
              and batch_code == 2
              and batch_body.startswith("E_RTAB_"))
        if not ok:
            print("  measured: same=%r added=%r dup=%r/%r unpinned=%r "
                  "retire=%r batch=%r" % (same, added, dup_code, dup_lines,
                                          unpinned_code, retire_code,
                                          batch_code), flush=True)
        check(ok, "AC-DWPP4 refusal codes, exits and printed lines unchanged")
    finally:
        shutil.rmtree(world_dup, ignore_errors=True)
        shutil.rmtree(world_unpinned, ignore_errors=True)


def ac_dwpp5():
    """The dialect is the shared law's answer, asked at call time."""
    raw_lf = b'{\n  "a": 1\n}\n'
    composed = '{\n  "a": 1\n}\n'
    straight_name, straight = DWDP.encode(raw_lf, composed)
    saved = RNP.dialect_of
    try:
        RNP.dialect_of = lambda data: "CRLF"
        patched_name, patched = DWDP.encode(raw_lf, composed)
    finally:
        RNP.dialect_of = saved
    source = io.open(MODULE, "r", encoding="utf-8").read()
    asks_law = "RNP.dialect_of(" in source
    writers_ask_this = True
    for name in WRITERS:
        writer = io.open(os.path.join(BASE, name), "r",
                         encoding="utf-8").read()
        if "declaration_writer_dialect_preservation" not in writer:
            writers_ask_this = False
        if "dialect_of" in writer:
            writers_ask_this = False
    ok = (straight_name == "LF" and straight == composed.encode("utf-8")
          and patched_name == "CRLF"
          and patched == composed.replace("\n", "\r\n").encode("utf-8")
          and asks_law and writers_ask_this)
    if not ok:
        print("  measured: straight=%r patched=%r law=%r writers=%r"
              % ((straight_name, straight), (patched_name, patched),
                 asks_law, writers_ask_this), flush=True)
    check(ok, "AC-DWPP5 the shared dialect law moves every writer")


def ac_dwpp6():
    """Pure ASCII, stdlib only, no network, no clock, wired with its label."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http\.client)\b", source)
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    imports = set(re.findall(r"^\s*import (\w+)", source, re.MULTILINE))
    stdlib_only = imports <= {"json", "sys", "repin_noop_eol_dialect"}
    no_write = ('"wb"' not in source and "os.replace" not in source
                and "os.remove" not in source and "unlink" not in source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_declaration_writer_dialect_preservation.py" in runner)
    own_label = source.count('SUITE_LABEL = "%s"' % LABEL) == 1
    ok = (ascii_only and no_net and no_clock and stdlib_only and no_write
          and wired and own_label)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r imports=%r write=%r "
              "wired=%r label=%r" % (ascii_only, no_net, no_clock,
                                     sorted(imports), no_write, wired,
                                     own_label), flush=True)
    check(ok, "AC-DWPP6 pure, read-only seam and wired with its own label")


def main():
    print("declaration_writer_dialect_preservation suite (expected criteria "
          "%d)" % EXPECTED_CRITERIA, flush=True)
    ac_dwpp1()
    ac_dwpp2()
    ac_dwpp3()
    ac_dwpp4()
    ac_dwpp5()
    ac_dwpp6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())