"""retire_accept suite (R2333; criteria AC-RAC1..AC-RAC6 were pre-registered
inside the R2331 seed row of state/queue/tech.md BEFORE this code existed).

What this proves: an accepted retirement is now a RECORD rather than a hand
deletion. The per-script verdicts are imported from retire_candidate (patched
resolver flows straight through), every entry lands in exactly one of the four
pinned classes, an absent declaration refuses instead of fabricating a green,
and an executed append is one atomic replace proved by a read-back with every
other entry byte-identical. The module never deletes a script.

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

import retire_accept as RA  # noqa: E402
import retire_candidate as RC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "retire_accept.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-retire-accept"

EVIDENCE = "retire-world-9001.log"

# One copy that still performs the whole ritual, so a fixture world can carry
# a REAL RETIRE-READY row for the CLI legs (the resolver is not patched there).
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


def decl_text(entries):
    """The declaration shape this module writes, built for a fixture."""
    body = ",\n    ".join(json.dumps(entry, ensure_ascii=True,
                                     sort_keys=False) for entry in entries)
    if entries:
        return ('{\n  "declared_by": "R2333",\n  "entries": [\n    %s\n  ]\n}\n'
                % body)
    return '{\n  "declared_by": "R2333",\n  "entries": [\n  ]\n}\n'


def make_world(entries=None, round_no=2333, ritual=False):
    """A world with a declaration, a state counter and (optionally) a real
    RETIRE-READY copy, so the CLI legs read it through the live resolver."""
    root = tempfile.mkdtemp(prefix="retire-accept-")
    folder = os.path.join(root, "state", "queue")
    os.makedirs(folder)
    os.makedirs(os.path.join(root, "src", "os"))
    if ritual:
        with open(os.path.join(root, "src", "os", "evidence_R9001.py"), "wb") \
                as handle:
            handle.write(RITUAL.encode("utf-8"))
        qa = os.path.join(root, "qa")
        os.makedirs(qa)
        with open(os.path.join(qa, EVIDENCE), "wb") as handle:
            handle.write(b"evidence body\n")
    if entries is not None:
        path = os.path.join(folder, "retire_accept.json")
        with open(path, "wb") as handle:
            handle.write(decl_text(entries).encode("utf-8"))
    state = {"tick": round_no - 1}
    with open(os.path.join(root, RA.STATE_REL), "wb") as handle:
        handle.write(json.dumps(state).encode("utf-8"))
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


def live(rows, ready=None):
    """A synthetic resolver report in retire_candidate's own shape."""
    names = [row["script"] for row in rows]
    return {"rows": rows, "scripts": len(names),
            "retire_ready": (len(names) if ready is None else ready),
            "owned": 0, "stale": 0, "parity_debt": 0, "collision": 0,
            "audit_verdict": "CLEAN", "map_verdict": "CLEAN",
            "parity_verdict": "ALL-PRESENT", "verdict": "CANDIDATES"}


def ready_row(name):
    return {"script": name, "verdict": RC.READY, "reason": "", "detail": ""}


def owned_row(name, reason="PARITY-DEBT", detail="single-writer missing=x"):
    return {"script": name, "verdict": RC.OWNED, "reason": reason,
            "detail": detail}


class Patched(object):
    """Swap RC.resolve for the duration of one criterion."""

    def __init__(self, report):
        self.report = report

    def __enter__(self):
        self.saved = RC.resolve
        RC.resolve = lambda *a, **k: self.report
        return self

    def __exit__(self, *exc):
        RC.resolve = self.saved
        return False


def run_cli(world, args):
    """The module as a program, from a world it was pointed at."""
    proc = subprocess.Popen([sys.executable, MODULE] + args + ["--root", world],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def ac_rac1():
    """The verdicts are imported; a patched resolver flows straight through."""
    entry = {"script": "src/os/evidence_R9001.py", "declared": "R2333",
             "reason": "superseded", "until": "R2400"}
    worlds = []
    try:
        world = make_world([entry])
        worlds.append(world)
        source = io.open(MODULE, "r", encoding="utf-8").read()
        no_second_wheel = ("import evidence_output_audit" not in source
                           and "import evidence_output_map" not in source
                           and "import evidence_parity" not in source
                           and "import retire_candidate" in source)
        with Patched(live([ready_row("src/os\\evidence_R9001.py")])):
            clean = RA.check(world, 2333)
        with Patched(live([owned_row("src/os\\evidence_R9001.py")])):
            stale = RA.check(world, 2333)
        with Patched(live([])):
            gone = RA.check(world, 2333)
        ok = (no_second_wheel
              and clean["rows"][0]["class"] == RA.ACCEPTED
              and clean["rows"][0]["live_verdict"] == RC.READY
              and stale["rows"][0]["class"] == RA.STALE
              and gone["rows"][0]["class"] == RA.UNMATCHED)
        if not ok:
            print("  measured: wheel=%r classes=%r/%r/%r"
                  % (no_second_wheel, clean["rows"][0]["class"],
                     stale["rows"][0]["class"], gone["rows"][0]["class"]),
                  flush=True)
        check(ok, "AC-RAC1 verdicts imported, each patch moving the class")
    finally:
        for world in worlds:
            shutil.rmtree(world, ignore_errors=True)


def ac_rac2():
    """Four disjoint classes; every entry lands in exactly one."""
    entries = [
        {"script": "src/os/evidence_R9001.py", "declared": "R2333",
         "reason": "accepted now", "until": "R2400"},
        {"script": "src/os/evidence_R9002.py", "declared": "R2333",
         "reason": "aged past its window", "until": "R2300"},
        {"script": "src/os/evidence_R9003.py", "declared": "R2333",
         "reason": "script vanished", "until": "R2400"},
        {"script": "src/os/evidence_R9004.py", "declared": "R2333",
         "reason": "blocker returned", "until": "R2400"},
    ]
    world = make_world(entries)
    try:
        report_rows = [
            ready_row("src/os\\evidence_R9001.py"),
            ready_row("src/os\\evidence_R9002.py"),
            ready_row("src/os\\evidence_R9004.py"),
            owned_row("src/os\\evidence_R9004.py"),
            ready_row("src/os\\evidence_R9005.py"),
        ]
        with Patched(live(report_rows)):
            report = RA.check(world, 2333)
        classes = [row["class"] for row in report["rows"]]
        exactly_one = (len(classes) == len(entries)
                       and sorted(set(classes)) == sorted(RA.CLASSES))
        disjoint = sum(1 for row in report["rows"]
                       if row["class"] not in RA.CLASSES) == 0
        counted = (report["entries"] == 4 and report["accepted"] == 1
                   and report["expired"] == 1 and report["unmatched"] == 1
                   and report["stale_decision"] == 1)
        names = dict((row["script"], row) for row in report["rows"])
        expired_names_until = ("R2300" in names["src/os/evidence_R9002.py"]
                               ["detail"])
        stale_names_reason = ("PARITY-DEBT" in names["src/os/evidence_R9004.py"]
                              ["detail"])
        expired_is_allowed = report["verdict"] == "DEFECTS"
        ok = (exactly_one and disjoint and counted and expired_names_until
              and stale_names_reason and expired_is_allowed
              and report["pending"] == 1
              and report["pending_scripts"] == ["src/os/evidence_R9005.py"])
        if not ok:
            print("  measured: classes=%r counts=%r/%r/%r/%r pending=%r"
                  % (classes, report["accepted"], report["expired"],
                     report["unmatched"], report["stale_decision"],
                     report["pending_scripts"]), flush=True)
        check(ok, "AC-RAC2 four disjoint classes, each naming its own fact")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rac3():
    """An absent declaration reads UNPINNED with the live candidate list."""
    world = make_world(None)
    cli_world = make_world(None, ritual=True)
    try:
        rows = [ready_row("src/os\\evidence_R9001.py"),
                ready_row("src/os\\evidence_R9002.py"),
                owned_row("src/os\\evidence_R9003.py")]
        with Patched(live(rows, ready=2)):
            report = RA.check(world, 2333)
        unpinned = (report["pinned"] is False
                    and report["verdict"] == "UNPINNED"
                    and report["entries"] == 0 and report["accepted"] == 0
                    and report["candidates"] == 2
                    and report["pending_scripts"] == ["src/os/evidence_R9001.py",
                                                     "src/os/evidence_R9002.py"])
        rc, body, _err = run_cli(cli_world, ["--round", "R2333"])
        cli_refuses = (rc == 2 and "UNPINNED" in body
                       and "PENDING src/os/evidence_R9001.py" in body
                       and "RETIRE-READY" not in body.split("PENDING")[0])
        ok = unpinned and cli_refuses
        if not ok:
            print("  measured: pinned=%r verdict=%r rc=%r pending=%r body=%r"
                  % (report["pinned"], report["verdict"], rc,
                     report["pending_scripts"], body[:200]), flush=True)
        check(ok, "AC-RAC3 absent declaration reads UNPINNED with candidates")
    finally:
        for world in (world, cli_world):
            shutil.rmtree(world, ignore_errors=True)


def ac_rac4():
    """Refusals before any byte; an executed accept keeps every other byte."""
    first = {"script": "src/os/evidence_R9001.py", "declared": "R2333",
             "reason": "already accepted", "until": "R2400"}
    world = make_world([first])
    try:
        path = os.path.join(world, RA.DECL_REL)
        before_text = io.open(path, "r", encoding="utf-8").read()
        before_bytes = len(before_text.encode("utf-8"))
        rows = [ready_row("src/os\\evidence_R9001.py"),
                ready_row("src/os\\evidence_R9002.py"),
                owned_row("src/os\\evidence_R9003.py")]
        with Patched(live(rows, ready=2)):
            dup_refused = until_refused = not_ready = None
            try:
                RA.accept(world, "src/os/evidence_R9001.py", "R2333", "again")
            except RA.RetireAcceptError as exc:
                dup_refused = exc.code
            try:
                RA.accept(world, "src/os/evidence_R9002.py", "R2340", "too old",
                          until="R2333")
            except RA.RetireAcceptError as exc:
                until_refused = exc.code
            try:
                RA.accept(world, "src/os/evidence_R9003.py", "R2333", "owned")
            except RA.RetireAcceptError as exc:
                not_ready = exc.code
            untouched = (io.open(path, "r", encoding="utf-8").read()
                         == before_text)
            dry = RA.accept(world, "src/os/evidence_R9002.py", "R2333",
                            "superseded by evidence_capture", until="R2400")
            still_dry = (io.open(path, "r", encoding="utf-8").read()
                         == before_text)
            report = RA.accept(world, "src/os/evidence_R9002.py", "R2333",
                               "superseded by evidence_capture", until="R2400",
                               execute=True)
        after_text = io.open(path, "r", encoding="utf-8").read()
        after_bytes = len(after_text.encode("utf-8"))
        residue = [name for name in os.listdir(os.path.dirname(path))
                   if name.endswith(RA.TEMP_SUFFIX)]
        kept = (after_text.startswith(before_text[:before_text.rfind("\n  ]")])
                and json.loads(after_text)["entries"][0] == first)
        ok = (dup_refused == "E_RAC_DUP" and until_refused == "E_RAC_UNTIL"
              and not_ready == "E_RAC_NOT_READY" and untouched
              and dry["wrote"] is False and still_dry
              and report["wrote"] is True and report["read_back_ok"] is True
              and after_bytes == report["predicted_bytes"]
              and after_bytes > before_bytes and kept and not residue
              and report["entry_count_before"] == 1
              and report["entry_count_after"] == 2)
        if not ok:
            print("  measured: refusals=%r/%r/%r untouched=%r dry=%r "
                  "bytes=%d->%d kept=%r residue=%r"
                  % (dup_refused, until_refused, not_ready, untouched,
                     still_dry, before_bytes, after_bytes, kept, residue),
                  flush=True)
        check(ok, "AC-RAC4 refuses first, then one atomic append keeps the rest")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rac5():
    """CLI 0 only when pinned and clean; 2 otherwise; 3 unreadable; 5 flags."""
    entry = {"script": "src/os/evidence_R9001.py", "declared": "R2333",
             "reason": "clean", "until": "R2400"}
    absent = {"script": "src/os/evidence_R9088.py", "declared": "R2333",
              "reason": "script vanished", "until": "R2400"}
    worlds = []
    try:
        # The CLI legs run the LIVE resolver (no patch), so the world carries
        # one copy that performs the whole ritual.
        clean_world = make_world([entry], ritual=True)
        worlds.append(clean_world)
        rc_ok, body, _e = run_cli(clean_world, ["--round", "R2333"])
        rc_a, json_a, _e = run_cli(clean_world, ["--round", "R2333", "--json"])
        rc_b, json_b, _e = run_cli(clean_world, ["--round", "R2333", "--json"])
        parsed = json.loads(json_a)

        defect_world = make_world([absent], ritual=True)
        worlds.append(defect_world)
        rc_defect, defect_body, _e = run_cli(defect_world, ["--round", "R2333"])

        expired_world = make_world([dict(entry, until="R2300")], ritual=True)
        worlds.append(expired_world)
        rc_expired, _b, _e = run_cli(expired_world, ["--round", "R2333"])

        broken_world = make_world(None, ritual=True)
        worlds.append(broken_world)
        broken = os.path.join(broken_world, RA.DECL_REL)
        with open(broken, "wb") as handle:
            handle.write(b"{ not json")
        rc_broken, _b, _e = run_cli(broken_world, ["--round", "R2333"])

        rc_flags, _b, _e = run_cli(clean_world, ["--bogus"])
        rc_round, _b, _e = run_cli(clean_world, ["--round", "2333"])
        ok = (rc_ok == 0 and rc_a == 0 and rc_b == 0 and json_a == json_b
              and tuple(parsed.keys())[:len(RA.REPORT_KEYS)] == RA.REPORT_KEYS
              and parsed["verdict"] == "PINNED" and parsed["accepted"] == 1
              and parsed["pinned"] is True
              and rc_defect == 2 and "UNMATCHED" in defect_body
              and rc_expired == 0 and rc_broken == 3 and rc_flags == 5
              and rc_round == 3 and "RETIRE ACCEPT" in body)
        if not ok:
            print("  measured: rc=%r/%r/%r/%r/%r/%r keys=%r verdict=%r acc=%r"
                  % (rc_ok, rc_defect, rc_expired, rc_broken, rc_flags,
                     rc_round, tuple(parsed.keys()), parsed.get("verdict"),
                     parsed.get("accepted")), flush=True)
        check(ok, "AC-RAC5 CLI 0/2/3/5 and a byte-stable JSON")
    finally:
        for world in worlds:
            shutil.rmtree(world, ignore_errors=True)


def ac_rac6():
    """Pure ASCII, stdlib only, no network, no clock, no script delete path."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    imports = re.findall(r"^import (\w+)", source, re.MULTILINE)
    stdlib_only = sorted(set(imports)) == ["io", "json", "os", "retire_candidate",
                                           "sys"]
    # The only removal in the module is its own temp file guard: a script or a
    # declaration can never be deleted by this module.
    removals = re.findall(r"os\.remove\(([^)]*)\)", source)
    no_delete = (not re.search(r"\b(?:unlink|rmtree|removedirs)\b", source)
                 and bool(removals)
                 and all(arg.strip() == "temp" for arg in removals))
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner and "test_retire_accept.py" in runner)
    ok = (ascii_only and no_net and no_clock and stdlib_only and no_delete
          and wired and "os.replace" in source)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r imports=%r delete=%r "
              "wired=%r" % (ascii_only, no_net, no_clock, sorted(set(imports)),
                            no_delete, wired), flush=True)
    check(ok, "AC-RAC6 pure, wired, and carries no script delete path")


def main():
    print("retire_accept suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rac1()
    ac_rac2()
    ac_rac3()
    ac_rac4()
    ac_rac5()
    ac_rac6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())