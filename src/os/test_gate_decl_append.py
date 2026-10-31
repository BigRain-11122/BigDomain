"""gate_decl_append suite (R2312; criteria AC-GDA1..AC-GDA6 were pre-registered
inside the R2300 seed row of state/queue/tech.md BEFORE this code existed).

What this proves: state/machine_gates.json can now gain a blocker through a
writer instead of a hand edit. The entry shape, the declaration shape and the
capability vocabulary are imported from machine_gate - the suite proves the
import by widening that vocabulary and watching the same call accept it, and
by checking that no copy of the key laws lives in the writer. A duplicate
identity and an unknown capability are refused before any byte changes, the
plan writes nothing and publishes its byte delta, execute proves its read-back,
the post text re-parses through machine_gate with the pre-existing entries
byte-intact, and the CLI refuses with its own codes while a second run of the
same flags reads byte-identical json.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import gate_decl_append as GDA  # noqa: E402
import machine_gate as MG  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "gate_decl_append.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-gate-decl-append"

DECL_BODY = {
    "version": 1,
    "declared_by": "R2286",
    "reason": "suite declaration",
    "gates": [
        {"identity": "-#aaaaaaaa", "capability": "docker",
         "reason": "docker is absent here", "declared_by": "R2286"},
    ],
}

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


def make_world(body=None, raw=None):
    """A temp root carrying one declaration at machine_gate's own path."""
    world = tempfile.mkdtemp(prefix="bigdomain-gda-")
    os.makedirs(os.path.join(world, "state"))
    path = os.path.join(world, MG.DEFAULT_DECLARATION)
    if raw is not None:
        text = raw
    else:
        text = json.dumps(body or DECL_BODY, ensure_ascii=True, indent=2) + "\n"
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return world


def read_bytes(world):
    path = os.path.join(world, MG.DEFAULT_DECLARATION)
    with io.open(path, "rb") as handle:
        return handle.read()


def tree_digest(world):
    """Every file under the world with its size, in walk order."""
    out = []
    for root, dirs, files in os.walk(world):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, world)
            out.append("%s:%d" % (rel, os.path.getsize(full)))
    return "|".join(out)


def run_cli(world, extra=()):
    argv = [sys.executable, MODULE, "--root", world]
    argv.extend(extra)
    proc = subprocess.run(argv, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


FLAGS = ("--identity", "AC-GDA1#beef0001", "--capability", "battery",
         "--reason", "suite leg", "--declared-by", "R2312")


def ac_gda1():
    """AC-GDA1: the shape law is machine_gate's, and a patch flows through."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    imported = ("MG.read_declaration_text(" in source
                and "MG.CAPABILITIES" in source
                and "MG.DEFAULT_DECLARATION" in source)
    # The writer must not own a second entry/declaration key list.
    no_copy = ('ENTRY_KEYS = (' not in source
               and 'DECLARATION_KEYS = (' not in source
               and 'CAPABILITIES = (' not in source)
    text = json.dumps(DECL_BODY, ensure_ascii=True, indent=2) + "\n"
    original = MG.CAPABILITIES
    patched_ok = False
    try:
        MG.CAPABILITIES = tuple(original) + ("sandbox",)
        report = GDA.plan(text, "AC-GDA1#beef0001", "sandbox",
                          "a capability the suite just added", "R2312")
        patched_ok = (report["declarations_after"] == 2
                      and "sandbox" in report["post"])
    except GDA.GateDeclAppendError as exc:
        print("  patched-vocabulary refusal: %s" % exc.code, flush=True)
    finally:
        MG.CAPABILITIES = original
    restored = False
    try:
        GDA.plan(text, "AC-GDA1#beef0002", "sandbox", "now refused", "R2312")
    except GDA.GateDeclAppendError as exc:
        restored = exc.code == "E_GDA_BAD_CAPABILITY"
    ok = imported and no_copy and patched_ok and restored
    if not ok:
        print("  measured: imported=%r no_copy=%r patched=%r restored=%r"
              % (imported, no_copy, patched_ok, restored), flush=True)
    check(ok, "AC-GDA1 shape law imported from machine_gate, patch flows")


def ac_gda2():
    """AC-GDA2: duplicate identity and unknown capability refuse, zero writes."""
    world = make_world()
    try:
        before = tree_digest(world)
        code_dup, out_dup = run_cli(world, (
            "--identity", "-#aaaaaaaa", "--capability", "docker",
            "--reason", "a second declaration of the same row", "--declared-by",
            "R2312"))
        code_cap, out_cap = run_cli(world, (
            "--identity", "AC-GDA2#beef0002", "--capability", "quantum",
            "--reason", "a capability nobody declared", "--declared-by",
            "R2312"))
        dup_detail = ""
        cap_detail = ""
        for identity, capability in (("-#aaaaaaaa", "docker"),
                                     ("AC-GDA2#beef0002", "quantum")):
            try:
                GDA.append_gate(world, identity, capability,
                                "a refusal the suite reads in detail", "R2312")
            except GDA.GateDeclAppendError as exc:
                if exc.code == "E_GDA_DUP":
                    dup_detail = exc.detail
                elif exc.code == "E_GDA_BAD_CAPABILITY":
                    cap_detail = exc.detail
        after = tree_digest(world)
        dup_named = ("E_GDA_DUP" in out_dup and "identity" in dup_detail)
        cap_named = ("E_GDA_BAD_CAPABILITY" in out_cap
                     and "capability" in cap_detail)
        ok = (code_dup == 2 and code_cap == 2 and dup_named and cap_named
              and before == after)
        if not ok:
            print("  measured: codes=%r/%r dup=%r cap=%r clean=%r"
                  % (code_dup, code_cap, dup_named, cap_named,
                     before == after), flush=True)
        check(ok, "AC-GDA2 duplicate identity and unknown capability refused")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gda3():
    """AC-GDA3: plan writes nothing, execute replaces atomically, no residue."""
    world = make_world()
    try:
        before = read_bytes(world)
        planned = GDA.append_gate(world, "AC-GDA3#beef0003", "battery",
                                  "planned only", "R2312")
        still = read_bytes(world)
        plan_clean = (still == before and planned["wrote"] is False
                      and planned["read_back_ok"] is None
                      and planned["verdict"] == "PLANNED")
        delta = planned["predicted_bytes"] - planned["before_bytes"]
        named = delta > 0 and planned["before_bytes"] == len(before)
        prediction = GDA.plan(before.decode("utf-8"), "AC-GDA3#beef0003",
                              "battery", "planned only", "R2312")
        predicted = prediction["post"].encode("utf-8")
        done = GDA.append_gate(world, "AC-GDA3#beef0003", "battery",
                               "planned only", "R2312", execute=True)
        after = read_bytes(world)
        temp_left = os.path.exists(
            os.path.join(world, MG.DEFAULT_DECLARATION) + GDA.TEMP_SUFFIX)
        wrote_ok = (done["wrote"] is True and done["read_back_ok"] is True
                    and done["verdict"] == "APPENDED"
                    and len(after) == done["predicted_bytes"]
                    and after == predicted and not temp_left)
        ok = plan_clean and named and wrote_ok
        if not ok:
            print("  measured: plan=%r delta=%r write=%r temp=%r"
                  % (plan_clean, delta, wrote_ok, temp_left), flush=True)
        check(ok, "AC-GDA3 dry run first, one atomic replace, no temp")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gda4():
    """AC-GDA4: the post re-parses and every pre-existing entry is intact."""
    world = make_world()
    try:
        before_text = read_bytes(world).decode("utf-8")
        before = MG.read_declaration_text(before_text)
        old_body = before_text[before_text.index("[") + 1:
                               before_text.rindex("]")]
        report = GDA.append_gate(world, "AC-GDA4#beef0004", "gpu",
                                 "cosmetic capability for the suite", "R2312",
                                 execute=True)
        post_text = read_bytes(world).decode("utf-8")
        post = MG.read_declaration_text(post_text)
        added = [row for row in post["gates"]
                 if row["identity"] == "AC-GDA4#beef0004"]
        intact = old_body.rstrip() in post_text
        ok = (len(post["gates"]) == len(before["gates"]) + 1 ==
              report["declarations_after"]
              and len(added) == 1
              and added[0]["capability"] == "gpu"
              and added[0]["declared_by"] == "R2312"
              and intact
              and post["declared_by"] == before["declared_by"])
        if not ok:
            print("  measured: before=%d after=%d added=%d intact=%r"
                  % (len(before["gates"]), len(post["gates"]), len(added),
                     intact), flush=True)
        check(ok, "AC-GDA4 post re-parses, one new entry, old bytes intact")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gda5():
    """AC-GDA5: pinned CLI codes, byte-stable json, refusals write nothing."""
    world = make_world()
    broken = make_world(raw='{"version": 1, "gates": [}\n')
    absent = tempfile.mkdtemp(prefix="bigdomain-gda-none-")
    two_headers = make_world(
        raw=json.dumps(DECL_BODY, ensure_ascii=True, indent=2) + "\n"
        + json.dumps(DECL_BODY, ensure_ascii=True, indent=2) + "\n")
    try:
        clean_before = tree_digest(world)
        broken_before = tree_digest(broken)
        two_before = tree_digest(two_headers)
        code_plan, out_plan = run_cli(world, FLAGS)
        _code_json, json_a = run_cli(world, tuple(FLAGS) + ("--json",))
        twin = make_world()
        try:
            _twin_code, json_b = run_cli(twin, tuple(FLAGS) + ("--json",))
        finally:
            shutil.rmtree(twin, ignore_errors=True)
        code_exec, exec_json = run_cli(world,
                                       tuple(FLAGS) + ("--execute", "--json"))
        code_dup, _out_d = run_cli(world, FLAGS)
        code_bad, _out_b = run_cli(broken, FLAGS)
        code_none, _out_n = run_cli(absent, FLAGS)
        code_two, _out_t = run_cli(two_headers, FLAGS)
        code_flag, _out_f = run_cli(world, ("--nonsense",))
        code_missing, _out_m = run_cli(world, ("--identity", "x"))
        pinned = True
        stable = json_a == json_b and json_a.strip() != ""
        try:
            planned_json = json.loads(json_a)
            executed_json = json.loads(exec_json)
            pinned = (sorted(planned_json.keys()) == sorted(GDA.REPORT_KEYS)
                      and planned_json["verdict"] == "PLANNED"
                      and planned_json["wrote"] is False
                      and executed_json["verdict"] == "APPENDED"
                      and executed_json["read_back_ok"] is True)
        except ValueError:
            pinned = False
        refusal_clean = (tree_digest(broken) == broken_before
                         and tree_digest(two_headers) == two_before)
        before_after = (code_plan == 0 and code_exec == 0 and code_dup == 2
                        and code_bad == 3 and code_none == 3 and code_two == 2
                        and code_flag == 5 and code_missing == 5)
        ok = before_after and pinned and stable and refusal_clean
        if not ok:
            print("  codes: plan=%r dup=%r bad=%r none=%r two=%r flag=%r "
                  "missing=%r pinned=%r stable=%r"
                  % (code_plan, code_dup, code_bad, code_none, code_two,
                     code_flag, code_missing, pinned, stable), flush=True)
            print("  clean_before len=%d" % len(clean_before), flush=True)
        check(ok, "AC-GDA5 pinned exit codes, byte-stable json, no stray writes")
    finally:
        for world in (world, broken, absent, two_headers):
            shutil.rmtree(world, ignore_errors=True)


def ac_gda6():
    """AC-GDA6: pure source, wired, and the live declaration still reads."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    no_clock = ("import time" not in source and "datetime" not in source)
    stdlib_only = True
    for line in source.splitlines():
        text = line.strip()
        if text.startswith("import ") and " " not in text[7:]:
            name = text[7:].strip()
            if name not in ("io", "json", "os", "sys"):
                stdlib_only = False
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner) or ("'%s'" % LABEL in runner)
    live_path = os.path.join(REPO, MG.DEFAULT_DECLARATION)
    live_before = io.open(live_path, "rb").read()
    live = MG.read_declaration(live_path)
    refused_live = False
    try:
        GDA.append_gate(REPO, "-#02878cdc", "docker",
                        "a declaration of the row already declared", "R2312")
    except GDA.GateDeclAppendError as exc:
        refused_live = exc.code == "E_GDA_DUP"
    live_after = io.open(live_path, "rb").read()
    ok = (ascii_only and no_net and no_clock and stdlib_only and wired
          and live["version"] >= 1 and live_before == live_after
          and refused_live)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r stdlib=%r wired=%r "
              "declarations=%d untouched=%r"
              % (ascii_only, no_net, no_clock, stdlib_only, wired,
                 len(live["gates"]), live_before == live_after), flush=True)
    check(ok, "AC-GDA6 pure source, wired, live declaration reads and is untouched")


def main():
    print("gate_decl_append suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_gda1()
    ac_gda2()
    ac_gda3()
    ac_gda4()
    ac_gda5()
    ac_gda6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())