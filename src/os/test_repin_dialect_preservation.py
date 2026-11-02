"""repin_dialect_preservation suite (R2406; criteria AC-RDPL1..AC-RDPL6 were
pre-registered inside the R2398 seed row of state/queue/tech.md line 478
BEFORE this code existed).

What this proves: the RE-RENDER writer now lands in the declaration's own
dialect instead of converting every line to LF, an LF declaration keeps
exactly today's bytes, the NOOP path still writes nothing, every refusal the
re-pin CLI already had is byte-identical to the HEAD module's own refusal, the
dialect is the shipped law's answer taken at call time, and the seam is pure
ASCII stdlib with its own reconcile label.

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

import declaration_writer_dialect_preservation as DWDP  # noqa: E402
import repin_dialect_preservation as RDPL  # noqa: E402
import repin_noop_eol_dialect as RNP  # noqa: E402
import residue_triage_append as RA  # noqa: E402
import residue_triage_repin as RTRP  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "repin_dialect_preservation.py")
REPIN = os.path.join(BASE, "residue_triage_repin.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-repin-dialect-preservation"

HEADER = "queue header\n"
TECH = ("- [x] [done 2026-11-01 R9001] a closed row delivered by the "
        "fixture\n"
        "- [x] [done 2026-11-01 R9002] a second closed row for the fixture\n"
        "- [ ] an open row so the fixture is not all closed\n")
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


def make_world(entries=None, dialect="LF", declared_by=2335):
    """A temp root: state.json, the three queues, the declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-rdpl-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    payload = {"tick": declared_by, "log": list(LOG_ITEMS)}
    with io.open(os.path.join(world, "src", "os", "state.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload))
    for name, body in (("tech", TECH), ("main", HEADER),
                       ("explore", HEADER)):
        with io.open(os.path.join(world, "state", "queue", name + ".md"),
                     "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    if entries is not None:
        text = decl_text(entries, declared_by)
        data = text.encode("utf-8")
        if dialect == "CRLF":
            data = text.replace("\n", "\r\n").encode("utf-8")
        with open(os.path.join(world, "state", "residue_triage.json"),
                  "wb") as handle:
            handle.write(data)
    return world


def declaration_path(world):
    return os.path.join(world, "state", "residue_triage.json")


def run_cli(script, world, args, extra_path=None):
    env = None
    if extra_path:
        env = dict(os.environ)
        env["PYTHONPATH"] = extra_path + os.pathsep + BASE
    proc = subprocess.Popen([sys.executable, script] + args
                            + ["--root", world],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env)
    out, err = proc.communicate()
    return (proc.returncode, out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


REPIN_OK = ["--round", "R9003", "--until", "R9010", "--reason",
            "fixture re-pin"]


def ac_rdpl1():
    """A re-pin of a CRLF declaration lands and the result is still CRLF."""
    world = make_world(entries=[entry(9001), entry(9002)], dialect="CRLF")
    try:
        path = declaration_path(world)
        rc, body, _err = run_cli(REPIN, world, REPIN_OK + ["--execute"])
        with open(path, "rb") as handle:
            after = handle.read()
        ok = (rc == 0
              and "PINNED" in body
              and RNP.dialect_of(after) == "CRLF"
              and after.count(b"\r\n") == after.count(b"\n")
              and after.count(b"\r") == after.count(b"\r\n")
              and b"\r\r\n" not in after
              and b'"round": 9001' in after
              and b'"round": 9002' in after
              and b'"declared_by": 9003' in after
              and not [name for name in os.listdir(os.path.dirname(path))
                       if ".tmp" in name])
        if not ok:
            print("  measured: rc=%r dialect=%r crlf=%d lf=%d cr=%d body=%r"
                  % (rc, RNP.dialect_of(after), after.count(b"\r\n"),
                     after.count(b"\n"), after.count(b"\r"), body[:300]),
                  flush=True)
        check(ok, "AC-RDPL1 a CRLF declaration is still CRLF after a re-pin")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rdpl2():
    """An LF declaration keeps today's bytes exactly."""
    world = make_world(entries=[entry(9001), entry(9002)], dialect="LF")
    try:
        path = declaration_path(world)
        with open(path, "rb") as handle:
            before = handle.read()
        planned = RTRP.build(world, "R9003", "R9010", "fixture re-pin")
        wanted = planned["_text"].encode("utf-8")
        rc, _body, _err = run_cli(REPIN, world, REPIN_OK + ["--execute"])
        with open(path, "rb") as handle:
            after = handle.read()
        ok = (rc == 0
              and planned["_payload"] == wanted
              and planned["predicted_bytes"] == len(wanted)
              and before != after
              and after == wanted
              and RNP.dialect_of(after) == "LF"
              and planned["_dialect"] == "LF")
        if not ok:
            print("  measured: rc=%r payload_is_lf=%r predicted=%r "
                  "equal=%r dialect=%r delta=%d"
                  % (rc, planned["_payload"] == wanted,
                     planned["predicted_bytes"], after == wanted,
                     RNP.dialect_of(after), len(after) - len(wanted)),
                  flush=True)
        check(ok, "AC-RDPL2 an LF declaration keeps today's bytes exactly")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rdpl3():
    """The NOOP path still writes nothing and creates no temp."""
    world = make_world(entries=[entry(9001), entry(9002)], dialect="LF")
    try:
        path = declaration_path(world)
        planned = RTRP.build(world, "R9003", "R9010", "fixture re-pin")
        with open(path, "wb") as handle:
            handle.write(planned["_payload"])
        with open(path, "rb") as handle:
            before = handle.read()
        report = RTRP.plan(world, "R9003", "R9010", "fixture re-pin",
                           execute=True)
        with open(path, "rb") as handle:
            after = handle.read()
        temps = [name for name in os.listdir(os.path.dirname(path))
                 if ".tmp" in name]
        ok = (report["verdict"] == "NOOP"
              and report["executed"] is False
              and after == before
              and temps == [])
        if not ok:
            print("  measured: verdict=%r executed=%r equal=%r temps=%r"
                  % (report["verdict"], report["executed"], after == before,
                     temps), flush=True)
        check(ok, "AC-RDPL3 the NOOP path writes nothing and leaves no temp")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rdpl4():
    """Every pre-existing refusal is byte-identical to the HEAD module's."""
    head_dir = tempfile.mkdtemp(prefix="bigdomain-rdpl-head-")
    world_unmatched = make_world(entries=[entry(9001), entry(9002),
                                          entry(9003)])
    world_future = make_world(entries=[entry(9001), entry(9002)],
                              declared_by=9500)
    try:
        proc = subprocess.Popen(
            ["git", "show", "HEAD:src/os/residue_triage_repin.py"],
            cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, _err = proc.communicate()
        same_source = proc.returncode == 0 and out
        if not same_source:
            check(False, "AC-RDPL4 refusal shapes unchanged against HEAD")
            print("  measured: git show HEAD failed rc=%r"
                  % proc.returncode, flush=True)
            return
        head_script = os.path.join(head_dir, "residue_triage_repin_head.py")
        with open(head_script, "wb") as handle:
            handle.write(out)
        cases = (
            REPIN_OK,
            ["--round", "R8800", "--until", "R9010", "--reason", "x"],
            ["--round", "R9003", "--until", "R8000", "--reason", "x"],
        )
        identical = True
        measured = []
        for args in cases:
            for world in (world_unmatched, world_future):
                now = run_cli(REPIN, world, args)
                was = run_cli(head_script, world, args, extra_path=head_dir)
                measured.append((args[:2], now[0], was[0],
                                 now[1] == was[1]))
                if now[0] != was[0] or now[1] != was[1]:
                    identical = False
        # the new refusal is the ONLY added one and it is over a MIXED file
        world_mixed = make_world(entries=[entry(9001), entry(9002)],
                                 dialect="LF")
        mixed_path = declaration_path(world_mixed)
        with open(mixed_path, "rb") as handle:
            raw = handle.read()
        with open(mixed_path, "wb") as handle:
            handle.write(raw.replace(b"\n", b"\r\n", 2))
        mixed_rc, mixed_body, _err = run_cli(REPIN, world_mixed,
                                             REPIN_OK + ["--execute"])
        with open(mixed_path, "rb") as handle:
            mixed_after = handle.read()
        shutil.rmtree(world_mixed, ignore_errors=True)
        mixed_ok = (mixed_rc == 2
                    and mixed_body.splitlines()[0] == "E_RDPL_MIXED"
                    and mixed_after == raw.replace(b"\n", b"\r\n", 2))
        ok = identical and mixed_ok
        if not ok:
            print("  measured: identical=%r cases=%r mixed=%r/%r"
                  % (identical, measured, mixed_rc,
                     mixed_body.splitlines()[:2]), flush=True)
        check(ok, "AC-RDPL4 refusal codes, exits and printed lines unchanged")
    finally:
        shutil.rmtree(head_dir, ignore_errors=True)
        shutil.rmtree(world_unmatched, ignore_errors=True)
        shutil.rmtree(world_future, ignore_errors=True)


def ac_rdpl5():
    """The dialect is the shared law's answer, asked at call time."""
    composed = '{\n  "a": 1\n}\n'
    raw_lf = composed.encode("utf-8")
    straight_name, straight = RDPL.resolve(raw_lf, composed)
    saved = RNP.dialect_of
    try:
        RNP.dialect_of = lambda data: "CRLF"
        patched_name, patched = RDPL.resolve(raw_lf, composed)
    finally:
        RNP.dialect_of = saved
    source = io.open(MODULE, "r", encoding="utf-8").read()
    asks_law = "DWDP.encode(" in source
    repin = io.open(REPIN, "r", encoding="utf-8").read()
    repin_asks = ("RDPL.payload_for(" in repin
                  and 'handle.write(report["_payload"])' in repin)
    no_second_law = ("dialect_of" not in repin
                     and 'replace("\\n", "\\r\\n")' not in repin)
    ok = (straight_name == "LF" and straight == raw_lf
          and patched_name == "CRLF"
          and patched == composed.replace("\n", "\r\n").encode("utf-8")
          and asks_law and repin_asks and no_second_law)
    if not ok:
        print("  measured: straight=%r patched=%r law=%r repin=%r "
              "second_law=%r" % ((straight_name, straight),
                                 (patched_name, patched), asks_law,
                                 repin_asks, no_second_law), flush=True)
    check(ok, "AC-RDPL5 the shared dialect law moves the re-pin too")


def ac_rdpl6():
    """Pure ASCII, stdlib only, no network, no clock, own reconcile label."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http\.client)\b", source)
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    imports = set(re.findall(r"^\s*import (\w+)", source, re.MULTILINE))
    stdlib_only = imports <= {"json", "sys",
                              "declaration_writer_dialect_preservation"}
    no_writer = ("os.replace(" not in source
                 and "def write_bytes" not in source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_repin_dialect_preservation.py" in runner)
    own_label = source.count('SUITE_LABEL = "%s"' % LABEL) == 1
    ok = (ascii_only and no_net and no_clock and stdlib_only and wired
          and own_label and no_writer)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r imports=%r wired=%r "
              "label=%r writer=%r" % (ascii_only, no_net, no_clock,
                                      sorted(imports), wired, own_label,
                                      no_writer), flush=True)
    check(ok, "AC-RDPL6 pure, stdlib only and wired with its own label")


def main():
    print("repin_dialect_preservation suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rdpl1()
    ac_rdpl2()
    ac_rdpl3()
    ac_rdpl4()
    ac_rdpl5()
    ac_rdpl6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())