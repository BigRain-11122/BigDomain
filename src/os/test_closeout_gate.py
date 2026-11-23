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
  AC-CLG11..13  the replacement ledger (R3219): an absent ledger is rows=0 and
           PASS, a bad row or a stale latest row REFUSES by name
           E_CLG_LEDGER, a gone file is counted missing, the face is read-only
           and opt-out-able, and the pinned PASS token shape never moves
  AC-CLG14  the chain between one name's records is published as `broken=` and
           never gated (R3220): a lost record and a lawful delete-then-recreate
           look identical here, so a refusal would accuse the lawful case
  AC-CLG15..16  the counts are VALUES, not prose (R3221): the verdict carries
           `ledger_rows` / `ledger_broken` filled from the same report the row
           is rendered from, an absent ledger reads 0/0, a refused ledger keeps
           what it read, the named opt-out publishes neither key, the PASS
           token shape stays byte-identical, the closeout carrier passes the
           values through, and publishing writes nothing

  AC-CGEF1..6  the CEO front door (R3375): the two pages a reader opens are
           asked at closeout by each writer's OWN `--check`, a non-zero from
           either REFUSES by name E_CLG_ENTRY_PAGES quoting that writer's last
           line, the face writes no page byte, it repeats the writer's rc
           rather than a second rule, and a world with no `preview/` says
           `absent=no-preview` instead of being skipped

Honest boundary: `flags` sees a new file or a class change; a rewrite that
stays inside the same class is invisible to both faces (the census keeps no
hashes), and that is why the gate is a precondition, not a jail.

Source discipline: pure ASCII, stdlib only, no clock, no network, writes only
inside its own temp fixture worlds.
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
    # R3177: the fixture log is written in the R2246 canonical layout (CRLF,
    # sixteen-space items). Before this the world carried a bare-LF log, which
    # the new carrier face honestly refuses as E_CLG_CARRIER_LAYOUT - so the
    # fixtures stopped isolating the law each arm asks. Correcting the fixture,
    # no criterion relaxed: the non-canonical world is now exercised by the
    # carrier suite, where it is the arm under test.
    with open(os.path.join(tmp, "src", "os", "state.json"), "w",
              encoding="utf-8", newline="") as fh:
        fh.write('{\r\n  "log": [\r\n%s"%s"\r\n  ],\r\n  "tick": 1\r\n}\r\n'
                 % (" " * 16, line.replace("\\", "\\\\").replace('"', '\\"')))
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

        def silent_row(_target, _baseline, stats=None):
            # R3124: the shipped face accepts an optional `stats` out-parameter
            # (files/readable/bytes, R3100) and the gate now passes it, so a
            # stub emulating that face keeps the signature. The arm's judgment
            # - a row without flags= is refused, never read as clean - is
            # unchanged, and this stub publishes no stats so the gate gets no
            # corpus reading rather than an invented one.
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
    ok("AC-CLG8 arm b - root=ROOT publishes eight named readings (R3177 added "
       "the carrier face, R3219 the ledger face, R3225 the claims face, R3375 "
       "the front-door face) and the PASS line is byte-identical",
       sorted(ms8) == ["carrier", "census", "claims", "flags", "ledger",
                       "matrix", "pages", "round_main"]
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

    # AC-CLG9 (R3104): the matrix face asked about a world it cannot address.
    # Six arms, one criterion. The measurement this pins: a fixture world that
    # carried a byte copy of the live document AND the leg that document
    # records used to read EVIDENCE-FACE rows=735/735 - a refusal on the leg
    # provenance string, publishing LIVE registry numbers about a tree with no
    # registry. The face now refuses by name, the same way check_census does.
    with open(os.path.join(ROOT, "docs", "sandbox-suite-matrix.md"),
              encoding="utf-8") as fh:
        doc_text9 = fh.read()
    sys.path.insert(0, os.path.join(ROOT, "src", "os"))
    import suite_matrix_reconcile as SMR9
    try:
        recorded9 = SMR9.SM.doc_evidence_face(doc_text9,
                                             SMR9.SM.load_patterns())
    except (IOError, OSError, ValueError):
        recorded9 = None
    with tempfile.TemporaryDirectory() as tmp9:
        world9 = os.path.join(tmp9, "world")
        os.makedirs(os.path.join(world9, "docs"))
        os.makedirs(os.path.join(world9, "qa"))
        with open(os.path.join(world9, "docs", "sandbox-suite-matrix.md"),
                  "wb") as fh:
            fh.write(doc_text9.encode("utf-8"))
        leg9 = None
        if recorded9:
            candidate = os.path.join(ROOT, recorded9)
            if os.path.isfile(candidate):
                leg9 = os.path.join(world9, "qa",
                                    os.path.basename(candidate))
                shutil.copy2(candidate, leg9)
        a_ok, a_line = CG.check_matrix(world9)
        ok("AC-CLG9 arm a - a foreign world is refused by NAME, and the line "
           "publishes no live row counts",
           a_ok is False
           and a_line.startswith(CG.E_CLG_FOREIGN_REGISTRY)
           and "face=matrix" in a_line and "rows=" not in a_line,
           "leg=%s line=%s" % (bool(leg9), a_line))

        b_ok, b_line = CG.check_matrix(ROOT)
        ok("AC-CLG9 arm b - the live tree stays green under the guard",
           b_ok is True and b_line.startswith("DOC-CURRENT "),
           "line=%s" % b_line)

        stale9 = os.path.join(tmp9, "candidate.md")
        stale_text9, changed9 = MUTATE_FIRST_COUNT(doc_text9)
        with open(stale9, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(stale_text9)
        c_ok, c_line = CG.check_matrix(ROOT, doc=stale9)
        ok("AC-CLG9 arm c - the guard sits on root/registry, not on the "
           "document path: a candidate document still gets the DOC verdict",
           changed9 and c_ok is False
           and not c_line.startswith(CG.E_CLG_FOREIGN_REGISTRY)
           and c_line.split(" ")[0] in ("ROWS-MISMATCH", "STALE-CONTENT",
                                        "EVIDENCE-FACE"),
           "changed=%s line=%s" % (changed9, c_line))

        d_ok, d_line = CG.check_round_main(world9)
        ok("AC-CLG9 arm d - a world with no state is refused by E_CLG_NO_STATE "
           "in this suite, not only in battery_followup",
           d_ok is False and d_line.startswith(CG.E_CLG_NO_STATE),
           "line=%s" % d_line)

        gate9 = os.path.join(tmp9, "gateworld")
        qa9 = os.path.join(gate9, "qa")
        os.makedirs(qa9)
        os.makedirs(os.path.join(gate9, "src", "os"))
        os.makedirs(os.path.join(gate9, "docs"))
        write_bytes(os.path.join(qa9, "healthy.log"), b"PASS suite row\n")
        base9 = os.path.join(qa9, CENSUS.BASELINE_NAME)
        _bl, _bcode, _bb = CENSUS.write_baseline(qa9, base9)
        # R3177: canonical layout (CRLF, sixteen-space item), same reason as
        # build_root above - a bare-LF fixture state is refused by the new
        # carrier face before the law this arm asks is reached.
        with open(os.path.join(gate9, "src", "os", "state.json"), "w",
                  encoding="utf-8", newline="") as fh:
            fh.write('{\r\n  "log": [\r\n%s"%s"\r\n  ],\r\n  "tick": 1\r\n}\r\n'
                     % (" " * 16,
                        "2026-11-20 R5009 PRODUCT: a fixture round main"))
        with open(os.path.join(gate9, "docs", "sandbox-suite-matrix.md"),
                  "wb") as fh:
            fh.write(doc_text9.encode("utf-8"))
        e_lines, e_rc, e_v = CG.evaluate(qa9, base9, root=gate9)
        ok("AC-CLG9 arm e - evaluate(root=world) wraps the new code in "
           "E_CLG_CENSUS instead of judging the live registry",
           _bcode == 0 and e_rc == 2
           and e_v.get("reason") == "E_CLG_CENSUS"
           and any(l.startswith(CG.E_CLG_FOREIGN_REGISTRY)
                   for l in e_lines),
           "rc=%s reason=%s lines=%s"
           % (e_rc, e_v.get("reason"), e_lines[:2]))

        import closeout as CO9
        f_word, f_line, _f_v = CO9.tree_refusal(gate9)
        ok("AC-CLG9 arm f - tree_refusal reads RED and carries the census "
           "refusal instead of a silent pass",
           f_word == "RED" and "E_CLG_CENSUS" in f_line,
           "word=%s line=%s" % (f_word, f_line))

    # AC-CLG10 (R3109): the PASS line says census=PASS and never named the
    # baseline it compared against - the name lived in a module constant bound
    # at import time, so a reader quoting the line could not verify which file,
    # how big, or how old. The gate publishes that identity on a row BELOW the
    # verdict (the PASS token shape stays byte-identical, which AC-CLG6a/b pin)
    # and every value on it is derived from the file the face was handed.
    with tempfile.TemporaryDirectory() as tmp10:
        live10 = os.path.join(ROOT, "qa")
        live_base10 = os.path.join(live10, CENSUS.BASELINE_NAME)
        deep10, deep10_rc, _dv10 = CG.evaluate(live10, live_base10, root=ROOT)
        ident = [line for line in deep10 if line.startswith("CENSUS-BASELINE ")]
        a_ok = (deep10_rc == 0 and len(ident) == 1
                and ident[0].startswith("CENSUS-BASELINE name=qa/%s bytes="
                                        % CENSUS.BASELINE_NAME))
        ok("AC-CLG10 arm a - a deep PASS names the baseline it judged", a_ok,
           "rc=%s ident=%s" % (deep10_rc, ident))

        with open(live_base10, "rb") as fh:
            live_raw = fh.read()
        want_sha = hashlib.sha256(live_raw).hexdigest()[:12]
        got_sha = re.search(r"sha256=(\w+)", ident[0]).group(1) if ident else ""
        ok("AC-CLG10 arm b - the sha256 is of those exact bytes, not typed",
           got_sha == want_sha, "got=%s want=%s" % (got_sha, want_sha))

        live_obj = json.loads(live_raw.decode("utf-8"))
        want_rows = sum(len(v) for v in live_obj.values() if isinstance(v, list))
        got_rows = re.search(r"rows=(\d+)", ident[0]).group(1) if ident else ""
        ok("AC-CLG10 arm c - rows is the sum of the baseline own class lists",
           got_rows == str(want_rows), "got=%s want=%d" % (got_rows, want_rows))

        world10, base10 = build_world(os.path.join(tmp10, "w10"))
        f_lines, f_rc, _fv = CG.evaluate(world10, base10, root=ROOT)
        f_ident = [line for line in f_lines
                   if line.startswith("CENSUS-BASELINE ")]
        ok("AC-CLG10 arm d - a fixture baseline prints ITS identity, not the "
           "live one",
           f_rc == 0 and len(f_ident) == 1 and f_ident[0] != ident[0],
           "live=%s fixture=%s" % (ident, f_ident))

        plain_lines, plain_rc, _pv = CG.evaluate(world10, base10)
        ok("AC-CLG10 arm e - the default face (root=None) publishes no "
           "identity row and keeps its shipped shape",
           plain_rc == 0
           and not any(line.startswith("CENSUS-BASELINE ")
                       for line in plain_lines)
           and plain_lines[0].startswith("CLOSEOUT-GATE PASS")
           and "gating=flags" in plain_lines[0]
           and "round_main=" not in plain_lines[0],
           "rc=%s lines=%s" % (plain_rc, plain_lines))

    # AC-CLG11..13 (R3219): the replacement ledger was write-only at closeout -
    # `qa_log --ledger-check` had no execution body, and measured on four
    # fixture worlds a truncated JSON row and a stale latest row both answered
    # the identical PASS with no ledger token. The gate now asks the writer's
    # own judgement against THIS world, publishes one LEDGER row below the
    # verdict, and refuses by name when the ledger cannot be believed.
    def ledger_world(tmp, payloads):
        """A root that passes every earlier face, plus its ledger rows."""
        root, reg, pin = build_root(tmp)
        state = os.path.join(root, "state")
        os.makedirs(state)
        qa_dir = os.path.join(root, "qa")
        os.makedirs(qa_dir)
        write_bytes(os.path.join(qa_dir, "probe-evidence.log"), b"beta two\n")
        ledger = os.path.join(state, "qa_replacements.jsonl")
        if payloads is not None:
            with open(ledger, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("".join(payloads))
        return root, reg, pin, ledger, qa_dir

    def replacement_row(name, old, new):
        return json.dumps({
            "event": "REPLACED", "name": name, "old_bytes": len(old),
            "old_sha16": hashlib.sha256(old).hexdigest()[:16],
            "new_bytes": len(new),
            "new_sha16": hashlib.sha256(new).hexdigest()[:16],
            "ts": "2026-11-22T00:00:00"}) + "\n"

    healthy_row = replacement_row("probe-evidence.log", b"alpha\n",
                                  b"beta two\n")
    live11 = os.path.join(ROOT, "qa")
    live_base11 = os.path.join(live11, CENSUS.BASELINE_NAME)
    lines11, rc11, v11 = CG.evaluate(live11, live_base11, root=ROOT)
    rows11 = [line for line in lines11 if line.startswith("LEDGER ")]
    ok("AC-CLG11 arm a - the live closeout publishes exactly one LEDGER row",
       rc11 == 0 and len(rows11) == 1 and rows11[0].startswith("LEDGER OK "),
       "rc=%s rows=%s" % (rc11, rows11))
    # R3224: this arm asserted the LIVE ledger was absent. R3223's own closeout
    # then wrote the live ledger, so the premise stopped being true one tick
    # after it passed. The strength is kept and the premise is now computed:
    # the live row must publish the count the live file actually holds.
    live_ledger11 = os.path.join(ROOT, "state", "qa_replacements.jsonl")
    expected11 = 0
    if os.path.isfile(live_ledger11):
        with io.open(live_ledger11, encoding="utf-8") as fh:
            expected11 = sum(1 for line in fh if line.strip())
    ok("AC-CLG11 arm b - the live row publishes the live ledger's own count",
       rc11 == 0 and ("rows=%d" % expected11) in rows11[0]
       and "path=state/qa_replacements.jsonl" in rows11[0],
       "expected=%d row=%s" % (expected11, rows11[:1]))
    ok("AC-CLG11 arm c - the pinned PASS token shape is byte-identical",
       lines11[0].startswith("CLOSEOUT-GATE PASS files=")
       and "gating=flags" in lines11[0]
       and "ledger=" not in lines11[0],
       "line=%s" % lines11[:1])

    with tempfile.TemporaryDirectory() as tmp12:
        root_a, reg_a, pin_a, _led_a, _qa_a = ledger_world(
            os.path.join(tmp12, "a"), [healthy_row])
        world_a, base_a = build_world(os.path.join(tmp12, "wa"))
        a_lines, a_rc, a_v = CG.evaluate(world_a, base_a, root=root_a,
                                         registry=reg_a, census_pin=pin_a,
                                         matrix=False)
        ok("AC-CLG12 arm a - a healthy ledger passes and says what it read",
           a_rc == 0 and a_v.get("ledger") == "OK"
           and any(line.startswith("LEDGER OK rows=1 names=1 ")
                   for line in a_lines),
           "rc=%s ledger=%s" % (a_rc, a_v.get("ledger")))

        root_b, reg_b, pin_b, _led_b, _qa_b = ledger_world(
            os.path.join(tmp12, "b"),
            [healthy_row, '{"event": "REPLACED", "name": "trunc\n'])
        world_b, base_b = build_world(os.path.join(tmp12, "wb"))
        b_lines, b_rc, b_v = CG.evaluate(world_b, base_b, root=root_b,
                                         registry=reg_b, census_pin=pin_b,
                                         matrix=False)
        ok("AC-CLG12 arm b - a truncated row REFUSES the closeout by name",
           b_rc == 2 and b_v.get("reason") == "E_CLG_LEDGER"
           and any("detail bad line=2" in line for line in b_lines),
           "rc=%s reason=%s lines=%s"
           % (b_rc, b_v.get("reason"), [l for l in b_lines if "bad" in l]))

        root_c, reg_c, pin_c, _led_c, _qa_c = ledger_world(
            os.path.join(tmp12, "c"),
            [replacement_row("probe-evidence.log", b"alpha\n", b"moved\n")])
        world_c, base_c = build_world(os.path.join(tmp12, "wc"))
        c_lines, c_rc, c_v = CG.evaluate(world_c, base_c, root=root_c,
                                         registry=reg_c, census_pin=pin_c,
                                         matrix=False)
        stale_lines = [l for l in c_lines if "detail stale" in l]
        ok("AC-CLG12 arm c - a stale latest row REFUSES and names both hashes",
           c_rc == 2 and c_v.get("reason") == "E_CLG_LEDGER"
           and len(stale_lines) == 1 and "disk_sha16=" in stale_lines[0]
           and "ledger_sha16=" in stale_lines[0],
           "rc=%s stale=%s" % (c_rc, stale_lines))

        root_d, reg_d, pin_d, _led_d, _qa_d = ledger_world(
            os.path.join(tmp12, "d"),
            [replacement_row("gone.log", b"alpha\n", b"beta two\n")])
        world_d, base_d = build_world(os.path.join(tmp12, "wd"))
        d_lines, d_rc, d_v = CG.evaluate(world_d, base_d, root=root_d,
                                         registry=reg_d, census_pin=pin_d,
                                         matrix=False)
        ok("AC-CLG12 arm d - a row whose file is gone counts missing, no red",
           d_rc == 0 and any(line.startswith("LEDGER OK ")
                             and "missing=1" in line for line in d_lines),
           "rc=%s lines=%s" % (d_rc, [l for l in d_lines
                                      if l.startswith("LEDGER")]))

        # AC-CLG13: read-only, honest opt-out, and the default face untouched.
        def stat_of(path):
            info = os.stat(path)
            return (info.st_size, info.st_mtime_ns)

        before_led = stat_of(_led_a)
        before_qa = stat_of(os.path.join(_qa_a, "probe-evidence.log"))
        names_before = sorted(os.listdir(root_a))
        first_run = CG.evaluate(world_a, base_a, root=root_a, registry=reg_a,
                                census_pin=pin_a, matrix=False)
        second_run = CG.evaluate(world_a, base_a, root=root_a, registry=reg_a,
                                 census_pin=pin_a, matrix=False)
        ok("AC-CLG13 arm a - two runs are identical and touch nothing",
           first_run[0] == second_run[0]
           and first_run[1] == second_run[1] == 0
           and stat_of(_led_a) == before_led
           and stat_of(os.path.join(_qa_a, "probe-evidence.log")) == before_qa
           and sorted(os.listdir(root_a)) == names_before,
           "rc=%s/%s" % (first_run[1], second_run[1]))
        opt_lines, opt_rc, opt_v = CG.evaluate(
            world_a, base_a, root=root_a, registry=reg_a, census_pin=pin_a,
            matrix=False, ledger=False)
        ok("AC-CLG13 arm b - ledger=False is a named opt-out that prints no row",
           opt_rc == 0
           and not any(line.startswith("LEDGER ") for line in opt_lines)
           and "ledger" not in opt_v,
           "rc=%s verdict=%s" % (opt_rc, sorted(opt_v)))
        plain13, plain13_rc, _pv13 = CG.evaluate(world_a, base_a)
        ok("AC-CLG13 arm c - root=None answers the pre-R3093 shape untouched",
           plain13_rc == 0
           and not any(line.startswith("LEDGER ") for line in plain13)
           and plain13[0].startswith("CLOSEOUT-GATE PASS")
           and "round_main=" not in plain13[0],
           "rc=%s lines=%s" % (plain13_rc, plain13[:1]))

        # AC-CLG14 (R3220): the count of names whose adjacent records do not
        # link is PUBLISHED on the row, and never gated. Measured before the
        # change: a clean three-row chain and a chain with its middle row lost
        # answered the identical "LEDGER OK rows=... bad=0 stale=0 missing=0".
        # A break can be a lost record OR a lawful deletion-then-recreate or an
        # external write_atomic call, and this face cannot tell them apart, so a
        # refusal would accuse the lawful cases.
        gap_rows = [replacement_row("probe-evidence.log", b"alpha\n",
                                    b"middle\n"),
                    replacement_row("probe-evidence.log", b"other\n",
                                    b"beta two\n")]
        root_e, reg_e, pin_e, _led_e, _qa_e = ledger_world(
            os.path.join(tmp12, "e"), gap_rows)
        world_e, base_e = build_world(os.path.join(tmp12, "we"))
        e_lines, e_rc, e_v = CG.evaluate(world_e, base_e, root=root_e,
                                         registry=reg_e, census_pin=pin_e,
                                         matrix=False)
        e_rows = [line for line in e_lines if line.startswith("LEDGER OK ")]
        e_chain = [line for line in e_lines if "detail chain" in line]
        ok("AC-CLG14 a broken chain is published on the row, never gated",
           e_rc == 0 and e_v.get("ledger") == "OK"
           and len(e_rows) == 1 and "broken=1" in e_rows[0]
           and "bad=0" in e_rows[0] and "stale=0" in e_rows[0]
           and e_chain == [],
           "rc=%s row=%s chain=%s" % (e_rc, e_rows, e_chain))

        # AC-CLG15..16 (R3221): the counts existed only as TEXT. Measured on
        # the three worlds above (absent / healthy / broken) the verdict key
        # set was identical and `ledger` was the word 'OK' in all three, so a
        # machine consumer had to parse the row. The gate now fills
        # `ledger_rows` / `ledger_broken` from the SAME report it renders.
        def reading_of(world, base, root, reg, pin):
            lines, rc, verdict = CG.evaluate(world, base, root=root,
                                             registry=reg, census_pin=pin,
                                             matrix=False)
            row = [l for l in lines if l.startswith("LEDGER ")]
            return lines, rc, verdict, (row[0] if row else "")

        def number(row, key):
            token = [part for part in row.split() if part.startswith(key + "=")]
            return int(token[0].split("=", 1)[1]) if token else None

        world_a2, base_a2 = build_world(os.path.join(tmp12, "wa2"))
        lines_a2, rc_a2, v_a2, row_a2 = reading_of(
            world_a2, base_a2, root_a, reg_a, pin_a)
        ok("AC-CLG15 arm a - a healthy ledger publishes rows/broken as VALUES",
           rc_a2 == 0 and v_a2.get("ledger_rows") == number(row_a2, "rows") == 1
           and v_a2.get("ledger_broken") == number(row_a2, "broken") == 0,
           "rc=%s rows=%r broken=%r row=%s"
           % (rc_a2, v_a2.get("ledger_rows"), v_a2.get("ledger_broken"),
              row_a2))
        world_b2, base_b2 = build_world(os.path.join(tmp12, "wb2"))
        lines_b2, rc_b2, v_b2, row_b2 = reading_of(
            world_b2, base_b2, root_e, reg_e, pin_e)
        ok("AC-CLG15 arm b - a broken chain is a VALUE, and still never gated",
           rc_b2 == 0 and v_b2.get("verdict") == "PASS"
           and v_b2.get("ledger_broken") == number(row_b2, "broken")
           and v_b2.get("ledger_rows") == number(row_b2, "rows"),
           "rc=%s broken=%r row=%s"
           % (rc_b2, v_b2.get("ledger_broken"), row_b2))
        world_c2, base_c2 = build_world(os.path.join(tmp12, "wc2"))
        root_f, reg_f, pin_f, _led_f, _qa_f = ledger_world(
            os.path.join(tmp12, "f"), None)
        lines_c2, rc_c2, v_c2, row_c2 = reading_of(
            world_c2, base_c2, root_f, reg_f, pin_f)
        ok("AC-CLG15 arm c - an absent ledger publishes rows=0 broken=0",
           rc_c2 == 0 and v_c2.get("ledger") == "OK"
           and v_c2.get("ledger_rows") == number(row_c2, "rows") == 0
           and v_c2.get("ledger_broken") == number(row_c2, "broken") == 0,
           "rc=%s rows=%r row=%s"
           % (rc_c2, v_c2.get("ledger_rows"), row_c2))
        world_d2, base_d2 = build_world(os.path.join(tmp12, "wd2"))
        lines_d2, rc_d2, v_d2, row_d2 = reading_of(
            world_d2, base_d2, root_c, reg_c, pin_c)
        ok("AC-CLG15 arm e - a REFUSED ledger still carries what it read",
           rc_d2 == 2 and v_d2.get("ledger") == "RED"
           and v_d2.get("reason") == "E_CLG_LEDGER"
           and v_d2.get("ledger_rows") == number(row_d2, "rows")
           and v_d2.get("ledger_broken") == number(row_d2, "broken"),
           "rc=%s rows=%r row=%s"
           % (rc_d2, v_d2.get("ledger_rows"), row_d2))
        opt_rows, opt_rc2, opt_v2 = CG.evaluate(
            world_a2, base_a2, root=root_a, registry=reg_a, census_pin=pin_a,
            matrix=False, ledger=False)
        ok("AC-CLG15 arm d - the named opt-out publishes NEITHER key",
           opt_rc2 == 0 and "ledger_rows" not in opt_v2
           and "ledger_broken" not in opt_v2
           and "ledger" not in opt_v2,
           "rc=%s keys=%s" % (opt_rc2, sorted(opt_v2)))

        # AC-CLG16: the pinned shapes do not move, the carrier passes the
        # values through, and the face stays read-only.
        expected = ("CLOSEOUT-GATE PASS files=%d flags=0 reader_refused=0 "
                    "gating=flags round_main=OK census=PASS"
                    % number(lines_a2[0], "files"))
        ok("AC-CLG16 arm a - the PASS token shape is byte-identical",
           lines_a2[0] == expected and "ledger_rows=" not in lines_a2[0]
           and "ledger_broken=" not in lines_a2[0],
           "line=%s" % lines_a2[0])
        source = io.open(os.path.join(ROOT, "tools", "closeout_gate.py"),
                         encoding="utf-8").read()
        ok("AC-CLG16 arm b - ONE report feeds both renderings (no re-parse)",
           source.count("QL.ledger_report(") == 1
           and "read_ledger" not in source
           and source.count("_ledger_values(") == 3,
           "ledger_report=%d _ledger_values=%d"
           % (source.count("QL.ledger_report("),
              source.count("_ledger_values(")))

        def stat_of2(path):
            info = os.stat(path)
            return (info.st_size, info.st_mtime_ns)

        before_led_a2 = stat_of2(_led_a)
        before_qa_a2 = stat_of2(os.path.join(_qa_a, "probe-evidence.log"))
        CG.evaluate(world_a2, base_a2, root=root_a, registry=reg_a,
                    census_pin=pin_a, matrix=False)
        ok("AC-CLG16 arm c - publishing the values writes nothing",
           stat_of2(_led_a) == before_led_a2
           and stat_of2(os.path.join(_qa_a, "probe-evidence.log"))
           == before_qa_a2,
           "ledger=%s qa=%s" % (before_led_a2, before_qa_a2))

        sys.path.insert(0, os.path.join(ROOT, "src", "os"))
        import closeout as CO
        word, headline, tree_v = CO.tree_refusal(ROOT)
        tree_led = [d for d in (tree_v.get("detail") or [])
                    if d.startswith("LEDGER ")]
        tree_row = tree_led[0] if tree_led else ""
        ok("AC-CLG16 arm d - the carrier publishes the counts, never re-types",
           word == "PASS" and tree_v.get("ledger_rows") == number(tree_row, "rows")
           and tree_v.get("ledger_broken") == number(tree_row, "broken"),
           "word=%s rows=%r broken=%r row=%s"
           % (word, tree_v.get("ledger_rows"), tree_v.get("ledger_broken"),
              tree_row))

    # AC-CGEF1..6 (R3375): the two pages a reader actually opens are asked at
    # closeout, by each writer's own `--check`, and a non-zero from either
    # refuses. WHY (measured at R3374): the entry page sat one generation
    # stale while every closeout read PASS.
    with tempfile.TemporaryDirectory() as tmp_pg:
        pg_lines, pg_rc, pg_v = CG.evaluate(live, live_base, root=ROOT)
        pgrow = [ln for ln in pg_lines if ln.startswith("ENTRY-PAGES")]
        ok("AC-CGEF1 the live closeout publishes the front-door reading",
           pg_rc == 0 and pg_v.get("entry_pages") == "OK" and len(pgrow) == 1
           and pgrow[0].startswith("ENTRY-PAGES faces=2 fail=0")
           and "entry-index=rc0" in pgrow[0]
           and "first-yuan-chain=rc0" in pgrow[0]
           and pg_lines[0].startswith("CLOSEOUT-GATE PASS"),
           "row=%s entry_pages=%s" % (pgrow[0] if pgrow else "",
                                      pg_v.get("entry_pages")))

        def _page_runner(script):
            if script == "first_yuan_chain.py":
                return 2, "VERDICT FAIL E_STALE html=0B json=0B"
            return 0, "VERDICT PASS 23/23"

        r_lines, r_rc, r_v = CG.evaluate(live, live_base, root=ROOT,
                                         pages_runner=_page_runner)
        ok("AC-CGEF2 a refusing writer REFUSES the closeout by name",
           r_rc == 2 and r_v.get("reason") == "E_CLG_ENTRY_PAGES"
           and r_v.get("entry_pages") == "FAIL"
           and r_lines[0].startswith("CLOSEOUT-GATE REFUSED "
                                    "reason=E_CLG_ENTRY_PAGES")
           and not any(ln.startswith("CLOSEOUT-GATE PASS") for ln in r_lines)
           and any("face=first-yuan-chain rc=2" in ln and "E_STALE" in ln
                   for ln in r_lines),
           "rc=%s reason=%s" % (r_rc, r_v.get("reason")))

        naked = os.path.join(tmp_pg, "naked")
        os.makedirs(os.path.join(naked, "preview"))
        nk_ok, nk_lines = CG.check_entry_pages(naked)
        ok("AC-CGEF3 an unanswerable world reddens on the writers' own rc "
           "(no injection)",
           nk_ok is False and nk_lines[0].startswith("ENTRY-PAGES FAIL")
           and "fail=2" in nk_lines[0]
           and "entry-index=rc127" in nk_lines[0]
           and any("E_PAGE_TOOL_MISSING" in ln for ln in nk_lines[1:]),
           "row=%s detail=%s" % (nk_lines[0], nk_lines[1:]))

        page_files = [os.path.join(ROOT, "preview", "index.html"),
                      os.path.join(ROOT, "preview", "first-yuan-chain.html")]

        def _stat_of(p):
            info = os.stat(p)
            return (info.st_size, info.st_mtime_ns)

        before_pg = [_stat_of(p) for p in page_files]
        CG.check_entry_pages(ROOT)
        after_pg = [_stat_of(p) for p in page_files]
        ok("AC-CGEF4 asking the face writes no page byte",
           before_pg == after_pg, "before=%s after=%s"
           % (before_pg, after_pg))

        direct = {}
        for face, script in CG.ENTRY_PAGES:
            proc = subprocess.run(
                [sys.executable, os.path.join(ROOT, "tools", script),
                 "--check"], cwd=ROOT, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            direct[face] = proc.returncode
        ok("AC-CGEF5 the row repeats each writer's own --check rc "
           "(no second rule)",
           all(("%s=rc%d" % (face, rc)) in pgrow[0]
               for face, rc in direct.items()),
           "direct=%s row=%s" % (direct, pgrow[0] if pgrow else ""))

        bare = os.path.join(tmp_pg, "bare")
        os.makedirs(bare)
        ab_ok, ab_lines = CG.check_entry_pages(bare)
        ok("AC-CGEF6 a world with no front door is NAMED, never skipped",
           ab_ok is True and ab_lines[0] == "ENTRY-PAGES absent=no-preview",
           "row=%s" % ab_lines[0])

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
