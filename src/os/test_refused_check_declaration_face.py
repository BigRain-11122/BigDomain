"""refused_check_declaration_face suite (R2393; criteria AC-RCDF1..AC-RCDF6
were pre-registered inside the R2392 seed row of state/queue/tech.md line 451
BEFORE this code existed).

What this proves: a refused `--check` now carries the declaration's own
declared_by instead of "-", so the JSON payload and the detail prose name one
boundary. The head is derived by the new module from residue_triage's own
loader, nothing is aged on that path (so a declaration whose entries would
raise a different triage code still reports the SAME refusal code), the
successful check payload and every --append line stay byte-identical, exits
stay 0/2/3/5 with the pinned key order, and the module is pure ASCII, stdlib
only, read-only, with its own reconcile label.

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

import refused_check_declaration_face as RCDF  # noqa: E402
import residue_triage as RT  # noqa: E402
import residue_triage_append as RA  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "refused_check_declaration_face.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-refused-check-declaration-face"

HEADER = "queue header\n"
TECH = "- [x] [done 2026-11-01 R9001] a closed row delivered by the fixture\n"
LOG_ITEMS = ["2026-11-01 R8900 a prior round in the fixture world"]

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


def make_world(entries=None, declared_by=2335, tech=TECH,
               log_items=LOG_ITEMS):
    world = tempfile.mkdtemp(prefix="bigdomain-rcdf-")
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


def run_cli(world, args):
    proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "residue_triage_append.py")]
        + args + ["--root", world],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return (proc.returncode, out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


class Patched(object):
    """Swap one callable for the duration of one criterion."""

    def __init__(self, owner, name, value):
        self.owner = owner
        self.name = name
        self.value = value
        self.saved = None

    def __enter__(self):
        self.saved = getattr(self.owner, self.name)
        setattr(self.owner, self.name, self.value)
        return self

    def __exit__(self, *exc):
        setattr(self.owner, self.name, self.saved)
        return False


def refusal(call):
    try:
        call()
    except RA.ResidueTriageAppendError as exc:
        return exc.code, exc.detail, exc.status, exc.round, exc.declared_by
    return None, "", None, None, None


def ac_rcdf1():
    """The payload's declared_by IS the loader's reading, patched and moved.

    The asked round sits BELOW both heads, so the refusal is the same
    E_RTA_UNREADABLE both times and only the boundary moves.
    """
    world = make_world(entries=[], declared_by=9400)
    try:
        straight = refusal(lambda: RA.check(world, "R3000"))

        def moved(root):
            return {"declared_by": 7777, "reason": "patched", "entries": [],
                    "until": 9999}

        with Patched(RT, "load_declaration", moved):
            patched = refusal(lambda: RA.check(world, "R3000"))
        direct = RCDF.head(world)
        ok = (straight[0] == "E_RTA_UNREADABLE"
              and straight[4] == "R9400"
              and patched[0] == "E_RTA_UNREADABLE"
              and patched[4] == "R7777"
              and direct == "R9400")
        if not ok:
            print("  measured: straight=%r patched=%r direct=%r"
                  % (straight, patched, direct), flush=True)
        check(ok, "AC-RCDF1 declared_by comes from the loader, patch moves it")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rcdf2():
    """The unknown stays '-' and the refusal code does not move.

    Disclosed wording correction, measured not assumed: a MISSING declaration
    does not reach a refusal at all on the --check path - it reads
    verdict=RESIDUE with declaration=UNPINNED at exit 2, because the status
    face still answers. The case where the refusal really IS
    E_RTA_UNREADABLE is an unreadable (malformed) declaration, and that is
    what this leg pins, together with the missing-file reading staying at "-"
    and NOT being dressed up as a refusal.
    """
    world_missing = make_world(entries=None)
    world_bad = make_world(entries=[entry(9001)])
    bad_path = os.path.join(world_bad, "state", "residue_triage.json")
    try:
        rc_missing, body_missing, _err = run_cli(
            world_missing, ["--check", "--round", "R9001"])
        rc_missing_json, json_missing, _err = run_cli(
            world_missing, ["--check", "--round", "R9001", "--json"])
        with io.open(bad_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("{ this is not the pinned shape }\n")
        rc_bad, body_bad, _err = run_cli(world_bad, ["--check", "--round",
                                                     "R9001"])
        rc_bad_json, json_bad, _err = run_cli(world_bad, ["--check", "--round",
                                                         "R9001", "--json"])
        parsed_missing = json.loads(json_missing)
        parsed_bad = json.loads(json_bad)
        ok = (rc_missing == 2 and "UNPINNED" in body_missing
              and rc_missing_json == 2
              and parsed_missing["declared_by"] == "-"
              and parsed_missing["declaration"] == "UNPINNED"
              and rc_bad == 3 and "E_RTA_UNREADABLE" in body_bad
              and rc_bad_json == 3
              and parsed_bad["declared_by"] == "-"
              and parsed_bad["verdict"] == "E_RTA_UNREADABLE"
              and RCDF.head(world_bad) == "-")
        if not ok:
            print("  measured: missing=%r/%r bad=%r/%r head_bad=%r"
                  % (rc_missing, parsed_missing, rc_bad, parsed_bad,
                     RCDF.head(world_bad)), flush=True)
        check(ok, "AC-RCDF2 an unreadable declaration keeps '-' and its code")
    finally:
        shutil.rmtree(world_missing, ignore_errors=True)
        shutil.rmtree(world_bad, ignore_errors=True)


def ac_rcdf3():
    """Nothing is AGED by the added derivation: the refusal code cannot move.

    The shipped check still ages through append_check_status_precedence's own
    read - that is how it refuses at all. What this criterion pins is that the
    NEW derivation adds no second aging pass: the module source carries no
    aging call, the head is readable while the aging reader is broken, and a
    declaration whose entries would raise a different triage code reports the
    SAME refusal code as the pre-wire path.
    """
    # A valid declaration whose head sits AHEAD of the asked round, so the
    # shipped read refuses; the head must still be readable with the aging
    # reader broken, and the reported code must equal the pre-wire code.
    world = make_world(entries=[entry(9001)], declared_by=9400)
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_aging = ("RT.read" not in source
                and "live_residue" not in source
                and "judge" not in source)
    try:
        straight = refusal(lambda: RA.check(world, "R9001"))
        with Patched(RCDF, "head", lambda root: "-"):
            pre_wire = refusal(lambda: RA.check(world, "R9001"))
        with Patched(RT, "read",
                     lambda *a, **k: (_ for _ in ()).throw(
                         AssertionError("the head derivation aged"))):
            head_under_broken_aging = RCDF.head(world)
        rc, body, _err = run_cli(world, ["--check", "--round", "R9001"])
        ok = (no_aging
              and straight[0] == "E_RTA_UNREADABLE"
              and pre_wire[0] == straight[0]
              and head_under_broken_aging == "R9400"
              and rc == 3 and "E_RTA_UNREADABLE" in body
              and straight[4] == "R9400")
        if not ok:
            print("  measured: no_aging=%r straight=%r pre_wire=%r head=%r "
                  "rc=%r" % (no_aging, straight, pre_wire,
                             head_under_broken_aging, rc), flush=True)
        check(ok, "AC-RCDF3 the aging step is never run by the added derivation")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rcdf4():
    """The successful check payload and every --append line stay identical."""
    world_ok = make_world(entries=[entry(9001)])
    world_dup = make_world(entries=[entry(9002)])
    try:
        rc_ok, ok_body, _err = run_cli(world_ok, ["--check", "--round",
                                                  "R9001"])
        rc_json, json_body, _err = run_cli(world_ok, ["--check", "--round",
                                                      "R9001", "--json"])
        parsed = json.loads(json_body)
        expected_append = ("E_RTA_DUPLICATE\n"
                           "  R9002 is already declared status=DELIVERED"
                           " declared_by=R2335 until=R9900\n")
        rc_dup, dup_body, _err = run_cli(
            world_dup, ["--append", "--round", "R9002", "--status",
                        "DELIVERED", "--by", "R2393", "--reason", "probe",
                        "--until", "R2400"])
        ok = (rc_ok == 0 and "declared_by=R2335" in ok_body
              and rc_json == 0 and parsed["declared_by"] == "R2335"
              and parsed["verdict"] == "TRIAGED"
              and rc_dup == 2
              and dup_body.replace("\r\n", "\n") == expected_append)
        if not ok:
            print("  measured: ok=%r json=%r dup=%r"
                  % (ok_body, parsed, dup_body), flush=True)
        check(ok, "AC-RCDF4 success payload and append lines byte-identical")
    finally:
        shutil.rmtree(world_ok, ignore_errors=True)
        shutil.rmtree(world_dup, ignore_errors=True)


def ac_rcdf5():
    """Exits stay 0/2/3/5 with the pinned key order on every face."""
    world_ok = make_world(entries=[entry(9001)])
    world_dup = make_world(entries=[entry(9002)])
    world_ref = make_world(entries=[], declared_by=9400)
    try:
        rc_zero, _b, _e = run_cli(world_ok, ["--check", "--round", "R9001"])
        rc_two, _b, _e = run_cli(world_dup, ["--append", "--round", "R9002",
                                             "--status", "DELIVERED",
                                             "--by", "R2393", "--reason",
                                             "dup", "--until", "R2400"])
        rc_three, _b, _e = run_cli(world_ref, ["--check", "--round", "R9001"])
        rc_five, _b, _e = run_cli(world_ok, ["--check"])
        rc_a, body_a, _e = run_cli(world_ref, ["--check", "--round", "R9001",
                                               "--json"])
        rc_b, body_b, _e = run_cli(world_ref, ["--check", "--round", "R9001",
                                               "--json"])
        parsed = json.loads(body_a)
        ok = (rc_zero == 0 and rc_two == 2 and rc_three == 3 and rc_five == 5
              and rc_a == 3 and body_a == body_b
              and tuple(parsed.keys()) == RA.REPORT_KEYS
              and parsed["declared_by"] == "R9400")
        if not ok:
            print("  measured: rcs=%r keys=%r declared_by=%r"
                  % ((rc_zero, rc_two, rc_three, rc_five, rc_a),
                     tuple(parsed.keys()), parsed["declared_by"]), flush=True)
        check(ok, "AC-RCDF5 exits and key order unchanged, boundary named")
    finally:
        shutil.rmtree(world_ok, ignore_errors=True)
        shutil.rmtree(world_dup, ignore_errors=True)
        shutil.rmtree(world_ref, ignore_errors=True)


def ac_rcdf6():
    """Pure ASCII, stdlib only, read-only, wired with its own label."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(
        r"\b(?:import time|import datetime|time\.time)\b", source)
    imports = re.findall(r"^\s*import (\w+)", source, re.MULTILINE)
    stdlib_only = sorted(set(imports)) == ["residue_triage"]
    no_write = not re.search(r"(?:\bopen\(|os\.replace|os\.remove|unlink)",
                             source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_refused_check_declaration_face.py" in runner)
    own_label = source.count('SUITE_LABEL = "%s"' % LABEL) == 1
    ok = (ascii_only and no_net and no_clock and stdlib_only and no_write
          and wired and own_label)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r imports=%r write=%r "
              "wired=%r label=%r" % (ascii_only, no_net, no_clock,
                                     sorted(set(imports)), no_write, wired,
                                     own_label), flush=True)
    check(ok, "AC-RCDF6 pure, read-only, and wired with its own label")


def main():
    print("refused_check_declaration_face suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rcdf1()
    ac_rcdf2()
    ac_rcdf3()
    ac_rcdf4()
    ac_rcdf5()
    ac_rcdf6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())