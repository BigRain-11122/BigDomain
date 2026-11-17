"""Acceptance suite: the documented msgSecCheck dialect wired into the pipeline.

Asserts AC-MSW1..AC-MSW5, pinned in src/os/backlog.md at R2909 BEFORE the edit
(pre-registration law). The subject is the SHIPPED path: every arm drives
pipeline.submit / submit_batch / ingest_lobby and reads what the face saw off
the pipeline itself, never a request typed into the test.

Chinese probe strings are sourced from config.json (data file) per the encoding
discipline; this file stays ASCII.

Usage: python test_msgsec_wire.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import pipeline as P  # noqa: E402
import msgsec_face as MSF  # noqa: E402
from sec_gate import GateOfflineError  # noqa: E402 (lobby gate product)

RESULTS = []
CLEAN = "idea for the lobby: a co-op mode with friends and a daily board"


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def load_cfg():
    with open(os.path.join(BASE, "config.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def make(tmp, tag, mut=None):
    cfg = load_cfg()
    cfg["noise"] = dict(cfg.get("noise") or {}, flood_max_submissions=50)
    cfg["export"] = dict(cfg.get("export") or {}, dir="export-msw-test")
    if mut is not None:
        mut(cfg)
    return P.UGCPipeline(cfg, os.path.join(tmp, "w-%s.db" % tag)), cfg


def grant(pipe, *actors):
    for actor in actors:
        pipe.grant_entrance_sandbox(actor)


def refused(fn):
    """Run fn; return (is_refused, code). A raised PipelineError is a refusal."""
    try:
        fn()
    except P.UGC.PipelineError as exc:
        return True, exc.code
    return False, "no-refusal"


def msw1(tmp):
    pipe, cfg = make(tmp, "msw1")
    try:
        grant(pipe, "alice")
        out = pipe.submit("direct", "alice", CLEAN)
        req = pipe.sec_last_request or {}
        problems = list(pipe.sec_last_problems)
        ok_keys = set(req) == {"content", "version", "scene", "openid"}
        ok_ver = req.get("version") == MSF.VERSION_FIXED == 2
        ok_scene = req.get("scene") == 2
        ok_open = isinstance(req.get("openid"), str) and \
            req["openid"].startswith("sandbox:") and len(req["openid"]) > 8
        ok_content = req.get("content") == CLEAN
        landed = out.get("received") is True
        ok = (ok_keys and ok_ver and ok_scene and ok_open and ok_content
              and landed and problems == [])
        record("AC-MSW1", ok,
               "request keys=%s version=%s scene=%s openid=%s content_match=%s "
               "face_problems=%s received=%s"
               % (sorted(req), req.get("version"), req.get("scene"),
                  req.get("openid"), ok_content, problems, landed))
    finally:
        pipe.store.close()


def msw2(tmp):
    """Red control on the SHIPPED path: an inconsistent pair never passes."""
    pipe, cfg = make(tmp, "msw2")
    orig = P.sec_response_from_verdict
    try:
        grant(pipe, "bob", "carol")
        P.sec_response_from_verdict = lambda kind, gate_no=0: {
            "errcode": 0, "result": {"suggest": "pass", "label": 20001}}
        bad_pair, code1 = refused(lambda: pipe.submit("direct", "bob", CLEAN))
        P.sec_response_from_verdict = lambda kind, gate_no=0: {
            "errcode": 40001, "result": {"suggest": "pass", "label": 100}}
        bad_code, code2 = refused(lambda: pipe.submit("direct", "carol", CLEAN))
        stored = pipe.store.content_seen(CLEAN, "none")
        ok = bad_pair and bad_code and code1 == "E_CONTENT_REJECTED" \
            and code2 == "E_CONTENT_REJECTED" and stored is None
        record("AC-MSW2", ok,
               "doctored_pass_label_20001 refused=%s code=%s | "
               "doctored_errcode_40001 refused=%s code=%s | stored_row=%s"
               % (bad_pair, code1, bad_code, code2, stored))
    finally:
        P.sec_response_from_verdict = orig
        pipe.store.close()


def msw3(tmp):
    """(a) contradiction is never a pass; (b) config above the documented
    ceiling refuses construction."""
    pipe, cfg = make(tmp, "msw3a")
    orig = P.sec_response_from_verdict
    try:
        grant(pipe, "dave")
        word = cfg["gate"]["forbidden_words"][0]
        P.sec_response_from_verdict = lambda kind, gate_no=0: {
            "errcode": 0, "result": {"suggest": "pass", "label": 100}}
        contradiction, code = refused(
            lambda: pipe.submit("direct", "dave", word + " " + CLEAN))
    finally:
        P.sec_response_from_verdict = orig
        pipe.store.close()
    tall = MSF.CONTENT_MAX + 100
    try:
        make(tmp, "msw3b", lambda c: c.update({"max_content_len": tall}))
        too_long, detail = False, "constructed"
    except GateOfflineError as exc:
        too_long, detail = exc.code == "E_GATE_OFFLINE", str(exc)
    ok = contradiction and code == "E_CONTENT_REJECTED" and too_long
    record("AC-MSW3", ok,
           "contradiction refused=%s code=%s | max_content_len %d -> %s"
           % (contradiction, code, tall, detail))


def msw4(tmp):
    """The face is read at STARTUP: a drifted table refuses construction."""
    doc = os.path.join(tmp, "doctored-face.json")
    face = MSF.load_face()
    face["request"]["fields"]["version"]["fixed"] = 3
    with open(doc, "w", encoding="utf-8") as fh:
        json.dump(face, fh)
    orig_path = MSF.FACE_PATH
    try:
        MSF.FACE_PATH = doc
        try:
            make(tmp, "msw4bad")
            drifted, detail = False, "constructed on a drifted face"
        except GateOfflineError as exc:
            drifted, detail = exc.code == "E_GATE_OFFLINE", str(exc)
    finally:
        MSF.FACE_PATH = orig_path
    pipe, cfg = make(tmp, "msw4good")
    try:
        shipped = MSF.check(MSF.load_face()) == []
    finally:
        pipe.store.close()
    ok = drifted and shipped
    record("AC-MSW4", ok,
           "doctored_version_3 -> %s | shipped face clean=%s"
           % (detail, shipped))


def msw5(tmp):
    """Non-regression: the four sibling suites green and the registry row
    declares exactly the criteria count this suite prints."""
    runs = {}
    for name in ("test_ugc.py", "test_msgsec_face.py", "test_ugc_console.py",
                 "test_sec_batch.py"):
        proc = subprocess.run([sys.executable, name], cwd=BASE,
                              capture_output=True, text=True)
        tail = [ln for ln in proc.stdout.splitlines()
                if ln.startswith("SUITE PASS")]
        runs[name] = (proc.returncode == 0, tail[-1] if tail else "no-pass-line")
    reg = os.path.join(BASE, "..", "reconcile_all.py")
    with open(reg, "r", encoding="utf-8") as fh:
        text = fh.read()
    declared = None
    for line in text.splitlines():
        if "test_msgsec_wire.py" in line:
            declared = line.strip()
    want = len(RESULTS) + 1  # this criterion counts itself
    ok_count = declared is not None and (", %d)" % want) in declared
    ok = all(v[0] for v in runs.values()) and ok_count
    record("AC-MSW5", ok,
           "siblings=%s | declared_ok=%s want=%d | registry_line=%s"
           % (",".join("%s:%s" % (k, "green" if v[0] else "red")
                       for k, v in runs.items()), ok_count, want, declared))


def main():
    tmp = tempfile.mkdtemp(prefix="msw-")
    try:
        msw1(tmp)
        msw2(tmp)
        msw3(tmp)
        msw4(tmp)
        msw5(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s (%d/%d criteria pass)%s"
          % ("PASS" if not failed else "FAIL",
             len(RESULTS) - len(failed), len(RESULTS),
             "" if not failed else " failing=" + ",".join(failed)))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
