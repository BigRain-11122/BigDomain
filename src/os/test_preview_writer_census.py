"""Battery suite for tools/preview_writer_census.py - AC-PWC1..AC-PWC6 (R3527, R3528).

Pinned in src/os/backlog.md BEFORE the tool, this file and the face_pair_receipt
wiring existed. AC-PWC6 was pinned in the R3528 window before
tools/ledger_reconcile_face.py was touched.

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


if __name__ == "__main__":
    unittest.main()
