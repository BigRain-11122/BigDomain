"""residue_triage_append_batch suite (R2369; criteria AC-RTAB1..AC-RTAB6 were
pre-registered inside the R2355 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: several residue rounds can now be declared in ONE call, so a
fold that creates two or more residue rounds no longer needs a one-off splice
script. The declaration reader, the status vocabulary, the shape check and the
judge stay owned by residue_triage, the entry layout stays owned by
residue_triage_append, every refusal happens before a byte moves, and the
write is one atomic replace whose size is proved and whose entries are re-read
one by one.

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

import residue_triage as RT  # noqa: E402
import residue_triage_append as RNA  # noqa: E402
import residue_triage_append_batch as RAB  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "residue_triage_append_batch.py")
SINGLE = os.path.join(BASE, "residue_triage_append.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-residue-triage-append-batch"

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


def entry(number, status="DELIVERED", declared_by=2350, until=2380,
          reason="fixture row"):
    return {"round": number, "status": status, "declared_by": declared_by,
            "reason": reason, "until": until}


def decl_text(entries, declared_by=2350, reason="fixture declaration"):
    """The declaration layout the reader pins, built for a fixture."""
    head = ('{\n  "declared_by": "R%d",\n  "reason": %s,\n  "entries": [\n'
            % (declared_by, json.dumps(reason, ensure_ascii=True)))
    body = ""
    for index, item in enumerate(entries):
        if index:
            body += ",\n"
        body += RNA.entry_text(item)
    if body:
        body += "\n"
    return head + body + "  ]\n}\n"


def make_world(entries=None, tech=TECH, log_items=LOG_ITEMS,
               declared_by=2350):
    """A temp root: state.json, the three queues, optionally a declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-rtab-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    payload = {"tick": declared_by, "log": list(log_items)}
    with io.open(os.path.join(world, "src", "os", "state.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload))
    bodies = {"tech": tech, "main": HEADER, "explore": HEADER}
    for name in bodies:
        path = os.path.join(world, "state", "queue", name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(bodies[name])
    if entries is not None:
        path = os.path.join(world, "state", "residue_triage.json")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(decl_text(entries, declared_by))
    return world


def decl_bytes(world):
    path = os.path.join(world, RAB.DECLARATION_PATH)
    with open(path, "rb") as handle:
        return handle.read()


def run_cli(module, world, args):
    proc = subprocess.Popen([sys.executable, module] + args
                            + ["--root", world],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return (proc.returncode, out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


class Patched(object):
    """Swap one reader or renderer for the duration of one criterion."""

    def __init__(self, module, name, value):
        self.module = module
        self.name = name
        self.value = value
        self.saved = None

    def __enter__(self):
        self.saved = getattr(self.module, self.name)
        setattr(self.module, self.name, self.value)
        return self

    def __exit__(self, *exc):
        setattr(self.module, self.name, self.saved)
        return False


def refusal(call):
    """Run one plan call and return its refusal code, or None."""
    try:
        call()
    except RAB.ResidueTriageAppendBatchError as exc:
        return exc.code, exc.detail
    return None, ""


def ac_rtab1():
    """Several pairs land in one call, and every other byte is preserved."""
    world = make_world(entries=[])
    try:
        before = decl_bytes(world)
        prepared = RAB.plan(world, [("R9002", "DELIVERED"),
                                    ("R9003", "DELIVERED"),
                                    ("R9004", "DELIVERED")],
                            "R2369", "fold 643 created three rounds", "R2379")
        after = prepared["after_bytes"]
        report = RAB.apply(world, prepared)
        reread = RT.load_declaration(world)
        rounds = sorted(item["round"] for item in reread["entries"])
        tail_kept = after.endswith(before[before.rindex(b"]"):])
        ok = (len(prepared["entries"]) == 3
              and prepared["entries_after"] == 3
              and rounds == [9002, 9003, 9004]
              and report["verdict"] == "TRIAGED"
              and report["untriaged"] == 0
              and tail_kept)
        if not ok:
            print("  measured: entries=%r after=%r rounds=%r verdict=%r "
                  "tail=%r" % (len(prepared["entries"]),
                               prepared["entries_after"], rounds,
                               report["verdict"], tail_kept), flush=True)
        check(ok, "AC-RTAB1 several entries in one call")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtab2():
    """A duplicate, a repeat or a DISAGREES refuses with the file untouched."""
    existing = entry(9002, status="DELIVERED", declared_by=2350)
    world = make_world(entries=[existing])
    try:
        before = decl_bytes(world)
        code_dup, detail_dup = refusal(
            lambda: RAB.plan(world, [("R9002", "DELIVERED"),
                                     ("R9003", "DELIVERED")],
                             "R2369", "second attempt", "R2379"))
        code_twice, _ = refusal(
            lambda: RAB.plan(world, [("R9003", "DELIVERED"),
                                     ("R9003", "DELIVERED")],
                             "R2369", "repeated round", "R2379"))
        code_dis, detail_dis = refusal(
            lambda: RAB.plan(world, [("R9003", "STAMP-ONLY-OPEN")],
                             "R2369", "wrong status", "R2379"))
        after = decl_bytes(world)
        ok = (code_dup == "E_RTAB_DUPLICATE"
              and "declared_by=R2350" in detail_dup
              and code_twice == "E_RTAB_DUPLICATE"
              and code_dis == "E_RTAB_DISAGREES"
              and "STAMP-ONLY-OPEN" in detail_dis
              and "DELIVERED" in detail_dis
              and before == after)
        if not ok:
            print("  measured: dup=%r twice=%r dis=%r unchanged=%r"
                  % (code_dup, code_twice, code_dis, before == after),
                  flush=True)
        check(ok, "AC-RTAB2 duplicates and DISAGREES refuse before a byte")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtab3():
    """One atomic replace at the predicted size, no temp residue."""
    world = make_world(entries=[entry(9002, declared_by=2350)])
    try:
        before = decl_bytes(world)
        prepared = RAB.plan(world, [("R9003", "DELIVERED"),
                                    ("R9004", "DELIVERED")],
                            "R2369", "one batch", "R2379")
        predicted = len(before) + prepared["delta"]
        RAB.apply(world, prepared)
        after = decl_bytes(world)
        temps = [name for name in os.listdir(os.path.join(
            world, os.path.dirname(RAB.DECLARATION_PATH)))
            if name.startswith("residue_triage.json.tmp")]
        ok = (len(after) == predicted
              and prepared["after_bytes"] == after
              and temps == [])
        if not ok:
            print("  measured: predicted=%d measured=%d temps=%r"
                  % (predicted, len(after), temps), flush=True)
        check(ok, "AC-RTAB3 one atomic replace at the predicted size")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtab4():
    """A partial batch refuses, and exit 0 only accompanies TRIAGED."""
    world = make_world(entries=[])
    try:
        code_partial, detail_partial = refusal(
            lambda: RAB.plan(world, [("R9002", "DELIVERED")],
                             "R2369", "only one of three", "R2379"))
        before = decl_bytes(world)
        rc_ok, out_ok, _ = run_cli(MODULE, world,
                                   ["--append", "--pair",
                                    "R9002=DELIVERED", "--pair",
                                    "R9003=DELIVERED", "--pair",
                                    "R9004=DELIVERED", "--by", "R2369",
                                    "--reason", "full batch", "--until",
                                    "R2379"])
        after = decl_bytes(world)
        rc_refuse, out_refuse, _ = run_cli(MODULE, world,
                                           ["--append", "--pair",
                                            "R9002=DELIVERED", "--by",
                                            "R2369", "--reason", "again",
                                            "--until", "R2379"])
        ok = (code_partial == "E_RTAB_NOT_TRIAGED"
              and "R9003" in detail_partial
              and before != after
              and rc_ok == 0
              and "verdict=TRIAGED" in out_ok
              and "wrote=yes" in out_ok
              and rc_refuse == 2
              and "E_RTAB_DUPLICATE" in out_refuse)
        if not ok:
            print("  measured: partial=%r detail=%r rc_ok=%r rc_refuse=%r"
                  % (code_partial, detail_partial, rc_ok, rc_refuse),
                  flush=True)
        check(ok, "AC-RTAB4 exit 0 only on TRIAGED, partial batch refused")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtab5():
    """The single-entry CLI keeps its own pinned behaviour."""
    world = make_world(entries=[entry(9002, declared_by=2350)])
    try:
        rc_check, out_check, _ = run_cli(SINGLE, world,
                                         ["--check", "--round", "R2369"])
        rc_dup, out_dup, _ = run_cli(SINGLE, world,
                                     ["--append", "--round", "R9002",
                                      "--status", "DELIVERED", "--by",
                                      "R2369", "--reason", "single", "--until",
                                      "R2379"])
        unchanged = "RESIDUE TRIAGE APPEND " in out_check
        ok = (rc_check == 2
              and unchanged
              and rc_dup == 2
              and "E_RTA_DUPLICATE" in out_dup)
        if not ok:
            print("  measured: rc_check=%r out=%r rc_dup=%r dup=%r"
                  % (rc_check, out_check[:60], rc_dup, out_dup[:60]),
                  flush=True)
        check(ok, "AC-RTAB5 single-entry CLI keeps its pinned behaviour")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtab6():
    """Pure stdlib, ASCII, zero network, and the owners stay the owners."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_ok = all(ord(char) < 128 for char in source)
    imports = ("import residue_triage as RT" in source
               and "import residue_triage_append as RNA" in source)
    no_second = ("json.load" not in source
                 and "re.compile" not in source
                 and "socket" not in source
                 and "urllib" not in source
                 and "http" not in source)
    world = make_world(entries=[entry(9003), entry(9004)])
    try:
        with Patched(RNA, "entry_text",
                     lambda item: "    {\"patched\": %d}" % item["round"]):
            prepared = RAB.plan(world, [("R9002", "DELIVERED")],
                                "R2369", "patched renderer", "R2379")
        rendered = prepared["after_bytes"].decode("utf-8")
        with Patched(RT, "live_residue",
                     lambda root: [{"round": 9002,
                                    "status": "STAMP-ONLY-OPEN"}]):
            code_patched, _ = refusal(
                lambda: RAB.plan(world, [("R9002", "DELIVERED")],
                                 "R2369", "patched reader", "R2379"))
        ok = (ascii_ok and imports and no_second
              and "\"patched\": 9002" in rendered
              and code_patched == "E_RTAB_DISAGREES"
              and os.path.exists(RUNNER))
        if not ok:
            print("  measured: ascii=%r imports=%r no_second=%r patched=%r "
                  "reader=%r" % (ascii_ok, imports, no_second,
                                 "\"patched\": 9002" in rendered,
                                 code_patched), flush=True)
        check(ok, "AC-RTAB6 pure stdlib, owners stay the owners")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("residue_triage_append_batch suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rtab1()
    ac_rtab2()
    ac_rtab3()
    ac_rtab4()
    ac_rtab5()
    ac_rtab6()
    total = PASSES + FAILS
    if total != EXPECTED_CRITERIA:
        print("FAIL criteria counted %d, expected %d"
              % (total, EXPECTED_CRITERIA), flush=True)
        return 1
    if FAILS:
        print("SUITE FAIL %d/%d" % (PASSES, total), flush=True)
        return 1
    print("SUITE PASS %d/%d" % (PASSES, total), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())