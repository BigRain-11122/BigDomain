"""retire_candidate suite (R2331; criteria AC-RET1..AC-RET6 were pre-registered
inside the R2308 seed row of state/queue/tech.md BEFORE this code existed).

What this proves: the retirement question is now ONE reading instead of three
held in one head. The resolver imports the audit, the map and the parity scan
from their own readers (each proven by patching it and watching the verdict
move), answers RETIRE-READY only when all three conditions hold at once, and
otherwise names the one reason that blocks with a fixture world that differs
by exactly that one fact. A stale declaration can never be retirable, a
collision blocks both owners by name and line, and the resolver writes nothing.

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

import evidence_output_audit as EOA  # noqa: E402
import evidence_output_map as EOM  # noqa: E402
import evidence_parity as EVP  # noqa: E402
import retire_candidate as RC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "retire_candidate.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-retire-candidate"

EVIDENCE = "retire-world-9001.log"

# One copy that still performs the whole ritual: every leg marker the parity
# reader asks for, plus one literal qa declaration the audit can resolve.
RITUAL = '''LEGS = 2
import hashlib
import subprocess
ADJACENT = "qa/retire-world-9001.log"


def run_suite(path):
    return subprocess.run([path])


def emit(out, body):
    with open(out, "wb") as handle:
        handle.write(body.encode("utf-8"))
    line = "SUITE PASS"
    if line.startswith("SUITE"):
        print("LIVE reading")
    return "--check"


def check(line, body):
    for tag in ("a", "b"):
        if body.startswith("PASS"):
            pass
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    subprocess.run(["echo", digest])
    newline = "\\n"
    return digest
'''

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


def make_world(scripts, evidence=(EVIDENCE,)):
    """A world with src/os scripts and a qa folder; returns its path."""
    root = tempfile.mkdtemp(prefix="retire-candidate-")
    folder = os.path.join(root, "src", "os")
    os.makedirs(folder)
    qa = os.path.join(root, "qa")
    os.makedirs(qa)
    for name, body in scripts:
        with open(os.path.join(folder, name), "wb") as handle:
            handle.write(body.encode("utf-8"))
    for name in evidence:
        with open(os.path.join(qa, name), "wb") as handle:
            handle.write(b"evidence body\n")
    return root


def tree_digest(root):
    """Name, size and mtime of every file under root, order-independent."""
    parts = []
    for folder, _dirs, names in os.walk(root):
        for name in sorted(names):
            path = os.path.join(folder, name)
            info = os.stat(path)
            parts.append("%s|%d|%d" % (os.path.relpath(path, root),
                                       info.st_size, info.st_mtime_ns))
    return "\n".join(sorted(parts))


def row_of(report, name):
    for row in report["rows"]:
        if row["script"].replace("\\", "/").endswith(name):
            return row
    return None


def run_cli(world, args):
    """The module as a program, from a world it was pointed at."""
    proc = subprocess.Popen([sys.executable, MODULE] + args + ["--root", world],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def ac_ret1():
    """Every input is imported; each patched reader moves the verdict."""
    base_rows = [{"script": "src/os/evidence_R9001.py", "count": 1,
                  "exists": 1, "absent": 0, "family_hit": 0,
                  "family_none": 0, "status": "OK", "reason": ""}]
    audit_ok = {"rows": base_rows, "verdict": "CLEAN", "unreadable": []}
    map_ok = {"collisions": [], "rows": [], "verdict": "CLEAN",
              "unreadable": []}
    parity_ok = {"rows": [{"script": "src/os/evidence_R9001.py",
                           "verdict": "ALL-PRESENT",
                           "legs": [{"name": "two-legs",
                                     "verdict": "PRESENT"}]}],
                 "verdict": "ALL-PRESENT", "unreadable": []}
    audit_stale = json.loads(json.dumps(audit_ok))
    audit_stale["rows"][0]["status"] = "STALE"
    audit_stale["rows"][0]["reason"] = "ALL-UNRESOLVED"
    map_hit = json.loads(json.dumps(map_ok))
    map_hit["collisions"] = [{"path": "qa/x.log",
                              "scripts": [{"script":
                                           "src/os/evidence_R9001.py",
                                           "line": 4},
                                          {"script":
                                           "src/os/evidence_R8001.py",
                                           "line": 9}]}]
    parity_debt = json.loads(json.dumps(parity_ok))
    parity_debt["rows"][0]["verdict"] = "PARITY-DEBT"
    parity_debt["rows"][0]["legs"] = [{"name": "single-writer",
                                       "verdict": "DIFFERENT"}]

    saved = (EOA.audit, EOM.build, EVP.scan)
    try:
        EOA.audit = lambda *a, **k: audit_ok
        EOM.build = lambda *a, **k: map_ok
        EVP.scan = lambda *a, **k: parity_ok
        clean = RC.resolve(REPO, "src/os")
        EOA.audit = lambda *a, **k: audit_stale
        stale = RC.resolve(REPO, "src/os")
        EOA.audit = lambda *a, **k: audit_ok
        EOM.build = lambda *a, **k: map_hit
        collided = RC.resolve(REPO, "src/os")
        EOM.build = lambda *a, **k: map_ok
        EVP.scan = lambda *a, **k: parity_debt
        debt = RC.resolve(REPO, "src/os")
    finally:
        EOA.audit, EOM.build, EVP.scan = saved

    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_second_wheel = ("re.compile" not in source
                       and "hexdigest" not in source
                       and "split_target" not in source)
    ok = (clean["retire_ready"] == 1 and clean["verdict"] == "CANDIDATES"
          and stale["retire_ready"] == 0
          and stale["rows"][0]["reason"] == "DECLARATION-STALE"
          and collided["rows"][0]["reason"] == "COLLISION"
          and debt["rows"][0]["reason"] == "PARITY-DEBT"
          and no_second_wheel)
    if not ok:
        print("  measured: clean=%r stale=%r collided=%r debt=%r wheel=%r"
              % (clean["retire_ready"], stale["rows"][0]["reason"],
                 collided["rows"][0]["reason"], debt["rows"][0]["reason"],
                 no_second_wheel), flush=True)
    check(ok, "AC-RET1 three imported readers, each patch moving the verdict")


def ac_ret2():
    """RETIRE-READY needs all three at once; each blocker names its own fact."""
    worlds = []
    try:
        base = make_world([("evidence_R9001.py", RITUAL)])
        worlds.append(base)
        live = RC.resolve(base, "src/os", qa="qa")
        ready = row_of(live, "evidence_R9001.py")
        ready_ok = (ready["verdict"] == RC.READY and ready["reason"] == ""
                    and live["retire_ready"] == 1
                    and ready["audit_status"] == "OK"
                    and ready["parity"] == "ALL-PRESENT")

        stale = make_world([("evidence_R9001.py", RITUAL)], evidence=())
        worlds.append(stale)
        stale_row = row_of(RC.resolve(stale, "src/os", qa="qa"),
                           "evidence_R9001.py")

        thin = make_world([("evidence_R9001.py",
                           RITUAL.replace("utf-8", "latin-1"))])
        worlds.append(thin)
        thin_row = row_of(RC.resolve(thin, "src/os", qa="qa"),
                          "evidence_R9001.py")

        crowded = make_world([("evidence_R9001.py", RITUAL),
                              ("evidence_R9002.py", RITUAL)])
        worlds.append(crowded)
        crowded_row = row_of(RC.resolve(crowded, "src/os", qa="qa"),
                             "evidence_R9001.py")

        reasons = (ready_ok, stale_row["reason"], thin_row["reason"],
                   crowded_row["reason"])
        ok = reasons == (True, "DECLARATION-STALE", "PARITY-DEBT", "COLLISION")
        if not ok:
            print("  measured: ready=%r reasons=%r"
                  % (ready_ok, reasons[1:]), flush=True)
        check(ok, "AC-RET2 one fixture, three single-fact blockers, own reasons")
    finally:
        for world in worlds:
            shutil.rmtree(world, ignore_errors=True)


def ac_ret3():
    """A STALE declaration is never retirable, and names the audit reason."""
    worlds = []
    try:
        empty = make_world([("evidence_R9001.py", "nothing declared here\n")],
                           evidence=())
        worlds.append(empty)
        report = RC.resolve(empty, "src/os", qa="qa")
        row = row_of(report, "evidence_R9001.py")
        no_decl = (row["verdict"] == RC.OWNED
                   and row["reason"] == "DECLARATION-STALE"
                   and row["audit_reason"] == "NO-DECLARATION"
                   and report["retire_ready"] == 0
                   and report["verdict"] == "NOTHING")

        gone = make_world([("evidence_R9001.py", RITUAL)], evidence=())
        worlds.append(gone)
        gone_report = RC.resolve(gone, "src/os", qa="qa")
        gone_row = row_of(gone_report, "evidence_R9001.py")
        unresolved = (gone_row["reason"] == "DECLARATION-STALE"
                      and gone_row["audit_reason"] == "ALL-UNRESOLVED"
                      and gone_report["stale"] == 1
                      and gone_report["retire_ready"] == 0)

        crowded = make_world([("evidence_R9001.py", RITUAL),
                              ("evidence_R9002.py", RITUAL)])
        worlds.append(crowded)
        collide = RC.resolve(crowded, "src/os", qa="qa")
        shared = [row for row in collide["rows"]
                  if row["reason"] == "COLLISION"]
        stale_wins = (all(row["verdict"] == RC.OWNED for row in shared)
                      and collide["retire_ready"] == 0)
        ok = no_decl and unresolved and stale_wins
        if not ok:
            print("  measured: nodecl=%r unresolved=%r stalewins=%r"
                  % (no_decl, unresolved, stale_wins), flush=True)
        check(ok, "AC-RET3 a stale declaration is never RETIRE-READY")
    finally:
        for world in worlds:
            shutil.rmtree(world, ignore_errors=True)


def ac_ret4():
    """A collision blocks both owners and names the other script and line."""
    world = make_world([("evidence_R9001.py", RITUAL),
                        ("evidence_R9002.py", RITUAL)])
    try:
        report = RC.resolve(world, "src/os", qa="qa")
        first = row_of(report, "evidence_R9001.py")
        second = row_of(report, "evidence_R9002.py")
        names_first = ("evidence_R9002.py" in first["detail"]
                       and ":" in first["detail"])
        names_second = ("evidence_R9001.py" in second["detail"]
                        and ":" in second["detail"])
        ok = (first["reason"] == "COLLISION"
              and second["reason"] == "COLLISION"
              and first["verdict"] == RC.OWNED
              and second["verdict"] == RC.OWNED
              and report["collision"] == 2
              and report["retire_ready"] == 0
              and names_first and names_second)
        if not ok:
            print("  measured: %r / %r" % (first["detail"], second["detail"]),
                  flush=True)
        check(ok, "AC-RET4 a collision blocks both owners and names the other")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_ret5():
    """Read-only on the live pile, CLI codes 0/2/3/5, byte-stable JSON."""
    worlds = []
    try:
        live_before = tree_digest(os.path.join(REPO, "src", "os"))
        qa_dir = os.path.join(REPO, "qa")
        qa_before = tree_digest(qa_dir) if os.path.isdir(qa_dir) else ""
        report = RC.resolve(REPO, "src/os")
        live_after = tree_digest(os.path.join(REPO, "src", "os"))
        qa_after = tree_digest(qa_dir) if os.path.isdir(qa_dir) else ""
        read_only = (live_before == live_after and qa_before == qa_after
                     and report["scripts"] > 0)

        world = make_world([("evidence_R9001.py", RITUAL)])
        worlds.append(world)
        rc_ready, body_ready, _err = run_cli(world, ["--dir", "src/os"])
        rc_json_a, json_a, _e = run_cli(world, ["--dir", "src/os", "--json"])
        rc_json_b, json_b, _e = run_cli(world, ["--dir", "src/os", "--json"])
        parsed = json.loads(json_a)
        bare = make_world([])
        worlds.append(bare)
        rc_none, _body, _err = run_cli(bare, ["--dir", "src/os"])
        rc_missing, _b, _e = run_cli(world, ["--dir", "no-such-dir"])
        rc_flags, _b, _e = run_cli(world, ["--bogus"])
        ok = (read_only and rc_ready == 0 and rc_json_a == 0
              and rc_json_b == 0 and json_a == json_b
              and tuple(parsed.keys()) == RC.REPORT_KEYS
              and parsed["verdict"] == "CANDIDATES"
              and parsed["retire_ready"] == 1
              and rc_none == 2 and rc_missing == 3 and rc_flags == 5)
        if not ok:
            print("  measured: readonly=%r rc=%r/%r/%r/%r/%r keys=%r"
                  % (read_only, rc_ready, rc_json_a, rc_none, rc_missing,
                     rc_flags, tuple(parsed.keys())), flush=True)
        check(ok, "AC-RET5 read-only pile, CLI 0/2/3/5 and a stable JSON")
    finally:
        for world in worlds:
            shutil.rmtree(world, ignore_errors=True)


def ac_ret6():
    """Pure ASCII, no network, no clock, no write path, wired, inert."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    no_write = not re.search(r"open\([^)]*['\"][wax]", source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_retire_candidate.py" in runner)
    world = make_world([("evidence_R9001.py", RITUAL)])
    try:
        before = tree_digest(world)
        RC.resolve(world, "src/os", qa="qa")
        RC.judge({"rows": [], "verdict": "", "unreadable": []},
                 {"collisions": [], "rows": [], "verdict": "",
                  "unreadable": []},
                 {"rows": [], "verdict": "", "unreadable": []})
        after = tree_digest(world)
        ok = (ascii_only and no_net and no_clock and no_write and wired
              and before == after)
        if not ok:
            print("  measured: ascii=%r net=%r clock=%r write=%r wired=%r "
                  "inert=%r" % (ascii_only, no_net, no_clock, no_write, wired,
                                before == after), flush=True)
        check(ok, "AC-RET6 pure, wired, and writes nothing")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("retire_candidate suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_ret1()
    ac_ret2()
    ac_ret3()
    ac_ret4()
    ac_ret5()
    ac_ret6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())