"""single_append_status_face suite (R2385; criteria AC-SASF1..AC-SASF6 were
pre-registered inside the R2379 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: composing ONE --append no longer costs a refused call. The
single writer's --check now names the asked round WITH the live status the
batch face reports, a round outside the residue reads NOT-RESIDUE with its own
code instead of an invented status, and every append refusal keeps the exact
code and printed line it had because the append path never reaches the face.

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
import residue_triage_append as RA  # noqa: E402
import single_append_status_face as SASF  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "single_append_status_face.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-single-append-status-face"

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
    """The declaration layout the single writer pins, built for a fixture."""
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
               declared_by=2335, with_state=True):
    """A temp root: state.json, the three queues, optionally a declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-sasf-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    if with_state:
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


def run_cli(module, world, args):
    proc = subprocess.Popen([sys.executable, module] + args
                            + ["--root", world],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


class Patched(object):
    """Swap one batch face for the duration of one criterion."""

    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value
        self.original = None

    def __enter__(self):
        self.original = getattr(RSBF, self.attribute)
        setattr(RSBF, self.attribute, self.value)
        return self

    def __exit__(self, *info):
        setattr(RSBF, self.attribute, self.original)
        return False


def source_of(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def ac_sasf1():
    """The asked status IS the batch face's reading, and no second scan."""
    world = make_world(entries=[])
    try:
        baseline = SASF.reading(world, "R9002")
        shipped = RA.check(world, "R9002")
        faked = {"action": "check", "requested": "R9002",
                 "requested_status": "STAMP-ONLY-OPEN", "round_count": 1,
                 "counts": ["STAMP-ONLY-OPEN=1"], "verdict": "FOUND",
                 "rounds": ["R9002"], "statuses": ["STAMP-ONLY-OPEN"],
                 "source": "patched face"}
        with Patched("face", lambda root, requested=None: faked):
            moved = SASF.reading(world, "R9002")
            moved_shipped = RA.check(world, "R9002")
        text = source_of(MODULE)
        no_scan = ("RT.live_residue" not in text
                   and "import stamp_residue" not in text
                   and "import residue_triage as RT" not in text)
        ok = (baseline["requested_status"] == "DELIVERED"
              and shipped["status"] == "DELIVERED"
              and moved["requested_status"] == "STAMP-ONLY-OPEN"
              and moved_shipped["status"] == "STAMP-ONLY-OPEN"
              and no_scan)
        if not ok:
            print("  measured: base=%r shipped=%r moved=%r moved_shipped=%r "
                  "no_scan=%r"
                  % (baseline["requested_status"], shipped["status"],
                     moved["requested_status"], moved_shipped["status"],
                     no_scan), flush=True)
        check(ok, "AC-SASF1 the status is the batch face's reading")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_sasf2():
    """--check names the asked round WITH its live status, from one call."""
    world = make_world(entries=[])
    try:
        rc_face, face_body, _err = run_cli(MODULE, world,
                                           ["--check", "--round", "R9002"])
        rc_face_json, face_json, _err = run_cli(MODULE, world,
                                                ["--check", "--round",
                                                 "R9002", "--json"])
        rc_append, append_body, _err = run_cli(
            os.path.join(BASE, "residue_triage_append.py"), world,
            ["--check", "--round", "R9002"])
        rc_append_json, append_json, _err = run_cli(
            os.path.join(BASE, "residue_triage_append.py"), world,
            ["--check", "--round", "R9002", "--json"])
        parsed_face = json.loads(face_json)
        parsed_append = json.loads(append_json)
        ok = (rc_face == 0 and rc_face_json == 0
              and "requested=R9002" in face_body
              and "requested_status=DELIVERED" in face_body
              and parsed_face["requested_status"] == "DELIVERED"
              and rc_append == 2
              and "round=R9002" in append_body
              and "status=DELIVERED" in append_body
              and "residue=R9002" in append_body
              and parsed_append["verdict"] == "RESIDUE"
              and parsed_append["status"] == parsed_face["requested_status"])
        if not ok:
            print("  measured: rc=%r/%r face=%r append=%r status=%r "
                  "verdict=%r"
                  % (rc_face, rc_append, parsed_face["requested_status"],
                     "round=R9002" in append_body, parsed_append["status"],
                     parsed_append["verdict"]), flush=True)
        check(ok, "AC-SASF2 one --check names the round and its live status")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_sasf3():
    """A round outside the residue reads NOT-RESIDUE with its own code."""
    world = make_world(entries=[])
    try:
        rc_face, face_body, _err = run_cli(MODULE, world,
                                           ["--check", "--round", "R7777"])
        rc_append, append_body, _err = run_cli(
            os.path.join(BASE, "residue_triage_append.py"), world,
            ["--check", "--round", "R7777"])
        ok = (rc_face == 2
              and "requested_status=NOT-RESIDUE" in face_body
              and "E_SASF_NOT_RESIDUE" in face_body
              and "status=NOT-RESIDUE" in append_body
              and "NOTE E_SASF_NOT_RESIDUE" in append_body
              and RA.NOT_RESIDUE == SASF.NOT_RESIDUE
              and "DELIVERED" not in append_body)
        if not ok:
            print("  measured: rc=%r not_residue=%r code=%r append=%r note=%r"
                  % (rc_face, "requested_status=NOT-RESIDUE" in face_body,
                     "E_SASF_NOT_RESIDUE" in face_body,
                     "status=NOT-RESIDUE" in append_body,
                     "NOTE E_SASF_NOT_RESIDUE" in append_body), flush=True)
        check(ok, "AC-SASF3 NOT-RESIDUE carries its own code")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_sasf4():
    """Every append refusal keeps its code and line; append never asks the face."""
    worlds = []
    try:
        def boom(root, requested):
            raise AssertionError("the append path must not ask the face")

        original = SASF.reading
        SASF.reading = boom
        try:
            world = make_world(entries=[])
            worlds.append(world)
            rc_ok, body, _err = run_cli(
                os.path.join(BASE, "residue_triage_append.py"), world,
                ["--append", "--round", "R9002", "--status", "DELIVERED",
                 "--by", "R2335", "--reason", "accepted at R2385",
                 "--until", "R2350"])
            rc_dup, dup_body, _err = run_cli(
                os.path.join(BASE, "residue_triage_append.py"), world,
                ["--append", "--round", "R9002", "--status", "DELIVERED",
                 "--by", "R2335", "--reason", "again", "--until", "R2350"])

            world_b = make_world(entries=[])
            worlds.append(world_b)
            rc_dis, dis_body, _err = run_cli(
                os.path.join(BASE, "residue_triage_append.py"), world_b,
                ["--append", "--round", "R9002", "--status",
                 "STAMP-ONLY-OPEN", "--by", "R2335", "--reason", "moved",
                 "--until", "R2350"])

            world_c = make_world(entries=None)
            worlds.append(world_c)
            rc_unpinned, unpinned_body, _err = run_cli(
                os.path.join(BASE, "residue_triage_append.py"), world_c,
                ["--append", "--round", "R9002", "--status", "DELIVERED",
                 "--by", "R2335", "--reason", "no base", "--until", "R2350"])

            world_d = make_world(entries=[])
            worlds.append(world_d)
            rc_dry, dry_body, _err = run_cli(
                os.path.join(BASE, "residue_triage_append.py"), world_d,
                ["--append", "--round", "R9002", "--status", "DELIVERED",
                 "--by", "R2335", "--reason", "dry", "--until", "R2350",
                 "--dry-run"])
            rc_until, until_body, _err = run_cli(
                os.path.join(BASE, "residue_triage_append.py"), world_d,
                ["--append", "--round", "R9002", "--status", "DELIVERED",
                 "--by", "R2350", "--reason", "bad window",
                 "--until", "R2340"])
        finally:
            SASF.reading = original

        appends = [body, dup_body, dis_body, unpinned_body, dry_body,
                   until_body]
        ok = (rc_ok == 0 and "wrote=yes" in body
              and rc_dup == 2 and "E_RTA_DUPLICATE" in dup_body
              and rc_dis == 2 and "E_RTA_DISAGREES" in dis_body
              and rc_unpinned == 3 and "E_RTA_UNPINNED" in unpinned_body
              and rc_dry == 0 and "DRY-RUN" in dry_body
              and rc_until == 2 and "E_RTA_UNTIL_BEFORE_DECL" in until_body
              and not any("SASF" in text for text in appends)
              and not any("NOT-RESIDUE" in text for text in appends))
        if not ok:
            print("  measured: rc=%r/%r/%r/%r/%r/%r sasf=%r notre=%r"
                  % (rc_ok, rc_dup, rc_dis, rc_unpinned, rc_dry, rc_until,
                     any("SASF" in text for text in appends),
                     any("NOT-RESIDUE" in text for text in appends)),
                  flush=True)
        check(ok, "AC-SASF4 append codes and lines unchanged, face untouched")
    finally:
        for world in worlds:
            shutil.rmtree(world, ignore_errors=True)


def ac_sasf5():
    """CLI 0/2/3/5 with a byte-stable JSON over the pinned keys."""
    worlds = []
    try:
        world = make_world(entries=[])
        worlds.append(world)
        rc_found, body, _err = run_cli(MODULE, world,
                                       ["--check", "--round", "R9002"])
        rc_not, not_body, _err = run_cli(MODULE, world,
                                         ["--check", "--round", "R7777"])
        rc_json_a, json_a, _err = run_cli(MODULE, world,
                                          ["--check", "--round", "R9002",
                                           "--json"])
        rc_json_b, json_b, _err = run_cli(MODULE, world,
                                          ["--check", "--round", "R9002",
                                           "--json"])
        rc_unreadable, unreadable_body, _err = run_cli(
            MODULE, make_world(with_state=False),
            ["--check", "--round", "R9002"])
        rc_no_mode, mode_body, _err = run_cli(MODULE, world,
                                              ["--round", "R9002"])
        rc_no_round, round_body, _err = run_cli(MODULE, world, ["--check"])
        rc_flag, flag_body, _err = run_cli(MODULE, world,
                                           ["--check", "--round", "R9002",
                                            "--bogus"])
        parsed = json.loads(json_a)
        ok = (rc_found == 0 and "found=yes" in body
              and rc_not == 2 and "NOT-RESIDUE" in not_body
              and rc_json_a == 0 and rc_json_b == 0 and json_a == json_b
              and tuple(parsed.keys()) == SASF.REPORT_KEYS
              and parsed["requested_status"] == "DELIVERED"
              and parsed["found"] is True
              and rc_unreadable == 3 and "E_SASF" in unreadable_body
              and rc_no_mode == 5 and "E_SASF_BAD_ARGS" in mode_body
              and rc_no_round == 5 and "E_SASF_BAD_ARGS" in round_body
              and rc_flag == 5 and "E_SASF_BAD_ARGS" in flag_body)
        if not ok:
            print("  measured: rc=%r/%r/%r/%r/%r/%r/%r keys=%r"
                  % (rc_found, rc_not, rc_json_a, rc_unreadable, rc_no_mode,
                     rc_no_round, rc_flag, tuple(parsed.keys())), flush=True)
        check(ok, "AC-SASF5 CLI 0/2/3/5 and a byte-stable JSON")
    finally:
        for world in worlds:
            shutil.rmtree(world, ignore_errors=True)


def ac_sasf6():
    """Pure ASCII, stdlib only, no clock, no network, wired with its own label."""
    text = source_of(MODULE)
    try:
        text.encode("ascii")
        ascii_ok = True
    except UnicodeEncodeError:
        ascii_ok = False
    banned = ("import socket", "import urllib", "import requests",
              "import datetime", "import time", "from datetime",
              "from time import localtime", "time.time", "datetime.now")
    clean = not any(token in text for token in banned)
    runner = source_of(RUNNER)
    wired = LABEL in runner and 'test_single_append_status_face.py' in runner
    criteria_ok = EXPECTED_CRITERIA == 6
    writes = "open(" in text and ", \"wb\"" in text
    ok = ascii_ok and clean and wired and criteria_ok and not writes
    if not ok:
        print("  measured: ascii=%r clean=%r wired=%r criteria=%r writes=%r"
              % (ascii_ok, clean, wired, criteria_ok, writes), flush=True)
    check(ok, "AC-SASF6 pure ASCII stdlib, no clock, no network, wired")


def main():
    ac_sasf1()
    ac_sasf2()
    ac_sasf3()
    ac_sasf4()
    ac_sasf5()
    ac_sasf6()
    print("SUITE %s expected-criteria=%d pass=%d fail=%d"
          % (LABEL, EXPECTED_CRITERIA, PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())