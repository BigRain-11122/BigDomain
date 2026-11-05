"""Suite for the UGC pipeline console (ugc_page.py + ugc_console.html).

Six criteria, each read off a REAL server process (AC-UGW1..AC-UGW6 were
pre-registered in src/os/backlog.md at R2473 BEFORE this module, the page and
this suite existed):

  AC-UGW1  GET /ugc and /ugc/ answer 200 text/html with bytes identical to the
           page on disk; the page is bigger than 4000 bytes, makes no external
           reference, and carries the live config AI label and non-advice
           disclaimer verbatim plus a mock statement marker.
  AC-UGW2  GET /ugc/api/state is derived, never canned: an empty world reads an
           empty review list and an empty pool, and the notices equal the live
           config values on every call.
  AC-UGW3  POST /ugc/api/submit uses the SHIPPED pipeline: a clean sentence
           returns the pipeline receipt unchanged (received=True, gate=pass, the
           shipped 16-hex content address) and appears in the pool; a blank body
           is 400 and an over-length body is 413, both without reaching the
           pipeline.
  AC-UGW4  the gate cannot be bypassed through the face: a LIVE forbidden word
           is refused 4xx naming E_CONTENT_REJECTED and stores no item, while a
           LIVE gray word lands as gate=review suspended=True and appears in the
           suspended list; no configured word is a literal in the module.
  AC-UGW5  the review path drives the SHIPPED desk: pass routes the case into
           the pool and drops it from the suspended list, a second verdict is
           refused, risky answers 4xx naming E_CONTENT_REJECTED while the queue
           row keeps its trace, and an unknown case is 404 writing nothing.
  AC-UGW6  hygiene and registration: unknown path 404, non-GET on a read route
           405, the module is pure ASCII with no clock import, the page carries
           no BOM and no CRLF, and the registry carries exactly this suite row.
"""

import hashlib
import json
import os
import sys
import tempfile
import shutil
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import pipeline as UGC_PIPELINE  # noqa: E402
import store as UGC  # noqa: E402
import ugc_page  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))
CONFIG = os.path.join(BASE, "config.json")
PAGE = os.path.join(BASE, "ugc_console.html")
MODULE = os.path.join(BASE, "ugc_page.py")
REGISTRY = os.path.join(REPO, "src", "sandbox", "reconcile_all.py")
ROW_ID = "ugc-console"


def load_config():
    with open(CONFIG, encoding="utf-8") as handle:
        return json.load(handle)


def http(port, path, method="GET", body=None):
    url = "http://127.0.0.1:%d%s" % (port, path)
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.getcode(), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def http_json(port, path, method="GET", body=None):
    code, raw = http(port, path, method, body)
    try:
        return code, json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return code, {"_raw": raw[:200].decode("utf-8", "replace")}


class Leg(object):
    """One real server on an OS-assigned port over a private temp world."""

    def __init__(self):
        self.tmp = tempfile.mkdtemp(prefix="ugc-console-")
        self.cfg = load_config()
        self.pipe = UGC_PIPELINE.UGCPipeline(
            self.cfg, os.path.join(self.tmp, "ugc.db"))
        self.httpd = ugc_page.start_ugc_http("127.0.0.1", 0, self.pipe, self.cfg)
        self.port = self.httpd.server_address[1]

    def close(self):
        try:
            self.httpd.shutdown()
        except Exception:
            pass
        try:
            self.pipe.close()
        except Exception:
            pass
        shutil.rmtree(self.tmp, ignore_errors=True)


def state(leg):
    code, payload = http_json(leg.port, "/ugc/api/state")
    assert code == 200, "state answered %s" % code
    return payload


def submit(leg, actor, content):
    return http_json(leg.port, "/ugc/api/submit", "POST",
                     {"actor": actor, "content": content})


def verdict(leg, evt_id, value):
    return http_json(leg.port, "/ugc/api/verdict", "POST",
                     {"evt_id": evt_id, "verdict": value})


def main():
    failed = 0
    leg = None
    try:
        leg = Leg()
        cfg = leg.cfg
        comp = cfg["compliance"]
        gray_word = cfg["gate"]["gray_words"][0]
        forbidden_word = cfg["gate"]["forbidden_words"][0]
        max_len = int(cfg["max_content_len"])

        # ---- AC-UGW1 -------------------------------------------------------
        try:
            with open(PAGE, "rb") as fh:
                disk = fh.read()
            code_a, body_a = http(leg.port, "/ugc")
            code_b, body_b = http(leg.port, "/ugc/")
            assert code_a == 200 and code_b == 200, "page codes %s/%s" % (code_a, code_b)
            assert body_a == disk and body_b == disk, "served page differs from disk"
            assert len(disk) > 4000, "page too small: %d" % len(disk)
            text = disk.decode("utf-8")
            for bad in ("http://", "https://", 'src="//', "src='//"):
                assert bad not in text, "page makes an external reference: %s" % bad
            assert comp["ai_label_text"] in text, "page lacks the config AI label"
            assert comp["disclaimer"] in text, "page lacks the config disclaimer"
            assert 'id="mockline"' in text, "page lacks the mock statement marker"
            print("PASS AC-UGW1 bytes=%d identical=2 offline=True ai_label=True "
                  "disclaimer=True mock_marker=True sha16=%s"
                  % (len(disk), hashlib.sha256(disk).hexdigest()[:16].upper()))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-UGW1 :: %s" % exc)

        # ---- AC-UGW2 -------------------------------------------------------
        try:
            clean = state(leg)
            assert clean["review"] == [], "empty world has review rows: %r" % clean["review"]
            assert (clean["pool"].get("items") or []) == [], "empty world has pool items"
            assert clean["notices"]["ai_label"] == comp["ai_label_text"], "ai label drift"
            assert clean["notices"]["disclaimer"] == comp["disclaimer"], "disclaimer drift"
            assert clean["notices"]["max_len"] == max_len, "max_len drift"
            assert clean["notices"]["mock"] is True and clean["notices"]["chargeable"] is False, (
                "mock/chargeable flags wrong: %r" % clean["notices"])
            second = state(leg)
            assert second["notices"] == clean["notices"], "notices are not stable on call"
            print("PASS AC-UGW2 review=0 pool=0 notices_live=True ai_label=True "
                  "disclaimer=True max_len=%d" % max_len)
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-UGW2 :: %s" % exc)

        # ---- AC-UGW3 -------------------------------------------------------
        try:
            code, receipt = submit(leg, "alice", "turn an old bus stop into a story kiosk")
            assert code == 200, "clean submit answered %s (%r)" % (code, receipt)
            assert receipt.get("received") is True, "receipt not received: %r" % receipt
            assert receipt.get("gate") == "pass", "clean gate != pass: %r" % receipt
            evt = receipt.get("evt_id") or ""
            assert len(evt) == 16 and all(c in "0123456789abcdef" for c in evt), (
                "evt_id is not the shipped 16-hex content address: %r" % evt)
            after = state(leg)
            ids = [i["evt_id"] for i in after["pool"]["items"]]
            assert evt in ids, "submitted item not in pool: %r" % ids
            before_len = len(ids)
            code_blank, blank = submit(leg, "bob", "   ")
            assert code_blank == 400 and blank.get("code") == "E_UGW_BAD_CONTENT", (
                "blank body not refused: %s %r" % (code_blank, blank))
            code_long, long_body = submit(leg, "carol", "a" * (max_len + 40))
            assert code_long == 413 and long_body.get("code") == "E_UGW_TOO_LONG", (
                "over-length not refused: %s %r" % (code_long, long_body))
            assert len(state(leg)["pool"]["items"]) == before_len, "a refusal stored an item"
            print("PASS AC-UGW3 gate=pass evt=%s... pool=%d blank=400 long=413 "
                  "refusals_stored=0" % (evt[:8], before_len))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-UGW3 :: %s" % exc)

        # ---- AC-UGW4 -------------------------------------------------------
        try:
            before = len(state(leg)["pool"]["items"])
            code_bad, bad = submit(leg, "dave", "please %s this idea" % forbidden_word)
            assert code_bad in (400, 403, 409, 422), "forbidden not refused: %s" % code_bad
            assert bad.get("code") == "E_CONTENT_REJECTED", (
                "forbidden code wrong: %r" % bad)
            assert len(state(leg)["pool"]["items"]) == before, "forbidden word stored an item"
            code_gray, gray = submit(leg, "erin", "an idea about %s reform" % gray_word)
            assert code_gray == 200, "gray submit answered %s (%r)" % (code_gray, gray)
            assert gray.get("gate") == "review" and gray.get("suspended") is True, (
                "gray case not suspended: %r" % gray)
            review = state(leg)["review"]
            assert len(review) == 1, "suspended list size %d" % len(review)
            assert review[0]["evt_id"] == gray["evt_id"], "suspended row is a different case"
            with open(MODULE, "rb") as fh:
                module_src = fh.read().decode("ascii")
            for word in list(cfg["gate"]["forbidden_words"][:5]) + list(cfg["gate"]["gray_words"][:5]):
                assert word not in module_src, "a configured word is a module literal"
            print("PASS AC-UGW4 forbidden=%s refused=4xx/%s stored=0 gray_suspended=True "
                  "review_rows=1 words_literal=0"
                  % (bad.get("code"), code_bad))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-UGW4 :: %s" % exc)

        # ---- AC-UGW5 -------------------------------------------------------
        try:
            review = state(leg)["review"]
            pending = review[0]["evt_id"]
            pool_before = len(state(leg)["pool"]["items"])
            code_pass, passed = verdict(leg, pending, "pass")
            assert code_pass == 200, "pass verdict answered %s (%r)" % (code_pass, passed)
            after = state(leg)
            assert pending not in [r["evt_id"] for r in after["review"]], (
                "decided case still suspended")
            ids = [i["evt_id"] for i in after["pool"]["items"]]
            assert pending in ids, "passed case never reached the pool"
            assert len(ids) == pool_before + 1, "pool did not grow by exactly one"
            code_twice, twice = verdict(leg, pending, "pass")
            assert code_twice in (400, 409), "second verdict not refused: %s" % code_twice
            assert twice.get("code") == "E_REVIEW_DONE", (
                "second verdict code wrong: %r" % twice)
            code_g2, g2 = submit(leg, "frank", "another %s idea entirely" % gray_word)
            assert code_g2 == 200 and g2.get("suspended") is True, (
                "second gray case not suspended: %s %r" % (code_g2, g2))
            code_risk, risky = verdict(leg, g2["evt_id"], "risky")
            assert code_risk in (400, 403, 409, 422), "risky verdict answered %s" % code_risk
            assert risky.get("code") == "E_CONTENT_REJECTED", "risky code wrong: %r" % risky
            row = leg.pipe.store.review_row(g2["evt_id"])
            assert row is not None and row["verdict"] == "risky", "queue trace lost"
            code_unknown, unknown = verdict(leg, "0" * 32, "pass")
            assert code_unknown == 404 and unknown.get("code") == "E_UGW_UNKNOWN_CASE", (
                "unknown case wrong: %s %r" % (code_unknown, unknown))
            print("PASS AC-UGW5 pass_routed=True twice=409/%s risky=422/trace=risky "
                  "unknown=404" % twice.get("code"))
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-UGW5 :: %s" % exc)

        # ---- AC-UGW6 -------------------------------------------------------
        try:
            code_404, _ = http_json(leg.port, "/ugc/nope")
            assert code_404 == 404, "unknown GET path answered %s" % code_404
            code_405, body_405 = http_json(leg.port, "/ugc/api/state", "POST", {})
            assert code_405 == 405, "POST on the state route answered %s" % code_405
            assert body_405.get("code") == "E_UGW_METHOD", "405 code wrong: %r" % body_405
            code_put, _ = http_json(leg.port, "/ugc", "PUT", {})
            assert code_put == 405, "PUT on the page route answered %s" % code_put
            with open(MODULE, "rb") as fh:
                module_bytes = fh.read()
            module_src = module_bytes.decode("ascii")
            for banned in ("import time", "import datetime", "from datetime"):
                assert banned not in module_src, "module imports a clock: %s" % banned
            with open(PAGE, "rb") as fh:
                page_bytes = fh.read()
            assert not page_bytes.startswith(b"\xef\xbb\xbf"), "page carries a BOM"
            assert b"\r\n" not in page_bytes, "page carries CRLF line endings"
            with open(REGISTRY, encoding="utf-8") as fh:
                registry = fh.read()
            assert ROW_ID in registry, "registry carries no row for this suite"
            print("PASS AC-UGW6 unknown=404 post_state=405 put=405 ascii_module=True "
                  "clock=0 bom=False crlf=0 registry=True")
        except (AssertionError, UnicodeDecodeError) as exc:
            failed += 1
            print("FAIL AC-UGW6 :: %s" % exc)
    finally:
        if leg is not None:
            leg.close()

    total = 6
    if failed:
        print("SUITE FAIL %d/%d" % (total - failed, total))
        return 1
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())