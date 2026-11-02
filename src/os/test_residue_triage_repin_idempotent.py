"""residue_triage_repin_idempotent suite (R2372).

Criteria AC-RTRI1..AC-RTRI6 were pinned inside the R2363 seed row of
state/queue/tech.md BEFORE this code existed.

What this proves: the re-pin could not tell "nothing to do" from "I wrote the
declaration". R2363 measured it at its own live write - a second plan composed
bytes identical to the file on disk and still read PLANNED, so --execute would
rewrite the same bytes and report PINNED. This suite pins the reading added:
NOOP when the composed document equals the file, decided by BYTES and never by
the declaration's head round, returning before the writer is entered, with
every non-NOOP path still the shipped writer's own report and codes.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
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

import residue_triage as RT  # noqa: E402
import residue_triage_repin as RTR  # noqa: E402
import residue_triage_repin_idempotent as RI  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "residue_triage_repin_idempotent.py")
SHIPPED = os.path.join(BASE, "residue_triage_repin.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-residue-triage-repin-idempotent"
WIRED_EXPECT = '"test_residue_triage_repin_idempotent.py"), 6),'

PIN_ROUND = "R2360"
PIN_UNTIL = "R2380"
PIN_REASON = "re-pinned at R2360 from one live reading"
HEADER = "# queue test world\n\nprose that never becomes a row\n\n"

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


def tech_rows(rounds=("R2300", "R2305", "R2348")):
    out = []
    for number in rounds:
        out.append("- [x] [done 2026-11-01 %s] a closed residue row\n"
                   % number)
    return "".join(out)


def seeded_declaration():
    """The declaration as it stands before this window re-pins it.

    Written as data because `residue_triage_repin` refuses to invent one (the
    append channel seeds), exactly the fixture the shipped re-pin suite uses;
    every byte this window measures after the pin is the writer's own.
    """
    rows = []
    for number, until in ((2300, 2350), (2305, 2350), (2348, 2360)):
        rows.append({
            "round": number,
            "status": "DELIVERED",
            "declared_by": 2331,
            "reason": "reviewed at R2331 at its live status",
            "until": until,
        })
    return {"declared_by": 2331, "reason": "reviewed at R2331",
            "entries": rows}


def make_world(rounds=("R2300", "R2305", "R2348")):
    """A throwaway root: state.json, the three queues, one declaration."""
    world = tempfile.mkdtemp(prefix="rtri-world-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    payload = {"tick": 2300, "log": ["R2200 a logged item"]}
    path = os.path.join(world, "src", "os", "state.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload))
    for name, body in (("tech", tech_rows(rounds)), ("main", HEADER),
                       ("explore", HEADER)):
        path = os.path.join(world, "state", "queue", name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    body = json.dumps(seeded_declaration(), ensure_ascii=True, indent=2)
    with io.open(os.path.join(world, RT.DECLARATION_PATH), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(body + "\n")
    return world


def pin(world):
    """Fill the declaration through the SHIPPED writer, never by hand."""
    return RTR.plan(world, PIN_ROUND, PIN_UNTIL, PIN_REASON, False, True)


def declaration_path(world):
    return os.path.join(world, RT.DECLARATION_PATH)


def digest_file(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def file_map(root):
    out = {}
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(dirs)
        for name in sorted(names):
            path = os.path.join(folder, name)
            out[os.path.relpath(path, root).replace(os.sep, "/")] = \
                open(path, "rb").read()
    return out


def run_cli(module, world, args):
    argv = [sys.executable, module, "--root", world] + list(args)
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace")


def code_only(text):
    """The source with comments and docstrings removed (executable text)."""
    body = re.sub(r'"""(?:.|\n)*?"""', '', text)
    body = re.sub(r"'''(?:.|\n)*?'''", '', body)
    return re.sub(r"#[^\n]*", "", body)


def ac_rtri1():
    """An already-pinned declaration reads NOOP and writes no byte."""
    world = make_world()
    try:
        pin(world)
        path = declaration_path(world)
        before_digest = digest_file(path)
        before_map = file_map(world)

        bomb_called = []

        def bomb(*args, **kwargs):
            bomb_called.append(True)
            raise AssertionError("the writer was entered on a NOOP reading")

        saved = RTR.plan
        RTR.plan = bomb
        try:
            report = RI.decide(world, PIN_ROUND, PIN_UNTIL, PIN_REASON)
        finally:
            RTR.plan = saved
        after_map = file_map(world)
        temps = [name for name in after_map if ".tmp-" in name]
        ok = (report["verdict"] == RI.NOOP
              and report["executed"] is False
              and report["round"] == PIN_ROUND
              and report["predicted_bytes"] == report["declaration_bytes"]
              and digest_file(path) == before_digest
              and before_map == after_map
              and temps == []
              and bomb_called == [])
        if not ok:
            print("  measured: verdict=%r executed=%r bytes=%r/%r "
                  "digest_same=%r temps=%r writer_calls=%d"
                  % (report.get("verdict"), report.get("executed"),
                     report.get("predicted_bytes"),
                     report.get("declaration_bytes"),
                     digest_file(path) == before_digest, temps,
                     len(bomb_called)), flush=True)
        check(ok, "AC-RTRI1 an already-pinned declaration reads NOOP with "
                  "executed=False, the file digest unchanged, no temp file "
                  "and the writer never entered")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtri2():
    """NOOP is decided by BYTES, not by the declaration's head round."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    code = code_only(source)
    # the module never reads the head round at all, so it cannot be deciding
    # on it - and the comparison it does make is bytes against bytes
    no_head_round = ("declared_by" not in code
                     and "entries_before" not in code)
    byte_law = ("on_disk_bytes(" in code
                and "current == composed" in code)

    world = make_world()
    try:
        pin(world)
        # the declaration was pinned at R2360, which is OLDER than the round
        # this window is checking at - identical content must still read NOOP
        older = RI.decide(world, PIN_ROUND, PIN_UNTIL, PIN_REASON)
        # the same file at the CURRENT round composes different bytes (every
        # entry's declared_by moves), so the reading is PLANNED - proving the
        # answer follows the bytes and not "is this the current round"
        newer = RI.decide(world, "R2372", PIN_UNTIL, "re-pinned at R2372")
        ok = (no_head_round and byte_law
              and older["verdict"] == RI.NOOP
              and older["round"] == PIN_ROUND
              and newer["verdict"] == "PLANNED"
              and newer["round"] == "R2372")
        if not ok:
            print("  measured: no_head_round=%r byte_law=%r older=%r newer=%r"
                  % (no_head_round, byte_law, older.get("verdict"),
                     newer.get("verdict")), flush=True)
        check(ok, "AC-RTRI2 the NOOP reading is decided by BYTES and not by "
                  "the head round: a declaration pinned at the older R2360 "
                  "still reads NOOP for R2360 while the same file at R2372 "
                  "reads PLANNED, and the module never mentions declared_by")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtri3():
    """A one-byte drift in the composition reads PLANNED again."""
    world = make_world()
    try:
        pin(world)
        path = declaration_path(world)
        before = digest_file(path)
        noop = RI.decide(world, PIN_ROUND, PIN_UNTIL, PIN_REASON)
        drifted_reason = PIN_REASON[:-1] + ("X" if PIN_REASON[-1] != "X"
                                            else "Y")
        drift = RI.decide(world, PIN_ROUND, PIN_UNTIL, drifted_reason)
        # "one byte" is measured as CONTENT, not as size: a same-length
        # substitution keeps the byte count and still drifts the composition
        with io.open(path, "rb") as handle:
            on_disk = handle.read()
        composed = RTR.build(world, PIN_ROUND, PIN_UNTIL,
                             drifted_reason)["_text"].encode("utf-8")
        drifted = sum(1 for left, right in zip(on_disk, composed)
                      if left != right)
        ok = (noop["verdict"] == RI.NOOP
              and drift["verdict"] == "PLANNED"
              and drift["executed"] is False
              and len(on_disk) == len(composed)
              and drifted == 1
              and digest_file(path) == before)
        if not ok:
            print("  measured: noop=%r drift=%r drifted_bytes=%r "
                  "sizes=%r/%r digest_same=%r"
                  % (noop.get("verdict"), drift.get("verdict"), drifted,
                     len(on_disk), len(composed),
                     digest_file(path) == before), flush=True)
        check(ok, "AC-RTRI3 a composition that drifts by exactly ONE byte "
                  "reads PLANNED again rather than NOOP, and the dry run "
                  "still writes nothing")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtri4():
    """Non-NOOP paths are the shipped CLI's own; NOOP is exit 0 with NOOP."""
    world = make_world()
    refused = make_world()
    try:
        pin(world)
        pin(refused)
        # grow the live residue under the pinned declaration: both CLIs must
        # refuse with the shipped writer's own UNMATCHED refusal
        path = os.path.join(refused, "state", "queue", "tech.md")
        with io.open(path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write("- [x] [done 2026-11-01 R2372] a newer residue row\n")

        planned_args = ["--round", "R2372", "--until", "R2390",
                        "--reason", "re-pinned at R2372"]
        bad_until = ["--round", PIN_ROUND, "--until", "R2350",
                     "--reason", "until before the round"]

        p_shipped = run_cli(SHIPPED, world, planned_args)
        p_wire = run_cli(MODULE, world, planned_args)
        r_shipped = run_cli(SHIPPED, refused, planned_args)
        r_wire = run_cli(MODULE, refused, planned_args)
        b_shipped = run_cli(SHIPPED, world, bad_until)
        b_wire = run_cli(MODULE, world, bad_until)

        json_shipped = run_cli(SHIPPED, world, planned_args + ["--json"])
        json_wire = run_cli(MODULE, world, planned_args + ["--json"])
        noop_json = run_cli(MODULE, world, ["--round", PIN_ROUND, "--until",
                                            PIN_UNTIL, "--reason",
                                            PIN_REASON, "--json"])
        keys_shipped = tuple(json.loads(json_shipped[1]).keys())
        keys_wire = tuple(json.loads(json_wire[1]).keys())
        noop_payload = json.loads(noop_json[1])
        noop_keys = tuple(noop_payload.keys())

        ok = (p_shipped == p_wire
              and r_shipped == r_wire
              and b_shipped[0] == b_wire[0] == 5
              and keys_shipped == keys_wire == RTR.PLAN_KEYS
              and keys_shipped == RI.REPORT_KEYS
              and noop_keys == RTR.PLAN_KEYS
              and noop_json[0] == 0
              and noop_payload["verdict"] == RI.NOOP
              and noop_payload["executed"] is False)
        if not ok:
            print("  measured: planned=%r/%r refused=%r/%r bad=%r/%r "
                  "keys=%r noop_rc=%r noop_verdict=%r"
                  % (p_shipped, p_wire, r_shipped, r_wire, b_shipped[0],
                     b_wire[0], keys_wire, noop_json[0],
                     noop_payload.get("verdict")), flush=True)
        check(ok, "AC-RTRI4 the PLANNED and refused paths are BYTE-IDENTICAL "
                  "to the shipped CLI (same rc and same stdout), every code "
                  "is unchanged (0/2/5), the --json key order is the shipped "
                  "PLAN_KEYS, and NOOP is exit 0 carrying its own verdict")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(refused, ignore_errors=True)


def ac_rtri5():
    """The NOOP branch returns before any temp file; the write is singular."""
    world = make_world()
    try:
        pin(world)
        path = declaration_path(world)
        noop = RI.decide(world, PIN_ROUND, PIN_UNTIL, PIN_REASON)
        temps_after_noop = [name for name in file_map(world)
                            if ".tmp-" in name]

        calls = []
        saved = RTR.plan

        def counting(*args, **kwargs):
            calls.append(args[1])
            return saved(*args, **kwargs)

        RTR.plan = counting
        try:
            executed = RI.decide(world, "R2372", "R2390",
                                 "re-pinned at R2372", False, True)
        finally:
            RTR.plan = saved
        temps_after_write = [name for name in file_map(world)
                             if ".tmp-" in name]
        reread = RT.read(world, "R2372")
        ok = (noop["verdict"] == RI.NOOP
              and temps_after_noop == []
              and calls == ["R2372"]
              and executed["verdict"] == "PINNED"
              and executed["executed"] is True
              and temps_after_write == []
              and reread["verdict"] == "TRIAGED"
              and os.path.getsize(path) == executed["predicted_bytes"])
        if not ok:
            print("  measured: temps_noop=%r writer_calls=%r executed=%r "
                  "temps_write=%r reread=%r size=%r/%r"
                  % (temps_after_noop, calls, executed.get("verdict"),
                     temps_after_write, reread.get("verdict"),
                     os.path.getsize(path),
                     executed.get("predicted_bytes")), flush=True)
        check(ok, "AC-RTRI5 the NOOP branch creates no temp file and never "
                  "enters the writer, while an executed re-pin goes through "
                  "the shipped atomic path exactly ONCE and leaves no temp "
                  "residue")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtri6():
    """Purity, both imports, the runner wiring, and a live reading."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    code = code_only(source)
    try:
        io.open(MODULE, "rb").read().decode("ascii")
        ascii_ok = True
    except (UnicodeDecodeError, IOError):
        ascii_ok = False
    forbidden = ("import socket", "import urllib", "import http",
                 "import time", "import datetime", "requests", "urlopen")
    no_network = not any(token in code for token in forbidden)
    imports_shipped = ("import residue_triage_repin as RTR" in code
                       and "RTR.build(" in code
                       and "RTR.plan(" in code
                       and "os.replace(" not in code
                       and "json.dumps" not in code)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = WIRED_EXPECT in runner and LABEL in runner

    # a patched composition moves this reading: the NOOP is decided on the
    # text `build` hands back, so a build that returns the file's own bytes
    # must read NOOP over a world whose real composition differs
    world = make_world()
    try:
        pin(world)
        path = declaration_path(world)
        with io.open(path, "rb") as handle:
            current = handle.read()
        saved_build = RTR.build

        def lying_build(root, round_text, until_text, reason,
                        allow_drop=False):
            return {"verdict": "PLANNED", "executed": False,
                    "round": "R2399", "until": "R2399",
                    "_path": path,
                    "_text": current.decode("utf-8"),
                    "_round": 2399}

        RTR.build = lying_build
        try:
            patched = RI.decide(world, "R2399", "R2399", "synthetic")
        finally:
            RTR.build = saved_build

        live = None
        live_refusal = None
        try:
            live = RI.decide(REPO, "R2372", "R2390",
                             "would re-pin at R2372", True)
        except (RTR.RepinError, RT.ResidueTriageError) as exc:
            live_refusal = exc.code
        if live is not None:
            print("LIVE %s" % RI.one_line(live), flush=True)
        else:
            print("LIVE refused %s" % live_refusal, flush=True)

        ok = (ascii_ok and no_network and imports_shipped and wired
              and patched["verdict"] == RI.NOOP
              and patched["round"] == "R2399"
              and (live is not None or live_refusal is not None))
        if not ok:
            print("  measured: ascii=%r net=%r imports=%r wired=%r "
                  "patched=%r" % (ascii_ok, no_network, imports_shipped,
                                  wired, patched.get("verdict")), flush=True)
        check(ok, "AC-RTRI6 pure ASCII, stdlib only, zero network, no clock, "
                  "the composition and the writer are the shipped ones (a "
                  "patched build moves the NOOP reading and nothing here "
                  "calls os.replace or json.dumps), wired as %s(%d), live "
                  "reading taken" % (LABEL, EXPECTED_CRITERIA))
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    ac_rtri1()
    ac_rtri2()
    ac_rtri3()
    ac_rtri4()
    ac_rtri5()
    ac_rtri6()
    total = PASSES + FAILS
    print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL",
                              PASSES, total), flush=True)
    if total != EXPECTED_CRITERIA:
        print("FAIL criteria count %d != %d" % (total, EXPECTED_CRITERIA),
              flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())