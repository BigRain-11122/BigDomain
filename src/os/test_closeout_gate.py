"""Battery suite for tools/closeout_gate.py - criteria AC-CLG1..AC-CLG5 (R2932).

WHY: the R2926 commit hook refuses STAGED evidence bytes only, so an
uncommitted shell-captured write still reaches disk and no gate has ever
refused it. The board asked for a closeout precondition AND for the face it
grades to be pinned, "because a precondition nobody has seen refuse is not a
precondition".

This suite grades both questions on fixture worlds:
  AC-CLG1  the live tree passes, and the gate's numbers are derived (file count
           from the directory, not typed)
  AC-CLG2  a NEW non-tee write is REFUSED by name (the red control)
  AC-CLG3  reader_refused ALONE does not refuse - flags is the gating face
  AC-CLG4  the gate is read-only and deterministic
  AC-CLG5  a missing baseline, an empty dir, and a census row that cannot be
           read are each a NAMED refusal, never a silent pass

Honest boundary: `flags` sees a new file or a class change; a rewrite that
stays inside the same class is invisible to both faces (the census keeps no
hashes), and that is why the gate is a precondition, not a jail.

Source discipline: pure ASCII, stdlib only, no clock, no network, writes only
inside its own temp fixture worlds.
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import closeout_gate as CG
import qa_writer_census as CENSUS

FAILS = []
CHECKS = []


def ok(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print("  | PASS %s %s" % (name, detail))
    else:
        FAILS.append(name)
        print("  | FAIL %s %s" % (name, detail))


def write_bytes(path, payload):
    with open(path, "wb") as fh:
        fh.write(payload)


def build_world(tmp):
    """A frozen world (tee + cmd-raw baselined) and its baseline path."""
    world = os.path.join(tmp, "world")
    os.makedirs(world)
    write_bytes(os.path.join(world, "healthy.log"), b"PASS suite row\n")
    write_bytes(os.path.join(world, "old-capture.log"),
                u"AI \u5224\u5b9a".encode("gbk") + b"\r\n")
    base = os.path.join(world, CENSUS.BASELINE_NAME)
    _lines, code, _base = CENSUS.write_baseline(world, base)
    if code != 0:
        raise RuntimeError("fixture baseline freeze failed rc=%d" % code)
    return world, base


def snapshot(world):
    rows = {}
    for name in sorted(os.listdir(world)):
        path = os.path.join(world, name)
        with open(path, "rb") as fh:
            raw = fh.read()
        rows[name] = (len(raw), raw, os.stat(path).st_mtime_ns)
    return rows


def main():
    # AC-CLG1: the live tree passes, and the count is read off the directory.
    live = os.path.join(ROOT, "qa")
    live_base = os.path.join(live, CENSUS.BASELINE_NAME)
    lines, code, verdict = CG.evaluate(live, live_base)
    disk_logs = len([n for n in os.listdir(live) if n.endswith(".log")])
    ok("AC-CLG1 live tree PASSES the closeout gate", code == 0,
       "rc=%d line=%s" % (code, lines[0] if lines else ""))
    ok("AC-CLG1 reported file count equals the directory, not a typed number",
       verdict.get("files") == disk_logs,
       "reported=%s disk=%d" % (verdict.get("files"), disk_logs))
    ok("AC-CLG1 gating face is flags", verdict.get("gating") == "flags"
       and verdict.get("flags") == 0,
       "gating=%s flags=%s" % (verdict.get("gating"), verdict.get("flags")))

    with tempfile.TemporaryDirectory() as tmp:
        # AC-CLG2: THE RED CONTROL - a new shell-captured file is refused.
        world, base = build_world(tmp)
        _l, clean_rc, clean_v = CG.evaluate(world, base)
        ok("AC-CLG2 frozen world passes before any leak",
           clean_rc == 0 and clean_v.get("flags") == 0,
           "rc=%d flags=%s" % (clean_rc, clean_v.get("flags")))
        leak = os.path.join(world, "this-round-leak.log")
        write_bytes(leak, u"AI \u5224\u5b9a".encode("gbk") + b"\r\nPASS x\r\n")
        leak_lines, leak_rc, leak_v = CG.evaluate(world, base)
        ok("AC-CLG2 a new non-tee write is REFUSED (the precondition fires)",
           leak_rc == 2 and leak_v.get("reason") == "E_CLG_DRIFT",
           "rc=%d reason=%s" % (leak_rc, leak_v.get("reason")))
        ok("AC-CLG2 the refusal NAMES the leaking file",
           any("this-round-leak.log" in line for line in leak_lines),
           "named=%s" % [l for l in leak_lines if "this-round-leak" in l])
        os.remove(leak)
        back_lines, back_rc, _back_v = CG.evaluate(world, base)
        ok("AC-CLG2 removing the leak returns the gate to PASS",
           back_rc == 0 and back_lines[0].startswith("CLOSEOUT-GATE PASS"),
           "rc=%d line=%s" % (back_rc, back_lines[0]))

        # AC-CLG3: the DECISION under test - reader_refused is informational.
        drown = os.path.join(tmp, "drown")
        os.makedirs(drown)
        # utf-8 BOM + invalid body: class=other (baselined), and no writer
        # family decodes it -> reader_refused=1 while nothing drifted.
        write_bytes(os.path.join(drown, "unreadable.log"),
                    b"\xef\xbb\xbf\xff\xff")
        drown_base = os.path.join(drown, CENSUS.BASELINE_NAME)
        _dl, drown_freeze, _db = CENSUS.write_baseline(drown, drown_base)
        d_lines, d_rc, d_v = CG.evaluate(drown, drown_base)
        ok("AC-CLG3 an undecodable BASELINED file counts reader_refused=1",
           d_v.get("reader_refused") == 1
           and any(l.startswith("[refuse-read] unreadable.log")
                   for l in d_lines),
           "reader_refused=%s" % d_v.get("reader_refused"))
        ok("AC-CLG3 reader_refused ALONE does not refuse the closeout",
           d_rc == 0 and d_v.get("verdict") == "PASS"
           and d_v.get("flags") == 0,
           "rc=%d verdict=%s flags=%s" % (d_rc, d_v.get("verdict"),
                                          d_v.get("flags")))

        # AC-CLG4: read-only and deterministic.
        before = snapshot(world)
        first, first_rc, _fv = CG.evaluate(world, base)
        second, second_rc, _sv = CG.evaluate(world, base)
        after = snapshot(world)
        ok("AC-CLG4 the gate writes nothing (bytes and mtimes unchanged)",
           before == after, "files=%d" % len(before))
        ok("AC-CLG4 two runs are byte-identical",
           (first, first_rc) == (second, second_rc), "rc=%d" % first_rc)

        # AC-CLG5: three named refusals, never a silent pass.
        missing = CG.evaluate(world, os.path.join(world, "no-such-baseline.json"))
        ok("AC-CLG5 a missing baseline is a NAMED refusal",
           missing[1] == 2 and "E_CLG_NO_BASELINE" in missing[0][0],
           "rc=%d line=%s" % (missing[1], missing[0][0]))
        empty = os.path.join(tmp, "empty")
        os.makedirs(empty)
        empty_base = os.path.join(empty, CENSUS.BASELINE_NAME)
        with open(empty_base, "w", encoding="utf-8") as fh:
            fh.write('{"cmd-raw": [], "pwsh-capture": [], "ps-utf16": [], '
                     '"nul-bytes": [], "other": []}\n')
        empty_run = CG.evaluate(empty, empty_base)
        ok("AC-CLG5 an empty evidence dir is a NAMED refusal",
           empty_run[1] == 2 and "E_CLG_EMPTY" in empty_run[0][0],
           "rc=%d line=%s" % (empty_run[1], empty_run[0][0]))
        real = CG.CENSUS.check_against_baseline

        def silent_row(_target, _baseline):
            return ["census: files=3 tee=3 baselined=0",
                    "reader_refused=0", "verdict: DRIFT-CLEAN"], 0

        try:
            CG.CENSUS.check_against_baseline = silent_row
            blind = CG.evaluate(world, base)
        finally:
            CG.CENSUS.check_against_baseline = real
        ok("AC-CLG5 a census row without flags= is REFUSED, not read as clean",
           blind[1] == 2 and "E_CLG_ROW" in blind[0][0],
           "rc=%d line=%s" % (blind[1], blind[0][0]))

    total = len(CHECKS)
    acs = set()
    for name in CHECKS:
        token = name.split(" ", 1)[0]
        for cut in range(len(token), 0, -1):
            if token[cut - 1].isdigit():
                acs.add(token[:cut])
                break
    print("suite: %d assertions over %d criteria" % (total, len(acs)))
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s" % (total - len(FAILS), total, FAILS))
        return 1
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
