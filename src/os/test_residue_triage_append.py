"""residue_triage_append suite (R2335; criteria AC-RTA1..AC-RTA6 were
pre-registered inside the R2310 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: accepting ONE more residue round is now its own operation
rather than a regeneration of the whole declaration. The loader and every
status are imported from residue_triage (patched readers flow straight
through), a duplicate refuses by naming the existing entry, a round whose live
status disagrees refuses naming BOTH statuses so the regeneration shortcut
cannot launder one, an `until` earlier than its own `declared_by` refuses, a
successful append leaves every other entry byte-identical, and the CLI speaks
0/2/3/5 with a byte-stable JSON.

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

import residue_triage as RT  # noqa: E402
import residue_triage_append as RA  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "residue_triage_append.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-residue-triage-append"

HEADER = "queue header\n"
TECH = "- [x] [done 2026-11-01 R9002] a closed row delivered by the fixture\n"
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


def entry(number, status="DELIVERED", declared_by=2335, until=2350,
          reason="fixture row"):
    return {"round": number, "status": status, "declared_by": declared_by,
            "reason": reason, "until": until}


def decl_text(entries, declared_by=2335, reason="fixture declaration"):
    """The declaration layout the reader pins, built for a fixture."""
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


def make_world(entries=None, tech=TECH, log_items=LOG_ITEMS,
               declared_by=2335):
    """A temp root: state.json, the three queues, optionally a declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-rta-")
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
    path = os.path.join(world, RA.DECLARATION_PATH)
    with open(path, "rb") as handle:
        return handle.read()


def run_cli(world, args):
    proc = subprocess.Popen([sys.executable, MODULE] + args
                            + ["--root", world],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


class Patched(object):
    """Swap one residue_triage reader for the duration of one criterion."""

    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.saved = None

    def __enter__(self):
        self.saved = getattr(RT, self.name)
        setattr(RT, self.name, self.value)
        return self

    def __exit__(self, *exc):
        setattr(RT, self.name, self.saved)
        return False


def refusal(call):
    """Run one plan call and return its refusal code, or OK."""
    try:
        call()
    except RA.ResidueTriageAppendError as exc:
        return exc.code, exc.detail
    return None, ""


def ac_rta1():
    """Loader and statuses are imported; patched readers flow through."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    imported = ("import residue_triage as RT" in source
                and "json.load" not in source
                and "re.compile" not in source)
    uses = ("RT.load_declaration" in source
            and "RT.live_residue" in source
            and "RT.shape" in source
            and "RT.judge" in source)
    world = make_world(entries=[])
    try:
        duplicate, _detail = refusal(lambda: None)
        with Patched("load_declaration",
                     lambda root: {"declared_by": 2335,
                                   "reason": "patched",
                                   "entries": [entry(9002)]}):
            code_dup, _ = refusal(
                lambda: RA.plan(world, "R9002", "DELIVERED", "R2335",
                                "patched world", "R2350"))
        with Patched("live_residue",
                     lambda root: [{"round": 9002,
                                    "status": "STAMP-ONLY-OPEN"}]):
            code_dis, detail_dis = refusal(
                lambda: RA.plan(world, "R9002", "DELIVERED", "R2335",
                                "patched world", "R2350"))
        with Patched("live_residue",
                     lambda root: [{"round": 9002,
                                    "status": "DELIVERED"}]):
            flowed, _ = refusal(
                lambda: RA.plan(world, "R9002", "DELIVERED", "R2335",
                                "patched world", "R2350"))
        with Patched("load_declaration", lambda root: None):
            code_unpinned, _ = refusal(
                lambda: RA.plan(world, "R9002", "DELIVERED", "R2335",
                                "patched world", "R2350"))
        ok = (duplicate is None and imported and uses
              and code_dup == "E_RTA_DUPLICATE"
              and code_dis == "E_RTA_DISAGREES"
              and "STAMP-ONLY-OPEN" in detail_dis
              and flowed is None
              and code_unpinned == "E_RTA_UNPINNED")
        if not ok:
            print("  measured: imported=%r uses=%r dup=%r dis=%r flow=%r "
                  "unpinned=%r" % (imported, uses, code_dup, code_dis,
                                   flowed, code_unpinned), flush=True)
        check(ok, "AC-RTA1 loader and statuses imported, patches flow through")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rta2():
    """A round already declared refuses BY NAME, never a quiet overwrite."""
    existing = entry(9002, reason="accepted earlier")
    world = make_world(entries=[existing])
    try:
        before = decl_bytes(world)
        code, detail = refusal(
            lambda: RA.plan(world, "R9002", "DELIVERED", "R2335",
                            "second attempt", "R2350"))
        after = decl_bytes(world)
        ok = (code == "E_RTA_DUPLICATE"
              and "R9002" in detail
              and "DELIVERED" in detail
              and "declared_by=R2335" in detail
              and "until=R2350" in detail
              and before == after)
        if not ok:
            print("  measured: code=%r detail=%r unchanged=%r"
                  % (code, detail, before == after), flush=True)
        check(ok, "AC-RTA2 duplicate refuses naming the existing entry")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rta3():
    """A live DISAGREES refuses and names BOTH statuses."""
    world = make_world(entries=[])
    try:
        before = decl_bytes(world)
        code, detail = refusal(
            lambda: RA.plan(world, "R9002", "STAMP-ONLY-OPEN", "R2335",
                            "laundering attempt", "R2350"))
        after = decl_bytes(world)
        ok = (code == "E_RTA_DISAGREES"
              and "STAMP-ONLY-OPEN" in detail
              and "DELIVERED" in detail
              and before == after)
        if not ok:
            print("  measured: code=%r detail=%r unchanged=%r"
                  % (code, detail, before == after), flush=True)
        check(ok, "AC-RTA3 live disagreement refuses naming both statuses")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rta4():
    """until before declared_by refuses; a real append keeps every other byte."""
    world = make_world(entries=[entry(9001), entry(9003)])
    try:
        code, _detail = refusal(
            lambda: RA.plan(world, "R9002", "DELIVERED", "R2335",
                            "bad window", "R2000"))
        before = decl_bytes(world)
        prepared = RA.plan(world, "R9002", "DELIVERED", "R2335",
                           "accepted at R2335 off the live stamp table",
                           "R2350")
        report = RA.apply(world, prepared)
        after = decl_bytes(world)
        cut = len(before) - len(RA.CLOSER)
        prefix_kept = after.startswith(before[:cut])
        tail_kept = after.endswith(before[cut:])
        delta_ok = (len(after) - len(before)) == prepared["delta"]
        reread = RT.load_declaration(world)
        old_kept = ([reread["entries"][0], reread["entries"][1]]
                    == [entry(9001), entry(9003)])
        appended = reread["entries"][2] == prepared["entry"]
        ok = (code == "E_RTA_UNTIL_BEFORE_DECL"
              and prefix_kept and tail_kept and delta_ok
              and old_kept and appended
              and report["verdict"] == "TRIAGED"
              and reread["declared_by"] == 2335)
        if not ok:
            print("  measured: code=%r prefix=%r tail=%r delta=%r old=%r "
                  "appended=%r verdict=%r"
                  % (code, prefix_kept, tail_kept, delta_ok, old_kept,
                     appended, report["verdict"]), flush=True)
        check(ok, "AC-RTA4 until guard and byte-identical neighbours")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rta5():
    """CLI 0/2/3/5 with a byte-stable JSON over the pinned keys."""
    worlds = []
    try:
        world = make_world(entries=[])
        worlds.append(world)
        args = ["--append", "--round", "R9002", "--status", "DELIVERED",
                "--by", "R2335", "--reason", "accepted at R2335",
                "--until", "R2350"]
        rc_ok, body, _err = run_cli(world, args)
        rc_again, dup_body, _err = run_cli(world, args)
        rc_json_a, json_a, _err = run_cli(world, ["--check", "--round",
                                                  "R2335", "--json"])
        rc_json_b, json_b, _err = run_cli(world, ["--check", "--round",
                                                  "R2335", "--json"])
        parsed = json.loads(json_a)

        world_b = make_world(entries=[])
        worlds.append(world_b)
        rc_dis, dis_body, _err = run_cli(
            world_b, ["--append", "--round", "R9002", "--status",
                      "STAMP-ONLY-OPEN", "--by", "R2335",
                      "--reason", "laundering attempt", "--until", "R2350"])

        world_c = make_world(entries=None)
        worlds.append(world_c)
        rc_unpinned, unpinned_body, _err = run_cli(
            world_c, ["--append", "--round", "R9002", "--status",
                      "DELIVERED", "--by", "R2335", "--reason", "no base",
                      "--until", "R2350"])

        world_d = make_world(entries=[])
        worlds.append(world_d)
        before = decl_bytes(world_d)
        rc_dry, dry_body, _err = run_cli(
            world_d, ["--append", "--round", "R9002", "--status",
                      "DELIVERED", "--by", "R2335", "--reason", "dry run",
                      "--until", "R2350", "--dry-run"])
        dry_kept = decl_bytes(world_d) == before

        rc_flags, flags_body, _err = run_cli(world_d, ["--append", "--round",
                                                       "R9002"])

        ok = (rc_ok == 0 and "wrote=yes" in body
              and rc_again == 2 and "E_RTA_DUPLICATE" in dup_body
              and rc_dis == 2 and "E_RTA_DISAGREES" in dis_body
              and rc_unpinned == 3 and "E_RTA_UNPINNED" in unpinned_body
              and rc_flags == 5 and "E_RTA_BAD_ARGS" in flags_body
              and rc_dry == 0 and "DRY-RUN" in dry_body and dry_kept
              and rc_json_a == 0 and rc_json_b == 0 and json_a == json_b
              and tuple(parsed.keys()) == RA.REPORT_KEYS
              and parsed["verdict"] == "TRIAGED"
              and parsed["wrote"] is False)
        if not ok:
            print("  measured: rc=%r/%r/%r/%r/%r/%r/%r wrote=%r dup=%r "
                  "keys=%r dry=%r" % (rc_ok, rc_again, rc_dis, rc_unpinned,
                                      rc_flags, rc_dry, rc_json_a,
                                      "wrote=yes" in body,
                                      "E_RTA_DUPLICATE" in dup_body,
                                      tuple(parsed.keys()), dry_kept),
                  flush=True)
        check(ok, "AC-RTA5 CLI 0/2/3/5 and a byte-stable JSON")
    finally:
        for world in worlds:
            shutil.rmtree(world, ignore_errors=True)


def ac_rta6():
    """Pure ASCII, stdlib only, no network, no clock, wired in the runner."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                            source)
    imports = re.findall(r"^import (\w+)", source, re.MULTILINE)
    stdlib_only = sorted(set(imports)) == ["json", "os", "residue_triage",
                                           "sys"]
    removals = re.findall(r"os\.remove\(([^)]*)\)", source)
    no_delete = (not re.search(r"\b(?:unlink|rmtree|removedirs)\b", source)
                 and bool(removals)
                 and all(arg.strip() == "temp" for arg in removals))
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_residue_triage_append.py" in runner)
    ok = (ascii_only and no_net and no_clock and stdlib_only and no_delete
          and wired and "os.replace" in source)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r imports=%r delete=%r "
              "wired=%r" % (ascii_only, no_net, no_clock,
                            sorted(set(imports)), no_delete, wired),
              flush=True)
    check(ok, "AC-RTA6 pure, wired, and never deletes a declaration")


def main():
    print("residue_triage_append suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rta1()
    ac_rta2()
    ac_rta3()
    ac_rta4()
    ac_rta5()
    ac_rta6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())