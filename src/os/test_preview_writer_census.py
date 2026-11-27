"""Battery suite for tools/preview_writer_census.py - AC-PWC1..AC-PWC8 (R3527-R3530).

Pinned in src/os/backlog.md BEFORE the tool, this file and the face_pair_receipt
wiring existed. AC-PWC6 was pinned in the R3528 window before
tools/ledger_reconcile_face.py was touched, AC-PWC7 in R3529 before
tools/lobby_session_trace.py, AC-PWC8 in R3530 before tools/first_yuan_path.py,
AC-PWC9 in R3531 before tools/filing_checklist.py, AC-PWC10 in R3532 before
tools/ship_checklist.py, AC-PWC11 in R3533 before tools/start_here.py.
AC-PWC12 in R3534 before tools/first_yuan_chain.py, AC-PWC13 in R3535 before
tools/payment_gate_report.py, AC-PWC14 in R3536 before tools/ugc_gate_report.py, AC-PWC15 in R3537 before
tools/merchant_onboard.py.

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


def mo_closure_positions(text, last_landing='f.write(text + "\\n")'):
    """(present, after_landing, check_clean, shared_only) for AC-PWC15."""
    if "def write():" not in text:
        return (False, False, False, False)
    body = text.rpartition("def write():")[2].split("\ndef ")[0]
    at = body.find("_refresh_face()")
    present = at != -1
    landing_at = body.rfind(last_landing)
    after = present and landing_at != -1 and at > landing_at
    check_body = text.rpartition("def check():")[2].split("\ndef ")[0]
    check_clean = present and "_refresh_face(" not in check_body
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, check_clean, shared and no_local_writer)


class PWC15EleventhProducerClosed(unittest.TestCase):
    """AC-PWC15: merchant_onboard re-derives the face on its landing path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "merchant_onboard.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(mo_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    _refresh_face()\n    return 0",
            "    return 0  # control: closure call removed").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(mo_closure_positions(deleted)[0])
        moved = text.replace("    _refresh_face()\n    return 0", "    return 0").replace(
            '    out["sizes"]["json_bytes"] = len(text.encode("utf-8")) + 1',
            '    _refresh_face()  # control: moved before the last landing write'
            '\n    out["sizes"]["json_bytes"] = len(text.encode("utf-8")) + 1', 1)
        pos = mo_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import merchant_onboard as MO
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
            self.assertEqual(MO._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [MO.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(MO._refresh_face(), "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(MO._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this root's preview/ derives once; scratch and --check do not."""
        import merchant_onboard as MO
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="mo-")
        os.makedirs(os.path.join(tmp, "preview"))
        saved = (MO.ROOT, MO.PREVIEW, MO.OUT_HTML, MO.OUT_JSON)
        saved_mod = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            MO.ROOT = tmp
            MO.PREVIEW = os.path.join(tmp, "preview")
            MO.OUT_HTML = os.path.join(MO.PREVIEW, "merchant-onboard.html")
            MO.OUT_JSON = os.path.join(MO.PREVIEW, "merchant-onboard.json")
            sys.stdout = io.StringIO()
            RC = MO.write()
            self.assertEqual(RC, 0)
            self.assertEqual(calls, [tmp])
            self.assertEqual(len(calls), 1)
            self.assertTrue(os.path.isfile(MO.OUT_HTML))
            self.assertTrue(os.path.isfile(MO.OUT_JSON))

            # scratch render: the halves land outside this root's preview/
            MO.OUT_HTML = os.path.join(tmp, "scratch.html")
            MO.OUT_JSON = os.path.join(tmp, "scratch.json")
            MO.write()
            self.assertEqual(len(calls), 1)

            MO.ROOT, MO.PREVIEW, MO.OUT_HTML, MO.OUT_JSON = saved
            calls[:] = []
            saved_argv = sys.argv
            sys.argv = ["merchant_onboard.py", "--check"]
            sys.stdout = io.StringIO()
            try:
                rc = MO.main()
            finally:
                sys.stdout = saved_stdout
                sys.argv = saved_argv
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            MO.ROOT, MO.PREVIEW, MO.OUT_HTML, MO.OUT_JSON = saved
            if saved_mod is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved_mod
            shutil.rmtree(tmp, ignore_errors=True)


def bt_closure_positions(text, last_landing='f.write(text + "\\n")'):
    """(present, after_landing, check_clean, shared_only) for AC-PWC16."""
    if "def write():" not in text:
        return (False, False, False, False)
    body = text.rpartition("def write():")[2].split("\ndef ")[0]
    at = body.find("_refresh_face()")
    present = at != -1
    landing_at = body.rfind(last_landing)
    after = present and landing_at != -1 and at > landing_at
    check_body = text.rpartition("def check():")[2].split("\ndef ")[0]
    check_clean = present and "_refresh_face(" not in check_body
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, check_clean, shared and no_local_writer)


class PWC16TwelfthProducerClosed(unittest.TestCase):
    """AC-PWC16: buyer_trial re-derives the face on its landing path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "buyer_trial.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(bt_closure_positions(text), (True, True, True, True))

    def test_four_census_paths_are_one_landing_and_three_reads(self):
        """The census names four html paths; only one pair is ever written."""
        text = self._source()
        body = text.rpartition("def write():")[2].split("\ndef ")[0]
        for name in ("membership-face.html", "merchant-onboard.html",
                     "money-path-demo.html"):
            self.assertNotIn(name, body)
        self.assertIn("OUT_HTML", body)
        self.assertEqual(body.count('io.open(OUT_JSON, "w"'), 2)

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    _refresh_face()\n    return 0",
            "    return 0  # control: closure call removed").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(bt_closure_positions(deleted)[0])
        moved = text.replace("    _refresh_face()\n    return 0", "    return 0").replace(
            '    # record its own size honestly on a second short pass',
            '    _refresh_face()  # control: moved before the last landing write'
            '\n    # record its own size honestly on a second short pass', 1)
        pos = bt_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import buyer_trial as BT
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
            self.assertEqual(BT._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [BT.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(BT._refresh_face(), "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(BT._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this root's preview/ derives once; scratch and --check do not."""
        import buyer_trial as BT
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="bt-")
        os.makedirs(os.path.join(tmp, "preview"))
        saved = (BT.ROOT, BT.PREVIEW, BT.OUT_HTML, BT.OUT_JSON)
        saved_mod = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            BT.ROOT = tmp
            BT.PREVIEW = os.path.join(tmp, "preview")
            BT.OUT_HTML = os.path.join(BT.PREVIEW, "buyer-trial.html")
            BT.OUT_JSON = os.path.join(BT.PREVIEW, "buyer-trial.json")
            sys.stdout = io.StringIO()
            RC = BT.write()
            self.assertEqual(RC, 0)
            self.assertEqual(calls, [tmp])
            self.assertEqual(len(calls), 1)
            self.assertTrue(os.path.isfile(BT.OUT_HTML))
            self.assertTrue(os.path.isfile(BT.OUT_JSON))

            # scratch render: the halves land outside this root's preview/
            BT.OUT_HTML = os.path.join(tmp, "scratch.html")
            BT.OUT_JSON = os.path.join(tmp, "scratch.json")
            BT.write()
            self.assertEqual(len(calls), 1)

            BT.ROOT, BT.PREVIEW, BT.OUT_HTML, BT.OUT_JSON = saved
            calls[:] = []
            sys.stdout = io.StringIO()
            try:
                rc = BT.main(["--check"])
            finally:
                sys.stdout = saved_stdout
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            BT.ROOT, BT.PREVIEW, BT.OUT_HTML, BT.OUT_JSON = saved
            if saved_mod is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved_mod
            shutil.rmtree(tmp, ignore_errors=True)


def mf_closure_positions(text):
    """(present, after_landing, gate_clean, shared_only) for AC-PWC17."""
    if "def main(argv):" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(argv):")[2].split("\ndef ")[0]
    at = body.find("_refresh_face()")
    present = at != -1
    landing_at = body.rfind("write_atomic(OUT_HTML, html_text.encode")
    after = present and landing_at != -1 and at > landing_at
    gate_body = text.rpartition("def gate(")[2].split("\ndef ")[0]
    gate_clean = present and "_refresh_face(" not in gate_body
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, gate_clean, shared and no_local_writer)


class PWC17ThirteenthProducerClosed(unittest.TestCase):
    """AC-PWC17: membership_face re-derives the face on its landing path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "membership_face.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(mf_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    _refresh_face()\n    return 0",
            "    return 0  # control: closure call removed").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(mf_closure_positions(deleted)[0])
        moved = text.replace("    _refresh_face()\n    return 0", "    return 0").replace(
            "    write_atomic(OUT_JSON, json_bytes)",
            "    _refresh_face()  # control: moved before the last landing write"
            "\n    write_atomic(OUT_JSON, json_bytes)", 1)
        pos = mf_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import membership_face as MF
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
            self.assertEqual(MF._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [MF.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(MF._refresh_face(), "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(MF._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this root's preview/ derives once; scratch and --check do not."""
        import membership_face as MF
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="mf-")
        saved = (MF.OUT_HTML, MF.OUT_JSON, MF.write_atomic)
        saved_mod = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            MF.write_atomic = lambda path, data: None  # no bytes touched
            sys.stdout = io.StringIO()
            self.assertEqual(MF.main([]), 0)
            self.assertEqual(calls, [MF.ROOT])
            self.assertEqual(len(calls), 1)

            # scratch render: the halves land outside this root's preview/
            MF.OUT_HTML = os.path.join(tmp, "scratch.html")
            MF.OUT_JSON = os.path.join(tmp, "scratch.json")
            MF.main([])
            self.assertEqual(len(calls), 1)

            MF.OUT_HTML, MF.OUT_JSON, MF.write_atomic = saved
            calls[:] = []
            sys.stdout = io.StringIO()
            try:
                rc = MF.main(["--check"])
            finally:
                sys.stdout = saved_stdout
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            MF.OUT_HTML, MF.OUT_JSON, MF.write_atomic = saved
            if saved_mod is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved_mod
            shutil.rmtree(tmp, ignore_errors=True)


def jd_closure_positions(text):
    """(present, after_landing, check_clean, shared_only) for AC-PWC18."""
    if "def write_artifacts(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def write_artifacts(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face()")
    present = at != -1
    landing_at = body.rfind("fh.write(json_text)")
    after = present and landing_at != -1 and at > landing_at
    check_body = text.rpartition("def check(")[2].split("\ndef ")[0]
    check_clean = present and "_refresh_face(" not in check_body
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, check_clean, shared and no_local_writer)


class PWC18FourteenthProducerClosed(unittest.TestCase):
    """AC-PWC18: journey_demo re-derives the face on its landing path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "journey_demo.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(jd_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    LAST_FACE = _refresh_face()\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(jd_closure_positions(deleted)[0])
        moved = text.replace(
            "    LAST_FACE = _refresh_face()\n", "").replace(
            "        fh.write(json_text)",
            "        LAST_FACE = _refresh_face()  # control: moved before the last landing write"
            "\n        fh.write(json_text)", 1)
        pos = jd_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import journey_demo as JD
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
            self.assertEqual(JD._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [JD.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(JD._refresh_face(), "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(JD._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in its own preview derives once; scratch and --check do not."""
        import journey_demo as JD
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="jd-")
        world = os.path.join(tmp, "preview")
        os.makedirs(world)
        saved = (JD.PREVIEW, JD.OUT_HTML, JD.OUT_JSON)
        saved_mod = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            JD.PREVIEW = world
            JD.OUT_HTML = os.path.join(world, "journey-19.9.html")
            JD.OUT_JSON = os.path.join(world, "journey-19.9.json")
            JD.write_artifacts("<html></html>", "{}\n")
            self.assertEqual(calls, [JD.ROOT])
            self.assertEqual(len(calls), 1)

            # scratch render: the halves land outside the tool's own preview
            JD.OUT_HTML = os.path.join(tmp, "scratch.html")
            JD.OUT_JSON = os.path.join(tmp, "scratch.json")
            JD.write_artifacts("<html></html>", "{}\n")
            self.assertEqual(len(calls), 1)

            # --check returns through check() and never reaches write_artifacts
            JD.PREVIEW = world
            JD.OUT_HTML = os.path.join(world, "journey-19.9.html")
            JD.OUT_JSON = os.path.join(world, "journey-19.9.json")
            html_text, json_text, _doc = JD.render_fixed_point()
            with io.open(JD.OUT_HTML, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(html_text)
            with io.open(JD.OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(json_text)
            before = len(calls)
            sys.stdout = io.StringIO()
            try:
                rc = JD.main(["--check"])
            finally:
                sys.stdout = saved_stdout
            self.assertEqual(len(calls), before)
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            JD.PREVIEW, JD.OUT_HTML, JD.OUT_JSON = saved
            if saved_mod is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved_mod
            shutil.rmtree(tmp, ignore_errors=True)


def mpd_closure_positions(text):
    """(present, after_landing, check_clean, shared_only) for AC-PWC19."""
    if "def write_all(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def write_all(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(")
    present = at != -1
    landing_at = body.rfind("fh.write(html)")
    after = present and landing_at != -1 and at > landing_at
    check_body = text.rpartition("def check(")[2].split("\ndef ")[0]
    check_clean = present and "_refresh_face(" not in check_body
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, check_clean, shared and no_local_writer)


class PWC19FifteenthProducerClosed(unittest.TestCase):
    """AC-PWC19: money_path_demo re-derives the face on its landing path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "money_path_demo.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(mpd_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    LAST_FACE = _refresh_face(html_path, json_path)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(mpd_closure_positions(deleted)[0])
        moved = text.replace(
            "    LAST_FACE = _refresh_face(html_path, json_path)\n", "").replace(
            "        fh.write(html)",
            "        LAST_FACE = _refresh_face(html_path, json_path)"
            "  # control: moved before the last landing write\n        fh.write(html)", 1)
        pos = mpd_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import money_path_demo as MPD
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

        pair = (os.path.join(MPD.PREVIEW, MPD.HTML_NAME),
                os.path.join(MPD.PREVIEW, MPD.JSON_NAME))
        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(MPD._refresh_face(*pair), "WRITTEN")
            self.assertEqual(calls, [MPD.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(MPD._refresh_face(*pair),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(MPD._refresh_face(*pair), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this root's preview derives once; scratch and --check do not."""
        import builtins
        import money_path_demo as MPD
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="mpd-")
        world = os.path.join(tmp, "preview")
        os.makedirs(world)
        for name in MPD.SOURCE_NAMES.values():
            shutil.copyfile(os.path.join(MPD.PREVIEW, name),
                            os.path.join(world, name))
        saved = MPD.PREVIEW
        saved_mod = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        real_open = builtins.open
        sink = os.path.join(tmp, "sink.bin")
        try:
            sys.modules["board_face_landing"] = Fake()

            def fake_open(path, mode="r", *a, **k):
                if "w" in mode:
                    return real_open(sink, "w")
                return real_open(path, mode, *a, **k)

            builtins.open = fake_open
            try:
                MPD.write_all()
            finally:
                builtins.open = real_open
            self.assertEqual(calls, [MPD.ROOT])
            self.assertEqual(len(calls), 1)

            # scratch render: PREVIEW points away from this root's preview
            MPD.PREVIEW = world
            MPD.write_all()
            self.assertEqual(len(calls), 1)

            # --check reads and never reaches write_all()
            MPD.PREVIEW = saved
            before = len(calls)
            sys.stdout = io.StringIO()
            try:
                rc = MPD.main(["--check"])
            finally:
                sys.stdout = saved_stdout
            self.assertEqual(len(calls), before)
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            MPD.PREVIEW = saved
            if saved_mod is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved_mod
            shutil.rmtree(tmp, ignore_errors=True)


def mbr_closure_positions(text):
    """(present, after_landing, readers_clean, shared_only) for AC-PWC20."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(")
    present = at != -1
    landing_at = body.rfind("handle.write(payload)")
    after = present and landing_at != -1 and at > landing_at
    readers = True
    for name in ("def verify(", "def measure("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC20SixteenthProducerClosed(unittest.TestCase):
    """AC-PWC20: membership_benefit_report re-derives the face on its landing path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "membership_benefit_report.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(mbr_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    LAST_FACE = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(mbr_closure_positions(deleted)[0])
        moved = text.replace(
            "    LAST_FACE = _refresh_face(args.out, args.json)\n", "").replace(
            "        handle.write(body)",
            "        LAST_FACE = _refresh_face(args.out, args.json)"
            "  # control: moved before the last landing write\n"
            "        handle.write(body)", 1)
        pos = mbr_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import membership_benefit_report as MBR
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

        pair = (os.path.join(MBR.ROOT, "preview",
                             "membership-benefit-report.html"),
                os.path.join(MBR.ROOT, "preview",
                             "membership-benefit-report.json"))
        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(MBR._refresh_face(*pair), "WRITTEN")
            self.assertEqual(calls, [MBR.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(MBR._refresh_face(*pair),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(MBR._refresh_face(*pair), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this root's preview derives once; scratch and --check do not."""
        import builtins
        import membership_benefit_report as MBR
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="mbr-")
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        real_open = builtins.open
        sink = os.path.join(tmp, "sink.bin")
        try:
            sys.modules["board_face_landing"] = Fake()

            def fake_open(path, mode="r", *a, **k):
                if "w" in mode:
                    if "b" in mode:
                        return real_open(sink, "wb")
                    return real_open(sink, "w", encoding="utf-8", newline="")
                return real_open(path, mode, *a, **k)

            builtins.open = fake_open
            try:
                sys.stdout = io.StringIO()
                MBR.main([])
            finally:
                builtins.open = real_open
            self.assertEqual(calls, [MBR.ROOT])
            self.assertEqual(len(calls), 1)

            # scratch render: both halves land away from this root's preview
            scratch = os.path.join(tmp, "scratch")
            os.makedirs(scratch, exist_ok=True)
            builtins.open = fake_open
            try:
                sys.stdout = io.StringIO()
                MBR.main(["--out", os.path.join(scratch, "o.html"),
                          "--json", os.path.join(scratch, "o.json")])
            finally:
                builtins.open = real_open
            self.assertEqual(len(calls), 1)

            # --check reads and never reaches the landing writes
            before = len(calls)
            sys.stdout = io.StringIO()
            try:
                rc = MBR.main(["--check"])
            finally:
                sys.stdout = saved_stdout
            self.assertEqual(len(calls), before)
            self.assertIn(rc, (0, 2, 3))
        finally:
            sys.stdout = saved_stdout
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def lws_closure_positions(text):
    """(present, after_landing, readers_clean, shared_only) for AC-PWC21."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(")
    present = at != -1
    last_write = body.rfind("_write(json_text, JSON_PATH)")
    # the sizes fixed-point loop may write the pair up to six times, so the
    # closure must sit AFTER the loop, not inside it
    loop_end = body.find('print("VERDICT FAIL size fixed point did not converge")')
    after = (present and last_write != -1 and loop_end != -1
             and at > last_write and at > loop_end)
    readers = True
    for name in ("def render(", "def build_evidence(", "def run_measurement("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC21SeventeenthProducerClosed(unittest.TestCase):
    """AC-PWC21: lobby_ws_report re-derives the face on its landing path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "lobby_ws_report.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(lws_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(HTML_PATH, JSON_PATH)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(lws_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(HTML_PATH, JSON_PATH)\n", "").replace(
            "        html_bytes = _write(doc, HTML_PATH)",
            "        html_bytes = _write(doc, HTML_PATH)\n"
            "        face = _refresh_face(HTML_PATH, JSON_PATH)"
            "  # control: moved inside the loop", 1)
        pos = lws_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import lobby_ws_report as LWS
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

        pair = (os.path.join(LWS.ROOT, "preview", "lobby-ws-report.html"),
                os.path.join(LWS.ROOT, "preview", "lobby-ws-report.json"))
        self.assertTrue(LWS._landing_is_default(*pair))
        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(LWS._refresh_face(*pair), "WRITTEN")
            self.assertEqual(calls, [LWS.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(LWS._refresh_face(*pair),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(LWS._refresh_face(*pair), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this root's own preview derives once; scratch and --check do not."""
        import lobby_ws_report as LWS
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        facts = {
            "uri": "ws://127.0.0.1:0/ws",
            "risk_text": "stand-in risk text",
            "hello": {"payload": {"v": 1, "rooms": ["lobby"]}},
            "risk": {"payload": {"text": "stand-in risk text"}},
            "broadcast": {"type": "chat.broadcast"},
            "census": {"id": "c1", "served": ["name"],
                       "whitelist": ["name", "tier"]},
            "shipped_sha": {},
        }
        ev = {cid: {"pass": True, "measured": "synthetic row for %s" % cid}
              for cid, _intent in LWS.CRITERIA}
        tmp = tempfile.mkdtemp(prefix="lws-")
        inner = os.path.join(tmp, "preview")
        os.makedirs(inner)
        saved_mod = sys.modules.get("board_face_landing")
        saved = (LWS.ROOT, LWS.PREVIEW, LWS.HTML_PATH, LWS.JSON_PATH,
                 LWS.build_evidence)
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            LWS.ROOT = tmp
            LWS.PREVIEW = inner
            LWS.HTML_PATH = os.path.join(inner, "lobby-ws-report.html")
            LWS.JSON_PATH = os.path.join(inner, "lobby-ws-report.json")
            LWS.build_evidence = lambda: (ev, facts)
            sys.stdout = io.StringIO()
            LWS.main([])
            self.assertEqual(calls, [tmp])
            self.assertEqual(len(calls), 1)

            # scratch render: both halves land away from this root's preview
            scratch = os.path.join(tmp, "scratch")
            os.makedirs(scratch, exist_ok=True)
            LWS.HTML_PATH = os.path.join(scratch, "o.html")
            LWS.JSON_PATH = os.path.join(scratch, "o.json")
            LWS.main([])
            self.assertEqual(len(calls), 1)

            # --check reads and never reaches the landing writes
            LWS.HTML_PATH = os.path.join(inner, "lobby-ws-report.html")
            LWS.JSON_PATH = os.path.join(inner, "lobby-ws-report.json")
            before = len(calls)
            rc = LWS.main(["--check"])
            self.assertEqual(len(calls), before)
            self.assertIn(rc, (0, 2, 3))
        finally:
            sys.stdout = saved_stdout
            LWS.ROOT, LWS.PREVIEW, LWS.HTML_PATH, LWS.JSON_PATH, LWS.build_evidence = saved
            if saved_mod is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved_mod
            shutil.rmtree(tmp, ignore_errors=True)


def lpm_closure_positions(text):
    """(present, after_landing, readers_clean, shared_only) for AC-PWC22."""
    if "def write_artifacts(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def write_artifacts(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(HTML, JSON_OUT)")
    present = at != -1
    last_write = body.rfind("f.write(js)")
    after = present and last_write != -1 and at > last_write
    readers = True
    for name in ("def check(", "def payload(", "def render_html("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC22EighteenthProducerClosed(unittest.TestCase):
    """AC-PWC22: lobby_protocol_map re-derives the face on its landing path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "lobby_protocol_map.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(lpm_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            '    p["face"] = _refresh_face(HTML, JSON_OUT)\n', "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(lpm_closure_positions(deleted)[0])
        moved = text.replace(
            '    p["face"] = _refresh_face(HTML, JSON_OUT)\n', "").replace(
            '    with open(JSON_OUT, "w", encoding="utf-8", newline="\\n") as f:',
            '    p["face"] = _refresh_face(HTML, JSON_OUT)  # control: moved\n'
            '    with open(JSON_OUT, "w", encoding="utf-8", newline="\\n") as f:', 1)
        pos = lpm_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import lobby_protocol_map as LPM
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

        pair = (os.path.join(LPM.ROOT, "preview", "lobby-protocol-map.html"),
                os.path.join(LPM.ROOT, "preview", "lobby-protocol-map.json"))
        self.assertTrue(LPM._landing_is_default(*pair))
        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(LPM._refresh_face(*pair), "WRITTEN")
            self.assertEqual(calls, [LPM.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(LPM._refresh_face(*pair),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(LPM._refresh_face(*pair), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this root's own preview derives once; scratch and --check do not."""
        import lobby_protocol_map as LPM
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="lpm-pwc-")
        write(os.path.join(tmp, "docs", "spec", "lobby-websocket-spec.md"),
              "# spec\n\n## one\n\nThe server answers `sys.hello` first.\n\n"
              "| # | row | method |\n|---|---|---|\n| AC-S1 | hello | assert |\n")
        write(os.path.join(tmp, "src", "sandbox", "lobby", "server.py"),
              "HELLO = 'sys.hello'\n")
        saved_mod = sys.modules.get("board_face_landing")
        saved = (LPM.ROOT, LPM.SPEC, LPM.IMPL, LPM.HTML, LPM.JSON_OUT)
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            LPM.ROOT = tmp
            LPM.SPEC = os.path.join(tmp, "docs", "spec", "lobby-websocket-spec.md")
            LPM.IMPL = os.path.join(tmp, "src", "sandbox", "lobby", "server.py")
            LPM.HTML = os.path.join(tmp, "preview", "lobby-protocol-map.html")
            LPM.JSON_OUT = os.path.join(tmp, "preview", "lobby-protocol-map.json")
            sys.stdout = io.StringIO()
            LPM.write_artifacts()
            self.assertEqual(calls, [tmp])
            scratch = os.path.join(tmp, "scratch")
            os.makedirs(scratch, exist_ok=True)
            LPM.HTML = os.path.join(scratch, "o.html")
            LPM.JSON_OUT = os.path.join(scratch, "o.json")
            LPM.write_artifacts()
            self.assertEqual(len(calls), 1)
            LPM.HTML = os.path.join(tmp, "preview", "lobby-protocol-map.html")
            LPM.JSON_OUT = os.path.join(tmp, "preview", "lobby-protocol-map.json")
            before = len(calls)
            sys.argv = ["lobby_protocol_map.py", "--check"]
            rc = LPM.main()
            self.assertEqual(len(calls), before)
            self.assertIn(rc, (0, 2, 3))
        finally:
            sys.stdout = saved_stdout
            LPM.ROOT, LPM.SPEC, LPM.IMPL, LPM.HTML, LPM.JSON_OUT = saved
            if saved_mod is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved_mod
            shutil.rmtree(tmp, ignore_errors=True)


def clw_closure_positions(text):
    """(present, after_landing, readers_clean, shared_only) for AC-PWC23."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face()")
    present = at != -1
    last_write = body.rfind("handle.write(render_html(payload))")
    after = present and last_write != -1 and at > last_write
    readers = True
    for name in ("def check(", "def build(", "def render_html("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC23TwentyFifthProducerClosed(unittest.TestCase):
    """AC-PWC23: core_loop_walkthrough re-derives the face on its landing path only."""

    def _source(self):
        with io.open(os.path.join(TOOLS, "core_loop_walkthrough.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_landing(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 2)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(clw_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face()\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(clw_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face()\n", "").replace(
            '    with io.open(HTML_PATH, "w", encoding="utf-8", newline="\\n") as handle:\n'
            '        handle.write(render_html(payload))',
            '    face = _refresh_face()  # control: moved before the last landing write\n'
            '    with io.open(HTML_PATH, "w", encoding="utf-8", newline="\\n") as handle:\n'
            '        handle.write(render_html(payload))', 1)
        pos = clw_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import core_loop_walkthrough as CLW
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

        self.assertTrue(CLW._landing_is_default())
        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(CLW._refresh_face(), "WRITTEN")
            self.assertEqual(calls, [CLW.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(CLW._refresh_face(),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(CLW._refresh_face(), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this root's own preview derives once; scratch and --check do not."""
        # Two sandboxes ship a top-level `store` module, so this in-process arm
        # pins the ugc one before the walkthrough module binds its imports.
        ugc_dir = os.path.join(ROOT, "src", "sandbox", "ugc")
        if ugc_dir not in sys.path:
            sys.path.insert(0, ugc_dir)
        saved_store = sys.modules.pop("store", None)
        saved_pipeline = sys.modules.pop("pipeline", None)
        import core_loop_walkthrough as CLW
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="clw-pwc-")
        for rel in (("src", "sandbox", "ugc", "pipeline.py"),
                    ("src", "sandbox", "ledger", "ledger.py")):
            path = os.path.join(tmp, *rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with io.open(path, "w", encoding="utf-8") as f:
                f.write("# private world stand-in\n")
        os.makedirs(os.path.join(tmp, "preview"), exist_ok=True)
        saved_mod = sys.modules.get("board_face_landing")
        saved = (CLW.ROOT, CLW.PREVIEW, CLW.JSON_PATH, CLW.HTML_PATH)
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            CLW.ROOT = tmp
            CLW.PREVIEW = os.path.join(tmp, "preview")
            CLW.JSON_PATH = os.path.join(CLW.PREVIEW, "core-loop-walkthrough.json")
            CLW.HTML_PATH = os.path.join(CLW.PREVIEW, "core-loop-walkthrough.html")
            sys.stdout = io.StringIO()
            rc = CLW.main([])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(CLW.HTML_PATH))
            self.assertTrue(os.path.isfile(CLW.JSON_PATH))

            # scratch render: the halves land in this root, but not in preview/
            CLW.HTML_PATH = os.path.join(tmp, "scratch.html")
            CLW.JSON_PATH = os.path.join(tmp, "scratch.json")
            CLW.main([])
            self.assertEqual(len(calls), 1)

            CLW.ROOT, CLW.PREVIEW, CLW.JSON_PATH, CLW.HTML_PATH = saved
            calls[:] = []
            sys.stdout = io.StringIO()
            rc = CLW.main(["--check"])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            CLW.ROOT, CLW.PREVIEW, CLW.JSON_PATH, CLW.HTML_PATH = saved
            if saved_mod is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved_mod
            if saved_store is not None:
                sys.modules["store"] = saved_store
            if saved_pipeline is not None:
                sys.modules["pipeline"] = saved_pipeline
            shutil.rmtree(tmp, ignore_errors=True)


def plr_closure_positions(text):
    """(present, after_landing, readers_clean, shared_only) for AC-PWC24."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(HTML_PATH, JSON_PATH)")
    present = at != -1
    last_write = body.rfind("_write(json_text, JSON_PATH)")
    after = present and last_write != -1 and at > last_write
    readers = True
    for name in ("def check(", "def measure(", "def render("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC24NineteenthProducerClosed(unittest.TestCase):
    """AC-PWC24: platform_live_report re-derives the face on its landing path only.

    That tool's own measure() boots the whole sandbox over real loopback sockets
    for up to 45 seconds, so the behavioural arms replace measure() with a
    synthetic (evidence, facts) pair and grade ONLY the number of face
    derivations; no socket is opened and no child process is spawned here.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "platform_live_report.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(plr_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(HTML_PATH, JSON_PATH)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(plr_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(HTML_PATH, JSON_PATH)\n", "").replace(
            "        json_bytes = _write(json_text, JSON_PATH)",
            "        face = _refresh_face(HTML_PATH, JSON_PATH)  "
            "# control: moved before the last landing write\n"
            "        json_bytes = _write(json_text, JSON_PATH)", 1)
        pos = plr_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import platform_live_report as PLR
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

        self.assertTrue(PLR._landing_is_default(PLR.HTML_PATH, PLR.JSON_PATH))
        saved = sys.modules.get("board_face_landing")
        try:
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(PLR._refresh_face(PLR.HTML_PATH, PLR.JSON_PATH),
                             "WRITTEN")
            self.assertEqual(calls, [PLR.ROOT])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(PLR._refresh_face(PLR.HTML_PATH, PLR.JSON_PATH),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(PLR._refresh_face(PLR.HTML_PATH, PLR.JSON_PATH),
                             "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import platform_live_report as PLR
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        def synthetic():
            keys = ("city", "lobby", "ledger", "ugc", "hub")
            faces, pages, ports = {}, {}, {}
            for i, key in enumerate(keys):
                faces[key] = "http://127.0.0.1:%d/" % (8000 + i)
                ports[key] = 8000 + i
                pages[key] = {"url": faces[key], "status": 200,
                              "bytes": 100 + i, "ctype": "text/html",
                              "title": "door " + key,
                              "sha": "%016x" % (i + 1)}
            facts = {
                "host": "127.0.0.1",
                "hub_url": faces["hub"],
                "ports": ports,
                "faces": faces,
                "pages": pages,
                "city_snapshot": {"status": 200, "bytes": 10,
                                  "keys": ["as_of"],
                                  "as_of": "2026-11-27T00:00:00"},
                "hub_live": dict((k, True) for k in keys),
                "ports_refusing": dict((k, True) for k in keys),
                "children_gone": {"child": True},
                "shipped_before": {"src/sandbox/start_all.py": "0" * 16},
                "shipped_after": {"src/sandbox/start_all.py": "0" * 16},
                "url_literals": [],
                "external_literals": [],
            }
            evidence = dict((cid, {"pass": True, "measured": "synthetic"})
                            for cid, _ in PLR.CRITERIA)
            return evidence, facts

        tmp = tempfile.mkdtemp(prefix="plr-pwc-")
        os.makedirs(os.path.join(tmp, "preview"), exist_ok=True)
        saved_mod = sys.modules.get("board_face_landing")
        saved = (PLR.ROOT, PLR.PREVIEW, PLR.HTML_PATH, PLR.JSON_PATH, PLR.measure)
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            PLR.ROOT = tmp
            PLR.PREVIEW = os.path.join(tmp, "preview")
            PLR.HTML_PATH = os.path.join(PLR.PREVIEW, "platform-live-report.html")
            PLR.JSON_PATH = os.path.join(PLR.PREVIEW, "platform-live-report.json")
            PLR.measure = synthetic
            sys.stdout = io.StringIO()
            rc = PLR.main([])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(PLR.HTML_PATH))
            self.assertTrue(os.path.isfile(PLR.JSON_PATH))

            # scratch render: the halves land outside this world's preview/
            PLR.HTML_PATH = os.path.join(tmp, "scratch.html")
            PLR.JSON_PATH = os.path.join(tmp, "scratch.json")
            PLR.main([])
            self.assertEqual(len(calls), 1)

            # --check is read-only: it derives nothing
            PLR.HTML_PATH = os.path.join(PLR.PREVIEW, "platform-live-report.html")
            PLR.JSON_PATH = os.path.join(PLR.PREVIEW, "platform-live-report.json")
            calls[:] = []
            rc = PLR.main(["--check"])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            (PLR.ROOT, PLR.PREVIEW, PLR.HTML_PATH, PLR.JSON_PATH,
             PLR.measure) = saved
            if saved_mod is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved_mod
            shutil.rmtree(tmp, ignore_errors=True)


def lbr_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC25."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find('if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def build_html(", "def check_sizes(", "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC25TwentiethProducerClosed(unittest.TestCase):
    """AC-PWC25: ledger_business_report re-derives the face on its landing path only.

    That tool seeds a demo ledger and runs the shipped reconciler, so its main()
    really does write a database; the behavioural arms point every output at a
    private world, so nothing of this repository moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "ledger_business_report.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(lbr_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(lbr_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = lbr_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import ledger_business_report as LBR
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

        tmp = tempfile.mkdtemp(prefix="lbr-face-")
        saved_root = LBR.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            LBR.ROOT = tmp
            os.makedirs(os.path.join(tmp, "preview"), exist_ok=True)
            html = os.path.join(tmp, "preview", "ledger-business-report.html")
            js = os.path.join(tmp, "preview", "ledger-business-report.json")
            self.assertTrue(LBR._landing_is_default(html, js))
            self.assertFalse(LBR._landing_is_default(os.path.join(tmp, "a.html"), js))
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(LBR._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(LBR._refresh_face(html, js),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(LBR._refresh_face(html, js), "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            LBR.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import ledger_business_report as LBR
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="lbr-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        db = os.path.join(tmp, "demo.db")
        html = os.path.join(preview, "ledger-business-report.html")
        js = os.path.join(preview, "ledger-business-report.json")
        saved_root = LBR.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            LBR.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = LBR.main(["prog", "--db", db, "--out", html, "--json", js])
            self.assertIn(rc, (0, 2))
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            # scratch render: the halves land in this world, but not in preview/
            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            LBR.main(["prog", "--db", db, "--out", scratch_html, "--json", scratch_js])
            self.assertEqual(len(calls), 1)

            # --check is read-only: it derives nothing
            calls[:] = []
            rc = LBR.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            LBR.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def mhh_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC26."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_face(", "def build_html(",
                 "def check_sizes(", "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC26TwentyFirstProducerClosed(unittest.TestCase):
    """AC-PWC26: market_hour_heatmap re-derives the face on its landing path only.

    That tool's read_face() builds a demo stack in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "market_hour_heatmap.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(mhh_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(mhh_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = mhh_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import market_hour_heatmap as MHH
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

        tmp = tempfile.mkdtemp(prefix="mhh-face-")
        saved_root = MHH.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            MHH.ROOT = tmp
            os.makedirs(os.path.join(tmp, "preview"), exist_ok=True)
            html = os.path.join(tmp, "preview", "market-hour-heatmap.html")
            js = os.path.join(tmp, "preview", "market-hour-heatmap.json")
            self.assertTrue(MHH._landing_is_default(html, js))
            self.assertFalse(MHH._landing_is_default(
                os.path.join(tmp, "a.html"), js))
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(MHH._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(
                False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(MHH._refresh_face(html, js),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(MHH._refresh_face(html, js),
                             "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            MHH.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import market_hour_heatmap as MHH
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="mhh-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "market-hour-heatmap.html")
        js = os.path.join(preview, "market-hour-heatmap.json")
        saved_root = MHH.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            MHH.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = MHH.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = MHH.main(["prog", "--out", scratch_html, "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = MHH.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            MHH.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def sqs_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC27."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_face(", "def build_html(",
                 "def check_sizes(", "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC27TwentySecondProducerClosed(unittest.TestCase):
    """AC-PWC27: seller_quality_scorecard re-derives the face on its landing path only.

    That tool's read_face() builds a demo world in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "seller_quality_scorecard.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(sqs_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(sqs_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = sqs_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import seller_quality_scorecard as SQS
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

        tmp = tempfile.mkdtemp(prefix="sqs-face-")
        saved_root = SQS.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            SQS.ROOT = tmp
            os.makedirs(os.path.join(tmp, "preview"), exist_ok=True)
            html = os.path.join(tmp, "preview", "seller-quality-scorecard.html")
            js = os.path.join(tmp, "preview", "seller-quality-scorecard.json")
            self.assertTrue(SQS._landing_is_default(html, js))
            self.assertFalse(SQS._landing_is_default(
                os.path.join(tmp, "a.html"), js))
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(SQS._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(
                False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(SQS._refresh_face(html, js),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(SQS._refresh_face(html, js),
                             "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            SQS.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import seller_quality_scorecard as SQS
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="sqs-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "seller-quality-scorecard.html")
        js = os.path.join(preview, "seller-quality-scorecard.json")
        saved_root = SQS.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            SQS.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = SQS.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = SQS.main(["prog", "--out", scratch_html, "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = SQS.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            SQS.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def srv_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC28."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_sellers(", "def build_html(",
                 "def check_sizes(", "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC28TwentyThirdProducerClosed(unittest.TestCase):
    """AC-PWC28: seller_revenue_board re-derives the face on its landing path only.

    That tool's read_sellers() builds a demo ledger in a private temp dir, so
    the behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "seller_revenue_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(srv_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(srv_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = srv_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import seller_revenue_board as SRV
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

        tmp = tempfile.mkdtemp(prefix="srv-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "seller-revenue-board.html")
        js = os.path.join(preview, "seller-revenue-board.json")
        saved_root = SRV.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            SRV.ROOT = tmp
            self.assertTrue(SRV._landing_is_default(html, js))
            self.assertFalse(SRV._landing_is_default(
                os.path.join(tmp, "a.html"), js))
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(SRV._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(
                False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(SRV._refresh_face(html, js),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(SRV._refresh_face(html, js),
                             "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            SRV.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import seller_revenue_board as SRV
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="srv-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "seller-revenue-board.html")
        js = os.path.join(preview, "seller-revenue-board.json")
        saved_root = SRV.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            SRV.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = SRV.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = SRV.main(["prog", "--out", scratch_html, "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = SRV.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            SRV.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def svrb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC29."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_world(", "def check_laws(",
                 "def build_html(", "def check_sizes(", "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC29TwentyFourthProducerClosed(unittest.TestCase):
    """AC-PWC29: seller_reviews_board re-derives the face on its landing path only.

    That tool's read_world() builds a demo world in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "seller_reviews_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(svrb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(svrb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = svrb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import seller_reviews_board as SRVB
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

        tmp = tempfile.mkdtemp(prefix="svrb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "seller-reviews-board.html")
        js = os.path.join(preview, "seller-reviews-board.json")
        saved_root = SRVB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            SRVB.ROOT = tmp
            self.assertTrue(SRVB._landing_is_default(html, js))
            self.assertFalse(SRVB._landing_is_default(
                os.path.join(tmp, "a.html"), js))
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(SRVB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(
                False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(SRVB._refresh_face(html, js),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(SRVB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            SRVB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import seller_reviews_board as SRVB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="svrb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "seller-reviews-board.html")
        js = os.path.join(preview, "seller-reviews-board.json")
        saved_root = SRVB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            SRVB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = SRVB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = SRVB.main(["prog", "--out", scratch_html, "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = SRVB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            SRVB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def slb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC30."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_sellers(", "def check_laws(",
                 "def build_html(", "def check_sizes(", "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC30TwentySixthProducerClosed(unittest.TestCase):
    """AC-PWC30: seller_ledger_board re-derives the face on its landing path only.

    That tool's read_sellers() builds a demo world in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "seller_ledger_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(slb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(slb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = slb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import seller_ledger_board as SLB
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

        tmp = tempfile.mkdtemp(prefix="slb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "seller-ledger-board.html")
        js = os.path.join(preview, "seller-ledger-board.json")
        saved_root = SLB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            SLB.ROOT = tmp
            self.assertTrue(SLB._landing_is_default(html, js))
            self.assertFalse(SLB._landing_is_default(
                os.path.join(tmp, "a.html"), js))
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(SLB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(
                False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(SLB._refresh_face(html, js),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(SLB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            SLB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import seller_ledger_board as SLB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="slb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "seller-ledger-board.html")
        js = os.path.join(preview, "seller-ledger-board.json")
        saved_root = SLB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            SLB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = SLB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = SLB.main(["prog", "--out", scratch_html, "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = SLB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            SLB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def rlb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC31."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_world(", "def check_laws(",
                 "def build_html(", "def check_sizes(", "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC31TwentySeventhProducerClosed(unittest.TestCase):
    """AC-PWC31: refund_latency_board re-derives the face on its landing path only.

    That tool's read_world() builds a demo ledger in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "refund_latency_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(rlb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(rlb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = rlb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import refund_latency_board as RLB
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

        tmp = tempfile.mkdtemp(prefix="rlb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "refund-latency-board.html")
        js = os.path.join(preview, "refund-latency-board.json")
        saved_root = RLB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            RLB.ROOT = tmp
            self.assertTrue(RLB._landing_is_default(html, js))
            self.assertFalse(RLB._landing_is_default(
                os.path.join(tmp, "a.html"), js))
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(RLB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(
                False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(RLB._refresh_face(html, js),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(RLB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            RLB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import refund_latency_board as RLB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="rlb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "refund-latency-board.html")
        js = os.path.join(preview, "refund-latency-board.json")
        saved_root = RLB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            RLB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = RLB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = RLB.main(["prog", "--out", scratch_html, "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = RLB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            RLB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def arb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC32."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_world(", "def check_laws(",
                 "def build_html(", "def check_sizes(", "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC32TwentyEighthProducerClosed(unittest.TestCase):
    """AC-PWC32: answer_revision_board re-derives the face on its landing path only.

    That tool's read_world() builds a demo ledger in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "answer_revision_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(arb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(arb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = arb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import answer_revision_board as ARB
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

        tmp = tempfile.mkdtemp(prefix="arb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "answer-revision-board.html")
        js = os.path.join(preview, "answer-revision-board.json")
        saved_root = ARB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            ARB.ROOT = tmp
            self.assertTrue(ARB._landing_is_default(html, js))
            self.assertFalse(ARB._landing_is_default(
                os.path.join(tmp, "a.html"), js))
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(ARB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(
                False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(ARB._refresh_face(html, js),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(ARB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            ARB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import answer_revision_board as ARB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="arb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "answer-revision-board.html")
        js = os.path.join(preview, "answer-revision-board.json")
        saved_root = ARB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            ARB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = ARB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = ARB.main(["prog", "--out", scratch_html, "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = ARB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            ARB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def cgh_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC33."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_world(", "def read_empty(",
                 "def check_laws(", "def build_html(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC33TwentyNinthProducerClosed(unittest.TestCase):
    """AC-PWC33: category_history_board re-derives the face on its landing path only.

    That tool's read_world() and read_empty() build demo worlds in private temp
    dirs, so the behavioural arms write only into their own world; nothing of
    this repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "category_history_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(cgh_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(cgh_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = cgh_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import category_history_board as CHB
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

        tmp = tempfile.mkdtemp(prefix="cgh-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "category-history-board.html")
        js = os.path.join(preview, "category-history-board.json")
        saved_root = CHB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            CHB.ROOT = tmp
            self.assertTrue(CHB._landing_is_default(html, js))
            self.assertFalse(CHB._landing_is_default(
                os.path.join(tmp, "a.html"), js))
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(CHB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(
                False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(CHB._refresh_face(html, js),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(CHB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            CHB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import category_history_board as CHB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="cgh-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "category-history-board.html")
        js = os.path.join(preview, "category-history-board.json")
        saved_root = CHB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            CHB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = CHB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = CHB.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = CHB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            CHB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def pib_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC34."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_world(", "def read_empty(",
                 "def derive_market(", "def check_laws(", "def build_html(",
                 "def check_sizes(", "def check_sources(",
                 "def payload_of("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC34ThirtiethProducerClosed(unittest.TestCase):
    """AC-PWC34: provider_identity_board re-derives the face on its landing path only.

    That tool's read_world() and read_empty() build demo worlds in private temp
    dirs, so the behavioural arms write only into their own world; nothing of
    this repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "provider_identity_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(pib_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(pib_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = pib_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import provider_identity_board as PIB
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

        tmp = tempfile.mkdtemp(prefix="pib-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "provider-identity-board.html")
        js = os.path.join(preview, "provider-identity-board.json")
        saved_root = PIB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            PIB.ROOT = tmp
            self.assertTrue(PIB._landing_is_default(html, js))
            self.assertFalse(PIB._landing_is_default(
                os.path.join(tmp, "a.html"), js))
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(PIB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(
                False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(PIB._refresh_face(html, js),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(PIB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            PIB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import provider_identity_board as PIB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="pib-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "provider-identity-board.html")
        js = os.path.join(preview, "provider-identity-board.json")
        saved_root = PIB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            PIB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = PIB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = PIB.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = PIB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            PIB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def wcmb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC35."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_world(", "def read_empty(",
                 "def _market(", "def check_laws(", "def build_html(",
                 "def check_sizes(", "def check_sources(",
                 "def payload_of("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC35ThirtyFirstProducerClosed(unittest.TestCase):
    """AC-PWC35: watch_category_mix_board re-derives the face on its landing path only.

    That tool's read_world() and read_empty() build demo stacks in private temp
    dirs, so the behavioural arms write only into their own world; nothing of
    this repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "watch_category_mix_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(wcmb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(wcmb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = wcmb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import watch_category_mix_board as WCMB
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

        tmp = tempfile.mkdtemp(prefix="wcmb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "watch-category-mix-board.html")
        js = os.path.join(preview, "watch-category-mix-board.json")
        saved_root = WCMB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            WCMB.ROOT = tmp
            self.assertTrue(WCMB._landing_is_default(html, js))
            self.assertFalse(WCMB._landing_is_default(
                os.path.join(tmp, "a.html"), js))
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(WCMB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(
                False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(WCMB._refresh_face(html, js),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(WCMB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            WCMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import watch_category_mix_board as WCMB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="wcmb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "watch-category-mix-board.html")
        js = os.path.join(preview, "watch-category-mix-board.json")
        saved_root = WCMB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            WCMB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = WCMB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = WCMB.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = WCMB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            WCMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def bawb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC36."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_world(", "def build_world(",
                 "def _month_index(", "def _envelope_problems(",
                 "def check_laws(", "def text(", "def kpi_html(",
                 "def month_table(", "def scope_card(", "def build_html(",
                 "def sha16(", "def source_fingerprints(",
                 "def check_sizes(", "def check_sources(",
                 "def trim_envelope(", "def payload_of("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC36ThirtySecondProducerClosed(unittest.TestCase):
    """AC-PWC36: buyer_answer_wait_board re-derives the face on its landing path only.

    That tool's read_world() builds a demo stack in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "buyer_answer_wait_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(bawb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(bawb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = bawb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import buyer_answer_wait_board as BAWB
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

        tmp = tempfile.mkdtemp(prefix="bawb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-answer-wait-board.html")
        js = os.path.join(preview, "buyer-answer-wait-board.json")
        saved_root = BAWB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            BAWB.ROOT = tmp
            self.assertTrue(BAWB._landing_is_default(html, js))
            self.assertFalse(BAWB._landing_is_default(
                os.path.join(tmp, "a.html"), js))
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(BAWB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(
                False, "E_BFL_FACE_UNPROVEN")
            self.assertEqual(BAWB._refresh_face(html, js),
                             "REFUSED E_BFL_FACE_UNPROVEN")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(BAWB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
            self.assertEqual(len(calls), 2)
        finally:
            BAWB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import buyer_answer_wait_board as BAWB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="bawb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-answer-wait-board.html")
        js = os.path.join(preview, "buyer-answer-wait-board.json")
        saved_root = BAWB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            BAWB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = BAWB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = BAWB.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = BAWB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            BAWB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def bcb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC37."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_cohort(", "def check_laws(",
                 "def fmt(", "def kpi_html(", "def split_html(",
                 "def build_html(", "def sha16(", "def source_fingerprints(",
                 "def check_sizes(", "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC37ThirtyThirdProducerClosed(unittest.TestCase):
    """AC-PWC37: buyer_cohort_board re-derives the face on its landing path only.

    That tool's read_cohort() builds a demo ledger in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "buyer_cohort_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(bcb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(bcb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = bcb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import buyer_cohort_board as BCB
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

        tmp = tempfile.mkdtemp(prefix="bcb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-cohort.html")
        js = os.path.join(preview, "buyer-cohort.json")
        saved_root = BCB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            BCB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(BCB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(BCB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(BCB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            BCB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import buyer_cohort_board as BCB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="bcb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-cohort.html")
        js = os.path.join(preview, "buyer-cohort.json")
        saved_root = BCB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            BCB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = BCB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = BCB.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = BCB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            BCB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def bccb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC38."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def enumerate_buyers(", "def read_world(",
                 "def check_laws(", "def pct(", "def bar_width(", "def fmt(",
                 "def verdict(", "def axis_table(", "def kpi_html(",
                 "def build_html(", "def sha16(", "def source_fingerprints(",
                 "def check_sizes(", "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC38ThirtyFourthProducerClosed(unittest.TestCase):
    """AC-PWC38: buyer_concentration_board re-derives the face on its landing path only.

    That tool's read_world() builds a demo ledger in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "buyer_concentration_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(bccb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(bccb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = bccb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import buyer_concentration_board as BCCB
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

        tmp = tempfile.mkdtemp(prefix="bccb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-concentration-board.html")
        js = os.path.join(preview, "buyer-concentration-board.json")
        saved_root = BCCB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            BCCB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(BCCB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(BCCB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(BCCB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            BCCB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import buyer_concentration_board as BCCB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="bccb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-concentration-board.html")
        js = os.path.join(preview, "buyer-concentration-board.json")
        saved_root = BCCB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            BCCB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = BCCB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = BCCB.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = BCCB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            BCCB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def bgb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC39."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def build_world(", "def read_world(",
                 "def _month_index(", "def _median(",
                 "def _envelope_problems(", "def check_laws(", "def text(",
                 "def kpi_html(", "def gap_table(", "def scope_card(",
                 "def build_html(", "def sha16(", "def source_fingerprints(",
                 "def check_sizes(", "def check_sources(",
                 "def trim_envelope(", "def payload_of("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC39ThirtyFifthProducerClosed(unittest.TestCase):
    """AC-PWC39: buyer_gap_board re-derives the face on its landing path only.

    That tool's read_world() builds a demo ledger in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "buyer_gap_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(bgb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(bgb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = bgb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import buyer_gap_board as BGB
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

        tmp = tempfile.mkdtemp(prefix="bgb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-gap-board.html")
        js = os.path.join(preview, "buyer-gap-board.json")
        saved_root = BGB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            BGB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(BGB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(BGB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(BGB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            BGB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import buyer_gap_board as BGB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="bgb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-gap-board.html")
        js = os.path.join(preview, "buyer-gap-board.json")
        saved_root = BGB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            BGB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = BGB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = BGB.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = BGB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            BGB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def blb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC40."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def enumerate_buyers(",
                 "def read_buyers(", "def check_laws(", "def fmt(",
                 "def kpi_html(", "def is_refund(", "def entry_cells(",
                 "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC40ThirtySixthProducerClosed(unittest.TestCase):
    """AC-PWC40: buyer_ledger_board re-derives the face on its landing path only.

    That tool's read_buyers() builds a demo ledger in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "buyer_ledger_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(blb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(blb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = blb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import buyer_ledger_board as BLB
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

        tmp = tempfile.mkdtemp(prefix="blb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-ledger-board.html")
        js = os.path.join(preview, "buyer-ledger-board.json")
        saved_root = BLB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            BLB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(BLB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(BLB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(BLB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            BLB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import buyer_ledger_board as BLB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="blb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-ledger-board.html")
        js = os.path.join(preview, "buyer-ledger-board.json")
        saved_root = BLB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            BLB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = BLB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = BLB.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = BLB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            BLB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def bmb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC41."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_buyers(", "def check_laws(",
                 "def fmt(", "def kpi_html(", "def month_cells(",
                 "def net_bar(", "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC41ThirtySeventhProducerClosed(unittest.TestCase):
    """AC-PWC41: buyer_months_board re-derives the face on its landing path only.

    That tool's read_buyers() builds a demo ledger in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "buyer_months_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(bmb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(bmb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = bmb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import buyer_months_board as BMB
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

        tmp = tempfile.mkdtemp(prefix="bmb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-months-board.html")
        js = os.path.join(preview, "buyer-months-board.json")
        saved_root = BMB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            BMB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(BMB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(BMB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(BMB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            BMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import buyer_months_board as BMB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="bmb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-months-board.html")
        js = os.path.join(preview, "buyer-months-board.json")
        saved_root = BMB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            BMB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = BMB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = BMB.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = BMB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            BMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def bpb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC42."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def enumerate_buyers(",
                 "def read_world(", "def market_block(", "def _close(",
                 "def _account_problems(", "def check_laws(",
                 "def fmt(", "def num(", "def text(", "def kpi_html(",
                 "def split_html(", "def account_table(",
                 "def buyer_section(", "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC42ThirtyEighthProducerClosed(unittest.TestCase):
    """AC-PWC42: buyer_profile_board re-derives the face on its landing path only.

    That tool's read_world() builds a demo world in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "buyer_profile_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(bpb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(bpb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = bpb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import buyer_profile_board as BPB
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

        tmp = tempfile.mkdtemp(prefix="bpb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-profile-board.html")
        js = os.path.join(preview, "buyer-profile-board.json")
        saved_root = BPB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            BPB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(BPB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(BPB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(BPB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            BPB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import buyer_profile_board as BPB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="bpb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-profile-board.html")
        js = os.path.join(preview, "buyer-profile-board.json")
        saved_root = BPB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            BPB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = BPB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = BPB.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = BPB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            BPB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def brpb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC43."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_buyers(", "def check_laws(",
                 "def fmt(", "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC43ThirtyNinthProducerClosed(unittest.TestCase):
    """AC-PWC43: buyer_rating_pattern_board re-derives the face on its landing path only.

    That tool's read_buyers() builds a demo stack in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "buyer_rating_pattern_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(brpb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(brpb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = brpb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import buyer_rating_pattern_board as BRPB
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

        tmp = tempfile.mkdtemp(prefix="brpb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-rating-pattern-board.html")
        js = os.path.join(preview, "buyer-rating-pattern-board.json")
        saved_root = BRPB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            BRPB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(BRPB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(BRPB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(BRPB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            BRPB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import buyer_rating_pattern_board as BRPB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="brpb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-rating-pattern-board.html")
        js = os.path.join(preview, "buyer-rating-pattern-board.json")
        saved_root = BRPB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            BRPB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = BRPB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = BRPB.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = BRPB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            BRPB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def brmb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC44."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_buyers(", "def check_laws(",
                 "def fmt(", "def kpi_html(", "def month_cells(",
                 "def refund_bar(", "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC44FortiethProducerClosed(unittest.TestCase):
    """AC-PWC44: buyer_refund_months_board re-derives the face on its landing path only.

    That tool's read_buyers() builds a demo stack in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "buyer_refund_months_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(brmb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(brmb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = brmb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import buyer_refund_months_board as BRMB
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

        tmp = tempfile.mkdtemp(prefix="brmb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-refund-months-board.html")
        js = os.path.join(preview, "buyer-refund-months-board.json")
        saved_root = BRMB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            BRMB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(BRMB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(BRMB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(BRMB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            BRMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import buyer_refund_months_board as BRMB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="brmb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-refund-months-board.html")
        js = os.path.join(preview, "buyer-refund-months-board.json")
        saved_root = BRMB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            BRMB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = BRMB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = BRMB.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = BRMB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            BRMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def bwmb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC45."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def build_world(", "def read_world(",
                 "def _month_index(", "def _envelope_problems(",
                 "def check_laws(", "def text(", "def kpi_html(",
                 "def month_table(", "def scope_card(", "def build_html(",
                 "def sha16(", "def source_fingerprints(",
                 "def check_sizes(", "def check_sources(",
                 "def trim_envelope(", "def payload_of("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC45FortyFirstProducerClosed(unittest.TestCase):
    """AC-PWC45: buyer_watch_months_board re-derives the face on its landing path only.

    That tool's read_world() builds a demo stack in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "buyer_watch_months_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(bwmb_closure_positions(text), (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(bwmb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = bwmb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import buyer_watch_months_board as BWMB
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

        tmp = tempfile.mkdtemp(prefix="bwmb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-watch-months-board.html")
        js = os.path.join(preview, "buyer-watch-months-board.json")
        saved_root = BWMB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            BWMB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(BWMB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(BWMB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(BWMB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            BWMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import buyer_watch_months_board as BWMB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="bwmb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "buyer-watch-months-board.html")
        js = os.path.join(preview, "buyer-watch-months-board.json")
        saved_root = BWMB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            BWMB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = BWMB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = BWMB.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = BWMB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            BWMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def cpmb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC46."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_world(", "def check_laws(",
                 "def text(", "def bar_html(", "def kpi_html(",
                 "def cells_table(", "def month_section(", "def build_html(",
                 "def sha16(", "def source_fingerprints(",
                 "def check_sizes(", "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC46FortySecondProducerClosed(unittest.TestCase):
    """AC-PWC46: category_price_months_board re-derives the face on its landing path only.

    That tool's read_world() builds a demo stack in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "category_price_months_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(cpmb_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(cpmb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = cpmb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import category_price_months_board as CPMB
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

        tmp = tempfile.mkdtemp(prefix="cpmb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "category-price-months-board.html")
        js = os.path.join(preview, "category-price-months-board.json")
        saved_root = CPMB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            CPMB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(CPMB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(CPMB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(CPMB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            CPMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import category_price_months_board as CPMB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="cpmb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "category-price-months-board.html")
        js = os.path.join(preview, "category-price-months-board.json")
        saved_root = CPMB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            CPMB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = CPMB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = CPMB.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = CPMB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            CPMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def cqmb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC47."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def build_world(", "def read_world(",
                 "def _month_index(", "def _category_order(", "def _rate(",
                 "def check_laws(", "def text(", "def kpi_html(",
                 "def category_name(", "def cell_token(", "def cell_table(",
                 "def month_card(", "def category_summary(",
                 "def build_html(", "def sha16(", "def source_fingerprints(",
                 "def check_sizes(", "def check_sources(",
                 "def trim_envelope(", "def payload_of("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC47FortyThirdProducerClosed(unittest.TestCase):
    """AC-PWC47: category_question_months_board re-derives the face on its landing path only.

    That tool's read_world() builds a demo stack in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS,
                                  "category_question_months_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(cqmb_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(cqmb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = cqmb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import category_question_months_board as CQMB
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

        tmp = tempfile.mkdtemp(prefix="cqmb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "category-question-months-board.html")
        js = os.path.join(preview, "category-question-months-board.json")
        saved_root = CQMB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            CQMB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(CQMB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(CQMB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(CQMB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            CQMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import category_question_months_board as CQMB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="cqmb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "category-question-months-board.html")
        js = os.path.join(preview, "category-question-months-board.json")
        saved_root = CQMB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            CQMB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = CQMB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = CQMB.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = CQMB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            CQMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def crf_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC48."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_face(", "def ordered(",
                 "def fmt(", "def pct(", "def cat_name(",
                 "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC48FortyFourthProducerClosed(unittest.TestCase):
    """AC-PWC48: category_refund_months re-derives the face on its landing path only.

    That tool's read_face() builds a demo stack in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "category_refund_months.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(crf_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(crf_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = crf_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import category_refund_months as CRFM
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

        tmp = tempfile.mkdtemp(prefix="crfm-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "category-refund-months.html")
        js = os.path.join(preview, "category-refund-months.json")
        saved_root = CRFM.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            CRFM.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(CRFM._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(CRFM._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(CRFM._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            CRFM.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import category_refund_months as CRFM
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="crfm-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "category-refund-months.html")
        js = os.path.join(preview, "category-refund-months.json")
        saved_root = CRFM.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            CRFM.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = CRFM.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = CRFM.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = CRFM.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            CRFM.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def cvm_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC49."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_world(", "def _next_month(",
                 "def check_laws(", "def text(", "def bar_html(",
                 "def kpi_html(", "def cells_table(", "def month_section(",
                 "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC49FortyFifthProducerClosed(unittest.TestCase):
    """AC-PWC49: category_velocity_months_board re-derives the face on its landing path only.

    That tool's read_world() builds a demo stack in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "category_velocity_months_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(cvm_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(cvm_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = cvm_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import category_velocity_months_board as CVMB
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

        tmp = tempfile.mkdtemp(prefix="cvmb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "category-velocity-months-board.html")
        js = os.path.join(preview, "category-velocity-months-board.json")
        saved_root = CVMB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            CVMB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(CVMB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(CVMB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(CVMB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            CVMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import category_velocity_months_board as CVMB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="cvmb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "category-velocity-months-board.html")
        js = os.path.join(preview, "category-velocity-months-board.json")
        saved_root = CVMB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            CVMB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = CVMB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = CVMB.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = CVMB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            CVMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def cwmb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC50."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def build_world(", "def read_world(",
                 "def _month_index(", "def _category_order(",
                 "def check_laws(", "def text(", "def kpi_html(",
                 "def category_name(", "def cell_token(", "def cell_table(",
                 "def month_card(", "def category_summary(",
                 "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources(", "def trim_envelope(",
                 "def payload_of("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC50FortySixthProducerClosed(unittest.TestCase):
    """AC-PWC50: category_watch_months_board re-derives the face on its landing path only.

    That tool's read_world()/build_world() work in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "category_watch_months_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(cwmb_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(cwmb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = cwmb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import category_watch_months_board as CWMB
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

        tmp = tempfile.mkdtemp(prefix="cwmb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "category-watch-months-board.html")
        js = os.path.join(preview, "category-watch-months-board.json")
        saved_root = CWMB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            CWMB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(CWMB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(CWMB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(CWMB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            CWMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import category_watch_months_board as CWMB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="cwmb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "category-watch-months-board.html")
        js = os.path.join(preview, "category-watch-months-board.json")
        saved_root = CWMB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            CWMB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = CWMB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = CWMB.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = CWMB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            CWMB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def libb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC51."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_world(", "def buyer_ids(",
                 "def market_block(", "def check_laws(", "def fmt(",
                 "def text(", "def kpi_html(", "def listing_cell(",
                 "def refund_cell(", "def delist_cell(", "def rating_cell(",
                 "def rows_table(", "def split_caption(",
                 "def buyer_section(", "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC51FortySeventhProducerClosed(unittest.TestCase):
    """AC-PWC51: library_board re-derives the face on its landing path only.

    That tool's read_world() works in a private temp dir, so the behavioural
    arms write only into their own world; nothing of this repository's
    preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "library_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(libb_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(libb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = libb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import library_board as LIBB
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

        tmp = tempfile.mkdtemp(prefix="libb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "library-board.html")
        js = os.path.join(preview, "library-board.json")
        saved_root = LIBB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            LIBB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(LIBB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(LIBB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(LIBB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            LIBB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import library_board as LIBB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="libb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "library-board.html")
        js = os.path.join(preview, "library-board.json")
        saved_root = LIBB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            LIBB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = LIBB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = LIBB.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = LIBB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            LIBB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def lmh_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC52."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def build_world(", "def read_world(",
                 "def _month(", "def _fields(", "def _merge(",
                 "def _market(", "def check_laws(", "def text(",
                 "def badge_of(", "def market_html(", "def envelope_card(",
                 "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources(", "def trim_envelope(",
                 "def payload_of("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC52FortyEighthProducerClosed(unittest.TestCase):
    """AC-PWC52: listing_metadata_history_board derives the face on landing only.

    That tool's build_world()/read_world() work in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS,
                                  "listing_metadata_history_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(lmh_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(lmh_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = lmh_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import listing_metadata_history_board as LMH
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

        tmp = tempfile.mkdtemp(prefix="lmh-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "listing-metadata-history-board.html")
        js = os.path.join(preview, "listing-metadata-history-board.json")
        saved_root = LMH.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            LMH.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(LMH._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(LMH._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(LMH._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            LMH.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import listing_metadata_history_board as LMH
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="lmh-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "listing-metadata-history-board.html")
        js = os.path.join(preview, "listing-metadata-history-board.json")
        saved_root = LMH.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            LMH.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = LMH.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = LMH.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = LMH.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            LMH.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def lpb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC53."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_board(", "def buckets_of(",
                 "def check_laws(", "def fmt(", "def rating_text(",
                 "def cat_name(", "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC53FortyNinthProducerClosed(unittest.TestCase):
    """AC-PWC53: listing_position_board derives the face on landing only.

    That tool's read_board()/buckets_of() work in a private temp dir, so the
    behavioural arms write only into their own world; nothing of this
    repository's preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "listing_position_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(lpb_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(lpb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = lpb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import listing_position_board as LPB
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

        tmp = tempfile.mkdtemp(prefix="lpb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "listing-position-board.html")
        js = os.path.join(preview, "listing-position-board.json")
        saved_root = LPB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            LPB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(LPB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(LPB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(LPB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            LPB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import listing_position_board as LPB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="lpb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "listing-position-board.html")
        js = os.path.join(preview, "listing-position-board.json")
        saved_root = LPB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            LPB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = LPB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = LPB.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = LPB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            LPB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def mdb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC54."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_face(", "def fmt(",
                 "def bar_width(", "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC54FiftiethProducerClosed(unittest.TestCase):
    """AC-PWC54: market_daily_board derives the face on landing only.

    That tool's read_face() works in a private temp dir, so the behavioural
    arms write only into their own world; nothing of this repository's
    preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "market_daily_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(mdb_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(mdb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = mdb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import market_daily_board as MDB
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

        tmp = tempfile.mkdtemp(prefix="mdb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "market-daily.html")
        js = os.path.join(preview, "market-daily.json")
        saved_root = MDB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            MDB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(MDB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(MDB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(MDB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            MDB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import market_daily_board as MDB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="mdb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "market-daily.html")
        js = os.path.join(preview, "market-daily.json")
        saved_root = MDB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            MDB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = MDB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = MDB.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = MDB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            MDB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def plb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC55."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_world(", "def derived(",
                 "def check_laws(", "def bar_none(", "def flag(",
                 "def state_text(", "def kpi_html(", "def listings_table(",
                 "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC55FiftyFirstProducerClosed(unittest.TestCase):
    """AC-PWC55: public_listings_board derives the face on landing only.

    That tool's read_world() works in a private temp dir, so the behavioural
    arms write only into their own world; nothing of this repository's
    preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "public_listings_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(plb_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(plb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = plb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import public_listings_board as PLB
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

        tmp = tempfile.mkdtemp(prefix="plb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "public-listings-board.html")
        js = os.path.join(preview, "public-listings-board.json")
        saved_root = PLB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            PLB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(PLB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(PLB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(PLB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            PLB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import public_listings_board as PLB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="plb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "public-listings-board.html")
        js = os.path.join(preview, "public-listings-board.json")
        saved_root = PLB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            PLB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = PLB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = PLB.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = PLB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            PLB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def lvb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC56."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_world(", "def derived(",
                 "def check_laws(", "def text(", "def number(",
                 "def badge_row(", "def kpi_html(", "def stamps_table(",
                 "def listing_section(", "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC56FiftySecondProducerClosed(unittest.TestCase):
    """AC-PWC56: listing_view_board derives the face on landing only.

    That tool's read_world() works in a private temp dir, so the behavioural
    arms write only into their own world; nothing of this repository's
    preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "listing_view_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(lvb_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(lvb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = lvb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import listing_view_board as LVB
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

        tmp = tempfile.mkdtemp(prefix="lvb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "listing-view-board.html")
        js = os.path.join(preview, "listing-view-board.json")
        saved_root = LVB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            LVB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(LVB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(LVB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(LVB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            LVB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import listing_view_board as LVB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="lvb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "listing-view-board.html")
        js = os.path.join(preview, "listing-view-board.json")
        saved_root = LVB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            LVB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = LVB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = LVB.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = LVB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            LVB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def lvbv_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC57."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def enumerate_sellers(", "def read_world(",
                 "def _secs(", "def _mean(", "def _median(", "def _close(",
                 "def _aggregate_problems(", "def check_laws(",
                 "def fmt_duration(", "def bar_share(", "def fmt(",
                 "def kpi_html(", "def rows_table(", "def sellers_table(",
                 "def build_html(", "def sha16(", "def source_fingerprints(",
                 "def check_sizes(", "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC57FiftyThirdProducerClosed(unittest.TestCase):
    """AC-PWC57: listing_velocity_board derives the face on landing only.

    That tool's read_world() builds a private temp world, so the behavioural
    arms write only into their own world; nothing of this repository's
    preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "listing_velocity_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(lvbv_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(lvbv_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = lvbv_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import listing_velocity_board as LVV
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

        tmp = tempfile.mkdtemp(prefix="lvv-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "listing-velocity-board.html")
        js = os.path.join(preview, "listing-velocity-board.json")
        saved_root = LVV.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            LVV.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(LVV._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(LVV._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(LVV._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            LVV.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import listing_velocity_board as LVV
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="lvv-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "listing-velocity-board.html")
        js = os.path.join(preview, "listing-velocity-board.json")
        saved_root = LVV.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            LVV.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = LVV.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = LVV.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = LVV.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            LVV.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def mpq_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC58."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def read_face(", "def quantiles(",
                 "def ordered(", "def fmt(", "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC58FiftyFourthProducerClosed(unittest.TestCase):
    """AC-PWC58: market_price_percentiles derives the face on landing only.

    That tool's read_face() builds a private temp world, so the behavioural
    arms write only into their own world; nothing of this repository's
    preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "market_price_percentiles.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(mpq_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(mpq_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = mpq_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import market_price_percentiles as MPQ
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

        tmp = tempfile.mkdtemp(prefix="mpq-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "market-price-percentiles.html")
        js = os.path.join(preview, "market-price-percentiles.json")
        saved_root = MPQ.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            MPQ.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(MPQ._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(MPQ._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(MPQ._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            MPQ.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import market_price_percentiles as MPQ
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="mpq-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "market-price-percentiles.html")
        js = os.path.join(preview, "market-price-percentiles.json")
        saved_root = MPQ.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            MPQ.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = MPQ.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = MPQ.main(["prog", "--out", scratch_html,
                           "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = MPQ.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            MPQ.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


def lphb_closure_positions(text):
    """(present, after_loop, readers_clean, shared_only) for AC-PWC59."""
    if "def main(" not in text:
        return (False, False, False, False)
    body = text.rpartition("def main(")[2].split("\ndef ")[0]
    at = body.find("_refresh_face(args.out, args.json)")
    present = at != -1
    loop_end = body.find(
        'if payload["sizes"]["json"] == os.path.getsize(args.json):')
    after = present and loop_end != -1 and at > loop_end
    readers = True
    for name in ("def read_copy(", "def build_world(", "def read_world(",
                 "def _clock(", "def _month(", "def _merge(",
                 "def _market(", "def check_laws(", "def text(",
                 "def market_html(", "def envelope_card(",
                 "def build_html(", "def sha16(",
                 "def source_fingerprints(", "def check_sizes(",
                 "def check_sources(", "def trim_envelope(",
                 "def payload_of("):
        if name in text:
            reader_body = text.rpartition(name)[2].split("\ndef ")[0]
            if "_refresh_face(" in reader_body:
                readers = False
    helper = text.rpartition("def _refresh_face(")[2].split("\ndef ")[0]
    shared = "board_face_landing.refresh_export_face(ROOT)" in helper
    no_local_writer = ".write(" not in helper
    return (present, after, readers and present, shared and no_local_writer)


class PWC59FiftyFifthProducerClosed(unittest.TestCase):
    """AC-PWC59: listing_price_history_board derives the face on landing only.

    That tool's read_world() builds a private temp world, so the behavioural
    arms write only into their own world; nothing of this repository's
    preview/ or ledger moves.
    """

    def _source(self):
        with io.open(os.path.join(TOOLS, "listing_price_history_board.py"),
                     encoding="utf-8") as f:
            return f.read()

    def test_closed_and_ordered_after_the_fixed_point_loop(self):
        text = self._source()
        kind, _html, writes, closes = MOD.classify_source(text)
        self.assertEqual(kind, "closed")
        self.assertGreaterEqual(writes, 1)
        self.assertGreaterEqual(closes, 1)
        self.assertEqual(lphb_closure_positions(text),
                         (True, True, True, True))

    def test_negative_controls_delete_and_move(self):
        text = self._source()
        deleted = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "board_face_landing.refresh_export_face(ROOT)",
            "None  # control: shared call removed")
        self.assertEqual(MOD.classify_source(deleted)[0], "gap")
        self.assertFalse(lphb_closure_positions(deleted)[0])
        moved = text.replace(
            "    face = _refresh_face(args.out, args.json)\n", "").replace(
            "    for _ in range(6):",
            "    face = _refresh_face(args.out, args.json)  "
            "# control: moved into the loop before the last landing write\n"
            "    for _ in range(6):", 1)
        pos = lphb_closure_positions(moved)
        self.assertTrue(pos[0])
        self.assertFalse(pos[1])

    def test_refresh_is_shared_and_named(self):
        import listing_price_history_board as LPHB
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

        tmp = tempfile.mkdtemp(prefix="lphb-face-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "listing-price-history-board.html")
        js = os.path.join(preview, "listing-price-history-board.json")
        saved_root = LPHB.ROOT
        saved = sys.modules.get("board_face_landing")
        try:
            LPHB.ROOT = tmp
            sys.modules["board_face_landing"] = Fake(True, "")
            self.assertEqual(LPHB._refresh_face(html, js), "WRITTEN")
            self.assertEqual(calls, [tmp])
            sys.modules["board_face_landing"] = Fake(False, "stale")
            self.assertEqual(LPHB._refresh_face(html, js), "REFUSED stale")
            sys.modules["board_face_landing"] = Boom()
            self.assertEqual(LPHB._refresh_face(html, js),
                             "SKIPPED RuntimeError")
        finally:
            LPHB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_landing_derives_once_and_scratch_and_check_derive_none(self):
        """A landing in this world's own preview derives once; scratch and --check do not."""
        import listing_price_history_board as LPHB
        calls = []

        class Fake(object):
            def refresh_export_face(self, root):
                calls.append(root)
                return (True, "", {})

        tmp = tempfile.mkdtemp(prefix="lphb-pwc-")
        preview = os.path.join(tmp, "preview")
        os.makedirs(preview, exist_ok=True)
        html = os.path.join(preview, "listing-price-history-board.html")
        js = os.path.join(preview, "listing-price-history-board.json")
        saved_root = LPHB.ROOT
        saved = sys.modules.get("board_face_landing")
        saved_stdout = sys.stdout
        try:
            sys.modules["board_face_landing"] = Fake()
            LPHB.ROOT = tmp
            sys.stdout = io.StringIO()
            rc = LPHB.main(["prog", "--out", html, "--json", js])
            self.assertEqual(rc, 0)
            self.assertEqual(calls, [tmp])
            self.assertTrue(os.path.isfile(html))
            self.assertTrue(os.path.isfile(js))

            scratch_html = os.path.join(tmp, "scratch.html")
            scratch_js = os.path.join(tmp, "scratch.json")
            rc = LPHB.main(["prog", "--out", scratch_html,
                            "--json", scratch_js])
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 1)

            calls[:] = []
            rc = LPHB.main(["prog", "--check", "--out", html, "--json", js])
            self.assertEqual(calls, [])
            self.assertIn(rc, (0, 2))
        finally:
            sys.stdout = saved_stdout
            LPHB.ROOT = saved_root
            if saved is None:
                sys.modules.pop("board_face_landing", None)
            else:
                sys.modules["board_face_landing"] = saved
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
