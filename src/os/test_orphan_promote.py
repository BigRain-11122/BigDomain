"""orphan_promote suite (R2339; criteria AC-OTP1..AC-OTP6 were pre-registered
inside the R2323 seed row of state/queue/tech.md:387 BEFORE this code existed).

What this proves: an ORPHAN round whose green leg is stranded under a variant
name can now be promoted to its canonical name by one writer, and the writer
refuses every case it cannot prove - no trace, no green leg, a named leg that
is not green, an existing canonical target - before a single byte is written.
The orphan round, its legs and its standing-in leg all come from orphan_trace
(patching that reader moves this module), a standings-only pick takes the
first RUNNER PASS leg in name order and names the others, a dry run writes
nothing, and an executed promotion copies rather than moves so the variant leg
survives its own promotion.

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

import orphan_promote as OP  # noqa: E402
import orphan_trace as OT  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "orphan_promote.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-orphan-promote"

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


def body(runner, verdict="PASS", sections=True):
    """One battery-shaped leg: runner token, verdict token, sections."""
    lines = ["RUNNER %s" % runner]
    if sections:
        lines.append("SECTION matrix %s" % verdict)
        lines.append("SECTION fingerprint %s" % verdict)
        lines.append("SECTION profile %s" % verdict)
        lines.append("SECTION census %s" % verdict)
    lines.append("VERDICT %s" % verdict)
    return "\n".join(lines) + "\n"


def make_world(legs, canonical=None, directory="qa"):
    """A temp root with one evidence directory holding the given legs."""
    world = tempfile.mkdtemp(prefix="bigdomain-otp-")
    path = os.path.join(world, directory)
    os.makedirs(path)
    for name in sorted(legs):
        with io.open(os.path.join(path, name), "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write(legs[name])
    if canonical is not None:
        with io.open(os.path.join(path, canonical), "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write("RUNNER PASS\nVERDICT PASS\n")
    return world


def listing(world, directory="qa"):
    return sorted(os.listdir(os.path.join(world, directory)))


def digest_of(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def run_cli(args):
    proc = subprocess.Popen([sys.executable, MODULE] + args,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def refusal(call):
    """Run one call and return (code, detail), or (None, "") on success."""
    try:
        call()
    except OP.OrphanPromoteError as exc:
        return exc.code, exc.detail
    return None, ""


class Patched(object):
    """Swap orphan_trace's reader for the duration of one criterion."""

    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.saved = None

    def __enter__(self):
        self.saved = getattr(OT, self.name)
        setattr(OT, self.name, self.value)
        return self

    def __exit__(self, *exc):
        setattr(OT, self.name, self.saved)
        return False


def ac_otp1():
    """The reading is imported, never re-derived; a patched one flows through."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    imported = ("import orphan_trace as OT" in source
                and "OT.traces" in source
                and "re.compile" not in source
                and "digest_of" not in source
                and "os.listdir" not in source)
    world = make_world({
        "reconcile-all-R9001a.log": body("FAIL", "FAIL"),
        "reconcile-all-R9001b.log": body("PASS"),
    })
    patched_report = {
        "dir": "qa",
        "counts": {"rounds": 1, "legs": 1, "trace_exists": 1, "no_trace": 0},
        "rounds": [{
            "round": "R9001",
            "status": "TRACE-EXISTS",
            "standing_in": "reconcile-all-R9001a.log",
            "legs": [{"name": "reconcile-all-R9001a.log", "runner": "PASS",
                      "verdict": "PASS", "digest": "patcheddigest"}],
        }],
        "verdict": "TRACE-FOUND",
    }
    try:
        with Patched("traces", lambda root, directory="qa": patched_report):
            report = OP.plan(world, "R9001")
        ok = (imported
              and report["source"] == "reconcile-all-R9001a.log"
              and report["digest"] == "patcheddigest"
              and report["standing_in"] == "reconcile-all-R9001a.log")
        if not ok:
            print("  measured: imported=%r source=%r digest=%r"
                  % (imported, report["source"], report["digest"]),
                  flush=True)
        check(ok, "AC-OTP1 round, legs and standing-in leg are imported")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_otp2():
    """A plan names source, target, bytes, digest; the pick prefers PASS first."""
    legs = {
        "reconcile-all-R9001a.log": body("FAIL", "FAIL"),
        "reconcile-all-R9001b.log": body("PASS"),
        "reconcile-all-R9001c.log": body("PASS"),
    }
    world = make_world(legs)
    try:
        report = OP.plan(world, "R9001")
        path = os.path.join(world, "qa", "reconcile-all-R9001b.log")
        ok = (report["source"] == "reconcile-all-R9001b.log"
              and report["target"] == "reconcile-all-R9001.log"
              and report["source_bytes"] == os.path.getsize(path)
              and report["digest"] == digest_of(path)
              and report["green_legs"]
              == ["reconcile-all-R9001b.log", "reconcile-all-R9001c.log"]
              and report["other_green"] == ["reconcile-all-R9001c.log"]
              and report["verdict"] == "PLANNED"
              and report["wrote"] is False)
        if not ok:
            print("  measured: %r" % (report,), flush=True)
        check(ok, "AC-OTP2 first PASS leg picked, other green leg named")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_otp3():
    """NO-TRACE, a non-green named source and an existing target all refuse."""
    trace_world = make_world({
        "reconcile-all-R9002a.log": "no runner line here\n",
        "reconcile-all-R9002b.log": "still no runner line\n",
    })
    target_world = make_world({
        "reconcile-all-R9003a.log": body("PASS"),
    }, canonical="reconcile-all-R9003.log")
    green_world = make_world({
        "reconcile-all-R9004a.log": body("FAIL", "FAIL"),
        "reconcile-all-R9004b.log": body("PASS"),
    })
    try:
        before = listing(target_world)
        canonical = os.path.join(target_world, "qa",
                                 "reconcile-all-R9003.log")
        canonical_before = digest_of(canonical)
        # The target guard exists for the RACE the seed row names: the reading
        # that saw an orphan and the write are separated in time, so the
        # canonical leg can appear in between. The fixture therefore reads the
        # round as an orphan (patched) while the canonical file is on disk.
        raced = {
            "dir": "qa",
            "counts": {"rounds": 1, "legs": 1, "trace_exists": 1,
                       "no_trace": 0},
            "rounds": [{
                "round": "R9003",
                "status": "TRACE-EXISTS",
                "standing_in": "reconcile-all-R9003a.log",
                "legs": [{"name": "reconcile-all-R9003a.log",
                          "runner": "PASS", "verdict": "PASS",
                          "digest": "racedigest"}],
            }],
            "verdict": "TRACE-FOUND",
        }
        code_trace, detail_trace = refusal(
            lambda: OP.plan(trace_world, "R9002"))
        with Patched("traces", lambda root, directory="qa": raced):
            code_target, _ = refusal(
                lambda: OP.plan(target_world, "R9003"))
        code_green, detail_green = refusal(
            lambda: OP.plan(green_world, "R9004", source="reconcile-all-R9004a.log"))
        code_round, _ = refusal(lambda: OP.plan(green_world, "R9100"))
        ok = (code_trace == "E_OTP_NO_TRACE"
              and "NO-TRACE" in detail_trace
              and code_target == "E_OTP_TARGET_EXISTS"
              and code_green == "E_OTP_NOT_GREEN"
              and "reconcile-all-R9004b.log" in detail_green
              and code_round == "E_OTP_NO_ROUND"
              and listing(target_world) == before
              and digest_of(canonical) == canonical_before)
        if not ok:
            print("  measured: trace=%r target=%r green=%r round=%r "
                  "tree=%r" % (code_trace, code_target, code_green, code_round,
                               listing(target_world)), flush=True)
        check(ok, "AC-OTP3 no trace, non-green source and target refuse")
    finally:
        for world in (trace_world, target_world, green_world):
            shutil.rmtree(world, ignore_errors=True)


def ac_otp4():
    """A dry run writes nothing; a promotion copies, proves both sides."""
    world = make_world({
        "reconcile-all-R9005a.log": body("FAIL", "FAIL"),
        "reconcile-all-R9005b.log": body("PASS"),
    })
    try:
        before = listing(world)
        source_path = os.path.join(world, "qa", "reconcile-all-R9005b.log")
        source_digest = digest_of(source_path)
        dry = OP.promote(world, "R9005")
        dry_ok = (dry["wrote"] is False and dry["verdict"] == "PLANNED"
                  and listing(world) == before)
        done = OP.promote(world, "R9005", execute=True)
        after = listing(world)
        target_path = os.path.join(world, "qa", "reconcile-all-R9005.log")
        ok = (dry_ok and done["wrote"] is True
              and done["verdict"] == "PROMOTED"
              and after == sorted(before + ["reconcile-all-R9005.log"])
              and digest_of(target_path) == source_digest
              and digest_of(source_path) == source_digest
              and not any(name.endswith(OP.PART_SUFFIX) for name in after))
        if not ok:
            print("  measured: dry=%r done=%r after=%r"
                  % (dry["verdict"], done["verdict"], after), flush=True)
        check(ok, "AC-OTP4 dry run writes nothing, promotion copies once")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_otp5():
    """CLI 0/2/3/5, byte-stable JSON over pinned keys, and no clock."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    world = make_world({
        "reconcile-all-R9006a.log": body("PASS"),
        "reconcile-all-R9006b.log": body("PASS"),
    })
    refuse_world = make_world({
        "reconcile-all-R9007a.log": body("FAIL", "FAIL"),
    })
    try:
        code_plan, out_plan, _ = run_cli(["--plan", "R9006", "qa",
                                          "--root", world])
        code_json_a, json_a, _ = run_cli(["--plan", "R9006", "qa",
                                          "--root", world, "--json"])
        code_json_b, json_b, _ = run_cli(["--plan", "R9006", "qa",
                                          "--root", world, "--json"])
        code_bad, _, _ = run_cli(["--plan", "R9006", "--nope"])
        code_noargs, _, _ = run_cli([])
        code_refuse, out_refuse, _ = run_cli(["--plan", "R9007", "qa",
                                              "--root", refuse_world])
        code_missing, _, _ = run_cli(["--plan", "R9006", "nodir",
                                      "--root", world])
        parsed = json.loads(json_a)
        keys_ok = tuple(parsed.keys()) == OP.REPORT_KEYS
        ok = (code_plan == 0 and "ORPHAN PROMOTE action=PLAN" in out_plan
              and code_json_a == 0 and code_json_b == 0
              and json_a == json_b and keys_ok
              and code_bad == 5 and code_noargs == 5
              and code_refuse == 2 and "E_OTP_NOT_GREEN" in out_refuse
              and code_missing == 3 and no_clock)
        if not ok:
            print("  measured: plan=%r json=%r/%r stable=%r keys=%r bad=%r "
                  "none=%r refuse=%r missing=%r clock=%r"
                  % (code_plan, code_json_a, code_json_b, json_a == json_b,
                     keys_ok, code_bad, code_noargs, code_refuse,
                     code_missing, no_clock), flush=True)
        check(ok, "AC-OTP5 CLI 0/2/3/5, stable JSON, no clock")
    finally:
        for item in (world, refuse_world):
            shutil.rmtree(item, ignore_errors=True)


def ac_otp6():
    """Pure ASCII, stdlib only, zero network, wired, and only one replace."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    imports = re.findall(r"^import (\w+)", source, re.MULTILINE)
    stdlib_only = sorted(set(imports)) == ["json", "orphan_trace", "os", "sys"]
    no_delete = not re.search(r"\b(?:unlink|rmtree|removedirs)\b", source)
    removals = re.findall(r"os\.remove\(([^)]*)\)", source)
    temp_only = all(arg.strip() == "part_path" for arg in removals)
    one_replace = source.count("os.replace(") == 1
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_orphan_promote.py" in runner)
    ok = (ascii_only and no_net and stdlib_only and no_delete and temp_only
          and one_replace and wired)
    if not ok:
        print("  measured: ascii=%r net=%r imports=%r delete=%r temp=%r "
              "replace=%r wired=%r"
              % (ascii_only, no_net, sorted(set(imports)), no_delete,
                 temp_only, one_replace, wired), flush=True)
    check(ok, "AC-OTP6 pure ASCII, stdlib only, wired, one replace")


def main():
    print("orphan_promote suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_otp1()
    ac_otp2()
    ac_otp3()
    ac_otp4()
    ac_otp5()
    ac_otp6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())