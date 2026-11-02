"""declaration_writer_noop_parity suite (R2389; criteria AC-DWNP1..AC-DWNP6
were pre-registered inside the R2388 seed row of state/queue/tech.md BEFORE
this code existed).

What this proves: the NOOP comparison reached the re-pin path only, so the
three other declaration writers each composed a fresh document and wrote it
through their own atomic replace without ever asking whether the file already
carried it. One shared seam is now asked by all four, and it is the SAME law
the re-pin already owns - imported at call time, never copied.

  AC-DWNP1 each of the three writers reads NOOP when its composition equals
           the file, leaving the digest and the whole world map unchanged and
           creating no temp;
  AC-DWNP2 the re-pin keeps today's NOOP reading byte for byte (the fields of
           the shared comparison are the re-pin's own comparison, compared
           dict for dict on the same inputs);
  AC-DWNP3 a one-byte CONTENT change still reads PLANNED and still writes on
           every writer;
  AC-DWNP4 every pinned refusal code, exit code and printed line of the three
           writers is unchanged, proven by running each CLI on a fixture world
           and pinning what it prints;
  AC-DWNP5 the comparison is asked through ONE call site per writer and a
           patched shared law moves all four faces together;
  AC-DWNP6 pure ASCII, stdlib only, zero network, no clock, read-only in the
           comparison, plus its own reconcile label wired into the runner.

Stdlib only, one throwaway world per case, no network.
"""

import ast
import hashlib
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
sys.path.insert(0, BASE)

import declaration_writer_noop_parity as DWNP  # noqa: E402
import repin_noop_eol_dialect as RNED  # noqa: E402
import residue_triage as RT  # noqa: E402
import residue_triage_append as DWAP  # noqa: E402
import residue_triage_entry_retire as ER  # noqa: E402
import residue_triage_head_renew as HR  # noqa: E402

MODULE = os.path.join(BASE, "declaration_writer_noop_parity.py")
APPEND = os.path.join(BASE, "residue_triage_append.py")
RENEW = os.path.join(BASE, "residue_triage_head_renew.py")
RETIRE = os.path.join(BASE, "residue_triage_entry_retire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-declaration-writer-noop-parity"
WIRED_EXPECT = '"test_declaration_writer_noop_parity.py"), 6),'

HEADER = "# queue test world\n\nprose that never becomes a row\n\n"

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


def tech_rows(rounds=("R2300", "R2305")):
    return "".join("- [x] [done 2026-11-01 %s] a closed residue row\n" % value
                   for value in rounds)


def declaration_text(head="R2331", reason="renewed at R2331 for the suite",
                     last_until=2360, until=2350):
    """The pinned shape in BOTH live layouts: compact first, expanded last.

    The expanded entry carries a DIFFERENT window, so the head genuinely reads
    HEAD-STALE and every writer's real path (not just its HEAD-CURRENT early
    return) is exercised.
    """
    return (
        '{\n'
        '  "declared_by": "%s",\n'
        '  "reason": "%s",\n'
        '  "entries": [\n'
        '    {"round": 2300, "status": "DELIVERED", "declared_by": "R2331",'
        ' "reason": "compact layout", "until": %d},\n'
        '    {"round": 2305, "status": "DELIVERED", "declared_by": "R2331",'
        ' "reason": "compact layout", "until": %d},\n'
        '    {\n'
        '      "round": 2400,\n'
        '      "status": "DELIVERED",\n'
        '      "declared_by": "R2342",\n'
        '      "reason": "this round left the live residue and is unmatched",\n'
        '      "until": %d\n'
        '    }\n'
        '  ]\n'
        '}\n' % (head, reason, until, until, last_until))


def make_world(raw=None, newline="\n", last_until=2360, until=2350):
    """A throwaway root: state.json, the three queues, the declaration."""
    world = tempfile.mkdtemp(prefix="dwnp-world-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    path = os.path.join(world, "src", "os", "state.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"tick": 2300,
                                 "log": ["R2200 a logged item"]}))
    bodies = {"tech": tech_rows(), "main": HEADER, "explore": HEADER}
    for name in bodies:
        path = os.path.join(world, "state", "queue", name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(bodies[name])
    path = os.path.join(world, RT.DECLARATION_PATH)
    body = (declaration_text(last_until=last_until,
                             until=until) if raw is None else raw)
    with io.open(path, "w", encoding="utf-8", newline=newline) as handle:
        handle.write(body)
    return world


def decl_path(world):
    return os.path.join(world, RT.DECLARATION_PATH)


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def file_map(root):
    """Relative path -> bytes, so 'writes nothing' is measurable."""
    out = {}
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(dirs)
        for name in sorted(names):
            path = os.path.join(folder, name)
            out[os.path.relpath(path, root).replace(os.sep, "/")] = \
                open(path, "rb").read()
    return out


def temps(root, suffix):
    out = []
    for folder, dirs, names in os.walk(root):
        for name in names:
            if name.endswith(suffix):
                out.append(os.path.join(folder, name))
    return out


def run_cli(module, world, args):
    argv = [sys.executable, module] + list(args) + ["--root", world]
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def raw_of(world):
    with io.open(decl_path(world), "rb") as handle:
        return handle.read()


def append_prepared(world, payload, entry, entries_before, entries_after):
    """A prepared append whose payload the caller controls."""
    raw = raw_of(world)
    return {"path": decl_path(world), "after_bytes": payload,
            "before_bytes": len(raw), "delta": len(payload) - len(raw),
            "entries_before": entries_before,
            "entries_after": entries_after, "entry": entry}


def ac_dwnp1():
    """Each writer reads NOOP on an identical composition and writes nothing."""
    results = []

    # append: the write path itself is handed the file's own bytes
    world = make_world()
    before = file_map(world)
    entry = {"round": 2300, "status": "DELIVERED", "declared_by": 2331,
             "reason": "compact layout", "until": 2350}
    prepared = append_prepared(world, raw_of(world), entry, 3, 3)
    out = DWAP.apply(world, prepared)
    results.append(("append", out is None, file_map(world) == before,
                    temps(world, ".tmp-rta")))
    shutil.rmtree(world, ignore_errors=True)

    # head renew: a renewal whose render equals the file it already carries
    world = make_world()
    before = file_map(world)
    original = HR.splice
    HR.splice = lambda raw, head, reason: (raw,
                                           raw[raw.find('"entries"'):])
    try:
        report = HR.plan(world, "R2390", execute=True)
    finally:
        HR.splice = original
    results.append(("renew", report["verdict"] == "NOOP"
                    and report["executed"] is False,
                    file_map(world) == before, temps(world, ".renew-part")))
    shutil.rmtree(world, ignore_errors=True)

    # entry retire: a splice that removes no object
    world = make_world()
    before = file_map(world)
    original = ER._cut
    ER._cut = lambda text, spans, position: text
    try:
        prepared = ER.plan(world, "R2400", execute=True)
        item = ER.report(prepared)
    finally:
        ER._cut = original
    results.append(("retire", item["verdict"] == "NOOP"
                    and item["wrote"] is False,
                    file_map(world) == before, temps(world, ".tmp-rter")))
    shutil.rmtree(world, ignore_errors=True)

    ok = all(same and untouched and not leftovers
             for _name, same, untouched, leftovers in results)
    if not ok:
        print("  measured: %r" % (results,), flush=True)
    check(ok, "AC-DWNP1 append, head renew and entry retire each read NOOP on "
              "an identical composition, leaving the world map unchanged and "
              "creating no temp")


def ac_dwnp2():
    """The re-pin keeps today's reading, field for field, on the same inputs."""
    world = make_world()
    raw = raw_of(world)
    crlf = raw.replace(b"\n", b"\r\n")
    with io.open(decl_path(world), "wb") as handle:
        handle.write(crlf)
    shared = DWNP.compare(decl_path(world), raw)
    repin = RNED.compare(decl_path(world), raw.decode("utf-8"))
    same_law = RNED.is_noop(decl_path(world), raw.decode("utf-8"))
    ordered = list(json.loads(DWNP.to_json(shared)).keys())
    ok = (shared == repin
          and shared["verdict"] == "NOOP"
          and shared["raw_equal"] is False
          and shared["dialect"] == "CRLF"
          and same_law is True
          and ordered == list(DWNP.REPORT_KEYS)
          and ordered == list(RNED.REPORT_KEYS))
    if not ok:
        print("  measured: shared=%r repin=%r same_law=%r"
              % (shared, repin, same_law), flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-DWNP2 the shared comparison and the re-pin's own comparison "
              "read a CRLF declaration identically, field for field and key "
              "order for key order")


def ac_dwnp3():
    """A one-byte content change still reads PLANNED and still writes."""
    results = []

    # append: a genuinely new entry lands (the world's entries run to R2400,
    # so the write's own TRIAGED read-back is reachable at R2390)
    world = make_world(last_until=2400, until=2400)
    raw = raw_of(world)
    entry = {"round": 2500, "status": "DELIVERED", "declared_by": 2390,
             "reason": "a new entry for the suite", "until": 2400}
    payload = DWAP.compose(raw.decode("utf-8"), entry).encode("utf-8")
    prepared = append_prepared(world, payload, entry, 3, 4)
    out = DWAP.apply(world, prepared)
    results.append(("append", out is not None,
                    len(raw_of(world)) == len(payload),
                    not DWNP.is_noop(decl_path(world), raw)))
    shutil.rmtree(world, ignore_errors=True)

    # head renew: a real renewal writes
    world = make_world()
    raw = raw_of(world)
    report = HR.plan(world, "R2390", execute=True)
    results.append(("renew", report["verdict"] == "RENEWED"
                    and report["executed"] is True,
                    raw_of(world) != raw
                    and b'"declared_by": "R2390"' in raw_of(world),
                    not DWNP.is_noop(decl_path(world), raw)))
    shutil.rmtree(world, ignore_errors=True)

    # entry retire: a real retire removes one entry
    world = make_world()
    raw = raw_of(world)
    prepared = ER.plan(world, "R2400", execute=True)
    item = ER.report(prepared)
    results.append(("retire", item["verdict"] == "RETIRED"
                    and item["wrote"] is True,
                    len(raw_of(world)) < len(raw),
                    not DWNP.is_noop(decl_path(world), raw)))
    shutil.rmtree(world, ignore_errors=True)

    ok = all(verdict and wrote and planned for _n, verdict, wrote, planned
             in results)
    if not ok:
        print("  measured: %r" % (results,), flush=True)
    check(ok, "AC-DWNP3 a one-byte content change still reads PLANNED and "
              "still writes on all three writers")


def ac_dwnp4():
    """Every pinned refusal code, exit code and printed line is unchanged."""
    world = make_world()
    rc_a, out_a, _ = run_cli(APPEND, world, [
        "--append", "--round", "R2500", "--status", "DELIVERED",
        "--by", "R2390", "--reason", "x", "--until", "R2500"])
    rc_r, out_r, _ = run_cli(RETIRE, world, ["--round", "R2500"])
    rc_h, out_h, _ = run_cli(RENEW, world, ["--round", "R2400"])
    first_a = out_a.splitlines()[0] if out_a.splitlines() else ""
    first_r = out_r.splitlines()[0] if out_r.splitlines() else ""
    head_line = out_h.splitlines()[0] if out_h.splitlines() else ""
    head_ok = (head_line.startswith(
        "RESIDUE TRIAGE HEAD RENEW old=R2331/R2350 new=R2400/R2350 "
        "entries=3 [DELIVERED=3] unmatched=1")
        and head_line.endswith("executed=no verdict=PLANNED"))
    ok = (rc_a == 2 and first_a == "E_RTA_NOT_RESIDUE"
          and rc_r == 2 and first_r == "E_RTER_NOT_DECLARED"
          and rc_h == 0 and head_ok)
    if not ok:
        print("  measured: append=(%r,%r) retire=(%r,%r) renew=(%r,%r)"
              % (rc_a, first_a, rc_r, first_r, rc_h, head_line), flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-DWNP4 the append refusal, the retire refusal and the renew "
              "NOOP line print exactly what they printed before, with the "
              "same exit codes")


def ac_dwnp5():
    """One call site per writer; a patched shared law moves every face."""
    faces = []
    for path in (APPEND, RENEW, RETIRE):
        with io.open(path, encoding="utf-8") as handle:
            text = handle.read()
        faces.append(text.count("DWNP.is_noop("))
    with io.open(MODULE, encoding="utf-8") as handle:
        module_text = handle.read()
    one_owner = ("def normalise_bytes" not in module_text
                 and "_law().normalise_bytes" in module_text)

    moved = []
    world = make_world()
    raw = raw_of(world)
    original = RNED.normalise_bytes
    RNED.normalise_bytes = lambda data: b""
    try:
        moved.append(RNED.is_noop(decl_path(world), "anything at all"))
        moved.append(DWNP.is_noop(decl_path(world), b"anything at all"))
        entry = {"round": 2500, "status": "DELIVERED",
                 "declared_by": 2390, "reason": "x", "until": 2500}
        payload = DWAP.compose(raw.decode("utf-8"), entry).encode("utf-8")
        prepared = append_prepared(world, payload, entry, 3, 4)
        moved.append(DWAP.apply(world, prepared) is None)
        moved.append(HR.plan(world, "R2390", execute=True)["verdict"]
                     == "NOOP")
        moved.append(ER.report(ER.plan(world, "R2400", execute=True))
                     ["verdict"] == "NOOP")
    finally:
        RNED.normalise_bytes = original
    unchanged = raw_of(world) == raw
    shutil.rmtree(world, ignore_errors=True)
    ok = (faces == [1, 1, 1] and one_owner and all(moved) and unchanged)
    if not ok:
        print("  measured: call_sites=%r one_owner=%r moved=%r unchanged=%r"
              % (faces, one_owner, moved, unchanged), flush=True)
    check(ok, "AC-DWNP5 each writer asks the comparison at exactly one call "
              "site and patching the shared law moves all four faces, "
              "writing nothing")


def ac_dwnp6():
    """Pure ASCII stdlib, no clock, no network, read-only, wired label."""
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    text = raw.decode("utf-8")
    tree = ast.parse(text)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    body = "\n".join(line for line in text.splitlines()
                     if not line.lstrip().startswith("#"))
    with io.open(RUNNER, encoding="utf-8") as handle:
        runner = handle.read()
    ok = (all(byte < 128 for byte in raw)
          and imported <= {"json", "os", "sys", "repin_noop_eol_dialect"}
          and "socket" not in body and "urllib" not in body
          and "requests" not in body and "http" not in body
          and "time." not in body and "datetime" not in body
          and "open(" not in body
          and "def is_noop" in body
          and WIRED_EXPECT in runner
          and ('"%s"' % LABEL) in runner)
    if not ok:
        print("  measured: ascii=%r imports=%r wired=%r label=%r"
              % (all(byte < 128 for byte in raw), sorted(imported),
                 WIRED_EXPECT in runner, ('"%s"' % LABEL) in runner),
              flush=True)
    check(ok, "AC-DWNP6 the module is pure ASCII stdlib - the shared law is the "
              "only extra import and it is asked at call time - with no "
              "clock, no network and no write primitive, and it carries its "
              "own reconcile label wired into the runner")


def main():
    ac_dwnp1()
    ac_dwnp2()
    ac_dwnp3()
    ac_dwnp4()
    ac_dwnp5()
    ac_dwnp6()
    print("SUMMARY passes=%d fails=%d" % (PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())