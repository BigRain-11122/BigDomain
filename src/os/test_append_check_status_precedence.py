"""append_check_status_precedence suite (R2392; criteria AC-ACSP1..AC-ACSP6
were pre-registered inside the R2385 seed row of state/queue/tech.md line 449
BEFORE this code existed).

What this proves: `residue_triage_append.py --check` now asks the single-append
status face FIRST, so a round whose triage read refuses still prints its live
status and one NOTE line while the refusal keeps its own code and exit code.
The --append path never asks the face and its printed lines stay
byte-identical, the pinned --json keys carry the status on the refused path,
and the whole module is pure, ASCII, stdlib only, with its own reconcile label.

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

import append_check_status_precedence as ACSP  # noqa: E402
import residue_triage_append as RA  # noqa: E402
import single_append_status_face as SASF  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "append_check_status_precedence.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-append-check-status-precedence"

HEADER = "queue header\n"
TECH = "- [x] [done 2026-11-01 R9001] a closed row delivered by the fixture\n"
# R9001 is a closed queue row this log does NOT name, so state_seq reports it
# as queue_only and stamp_residue reads it DELIVERED - the live residue this
# suite drives.
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
    """A temp root: state.json, the three queues, optionally a declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-acsp-")
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
    proc = subprocess.Popen([sys.executable, os.path.join(BASE,
                                                          "residue_triage_append.py")]
                            + args + ["--root", world],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


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
    """Run one check call and return (code, detail, status, round)."""
    try:
        call()
    except RA.ResidueTriageAppendError as exc:
        return exc.code, exc.detail, exc.status, exc.round
    return None, "", None, None


def ac_acsp1():
    """The face is asked BEFORE the triage read, and no second scan exists."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_second_scan = ("live_residue" not in source
                      and "stamp_residue" not in source
                      and "open(" not in source)
    world = make_world(entries=[], declared_by=9400)
    try:
        straight = refusal(lambda: RA.check(world, "R9001"))
        patched_face = {"action": "check", "requested": "R9001",
                        "requested_status": "PATCHED-STATUS", "found": True,
                        "verdict": "FOUND", "round_count": 1,
                        "source": "patched"}
        with Patched(SASF, "reading",
                     lambda root, requested: patched_face):
            moved = refusal(lambda: RA.check(world, "R9001"))
        ok = (no_second_scan
              and straight[0] == "E_RTA_UNREADABLE"
              and straight[2] == "DELIVERED"
              and moved[0] == "E_RTA_UNREADABLE"
              and moved[2] == "PATCHED-STATUS"
              and moved[3] == "R9001")
        if not ok:
            print("  measured: no_scan=%r straight=%r moved=%r"
                  % (no_second_scan, straight, moved), flush=True)
        check(ok, "AC-ACSP1 the face decides the status on a refused read")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_acsp2():
    """A round below declared_by prints status beside the unchanged refusal."""
    world = make_world(entries=[], declared_by=9400)
    try:
        rc, body, _err = run_cli(world, ["--check", "--round", "R9001"])
        lines = [line for line in body.splitlines() if line.strip()]
        ok = (rc == 3
              and lines[0] == "E_RTA_UNREADABLE"
              and "E_RTR_DECL_FUTURE: declared_by R9400 is later than the "
                  "round being checked R9001" in lines[1]
              and lines[2] == "  STATUS R9001 DELIVERED"
              and lines[3].startswith("  NOTE E_ACSP_STATUS_ON_REFUSAL"))
        if not ok:
            print("  measured: rc=%r lines=%r" % (rc, lines), flush=True)
        check(ok, "AC-ACSP2 refused check names the live status at exit 3")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_acsp3():
    """A round outside the residue reads NOT-RESIDUE on the refused path."""
    world = make_world(entries=[], declared_by=99999)
    try:
        rc, body, _err = run_cli(world, ["--check", "--round", "R9999"])
        ok = (rc == 3
              and "STATUS R9999 NOT-RESIDUE" in body
              and "E_SASF_NOT_RESIDUE" in body
              and "E_ACSP_STATUS_ON_REFUSAL" not in body)
        if not ok:
            print("  measured: rc=%r body=%r" % (rc, body), flush=True)
        check(ok, "AC-ACSP3 NOT-RESIDUE stays distinguishable when refused")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_acsp4():
    """Append refusals stay byte-identical and never ask the face."""
    world = make_world(entries=[entry(9002)])
    world_b = make_world(entries=[])
    expected = ("E_RTA_DUPLICATE\n"
                "  R9002 is already declared status=DELIVERED declared_by"
                "=R2335 until=R9900\n")
    try:
        rc, body, _err = run_cli(world, ["--append", "--round", "R9002",
                                         "--status", "DELIVERED",
                                         "--by", "R2392",
                                         "--reason", "probe",
                                         "--until", "R2400"])
        clean = body.replace("\r\n", "\n") == expected
        loud = ("STATUS " in body or "NOTE " in body)

        def boom(root, requested):
            raise AssertionError("the --append path asked the face: %s"
                                 % requested)

        with Patched(ACSP, "asked", boom):
            rc_patched, body_patched, _err = run_cli(
                world, ["--append", "--round", "R9002",
                        "--status", "DELIVERED", "--by", "R2392",
                        "--reason", "probe", "--until", "R2400"])
            rc_ok, ok_body, _err = run_cli(
                world_b, ["--append", "--round", "R9001",
                          "--status", "DELIVERED", "--by", "R2392",
                          "--reason", "accepted", "--until", "R2400"])
        # Subprocesses import fresh modules, so the patch above proves the
        # source-level claim only inside this process; the in-process call is
        # what actually exercises the patched seam.
        in_process = None
        try:
            in_process = RA.main(
                ["--append", "--round", "R9002", "--status", "DELIVERED",
                 "--by", "R2392", "--reason", "probe", "--until",
                 "R2400", "--root", world])
        except AssertionError as exc:
            in_process = str(exc)
        ok = (rc == 2 and clean and not loud
              and rc_patched == 2
              and body_patched.replace("\r\n", "\n") == expected
              and rc_ok == 0 and "wrote=yes" in ok_body
              and in_process == 2)
        if not ok:
            print("  measured: rc=%r clean=%r loud=%r patched=%r ok=%r "
                  "in_process=%r" % (rc, clean, loud, rc_patched, rc_ok,
                                     in_process), flush=True)
        check(ok, "AC-ACSP4 append lines unchanged, the face never asked")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(world_b, ignore_errors=True)


def ac_acsp5():
    """Exits 0/2/3/5 and a byte-stable JSON carrying status when refused."""
    world_ok = make_world(entries=[entry(9001)])
    world_dup = make_world(entries=[entry(9002)])
    world_ref = make_world(entries=[], declared_by=9400)
    try:
        rc_zero, _body, _err = run_cli(world_ok, ["--check", "--round",
                                                  "R9001"])
        rc_two, _body, _err = run_cli(world_dup, ["--append", "--round",
                                                  "R9002", "--status",
                                                  "DELIVERED", "--by",
                                                  "R2392", "--reason", "dup",
                                                  "--until", "R2400"])
        rc_three, _body, _err = run_cli(world_ref, ["--check", "--round",
                                                    "R9001"])
        rc_five, _body, _err = run_cli(world_ok, ["--check"])
        rc_json_a, json_a, _err = run_cli(world_ref, ["--check", "--round",
                                                      "R9001", "--json"])
        rc_json_b, json_b, _err = run_cli(world_ref, ["--check", "--round",
                                                      "R9001", "--json"])
        parsed = json.loads(json_a)
        ok = (rc_zero == 0 and rc_two == 2 and rc_three == 3 and rc_five == 5
              and rc_json_a == 3 and json_a == json_b
              and tuple(parsed.keys()) == RA.REPORT_KEYS
              and parsed["status"] == "DELIVERED"
              and parsed["round"] == "R9001"
              and parsed["verdict"] == "E_RTA_UNREADABLE"
              and parsed["wrote"] is False)
        if not ok:
            print("  measured: rcs=%r json_eq=%r keys=%r status=%r verdict=%r"
                  % ((rc_zero, rc_two, rc_three, rc_five, rc_json_a),
                     json_a == json_b, tuple(parsed.keys()),
                     parsed["status"], parsed["verdict"]), flush=True)
        check(ok, "AC-ACSP5 exits unchanged, JSON carries the refused status")
    finally:
        for world in (world_ok, world_dup, world_ref):
            shutil.rmtree(world, ignore_errors=True)


def ac_acsp6():
    """Pure ASCII, stdlib only, no network, no clock, wired in the runner."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    imports = re.findall(r"^\s*import (\w+)", source, re.MULTILINE)
    stdlib_only = sorted(set(imports)) == ["residue_triage",
                                           "single_append_status_face"]
    no_write = not re.search(r"(?:\bopen\(|os\.replace|os\.remove|unlink)",
                             source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_append_check_status_precedence.py" in runner)
    own_label = source.count('SUITE_LABEL = "%s"' % LABEL) == 1
    ok = (ascii_only and no_net and no_clock and stdlib_only and no_write
          and wired and own_label)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r imports=%r write=%r "
              "wired=%r label=%r" % (ascii_only, no_net, no_clock,
                                     sorted(set(imports)), no_write, wired,
                                     own_label), flush=True)
    check(ok, "AC-ACSP6 pure, read-only, and wired with its own label")


def main():
    print("append_check_status_precedence suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_acsp1()
    ac_acsp2()
    ac_acsp3()
    ac_acsp4()
    ac_acsp5()
    ac_acsp6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())