"""residue_batch_status_face suite (R2379; criteria AC-RSBF1..AC-RSBF6 were
pre-registered inside the R2369 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the batch CLI can finally answer WHAT the live status of each
residue round is, so a --pair list is composed from one call instead of a
second tool plus a guess. The status map stays stamp_residue's own reading
(reached through residue_triage), the vocabulary is stamp_residue's own status
tuple read at call time, a round outside the residue reads NOT-RESIDUE with its
own code, and the --append path of the batch CLI is proved untouched by
patching this face to raise and watching append still work.

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

import residue_batch_status_face as RSBF  # noqa: E402
import residue_triage as RT  # noqa: E402
import residue_triage_append as RNA  # noqa: E402
import residue_triage_append_batch as RAB  # noqa: E402
import stamp_residue as SR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "residue_batch_status_face.py")
BATCH = os.path.join(BASE, "residue_triage_append_batch.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-residue-batch-status-face"

HEADER = "queue header\n"
TECH = ("- [x] [done 2026-11-01 R9002] first closed row\n"
        "- [x] [done 2026-11-01 R9003] second closed row\n"
        "- [x] [done 2026-11-01 R9004] third closed row\n")
LOG_ITEMS = ["2026-11-01 R9001 product window in the fixture world"]

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


def make_world(tech=TECH, log_items=LOG_ITEMS, decl_entries=None):
    """A temp root: state.json, the three queues, optionally a declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-rsbf-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    payload = {"tick": 2379, "log": list(log_items)}
    with io.open(os.path.join(world, "src", "os", "state.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload))
    bodies = {"tech": tech, "main": HEADER, "explore": HEADER}
    for name in bodies:
        path = os.path.join(world, "state", "queue", name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(bodies[name])
    if decl_entries is not None:
        path = os.path.join(world, "state", "residue_triage.json")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(decl_text(decl_entries))
    return world


def decl_text(entries):
    """The declaration layout the reader pins, built for a fixture."""
    head = ('{\n  "declared_by": "R2350",\n  "reason": "fixture",\n'
            '  "entries": [\n')
    body = ""
    for index, item in enumerate(entries):
        if index:
            body += ",\n"
        body += RNA.entry_text(item)
    if body:
        body += "\n"
    return head + body + "  ]\n}\n"


def run_cli(module, world, args):
    proc = subprocess.Popen([sys.executable, module] + args
                            + ["--root", world],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return (proc.returncode, out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


class Patched(object):
    """Swap one reader for the duration of one criterion."""

    def __init__(self, module, name, value):
        self.module = module
        self.name = name
        self.value = value

    def __enter__(self):
        self.saved = getattr(self.module, self.name)
        setattr(self.module, self.name, self.value)
        return self

    def __exit__(self, *exc):
        setattr(self.module, self.name, self.saved)
        return False


def refusal(call):
    """Run a call expecting a coded refusal; return (code, detail)."""
    try:
        call()
    except Exception as exc:  # noqa: BLE001 - the code is the assertion
        return getattr(exc, "code", None), getattr(exc, "detail", "")
    return None, ""


def ac_rsbf1():
    """The status map is stamp_residue's own reading, not a second scan."""
    world = make_world()
    try:
        live = RSBF.face(world)
        counted = RSBF.face(world)["counts"]
        patched_report = {
            "round_count": 2,
            "delivered": 1,
            "stamp_only_open": 1,
            "no_hit": 0,
            "verdict": "RESIDUE",
            "rounds": [
                {"round": 9002, "hit_count": 1, "closed_hits": 1,
                 "open_hits": 0, "status": "DELIVERED", "hits": []},
                {"round": 9003, "hit_count": 1, "closed_hits": 0,
                 "open_hits": 1, "status": "STAMP-ONLY-OPEN", "hits": []},
            ],
        }
        with Patched(SR, "read", lambda root: patched_report):
            moved_sr = RSBF.face(world)
        with Patched(RT, "live_residue",
                     lambda root: [{"round": 9002, "status": "NO-HIT"}]):
            moved_rt = RSBF.face(world)
        source = io.open(MODULE, "r", encoding="utf-8").read()
        no_second = ("json.load" not in source
                     and "state.json" not in source
                     and "import state_seq" not in source
                     and "re.compile" not in source)
        ok = (live["rounds"] == ["R9002", "R9003", "R9004"]
              and live["statuses"] == ["DELIVERED", "DELIVERED", "DELIVERED"]
              and "DELIVERED=3" in counted
              and moved_sr["rounds"] == ["R9002", "R9003"]
              and moved_sr["statuses"] == ["DELIVERED", "STAMP-ONLY-OPEN"]
              and moved_rt["statuses"] == ["NO-HIT"]
              and no_second)
        if not ok:
            print("  measured: live=%r counts=%r moved_sr=%r moved_rt=%r "
                  "no_second=%r" % (live["rounds"], counted,
                                    moved_sr["statuses"],
                                    moved_rt["statuses"], no_second),
                  flush=True)
        check(ok, "AC-RSBF1 the status map is stamp_residue's own reading")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rsbf2():
    """--check names every residue round WITH its live status."""
    world = make_world()
    try:
        rc, out, _ = run_cli(MODULE, world, ["--check"])
        named = ("  ROUND R9002 status=DELIVERED" in out
                 and "  ROUND R9003 status=DELIVERED" in out
                 and "  ROUND R9004 status=DELIVERED" in out)
        rc_batch, out_batch, _ = run_cli(
            BATCH, world, ["--check", "--round", "R2379"])
        batch_named = ("rounds=R9002,R9003,R9004" in out_batch
                       and "statuses=DELIVERED,DELIVERED,DELIVERED"
                       in out_batch)
        ok = rc == 0 and named and "rounds=3" in out and batch_named
        if not ok:
            print("  measured: rc=%r named=%r batch_rc=%r batch=%r"
                  % (rc, named, rc_batch, out_batch[:160]), flush=True)
        check(ok, "AC-RSBF2 every residue round is named with its status")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rsbf3():
    """A round outside the live residue reads NOT-RESIDUE with its own code."""
    world = make_world()
    try:
        rc, out, _ = run_cli(MODULE, world, ["--check", "--round", "R9999"])
        found_rc, found_out, _ = run_cli(MODULE, world,
                                         ["--check", "--round", "R9003"])
        ok = (rc == 2
              and "verdict=NOT-RESIDUE" in out
              and "requested_status=NOT-RESIDUE" in out
              and "E_RSBF_NOT_RESIDUE" in out
              and found_rc == 0
              and "requested_status=DELIVERED" in found_out
              and "verdict=FOUND" in found_out)
        if not ok:
            print("  measured: rc=%r out=%r found_rc=%r found=%r"
                  % (rc, out[:200], found_rc, found_out[:160]), flush=True)
        check(ok, "AC-RSBF3 NOT-RESIDUE carries its own code")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rsbf4():
    """The --append path of the batch CLI never touches this face."""
    single = ("- [x] [done 2026-11-01 R9002] the only closed row\n")
    world = make_world(tech=single, decl_entries=[])
    try:
        ok_args = ["--append", "--pair", "R9002=DELIVERED", "--by", "R2379",
                   "--reason", "fixture", "--until", "R2395", "--dry-run"]
        rc_ok, out_ok, _ = run_cli(BATCH, world, ok_args)
        disagree = ["--append", "--pair", "R9002=STAMP-ONLY-OPEN",
                    "--by", "R2379", "--reason", "fixture",
                    "--until", "R2395", "--dry-run"]
        rc_bad, out_bad, _ = run_cli(BATCH, world, disagree)

        def boom(root, requested=None):
            raise RSBF.ResidueBatchStatusFaceError(
                "E_RSBF_BAD_STATE", "patched face")

        with Patched(RSBF, "face", boom):
            planned = RAB.plan(world, [("R9002", "DELIVERED")],
                               "R2379", "fixture", "R2395")
            check_code, _ = refusal(lambda: RAB.check(world, "R2379"))
        source = io.open(BATCH, "r", encoding="utf-8").read()
        head = source.split("def check(")[0]
        append_clean = "residue_batch_status_face" not in head
        ok = (rc_ok == 0
              and "action=dry-run" in out_ok
              and "rounds=R9002 statuses=DELIVERED" in out_ok
              and rc_bad == 2
              and out_bad.startswith("E_RTAB_DISAGREES")
              and planned["delta"] > 0
              and check_code == "E_RTAB_BAD_STATE"
              and append_clean)
        if not ok:
            print("  measured: rc_ok=%r ok=%r rc_bad=%r bad=%r delta=%r "
                  "check=%r append_clean=%r"
                  % (rc_ok, out_ok[:120], rc_bad, out_bad[:80],
                     planned["delta"], check_code, append_clean), flush=True)
        check(ok, "AC-RSBF4 the append path is untouched by this face")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rsbf5():
    """Exits 0/2/3/5 and a byte-stable --json over the pinned key order."""
    world = make_world()
    bad = tempfile.mkdtemp(prefix="bigdomain-rsbf-empty-")
    try:
        rc_map, out_map, _ = run_cli(MODULE, world, ["--check"])
        rc_json_a, out_a, _ = run_cli(MODULE, world, ["--check", "--json"])
        rc_json_b, out_b, _ = run_cli(MODULE, world, ["--check", "--json"])
        rc_absent, out_absent, _ = run_cli(MODULE, world,
                                           ["--check", "--round", "R9999"])
        rc_bad, out_bad, _ = run_cli(MODULE, bad, ["--check"])
        rc_flags, _, _ = run_cli(MODULE, world, ["--nope"])
        order = False
        if rc_json_a == 0:
            payload = json.loads(out_a)
            order = tuple(payload.keys()) == RSBF.REPORT_KEYS
        ok = (rc_map == 0 and rc_json_a == 0 and out_a == out_b and order
              and rc_absent == 2 and "E_RSBF_NOT_RESIDUE" in out_absent
              and rc_bad == 3 and "E_RSBF_BAD_STATE" in out_bad
              and rc_flags == 5)
        if not ok:
            print("  measured: map=%r json=%r stable=%r order=%r absent=%r "
                  "bad=%r flags=%r" % (rc_map, rc_json_a, out_a == out_b,
                                       order, rc_absent, rc_bad, rc_flags),
                  flush=True)
        check(ok, "AC-RSBF5 exit codes and a byte-stable pinned --json")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(bad, ignore_errors=True)


def ac_rsbf6():
    """Pure ASCII, stdlib only, zero network, no clock, and the runner label."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_ok = all(ord(char) < 128 for char in source)
    imports_ok = "import residue_triage as RT" in source
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source and "import time" not in source
              and "datetime" not in source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"os-residue-batch-status-face"' in runner
             and "os-residue-batch-status-face" in LABEL)
    ok = ascii_ok and imports_ok and no_net and wired
    if not ok:
        print("  measured: ascii=%r imports=%r no_net=%r wired=%r"
              % (ascii_ok, imports_ok, no_net, wired), flush=True)
    check(ok, "AC-RSBF6 pure stdlib, ASCII, no clock, runner label wired")


def main():
    print("SUITE %s" % LABEL, flush=True)
    ac_rsbf1()
    ac_rsbf2()
    ac_rsbf3()
    ac_rsbf4()
    ac_rsbf5()
    ac_rsbf6()
    total = PASSES + FAILS
    print("SUITE %s/%s" % (PASSES, EXPECTED_CRITERIA), flush=True)
    if total != EXPECTED_CRITERIA:
        print("E_RSBF_SUITE_COUNT: %d criteria ran, %d expected"
              % (total, EXPECTED_CRITERIA), flush=True)
        return 2
    if FAILS:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())