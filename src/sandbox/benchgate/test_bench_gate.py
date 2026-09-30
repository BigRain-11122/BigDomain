"""Tests for the D-20260930-36 BigDomain line gate (bench_gate.py).

AC-BG3 of the R691 claim row: real-repo positive case, tmp negative
cases, registry/loop fixture positive cases, exit codes.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bench_gate  # noqa: E402

REPO = bench_gate.REPO
PREVIEW = os.path.join(REPO, "preview")

FRONT_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>front</title></head><body>
<p>%s</p></body></html>""" % ("x" * 4200 + " AIGC msgSecCheck 投顾 19.9")


def make_front(root, name="index.html"):
    with open(os.path.join(root, name), "w", encoding="utf-8") as fh:
        fh.write(FRONT_HTML)


class Rd1Tests(unittest.TestCase):
    def test_pass_on_real_repo_front(self):
        fronts = bench_gate.find_fronts(PREVIEW)
        self.assertEqual(len(fronts), 1)
        v = bench_gate.check_rd1(PREVIEW)
        self.assertEqual(v["status"], "PASS")
        self.assertTrue(any("deliverable-metrics-R683.json" in e for e in v["evidence"]))

    def test_fail_on_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            v = bench_gate.check_rd1(tmp)
            self.assertEqual(v["status"], "FAIL")
            self.assertEqual(v["fronts"], 0)

    def test_rejects_doc_substitute(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "doc.html"), "w", encoding="utf-8") as fh:
                fh.write("<html>plain doc, no markers</html>")
            self.assertEqual(bench_gate.find_fronts(tmp), [])


class Rd2Tests(unittest.TestCase):
    def test_fail_blocked_without_registry(self):
        v = bench_gate.check_rd2(PREVIEW, bench_gate.find_fronts(PREVIEW))
        self.assertEqual(v["status"], "FAIL")
        self.assertEqual(v["reason"], "blocked-on-CEO-physicals")

    def test_pass_with_registry_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_front(tmp)
            cast = os.path.join(tmp, "cast.mp4")
            open(cast, "w").close()
            rel = os.path.relpath(os.path.join(tmp, "index.html"), REPO)
            with open(os.path.join(tmp, "front-urls.json"), "w", encoding="utf-8") as fh:
                json.dump({"fronts": [{"front": rel.replace("\\", "/"),
                                       "url": "https://example.city/",
                                       "clickcast_evidence": rel.replace("\\", "/")}],
                           "dummy": True}, fh)
            # rel path trick: clickcast_evidence resolved against REPO; use abs-safe path
            data = json.load(open(os.path.join(tmp, "front-urls.json"), encoding="utf-8"))
            data["fronts"][0]["clickcast_evidence"] = os.path.relpath(cast, REPO).replace("\\", "/")
            with open(os.path.join(tmp, "front-urls.json"), "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            v = bench_gate.check_rd2(tmp, bench_gate.find_fronts(tmp))
            self.assertEqual(v["status"], "PASS")

    def test_fail_when_clickcast_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_front(tmp)
            with open(os.path.join(tmp, "front-urls.json"), "w", encoding="utf-8") as fh:
                json.dump({"fronts": [{"front": "index.html",
                                       "url": "https://example.city/",
                                       "clickcast_evidence": "nope.mp4"}]}, fh)
            v = bench_gate.check_rd2(tmp, bench_gate.find_fronts(tmp))
            self.assertEqual(v["status"], "FAIL")


class Rd3Tests(unittest.TestCase):
    def test_fail_blocked_without_loop_file(self):
        v = bench_gate.check_rd3(PREVIEW)
        self.assertEqual(v["status"], "FAIL")
        self.assertEqual(v["reason"], "blocked-on-CEO-physicals")

    def test_pass_with_loop_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "external-loop.json"), "w", encoding="utf-8") as fh:
                json.dump({"stages": {"register": {"external_participant": True},
                                      "produce": {"external_participant": True},
                                      "be_seen": {"external_participant": True}}}, fh)
            v = bench_gate.check_rd3(tmp)
            self.assertEqual(v["status"], "PASS")

    def test_fail_when_stage_not_external(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "external-loop.json"), "w", encoding="utf-8") as fh:
                json.dump({"stages": {"register": {"external_participant": True},
                                      "produce": {"external_participant": False},
                                      "be_seen": {"external_participant": True}}}, fh)
            v = bench_gate.check_rd3(tmp)
            self.assertEqual(v["status"], "FAIL")


class GateRunTests(unittest.TestCase):
    def test_real_repo_overall_honest_red(self):
        rep = bench_gate.Report(None)
        try:
            verdicts, code = bench_gate.run_gate(PREVIEW, rep)
        finally:
            rep.close()
        self.assertEqual([v["status"] for v in verdicts],
                         ["PASS", "FAIL", "FAIL"])
        self.assertEqual(code, 1)

    def test_skip_when_preview_missing(self):
        rep = bench_gate.Report(None)
        try:
            verdicts, code = bench_gate.run_gate(os.path.join(REPO, "no-such-preview"), rep)
        finally:
            rep.close()
        self.assertIsNone(verdicts)
        self.assertEqual(code, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
