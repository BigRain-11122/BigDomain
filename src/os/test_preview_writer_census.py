"""Battery suite for tools/preview_writer_census.py - AC-PWC1..AC-PWC8 (R3527-R3530).

Pinned in src/os/backlog.md BEFORE the tool, this file and the face_pair_receipt
wiring existed. AC-PWC6 was pinned in the R3528 window before
tools/ledger_reconcile_face.py was touched, AC-PWC7 in R3529 before
tools/lobby_session_trace.py, AC-PWC8 in R3530 before tools/first_yuan_path.py,
AC-PWC9 in R3531 before tools/filing_checklist.py, AC-PWC10 in R3532 before
tools/ship_checklist.py, AC-PWC11 in R3533 before tools/start_here.py.
AC-PWC12 in R3534 before tools/first_yuan_chain.py, AC-PWC13 in R3535 before
tools/payment_gate_report.py, AC-PWC14 in R3536 before tools/ugc_gate_report.py.

Why this exists: R3524..R3526 each closed the same birth-site gap for ONE
producer (one board battery page, the rest of BOARD_PAGES, one non-board census).
Nobody had counted the class. This round's read-only pass answered it: 98 non-test
modules declare a preview .html landing path and carry a write call, and only two
carried an in-process face re-derivation. This suite grades the census that says
so, and grades the first newly closed producer by its source.

Scope, stated honestly: the census grades SOURCE, not runtime behaviour - a
producer that writes a page through an indirection this reader cannot see is
counted as a gap (the safe direction: a false gap costs one look, a false closed
hides a stale CEO face). No page is rendered here, no network, no child process.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

import preview_writer_census as pwc  # noqa: E402

MOD = pwc


def write(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def world():
    """A private tree with one module per class the law can answer."""
    root = tempfile.mkdtemp(prefix="pwc-")
    write(os.path.join(root, "src", "os", "state.json"), '{"tick": 42}')
    write(os.path.join(root, "src", "os", "export_round.py"), "X = 1\n")
    write(os.path.join(root, "src", "os", "board_face_landing.py"), "Y = 1\n")
    write(os.path.join(root, "tools", "gap_producer.py"),
          'import os\nP = os.path.join("preview", "gap-face.html")\n'
          'open(P, "w").write("<html></html>")\n')
    write(os.path.join(root, "tools", "closed_producer.py"),
          'import os\nP = os.path.join("preview", "closed-face.html")\n'
          'open(P, "w").write("x")\n'
          'import board_face_landing\n'
          'board_face_landing.refresh_export_face(".")\n')
    write(os.path.join(root, "tools", "reader_only.py"),
          'import os\nP = os.path.join("preview", "read-face.html")\n'
          'TEXT = open(P, encoding="utf-8").read()\n')
    write(os.path.join(root, "tools", "prose_only.py"),
          '"""A module that documents ER.write(P) and board_face_landing but '
          'writes nothing real."""\n# ER.write(\'preview/x.html\', 1)\n')
    return root


class PWC1WriterIdentity(unittest.TestCase):
    """AC-PWC1: writer vs reader is a Call measurement, not a text match."""

    def test_kinds(self):
        w = world()
        try:
            rows, totals, excluded = MOD.census(w)
        finally:
            shutil.rmtree(w, ignore_errors=True)
        by_path = {r["path"]: r["kind"] for r in rows}
        self.assertEqual(by_path["tools/gap_producer.py"], "gap")
        self.assertEqual(by_path["tools/closed_producer.py"], "closed")
        self.assertEqual(by_path["tools/reader_only.py"], "reader")
        self.assertNotIn("tools/prose_only.py", by_path)
        self.assertEqual(totals["gap"], 1)
        self.assertEqual(totals["closed"], 1)
        self.assertEqual(totals["reader"], 1)
        self.assertEqual(sorted(excluded),
                         ["src/os/board_face_landing.py", "src/os/export_round.py"])

    def test_definition_sites_are_excluded_and_counted(self):
        w = world()
        try:
            _rows, totals, excluded = MOD.census(w)
        finally:
            shutil.rmtree(w, ignore_errors=True)
        self.assertEqual(totals["excluded"], 2)
        self.assertNotIn("src/os/export_round.py", [r["path"] for r in _rows])


class PWC2ClosureIsACall(unittest.TestCase):
    """AC-PWC2: prose naming the closure is never closure."""

    def test_prose_is_not_closure(self):
        kind, _html, writes, closes = MOD.classify_source(
            '"""calls board_face_landing.refresh_export_face(root)"""\n'
            'P = "preview/a.html"\nopen(P, "w").write("x")\n')
        self.assertEqual(kind, "gap")
        self.assertGreaterEqual(writes, 1)
        self.assertEqual(closes, 0)

    def test_shipped_writer_alias_closes(self):
        kind, _h, _w, closes = MOD.classify_source(
            'P = "preview/a.html"\nER.write(".", "2026-01-01")\n')
        self.assertEqual(kind, "closed")
        self.assertEqual(closes, 1)


class PWC3TwoHalvesOneDerivation(unittest.TestCase):
    """AC-PWC3: both halves are one derivation and tampering reddens --check."""

    def test_tamper_detected_and_stamp_ignored(self):
        w = world()
        try:
            payload = MOD.payload_for(w)
            out_j = os.path.join(w, "preview", MOD.LABEL + ".json")
            out_h = os.path.join(w, "preview", MOD.LABEL + ".html")
            write(out_j, MOD.dumps(payload))
            write(out_h, MOD.html_of(payload))
            self.assertEqual(MOD.check(payload, out_j, out_h), [])
            fresh = MOD.payload_for(w)
            fresh["generated_at"] = "1999-01-01T00:00:00+00:00"
            self.assertEqual(MOD.check(fresh, out_j, out_h), [])
            payload["totals"]["gap"] = 999
            problems = MOD.check(payload, out_j, out_h)
            self.assertTrue(any("json" in p for p in problems), problems)
        finally:
            shutil.rmtree(w, ignore_errors=True)


class PWC4CheckIsReadOnly(unittest.TestCase):
    """AC-PWC4: --check returns before the first landing write."""

    def test_check_writes_nothing(self):
        w = world()
        try:
            before = sorted(os.listdir(os.path.join(w, "tools")))
            rc = MOD.main(["--root", w, "--check"])
            self.assertEqual(rc, 2)
            self.assertFalse(os.path.isdir(os.path.join(w, "preview")))
            self.assertEqual(sorted(os.listdir(os.path.join(w, "tools"))), before)
            self.assertEqual(MOD.main(["--root", w]), 0)
            self.assertTrue(os.path.isfile(
                os.path.join(w, "preview", MOD.LABEL + ".json")))
            self.assertEqual(MOD.main(["--root", w, "--check"]), 0)
        finally:
            shutil.rmtree(w, ignore_errors=True)


class PWC5FirstProducerClosed(unittest.TestCase):
    """AC-PWC5: face_pair_receipt re-derives the face after its last landing."""

    def test_source_carries_in_process_face_after_writes(self):
        path = os.path.join(TOOLS, "face_pair_receipt.py")
        with io.open(path, encoding="utf-8") as f:
            text = f.read()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        # The call must sit in main(), after the last landing write, and the
        # --check branch must return before it (position measured, not assumed).
        head, _sep, tail = text.rpartition("def main(argv):")
        main_body = tail
        check_at = main_body.index('if "--check" in argv:')
        call_at = main_body.index("refresh_export_face(")
        last_write = main_body.rindex(".write(")
        self.assertGreater(call_at, last_write)
        self.assertLess(check_at, call_at)
        self.assertIn("board_face_landing", main_body)


def face_after_landing(text, landing="render(write=True)"):
    """(present, after_landing, shared_definition) measured from main() source."""
    if "def main(argv):" not in text:
        return (False, False, False)
    main_body = text.rpartition("def main(argv):")[2]
    at = main_body.find("refresh_export_face(")
    present = at != -1
    landing_at = main_body.find(landing)
    after = present and landing_at != -1 and at > landing_at
    shared = present and "board_face_landing" in main_body
    return (present, after, shared)


class PWC6SecondProducerClosed(unittest.TestCase):
    """AC-PWC6: ledger_reconcile_face re-derives the face after its landing."""

    def _source(self):
        path = os.path.join(TOOLS, "ledger_reconcile_face.py")
        with io.open(path, encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(face_after_landing(text), (True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "board_face_landing.refresh_export_face(HERE)",
            "None  # control: closure removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertEqual(face_after_landing(deleted),
                         (False, False, False))
        moved = text.replace(
            "    html, text, doc = render(write=True)",
            "    ok, note, _proof = board_face_landing.refresh_export_face(HERE)"
            "  # control: moved before the landing\n"
            "    html, text, doc = render(write=True)")
        self.assertEqual(face_after_landing(moved), (True, False, True))


def lst_closure_positions(text, landing="write_file_atomic(out_html, robot)"):
    """(present, after_landing, check_returns_first, shared_only) for AC-PWC7."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2]
    at = body.find("_refresh_face()")
    present = at != -1
    landing_at = body.find(landing)
    after = present and landing_at != -1 and at > landing_at
    check_at = body.find("if checking:")
    first = check_at != -1 and present and check_at < at
    helper = text.rpartition("def _refresh_face(")[2]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = "ER.write(" not in helper and ".write(" not in helper
    return (present, after, first, shared and no_local_writer)


class PWC7ThirdProducerClosed(unittest.TestCase):
    """AC-PWC7: lobby_session_trace re-derives the face after its landing only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "lobby_session_trace.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(lst_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            '        print("face export=" + _refresh_face())',
            "        pass  # control: closure call removed")
        self.assertEqual(lst_closure_positions(deleted)[0], False)
        moved = text.replace(
            "    write_file_atomic(out_json, dump_json(payload))",
            "    _refresh_face()  # control: moved before the landing\n"
            "    write_file_atomic(out_json, dump_json(payload))")
        pos = lst_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import lobby_session_trace as LST
        calls = []

        class Fake(object):
            def __init__(self, ok, note):
                self.ok, self.note = ok, note

            def refresh_export_face(self, root):
                calls.append(root)
                return (self.ok, self.note, {})

        class Boom(object):
            def refresh_export_face(self, root):
                raise RuntimeError("no writer here")

        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(LST._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [LST.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(LST._refresh_face(), "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(LST._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_scratch_render_lands_nothing(self):
        import lobby_session_trace as LST
        scratch = os.path.join(ROOT, "preview", "_scratch_render_probe.html")
        self.assertFalse(LST._landing_is_default(scratch, scratch))
        self.assertFalse(LST._landing_is_default(LST.OUT_HTML, scratch))
        self.assertTrue(LST._landing_is_default(LST.OUT_HTML, LST.OUT_JSON))

    def test_check_path_does_not_refresh(self):
        import lobby_session_trace as LST
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        saved = sys.modules.get("board_face_landing")
        saved_argv = sys.argv
        try:
            sys.modules["board_face_landing"] = Fake()
            sys.argv = ["lobby_session_trace.py", "--check"]
            LST.main()
        finally:
            sys.argv = saved_argv
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
        self.assertEqual(calls, [])


def fyp_closure_positions(text, landing="fh.write(body)"):
    """(present, after_landing, check_clean, shared_only) for AC-PWC8."""
    if "def cmd_write(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def cmd_write(")[2].split("def cmd_check(")[0]
    at = body.find("_refresh_face()")
    present = at != -1
    landing_at = body.rfind(landing)
    after = present and landing_at != -1 and at > landing_at
    check_body = text.rpartition("def cmd_check(")[2].split("def main(")[0]
    check_clean = "_refresh_face()" not in check_body
    helper = text.rpartition("def _refresh_face(")[2].split("def cmd_write(")[0]
    shared = "board_face_landing.refresh_export_face(BASE)" in helper
    no_local_writer = "ER.write(" not in helper and ".write(" not in helper
    return (present, after, check_clean, shared and no_local_writer)


class PWC8FourthProducerClosed(unittest.TestCase):
    """AC-PWC8: first_yuan_path re-derives the face after its landing only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "first_yuan_path.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(fyp_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            '    print("face export=" + _refresh_face())',
            "    pass  # control: closure call removed").replace(
            "board_face_landing.refresh_export_face(BASE)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(fyp_closure_positions(deleted)[0])
        moved = text.replace(
            "    for rel, body in ((HTML_REL, html), (JSON_REL, text)):",
            "    _refresh_face()  # control: moved before the landing\n"
            "    for rel, body in ((HTML_REL, html), (JSON_REL, text)):")
        pos = fyp_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import first_yuan_path as FYP
        calls = []

        class Fake(object):
            def __init__(self, ok, note):
                self.ok, self.note = ok, note

            def refresh_export_face(self, root):
                calls.append(root)
                return (self.ok, self.note, {})

        class Boom(object):
            def refresh_export_face(self, root):
                raise RuntimeError("no writer here")

        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(FYP._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [FYP.BASE])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(FYP._refresh_face(), "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(FYP._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_check_path_does_not_refresh(self):
        import first_yuan_path as FYP
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        saved = sys.modules.get("board_face_landing")
        out = io.StringIO()
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            sys.stdout = out
            FYP.cmd_check()
        finally:
            sys.stdout = saved_stdout
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
        self.assertEqual(calls, [])


def fcl_closure_positions(text, last_landing="f.write(text)"):
    """(present, after_landing, check_clean, shared_only) for AC-PWC9."""
    if "def render(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def render(")[2].split("def check(")[0]
    at = body.find("_refresh_face()")
    present = at != -1
    landing_at = body.rfind(last_landing)
    after = present and landing_at != -1 and at > landing_at
    check_body = text.rpartition("def check(")[2].split("def main(")[0]
    check_clean = "_refresh_face()" not in check_body
    helper = text.rpartition("def _refresh_face(")[2].split("def render(")[0]
    shared = "board_face_landing.refresh_export_face(REPO)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, check_clean, shared and no_local_writer)


class PWC9FifthProducerClosed(unittest.TestCase):
    """AC-PWC9: filing_checklist re-derives the face on its write path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "filing_checklist.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(fcl_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "        LAST_FACE = _refresh_face()",
            "        pass  # control: closure call removed").replace(
            "board_face_landing.refresh_export_face(REPO)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(fcl_closure_positions(deleted)[0])
        moved = text.replace(
            '        with io.open(JSON, "w", encoding="utf-8", newline="\\n") as f:',
            "        _refresh_face()  # control: moved before the JSON landing\n"
            '        with io.open(JSON, "w", encoding="utf-8", newline="\\n") as f:')
        pos = fcl_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import filing_checklist as FCL
        calls = []

        class Fake(object):
            def __init__(self, ok, note):
                self.ok, self.note = ok, note

            def refresh_export_face(self, root):
                calls.append(root)
                return (self.ok, self.note, {})

        class Boom(object):
            def refresh_export_face(self, root):
                raise RuntimeError("no writer here")

        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(FCL._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [FCL.REPO])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(FCL._refresh_face(), "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(FCL._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_only_the_write_mode_closes(self):
        """The tool lands through one function with two modes: measure each."""
        import filing_checklist as FCL
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="fcl-")
        saved_html, saved_json = FCL.HTML, FCL.JSON
        saved = sys.modules.get("board_face_landing")
        cwd = os.getcwd()
        try:
            FCL.HTML = os.path.join(tmp, "filing-checklist.html")
            FCL.JSON = os.path.join(tmp, "filing-checklist.json")
            sys.modules["board_face_landing"] = Fake()
            os.chdir(ROOT)
            FCL.render(write=False)
            self.assertEqual(calls, [])
            FCL.render(write=True)
            self.assertEqual(calls, [FCL.REPO])
            self.assertEqual(len(calls), 1)
            self.assertTrue(os.path.isfile(FCL.HTML))
            self.assertTrue(os.path.isfile(FCL.JSON))
        finally:
            os.chdir(cwd)
            FCL.HTML, FCL.JSON = saved_html, saved_json
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


class PWC10SixthProducerClosed(unittest.TestCase):
    """AC-PWC10: ship_checklist re-derives the face on its write path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "ship_checklist.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(fcl_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "        LAST_FACE = _refresh_face()",
            "        pass  # control: closure call removed").replace(
            "board_face_landing.refresh_export_face(REPO)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(fcl_closure_positions(deleted)[0])
        moved = text.replace(
            '        with io.open(JSON, "w", encoding="utf-8", newline="\\n") as f:',
            "        _refresh_face()  # control: moved before the JSON landing\n"
            '        with io.open(JSON, "w", encoding="utf-8", newline="\\n") as f:')
        pos = fcl_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import ship_checklist as SCL
        calls = []

        class Fake(object):
            def __init__(self, ok, note):
                self.ok, self.note = ok, note

            def refresh_export_face(self, root):
                calls.append(root)
                return (self.ok, self.note, {})

        class Boom(object):
            def refresh_export_face(self, root):
                raise RuntimeError("no writer here")

        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(SCL._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [SCL.REPO])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(SCL._refresh_face(), "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(SCL._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_only_the_write_mode_closes(self):
        """One function, two modes: the scratch render must close nothing."""
        import ship_checklist as SCL
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="scl-")
        saved_html, saved_json = SCL.HTML, SCL.JSON
        saved = sys.modules.get("board_face_landing")
        cwd = os.getcwd()
        try:
            SCL.HTML = os.path.join(tmp, "ship-checklist.html")
            SCL.JSON = os.path.join(tmp, "ship-checklist.json")
            sys.modules["board_face_landing"] = Fake()
            os.chdir(ROOT)
            SCL.render(write=False)
            self.assertEqual(calls, [])
            SCL.render(write=True)
            self.assertEqual(calls, [SCL.REPO])
            self.assertEqual(len(calls), 1)
            self.assertTrue(os.path.isfile(SCL.HTML))
            self.assertTrue(os.path.isfile(SCL.JSON))
        finally:
            os.chdir(cwd)
            SCL.HTML, SCL.JSON = saved_html, saved_json
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def sth_closure_positions(text, last_landing='fh.write("\\n")'):
    """(present, after_landing, check_clean, shared_only) for AC-PWC11."""
    if "def write(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def write(")[2].split("def check(")[0]
    at = body.find("_refresh_face()")
    present = at != -1
    landing_at = body.rfind(last_landing)
    after = present and landing_at != -1 and at > landing_at
    check_body = text.rpartition("def check(")[2].split("def main(")[0]
    check_clean = "_refresh_face()" not in check_body
    helper = text.rpartition("def _refresh_face(")[2].split("LAST_FACE = ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, check_clean, shared and no_local_writer)


class PWC11SeventhProducerClosed(unittest.TestCase):
    """AC-PWC11: start_here re-derives the face on its write path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "start_here.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(sth_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    LAST_FACE = _refresh_face()",
            "    pass  # control: closure call removed").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(sth_closure_positions(deleted)[0])
        moved = text.replace(
            '    with open(OUT_JSON, "w", encoding="utf-8", newline="\\n") as fh:',
            "    _refresh_face()  # control: moved before the JSON landing\n"
            '    with open(OUT_JSON, "w", encoding="utf-8", newline="\\n") as fh:')
        pos = sth_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import start_here as STH
        calls = []

        class Fake(object):
            def __init__(self, ok, note):
                self.ok, self.note = ok, note

            def refresh_export_face(self, root):
                calls.append(root)
                return (self.ok, self.note, {})

        class Boom(object):
            def refresh_export_face(self, root):
                raise RuntimeError("no writer here")

        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(STH._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [STH.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(STH._refresh_face(), "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(STH._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_write_derives_once_and_check_derives_none(self):
        """The landing path derives exactly once; --check derives nothing."""
        import start_here as STH
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="sth-")
        saved_html, saved_json = STH.OUT_HTML, STH.OUT_JSON
        saved = sys.modules.get("board_face_landing")
        cwd = os.getcwd()
        try:
            STH.OUT_HTML = os.path.join(tmp, "start-here.html")
            STH.OUT_JSON = os.path.join(tmp, "start-here.json")
            sys.modules["board_face_landing"] = Fake()
            os.chdir(ROOT)
            STH.write()
            self.assertEqual(calls, [STH.ROOT])
            self.assertEqual(len(calls), 1)
            self.assertTrue(os.path.isfile(STH.OUT_HTML))
            self.assertTrue(os.path.isfile(STH.OUT_JSON))
            calls[:] = []
            saved_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                STH.check()
            finally:
                sys.stdout = saved_stdout
            self.assertEqual(calls, [])
        finally:
            os.chdir(cwd)
            STH.OUT_HTML, STH.OUT_JSON = saved_html, saved_json
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def fyc_closure_positions(text, last_landing="write_atomic(HTML_PATH, body)"):
    """(present, after_landing, check_clean, shared_only) for AC-PWC12."""
    if "def do_render(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def do_render(")[2].split("def do_check(")[0]
    at = body.find("_refresh_face()")
    present = at != -1
    landing_at = body.rfind(last_landing)
    after = present and landing_at != -1 and at > landing_at
    check_body = text.rpartition("def do_check(")[2].split("def main(")[0]
    check_clean = "_refresh_face()" not in check_body
    helper = text.rpartition("def _refresh_face(")[2].split("def do_render(")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, check_clean, shared and no_local_writer)


class PWC12EighthProducerClosed(unittest.TestCase):
    """AC-PWC12: first_yuan_chain re-derives the face on its landing path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "first_yuan_chain.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(fyc_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face()",
            "    pass  # control: closure call removed").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(fyc_closure_positions(deleted)[0])
        moved = text.replace(
            "    write_atomic(JSON_PATH, dumps(payload))",
            "    _refresh_face()  # control: moved before the JSON landing\n"
            "    write_atomic(JSON_PATH, dumps(payload))")
        pos = fyc_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import first_yuan_chain as FYC
        calls = []

        class Fake(object):
            def __init__(self, ok, note):
                self.ok, self.note = ok, note

            def refresh_export_face(self, root):
                calls.append(root)
                return (self.ok, self.note, {})

        class Boom(object):
            def refresh_export_face(self, root):
                raise RuntimeError("no writer here")

        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(FYC._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [FYC.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(FYC._refresh_face(), "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(FYC._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_render_derives_once_and_check_derives_none(self):
        """The landing path derives exactly once; --check derives nothing."""
        import first_yuan_chain as FYC
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="fyc-")
        saved_html, saved_json = FYC.HTML_PATH, FYC.JSON_PATH
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            FYC.HTML_PATH = os.path.join(tmp, "first-yuan-chain.html")
            FYC.JSON_PATH = os.path.join(tmp, "first-yuan-chain.json")
            sys.modules["board_face_landing"] = Fake()
            sys.stdout = io.StringIO()
            FYC.do_render()
            sys.stdout = saved_stdout
            self.assertEqual(calls, [FYC.ROOT])
            self.assertEqual(len(calls), 1)
            self.assertTrue(os.path.isfile(FYC.HTML_PATH))
            self.assertTrue(os.path.isfile(FYC.JSON_PATH))
            calls[:] = []
            sys.stdout = io.StringIO()
            try:
                FYC.do_check()
            finally:
                sys.stdout = saved_stdout
            self.assertEqual(calls, [])
        finally:
            sys.stdout = saved_stdout
            FYC.HTML_PATH, FYC.JSON_PATH = saved_html, saved_json
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def pgr_closure_positions(text, last_landing='fh.write("\\n")'):
    """(present, after_landing, check_clean, shared_only) for AC-PWC13."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2]
    at = body.find("_refresh_face()")
    present = at != -1
    landing_at = body.rfind(last_landing)
    after = present and landing_at != -1 and at > landing_at
    # the --check branch must return before the landing loop, so the closure
    # call can never sit inside it
    check_clean = present and at > body.find("if args.check:")
    helper = text.rpartition("def _refresh_face(")[2].split("def main(")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, check_clean, shared and no_local_writer)


class PWC13NinthProducerClosed(unittest.TestCase):
    """AC-PWC13: payment_gate_report re-derives the face on its landing path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "payment_gate_report.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(pgr_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face()",
            "    face = None  # control: closure call removed").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(pgr_closure_positions(deleted)[0])
        moved = text.replace(
            "    for _ in range(6):",
            "    _refresh_face()  # control: moved before the landing loop\n"
            "    for _ in range(6):")
        pos = pgr_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import payment_gate_report as PGR
        calls = []

        class Fake(object):
            def __init__(self, ok, note):
                self.ok, self.note = ok, note

            def refresh_export_face(self, root):
                calls.append(root)
                return (self.ok, self.note, {})

        class Boom(object):
            def refresh_export_face(self, root):
                raise RuntimeError("no writer here")

        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(PGR._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [PGR.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(PGR._refresh_face(), "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(PGR._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_landing_derives_once_and_check_derives_none(self):
        """The landing path derives exactly once; --check derives nothing."""
        import payment_gate_report as PGR
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="pgr-")
        out = os.path.join(tmp, "payment-gate-report.html")
        jout = os.path.join(tmp, "payment-gate-report.json")
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            sys.stdout = io.StringIO()
            rc = PGR.main(["--out", out, "--json", jout])
            sys.stdout = saved_stdout
            self.assertEqual(calls, [PGR.ROOT])
            self.assertEqual(len(calls), 1)
            self.assertTrue(os.path.isfile(out))
            self.assertTrue(os.path.isfile(jout))
            self.assertIn(rc, (0, 2))
            calls[:] = []
            sys.stdout = io.StringIO()
            try:
                rc2 = PGR.main(["--check", "--out", out, "--json", jout])
            finally:
                sys.stdout = saved_stdout
            self.assertEqual(calls, [])
            self.assertIn(rc2, (0, 2))
        finally:
            sys.stdout = saved_stdout
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def ugr_closure_positions(text, last_landing='fh.write(render_json(data) + "\\n")'):
    """(present, after_landing, check_clean, shared_only) for AC-PWC14."""
    if "def write_outputs(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def write_outputs(")[2].split("\ndef check(")[0]
    at = body.find("_refresh_face()")
    present = at != -1
    landing_at = body.rfind(last_landing)
    after = present and landing_at != -1 and at > landing_at
    check_body = text.rpartition("def check(")[2].split("\ndef ")[0]
    check_clean = present and "_refresh_face(" not in check_body
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef write_outputs(")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, check_clean, shared and no_local_writer)


class PWC14TenthProducerClosed(unittest.TestCase):
    """AC-PWC14: ugc_gate_report re-derives the face on its landing path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "ugc_gate_report.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(ugr_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    if _lands_this_face():\n        LAST_FACE = _refresh_face()",
            "    pass  # control: closure call removed").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(ugr_closure_positions(deleted)[0])
        moved = text.replace(
            "    # R3536 (AC-PWC14): the landing and the CEO face are one derivation."
            "\n    if _lands_this_face():\n        LAST_FACE = _refresh_face()", "").replace(
            "    for _ in range(6):",
            "    _refresh_face()  # control: moved before the landing loop"
            "\n    for _ in range(6):", 1)
        pos = ugr_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import ugc_gate_report as UGR
        calls = []

        class Fake(object):
            def __init__(self, ok, note):
                self.ok, self.note = ok, note

            def refresh_export_face(self, root):
                calls.append(root)
                return (self.ok, self.note, {})

        class Boom(object):
            def refresh_export_face(self, root):
                raise RuntimeError("no writer here")

        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(UGR._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [UGR.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(UGR._refresh_face(), "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(UGR._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this root's preview/ derives once; scratch and --check do not."""
        import ugc_gate_report as UGR
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        data = UGR.collect()
        tmp = tempfile.mkdtemp(prefix="ugr-")
        os.makedirs(os.path.join(tmp, "preview"))
        saved_root, saved_html, saved_json = UGR.ROOT, UGR.OUT_HTML, UGR.OUT_JSON
        saved_mod = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            UGR.ROOT = tmp
            UGR.OUT_HTML = os.path.join(tmp, "preview", "ugc-gate-report.html")
            UGR.OUT_JSON = os.path.join(tmp, "preview", "ugc-gate-report.json")
            UGR.write_outputs(data)
            self.assertEqual(calls, [tmp])
            self.assertEqual(len(calls), 1)
            self.assertTrue(os.path.isfile(UGR.OUT_HTML))
            self.assertTrue(os.path.isfile(UGR.OUT_JSON))

            # scratch render: the halves land outside this root's preview/
            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_json = os.path.join(tmp, "scratch.json")
            UGR.OUT_HTML, UGR.OUT_JSON = scratch_html, scratch_json
            UGR.write_outputs(data)
            self.assertEqual(len(calls), 1)
            self.assertEqual(UGR.LAST_FACE, "")

            UGR.ROOT, UGR.OUT_HTML, UGR.OUT_JSON = saved_root, saved_html, saved_json
            calls[:] = []
            saved_argv = sys.argv
            sys.argv = ["ugc_gate_report.py", "--check"]
            sys.stdout = io.StringIO()
            try:
                rc = UGR.main()
            finally:
                sys.stdout = saved_stdout
                sys.argv = saved_argv
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            UGR.ROOT, UGR.OUT_HTML, UGR.OUT_JSON = saved_root, saved_html, saved_json
            if saved_mod is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved_mod
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
