"""Battery suite for tools/closeout_gate.py - criteria AC-CLG1..AC-CLG8.

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
import ast
import io
import json
import os
import re
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


def MUTATE_FIRST_COUNT(text):
    """(text, changed): decrement the first totals row by one.

    The document is DERIVED, so its totals move every round; the arm derives
    its mutation from today's document instead of typing 734/5982, which is
    the stale-literal defect the R3093 census arms were repaired for.
    """
    match = re.search(r"^\| (\d+) \| (\d+) \|", text, re.M)
    if not match:
        return text, False
    new = "| %d | %s |" % (int(match.group(1)) - 1, match.group(2))
    return text.replace(match.group(0), new, 1), True


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


def build_root(tmp, dated=True):
    """A private repo ROOT for the R3093 faces: one log, one registry row, one pin.

    Shaped like the real root in the only three places the two faces read it,
    so the arms prove the wiring instead of a mock of it: src/os/state.json,
    a registry whose SUITES row names a fixture suite, and that fixture suite
    printing one parseable SUITE leaf.
    """
    os.makedirs(os.path.join(tmp, "src", "os"))
    os.makedirs(os.path.join(tmp, "src", "sandbox"))
    line = ("2026-11-20 R5001 PRODUCT: a fixture round main line" if dated
            else "R5001 PRODUCT: no date anchor on this line")
    with open(os.path.join(tmp, "src", "os", "state.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"log": [line]}) + "\n")
    with open(os.path.join(tmp, "src", "os", "fixture_suite.py"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write('print("SUITE PASS 1/1")\n')
    reg = os.path.join(tmp, "src", "sandbox", "reg.py")
    with open(reg, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('import os\nSUITES = [\n'
                 '    ("fixture-suite", os.path.join("..", "os", '
                 '"fixture_suite.py"), 1),\n]\n')
    pin = os.path.join(tmp, "src", "os", "census_pin.json")
    with open(pin, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('{"readable": ["fixture-suite"], "unparsed": [], '
                 '"silent": []}\n')
    return tmp, reg, pin


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

    # AC-CLG6 (R3093): the two laws a round could slip past are now asked by
    # THIS gate - opt-in through root, and the default face is unchanged.
    ok("AC-CLG6 arm a - the default face (root=None) is the shipped question",
       lines[0] == ("CLOSEOUT-GATE PASS files=%d flags=0 reader_refused=0 "
                    "gating=flags" % disk_logs)
       and "round_main=" not in lines[0]
       and "round_main" not in verdict,
       "line=%s" % lines[0])
    deep, deep_rc, deep_v = CG.evaluate(live, live_base, root=ROOT)
    ok("AC-CLG6 arm b - root=ROOT asks all three faces and PASS names them",
       deep_rc == 0
       and deep[0] == ("CLOSEOUT-GATE PASS files=%d flags=0 reader_refused=0 "
                       "gating=flags round_main=OK census=PASS "
                       "matrix=DOC-CURRENT" % disk_logs)
       and deep_v.get("round_main") == "OK"
       and deep_v.get("census") == "PASS"
       and deep_v.get("matrix") == "DOC-CURRENT",
       "rc=%d line=%s" % (deep_rc, deep[0] if deep else ""))

    with tempfile.TemporaryDirectory() as tmp2:
        root_ok, reg_ok, pin_ok = build_root(os.path.join(tmp2, "root-ok"))
        world2, base2 = build_world(os.path.join(tmp2, "ev2"))
        # arm e: the new faces are read-only and repeat byte-identically
        before2 = snapshot(world2)
        first2, first2_rc, first2_v = CG.evaluate(
            world2, base2, root=root_ok, registry=reg_ok, census_pin=pin_ok,
            matrix=False)
        second2, second2_rc, _s2v = CG.evaluate(
            world2, base2, root=root_ok, registry=reg_ok, census_pin=pin_ok,
            matrix=False)
        after2 = snapshot(world2)
        ok("AC-CLG6 arm e - the root faces write nothing and repeat exactly",
           before2 == after2 and (first2, first2_rc) == (second2, second2_rc)
           and first2_rc == 0 and first2_v.get("census") == "PASS",
           "rc=%d files=%d line=%s"
           % (first2_rc, len(before2), first2[0] if first2 else ""))
        # arm c: a round with no dated labelled main line is refused BY NAME
        root_undated, _ru, _pu = build_root(os.path.join(tmp2, "root-undated"),
                                            dated=False)
        u_lines, u_rc, u_v = CG.evaluate(world2, base2, root=root_undated)
        ok("AC-CLG6 arm c - an undated round is refused by E_CLG_ROUND_MAIN",
           u_rc == 2 and u_v.get("reason") == "E_CLG_ROUND_MAIN"
           and any(l.startswith("ROUND-MAIN FAIL E_RMS_NO_DATE")
                   for l in u_lines),
           "rc=%d lines=%s" % (u_rc, u_lines[:2]))
        # arm d: a registry row that was never re-pinned is refused BY NAME
        bad_pin = os.path.join(root_ok, "src", "os", "census_pin.json")
        with open(bad_pin, "w", encoding="utf-8", newline="\n") as fh:
            fh.write('{"readable": [], "unparsed": [], "silent": []}\n')
        c_lines, c_rc, c_v = CG.evaluate(world2, base2, root=root_ok,
                                        registry=reg_ok, census_pin=bad_pin)
        ok("AC-CLG6 arm d - an unpinned registry row is refused by E_CLG_CENSUS",
           c_rc == 2 and c_v.get("reason") == "E_CLG_CENSUS"
           and any(l.startswith("VERDICT FAIL") for l in c_lines),
           "rc=%d reason=%s" % (c_rc, c_v.get("reason")))
        # arm f: flags is asked FIRST - a drifted tree never reaches round-main
        write_bytes(os.path.join(world2, "late-leak.log"),
                    u"AI \u5224\u5b9a".encode("gbk") + b"\r\n")
        f_lines, f_rc, f_v = CG.evaluate(world2, base2, root=root_undated)
        ok("AC-CLG6 arm f - a drifted tree is refused as DRIFT, before round-main",
           f_rc == 2 and f_v.get("reason") == "E_CLG_DRIFT"
           and not any("ROUND-MAIN" in l for l in f_lines),
           "rc=%d reason=%s" % (f_rc, f_v.get("reason")))

    # AC-CLG7 (R3094): the DERIVED document is the third root face - the law
    # already shipped, but a round could close without asking it.
    ok("AC-CLG7 arm a - the default face carries no matrix token either",
       "matrix=" not in lines[0] and "matrix" not in verdict,
       "line=%s" % lines[0])
    ok("AC-CLG7 arm b - the live matrix face is green and named LAST",
       deep[0].endswith("matrix=DOC-CURRENT")
       and deep_v.get("matrix") == "DOC-CURRENT",
       "line=%s" % (deep[0] if deep else ""))

    live_doc = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")
    with open(live_doc, encoding="utf-8") as fh:
        doc_text = fh.read()
    stale_text, changed = MUTATE_FIRST_COUNT(doc_text)

    with tempfile.TemporaryDirectory() as tmp3:
        stale = os.path.join(tmp3, "stale.md")
        with open(stale, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(stale_text)
        w3, b3 = build_world(tmp3)
        write_bytes(os.path.join(w3, "late-leak.log"),
                    u"AI \u5224\u5b9a".encode("gbk") + b"\r\n")
        s_lines, s_rc, s_v = CG.evaluate(live, live_base, root=ROOT,
                                         matrix=stale)
        ok("AC-CLG7 arm c - a document that drifted from the registry is "
           "refused by E_CLG_MATRIX",
           changed and s_rc == 2 and s_v.get("reason") == "E_CLG_MATRIX"
           and any(("STALE" in l) or l.startswith("E_EDM") for l in s_lines),
           "changed=%s rc=%d reason=%s lines=%s"
           % (changed, s_rc, s_v.get("reason"), s_lines[:2]))
        gone = os.path.join(tmp3, "absent.md")
        a_lines, a_rc, a_v = CG.evaluate(live, live_base, root=ROOT,
                                         matrix=gone)
        ok("AC-CLG7 arm d - a missing document is a NAMED refusal, not a skip",
           a_rc == 2 and a_v.get("reason") == "E_CLG_MATRIX"
           and any(l.startswith("E_EDM_NO_DOC") for l in a_lines),
           "rc=%d lines=%s" % (a_rc, a_lines[:2]))
        # arm e: ordering - a census red is refused BEFORE the matrix is read,
        # so the newest face never runs behind a face that already refused.
        bad = os.path.join(tmp3, "pin.json")
        with open(bad, "w", encoding="utf-8", newline="\n") as fh:
            fh.write('{"readable": [], "unparsed": [], "silent": []}\n')
        o_lines, o_rc, o_v = CG.evaluate(w3, b3, root=ROOT, matrix=stale)
        ok("AC-CLG7 arm e - the matrix face is asked only after the bytes face",
           o_rc == 2 and o_v.get("reason") == "E_CLG_DRIFT"
           and "matrix" not in o_v,
           "rc=%d reason=%s" % (o_rc, o_v.get("reason")))
        # arm f: the face is read-only and repeatable on the live document.
        before_doc = (os.path.getsize(live_doc),
                      os.path.getmtime(live_doc))
        m1 = CG.check_matrix(ROOT)
        m2 = CG.check_matrix(ROOT)
        after_doc = (os.path.getsize(live_doc), os.path.getmtime(live_doc))
        ok("AC-CLG7 arm f - the matrix face writes nothing and repeats",
           m1 == m2 and m1[0] is True and before_doc == after_doc,
           "m1=%s m2=%s" % (m1, m2))

    # AC-CLG8 (R3097): the dry run grows a name for its own seconds. Each face
    # the gate asked publishes its wall time in the verdict (never on the line,
    # so no decision moves with a machine's speed), and the registry census
    # reads each suite source once instead of twice with the same result.
    ok("AC-CLG8 arm a - the default face carries no timing key",
       "face_ms" not in verdict, "keys=%s" % sorted(verdict))
    ms8 = deep_v.get("face_ms") or {}
    ok("AC-CLG8 arm b - root=ROOT publishes four named readings and the PASS "
       "line is byte-identical",
       sorted(ms8) == ["census", "flags", "matrix", "round_main"]
       and all(isinstance(v, float) and v >= 0.0 for v in ms8.values())
       and deep[0] == ("CLOSEOUT-GATE PASS files=%d flags=0 reader_refused=0 "
                       "gating=flags round_main=OK census=PASS "
                       "matrix=DOC-CURRENT" % disk_logs),
       "face_ms=%s" % ms8)
    ms2 = first2_v.get("face_ms") or {}
    ok("AC-CLG8 arm c - a named opt-out still publishes a reading",
       ms2.get("matrix") == 0.0
       and all(ms2.get(k) is not None
               for k in ("flags", "round_main", "census")),
       "face_ms=%s" % ms2)
    ok("AC-CLG8 arm d - a red census is still refused by the same name",
       c_v.get("reason") == "E_CLG_CENSUS"
       and (c_v.get("face_ms") or {}).get("census", 0.0) > 0.0,
       "reason=%s face_ms=%s" % (c_v.get("reason"), c_v.get("face_ms")))

    # arm e: one parse reads a real suite exactly as two parses did.
    import registry_counter_census as RC
    module8 = RC.reader()
    sandbox8 = os.path.dirname(RC.REGISTRY)
    rows8 = RC.registry_rows(RC.REGISTRY)[:5]
    mism8 = []
    for label8, rel8, _crit8 in rows8:
        text8 = io.open(os.path.join(sandbox8, rel8), encoding="utf-8-sig",
                        errors="replace").read()
        try:
            tree8 = ast.parse(text8)
        except SyntaxError:
            tree8 = None
        old8 = RC.classify(text8, module8, RC.suite_constants(text8))[0]
        new8 = RC.classify(text8, module8, RC.suite_constants(text8, tree8),
                           tree8)[0]
        if old8 != new8:
            mism8.append((label8, old8, new8))
    ok("AC-CLG8 arm e - one parse reads a suite exactly as two parses did",
       not mism8, "rows=%d mismatch=%s" % (len(rows8), mism8))

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
