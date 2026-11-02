"""repin_noop_parity suite (R2382).

Criteria AC-RNP1..AC-RNP6 were pinned inside the R2372 seed row of
state/queue/tech.md BEFORE this code existed.

What this proves: the re-pin had a NOOP in ONE module and not in the tool
operators actually run. `residue_triage_repin.py --execute` rewrote bytes that
already equalled the file and reported PINNED, while
`residue_triage_repin_idempotent.decide` read NOOP over the same composition -
two answers to one question, and no measurement that they agreed. This suite
pins the collapse: one comparison law (`is_noop`) imported by both, one CLI
reading NOOP, byte-identical non-NOOP output (including refusals and their
exit codes), and a parity that names the first differing field the moment
either face moves.

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

import repin_noop_parity as RNP  # noqa: E402
import residue_triage as RT  # noqa: E402
import residue_triage_repin as RTR  # noqa: E402
import residue_triage_repin_idempotent as RI  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "repin_noop_parity.py")
SHIPPED = os.path.join(BASE, "residue_triage_repin.py")
WIRE = os.path.join(BASE, "residue_triage_repin_idempotent.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-repin-noop-parity"
WIRED_EXPECT = '"test_repin_noop_parity.py"), 6),'

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


def make_world(no_decl=False, raw=None, rounds=("R2300", "R2305", "R2348")):
    """A throwaway root: state.json, the three queues, one declaration.

    `rounds` narrows the LIVE residue, so a declared round that is no longer
    live is a real UNMATCHED refusal rather than a fixture guess.
    """
    world = tempfile.mkdtemp(prefix="rnp-world-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    payload = {"tick": 2300, "log": ["R2200 a logged item"]}
    path = os.path.join(world, "src", "os", "state.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload))
    tech = tech_rows(rounds)
    for name, body in (("tech", tech), ("main", HEADER), ("explore", HEADER)):
        path = os.path.join(world, "state", "queue", name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    if no_decl:
        return world
    path = os.path.join(world, RT.DECLARATION_PATH)
    if raw is not None:
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(raw)
        return world
    body = json.dumps(seeded_declaration(), ensure_ascii=True, indent=2)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body + "\n")
    return world


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
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def pin(world):
    """Fill the declaration through the SHIPPED writer, never by hand."""
    return RTR.plan(world, PIN_ROUND, PIN_UNTIL, PIN_REASON, False, True)


def code_only(text):
    """The source with comments and docstrings removed (executable text)."""
    body = re.sub(r'"""(?:.|\n)*?"""', '', text)
    body = re.sub(r"'''(?:.|\n)*?'''", '', body)
    return re.sub(r"#[^\n]*", "", body)


def ac_rnp1():
    """The shipped CLI reads NOOP over an already-pinned declaration."""
    world = make_world()
    try:
        pinned = pin(world)
        path = declaration_path(world)
        before_digest = digest_file(path)
        before_map = file_map(world)

        report = RTR.plan(world, PIN_ROUND, PIN_UNTIL, PIN_REASON,
                          False, True)
        after_map = file_map(world)
        temps = [name for name in after_map
                 if RTR.TEMP_SUFFIX in name or name.endswith(".tmp")]
        code, out, _ = run_cli(SHIPPED, world, [
            "--round", PIN_ROUND, "--until", PIN_UNTIL,
            "--reason", PIN_REASON, "--execute"])
        code_j, out_j, _ = run_cli(SHIPPED, world, [
            "--round", PIN_ROUND, "--until", PIN_UNTIL,
            "--reason", PIN_REASON, "--execute", "--json"])
        payload = json.loads(out_j) if out_j.strip() else {}
        ok = (pinned["verdict"] == "PINNED"
              and report["verdict"] == "NOOP"
              and report["executed"] is False
              and report["predicted_bytes"] == report["declaration_bytes"]
              and digest_file(path) == before_digest
              and before_map == after_map
              and temps == []
              and code == 0 and "NOOP" in out
              and code_j == 0 and payload.get("verdict") == "NOOP"
              and payload.get("executed") is False)
        if not ok:
            print("  measured: verdict=%r executed=%r digest_same=%r "
                  "temps=%r rc=%r out=%r"
                  % (report.get("verdict"), report.get("executed"),
                     digest_file(path) == before_digest, temps, code,
                     out.strip()), flush=True)
        check(ok, "AC-RNP1 the shipped CLI reads NOOP over an already-pinned "
                  "declaration, the file digest and the whole world map are "
                  "unchanged, no temp file is created, and the NOOP verdict "
                  "travels in --json with executed=False")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rnp2():
    """Non-NOOP output and refusals are byte-identical between the CLIs."""
    shipped_world = make_world()
    wire_world = make_world()
    ref_shipped = make_world(rounds=("R2300", "R2305"))
    ref_wire = make_world(rounds=("R2300", "R2305"))
    missing = make_world(no_decl=True)
    unreadable = make_world(raw="{not json")
    plan_args = ["--round", "R2351", "--until", "R2370",
                 "--reason", "re-pinned at R2351"]
    bad_until = ["--round", "R2351", "--until", "R2300",
                 "--reason", "until before the round"]
    try:
        dry_s = run_cli(SHIPPED, shipped_world, plan_args)
        dry_w = run_cli(WIRE, wire_world, plan_args)
        exec_s = run_cli(SHIPPED, shipped_world, plan_args + ["--execute"])
        exec_w = run_cli(WIRE, wire_world, plan_args + ["--execute"])
        same_decl = (io.open(declaration_path(shipped_world), "rb").read()
                     == io.open(declaration_path(wire_world), "rb").read())
        ref_s = run_cli(SHIPPED, ref_shipped, plan_args)
        ref_w = run_cli(WIRE, ref_wire, plan_args)
        bad_s = run_cli(SHIPPED, shipped_world, bad_until)
        bad_w = run_cli(WIRE, shipped_world, bad_until)
        miss_s = run_cli(SHIPPED, missing, plan_args)
        miss_w = run_cli(WIRE, missing, plan_args)
        unr_s = run_cli(SHIPPED, unreadable, plan_args)
        unr_w = run_cli(WIRE, unreadable, plan_args)
        ok = (dry_s[:2] == dry_w[:2]
              and exec_s[:2] == exec_w[:2]
              and same_decl
              and "PINNED" in exec_s[1] and "PINNED" in exec_w[1]
              and ref_s[:2] == ref_w[:2]
              and ref_s[0] == 2 and "E_RTRP_UNMATCHED" in ref_s[1]
              and bad_s[:2] == bad_w[:2]
              and bad_s[0] == 5 and "E_RTRP_UNTIL_PREDATES" in bad_s[1]
              and miss_s[:2] == miss_w[:2]
              and miss_s[0] == 3 and "E_RTRP_UNPINNED" in miss_s[1]
              and unr_s[:2] == unr_w[:2]
              and unr_s[0] == 3 and "E_RTR_UNREADABLE" in unr_s[1])
        if not ok:
            print("  measured: dry=%r/%r exec=%r/%r ref=%r/%r bad=%r/%r "
                  "miss=%r/%r unr=%r/%r"
                  % (dry_s[:2], dry_w[:2], exec_s[:2], exec_w[:2],
                     ref_s[:2], ref_w[:2], bad_s[:2], bad_w[:2],
                     miss_s[:2], miss_w[:2], unr_s[:2], unr_w[:2]),
                  flush=True)
        check(ok, "AC-RNP2 the shipped CLI and the wire print byte-identical "
                  "output and exit codes on the dry, executed and every "
                  "refusing path (2 UNMATCHED, 5 bad until, 3 UNPINNED, "
                  "3 unreadable), and both executed worlds end on the same "
                  "declaration bytes")
    finally:
        for world in (shipped_world, wire_world, ref_shipped, ref_wire,
                      missing, unreadable):
            shutil.rmtree(world, ignore_errors=True)


def ac_rnp3():
    """The parity reads AGREES over one declaration or names the first diff."""
    fresh = make_world()
    pinned = make_world()
    unmatched = make_world(rounds=("R2300", "R2305"))
    saved_plan = RTR.plan
    saved_decide = RI.decide
    try:
        pin(pinned)
        agree_fresh = RNP.check(fresh, "R2351", "R2370",
                                "re-pinned at R2351")
        agree_pinned = RNP.check(pinned, PIN_ROUND, PIN_UNTIL, PIN_REASON)
        agree_refused = RNP.check(unmatched, "R2351", "R2370",
                                  "re-pinned at R2351")

        # The wire answers an already-pinned declaration from its OWN NOOP
        # branch without entering the shipped writer, so patching RTR.plan
        # moves the shipped side alone on that world - which is exactly the
        # split a future edit could introduce.
        RTR.plan = lambda *a, **k: {
            "verdict": "PLANNED", "executed": False}
        try:
            split_shipped = RNP.check(pinned, PIN_ROUND, PIN_UNTIL,
                                      PIN_REASON)
        finally:
            RTR.plan = saved_plan

        RI.decide = lambda *a, **k: {
            "verdict": "NOOP", "executed": False}
        try:
            split_wire = RNP.check(fresh, "R2351", "R2370",
                                   "re-pinned at R2351")
        finally:
            RI.decide = saved_decide

        def different_detail(*a, **k):
            raise RTR.RepinError("E_RTRP_UNMATCHED", "a different detail")

        RI.decide = different_detail
        try:
            split_detail = RNP.check(unmatched, "R2351", "R2370",
                                     "re-pinned at R2351")
        finally:
            RI.decide = saved_decide

        ok = (agree_fresh["verdict"] == "AGREES"
              and agree_fresh["first_diff"] is None
              and agree_fresh["shipped"] == "PLANNED"
              and agree_fresh["wire"] == "PLANNED"
              and agree_pinned["verdict"] == "AGREES"
              and agree_pinned["shipped"] == "NOOP"
              and agree_pinned["wire"] == "NOOP"
              and agree_refused["verdict"] == "AGREES"
              and agree_refused["shipped_code"] == "E_RTRP_UNMATCHED"
              and agree_refused["wire_code"] == "E_RTRP_UNMATCHED"
              and split_shipped["verdict"] == "DISAGREES"
              and split_shipped["first_diff"] != "detail"
              and split_wire["verdict"] == "DISAGREES"
              and split_detail["verdict"] == "DISAGREES"
              and split_detail["first_diff"] == "detail")
        if not ok:
            print("  measured: fresh=%r pinned=%r refused=%r shipped=%r "
                  "wire=%r detail=%r"
                  % (agree_fresh, agree_pinned, agree_refused,
                     split_shipped, split_wire, split_detail), flush=True)
        check(ok, "AC-RNP3 both faces agree over ONE declaration (PLANNED, "
                  "NOOP and a shared refusal), and a patched face on either "
                  "side reads DISAGREES while a differing refusal DETAIL is "
                  "named as first_diff=detail")
    finally:
        RTR.plan = saved_plan
        RI.decide = saved_decide
        for world in (fresh, pinned, unmatched):
            shutil.rmtree(world, ignore_errors=True)


def ac_rnp4():
    """--json keeps PLAN_KEYS on both faces and NOOP adds no key."""
    world = make_world()
    try:
        pin(world)
        args = ["--round", PIN_ROUND, "--until", PIN_UNTIL,
                "--reason", PIN_REASON, "--json"]
        code_s, out_s, _ = run_cli(SHIPPED, world, args)
        code_w, out_w, _ = run_cli(WIRE, world, args)
        shipped_keys = tuple(json.loads(out_s).keys()) if out_s.strip() else ()
        wire_keys = tuple(json.loads(out_w).keys()) if out_w.strip() else ()
        parity = RNP.check(world, PIN_ROUND, PIN_UNTIL, PIN_REASON)
        parity_keys = tuple(json.loads(RNP.to_json(parity)).keys())
        ok = (code_s == 0 and code_w == 0
              and shipped_keys == RTR.PLAN_KEYS
              and wire_keys == RTR.PLAN_KEYS
              and wire_keys == RI.REPORT_KEYS
              and parity_keys == RNP.REPORT_KEYS
              and json.loads(out_s)["verdict"] == "NOOP"
              and json.loads(out_w)["verdict"] == "NOOP")
        if not ok:
            print("  measured: keys_s=%r keys_w=%r parity=%r"
                  % (shipped_keys, wire_keys, parity_keys), flush=True)
        check(ok, "AC-RNP4 the --json key order stays the shipped PLAN_KEYS "
                  "on BOTH CLIs, a NOOP reading adds no key, and the parity "
                  "serialises its own pinned REPORT_KEYS")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rnp5():
    """One comparison, one writer: the law is imported, never copied."""
    world = make_world()
    saved = RNP.is_noop
    try:
        shipped_source = io.open(SHIPPED, "r", encoding="utf-8").read()
        shipped_code = code_only(shipped_source)
        parity_code = code_only(io.open(MODULE, "r", encoding="utf-8").read())
        imports_law = ("import repin_noop_parity as RNP" in shipped_code
                       and "RNP.is_noop(" in shipped_code
                       and "def is_noop" not in shipped_code)
        one_writer = shipped_code.count("os.replace(") == 1
        no_second_comp = ("def build" not in parity_code
                          and "def plan" not in parity_code
                          and "os.replace(" not in parity_code)

        before = file_map(world)
        RNP.is_noop = lambda path, text: True
        try:
            patched = RTR.plan(world, "R2351", "R2370", "re-pinned at R2351",
                               False, True)
        finally:
            RNP.is_noop = saved
        after = file_map(world)
        check(imports_law and one_writer and no_second_comp
              and patched["verdict"] == "NOOP"
              and patched["executed"] is False
              and before == after,
              "AC-RNP5 the shipped module imports the comparison and keeps "
              "its ONE os.replace writer, the parity module composes nothing "
              "and writes nothing, and patching is_noop moves the shipped "
              "verdict to NOOP without touching a byte")
    finally:
        RNP.is_noop = saved
        shutil.rmtree(world, ignore_errors=True)


def ac_rnp6():
    """Pure ASCII, stdlib only, no network, no clock, wired, live reading."""
    ascii_ok = True
    for path in (MODULE, os.path.join(BASE, "test_repin_noop_parity.py")):
        try:
            io.open(path, "rb").read().decode("ascii")
        except (UnicodeDecodeError, IOError):
            ascii_ok = False
    source = io.open(MODULE, "r", encoding="utf-8").read()
    forbidden = ("import socket", "import urllib", "import http",
                 "import time", "import datetime", "requests", "urlopen")
    no_network = not any(token in source for token in forbidden)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = WIRED_EXPECT in runner and LABEL in runner
    live = RNP.check(REPO, "R2382", "R2400", "live parity reading at R2382")
    print("LIVE %s" % RNP.one_line(live), flush=True)
    check(ascii_ok and no_network and wired
          and live["verdict"] in RNP.VERDICTS
          and (live["verdict"] == "AGREES") == (live["first_diff"] is None),
          "AC-RNP6 pure ASCII, stdlib only, zero network, no clock, wired as "
          "%s(%d), with a live reading over the real tree"
          % (LABEL, EXPECTED_CRITERIA))


def main():
    ac_rnp1()
    ac_rnp2()
    ac_rnp3()
    ac_rnp4()
    ac_rnp5()
    ac_rnp6()
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