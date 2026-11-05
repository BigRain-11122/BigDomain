"""Suite for the 19.9 entrance checkout face (BigDomain R2459, P-47-4).

Six criteria AC-CKD1..AC-CKD6 pre-registered in the R2459 backlog row BEFORE
this code existed. Every criterion is read off a REAL server started on port
0 (the OS assigns it) over the shipped pay_mock and msgsec_stub modules, so
nothing here proves a fixture instead of the product.

Usage: python test_checkout_demo.py
Exit: 0 = SUITE PASS 6/6, 2 = FAIL.
"""

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

sys.path.insert(0, HERE)

import checkout_demo  # noqa: E402  (path wired above)

PAGE = os.path.join(HERE, "checkout.html")
MODULE = os.path.join(HERE, "checkout_demo.py")
CONFIG = os.path.join(HERE, "config.json")
REGISTRY = os.path.join(REPO, "src", "sandbox", "reconcile_all.py")

# Standing notices the served page must carry (same escapes the page uses).
NOTICE_MOCK = "\u975e\u771f\u5b9e\u6263\u8d39"          # non-chargeable
NOTICE_AI = "AI \u751f\u6210\u5185\u5bb9\u6807\u8bc6"     # AI generated label
NOTICE_ADVICE = "\u975e\u6295\u987e\u98ce\u9669\u63d0\u793a"  # non-advice note

RESULTS = []


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % (name, "FAIL" if bad else "PASS",
                       ("  " + detail) if detail else ""))
    return bad


TRANSPORT_RETRIES = 3


def http(url, method="GET", body=None):
    """Read the response, retrying TRANSPORT failures only.

    Every criterion here is about the product response (status, bytes,
    counts), never about how many TCP attempts it took, so a socket-level
    abort under load is retried a bounded number of times and printed when
    it happens. An HTTP status is never retried and no assertion is relaxed.
    """
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    for attempt in range(TRANSPORT_RETRIES):
        req = urllib.request.Request(url, data=data, headers=headers,
                                     method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                raw = res.read()
                if attempt:
                    print("  transport retries used=%d on %s" % (attempt, url))
                return res.status, raw, dict(res.headers)
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read(), dict(exc.headers)
        except (ConnectionError, OSError) as exc:
            if attempt == TRANSPORT_RETRIES - 1:
                raise
            print("  transport retry %d on %s: %s"
                  % (attempt + 1, url, type(exc).__name__))
            time.sleep(0.1 * (attempt + 1))
    raise AssertionError("unreachable")


def json_of(raw):
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def main():
    with open(CONFIG, "r", encoding="utf-8") as handle:
        cfg = json.load(handle)
    gate_cfg = cfg["gate"]
    forbidden = gate_cfg["forbidden_words"][0]
    advisory = gate_cfg["advisory_ban_words"][0]

    demo = checkout_demo.build_demo(CONFIG, with_gate=True)
    server = checkout_demo.start_server("127.0.0.1", 0, demo)
    base = "http://127.0.0.1:%d" % server.server_address[1]

    try:
        # -- AC-CKD1: page bytes, offline, three standing notices ----------
        st_a, raw_a, hdr_a = http(base + "/checkout/")
        st_b, raw_b, _ = http(base + "/checkout")
        with open(PAGE, "rb") as handle:
            disk = handle.read()
        text = raw_a.decode("utf-8")
        bad1 = (
            st_a != 200 or st_b != 200
            or "text/html" not in (hdr_a.get("Content-Type") or "")
            or raw_a != raw_b
            or raw_a != disk
            or "http://" in text.replace("http://127.0.0.1", "")
            or "https://" in text
            or NOTICE_MOCK not in text
            or NOTICE_AI not in text
            or NOTICE_ADVICE not in text
        )
        report("AC-CKD1 page=200 html identical=%s bytes=%d notices=mock/ai/advice"
               % (raw_a == raw_b == disk, len(raw_a)), bad1)

        # -- AC-CKD2: order pinned to the canon; blank actor refused -------
        st_o, raw_o, _ = http(base + "/checkout/api/order", "POST",
                              {"actor": "acct-ckd"})
        order = json_of(raw_o).get("order") or {}
        before_orders = len(demo.pay.orders)
        st_blank, raw_blank, _ = http(base + "/checkout/api/order", "POST",
                                      {"actor": "   "})
        blank = json_of(raw_blank)
        bad2 = (
            st_o != 201
            or order.get("amount_cents") != 1990
            or order.get("mock") is not True
            or order.get("chargeable") is not False
            or order.get("state") != "created"
            or st_blank != 400
            or blank.get("error") != "E_PAYMOCK_BAD_ACTOR"
            or len(demo.pay.orders) != before_orders
        )
        report("AC-CKD2 order=%d mock=%s chargeable=%s blank=%d/%s orders_kept=%s"
               % (order.get("amount_cents"), order.get("mock"),
                  order.get("chargeable"), st_blank, blank.get("error"),
                  len(demo.pay.orders) == before_orders), bad2)

        # -- AC-CKD3: settle once; replay same receipt; month card active ---
        st_p1, raw_p1, _ = http(base + "/checkout/api/pay", "POST",
                                {"order_id": order.get("order_id")})
        p1 = json_of(raw_p1)
        st_p2, raw_p2, _ = http(base + "/checkout/api/pay", "POST",
                                {"order_id": order.get("order_id")})
        p2 = json_of(raw_p2)
        st_s, raw_s, _ = http(base + "/checkout/api/state?actor=acct-ckd")
        state = json_of(raw_s)
        ent = (p1.get("entitlement") or state.get("entitlement") or {})
        r1 = p1.get("receipt") or {}
        r2 = p2.get("receipt") or {}
        bad3 = (
            st_p1 != 200 or st_p2 != 200
            or r1.get("replay") is not False
            or r2.get("replay") is not True
            or r1.get("receipt_no") != r2.get("receipt_no")
            or r1.get("chargeable") is not False
            or ent.get("active") is not True
            or ent.get("mock") is not True
            or ent.get("chargeable") is not False
            or state.get("entrance_active") is not True
        )
        report("AC-CKD3 replay1=%s replay2=%s same_receipt=%s card_active=%s"
               % (r1.get("replay"), r2.get("replay"),
                  r1.get("receipt_no") == r2.get("receipt_no"),
                  ent.get("active")), bad3)

        # -- AC-CKD4: entrance gate first, then the shipped content gate ---
        calls0 = demo.counts["gate_calls"]
        st_x, raw_x, _ = http(base + "/checkout/api/send", "POST",
                              {"actor": "acct-nobody", "text": "hello"})
        unpaid = json_of(raw_x)
        calls1 = demo.counts["gate_calls"]

        st_r, raw_r, _ = http(base + "/checkout/api/send", "POST",
                              {"actor": "acct-ckd", "text": "note " + forbidden})
        risky = json_of(raw_r)
        st_v, raw_v, _ = http(base + "/checkout/api/send", "POST",
                              {"actor": "acct-ckd", "text": "note " + advisory})
        review = json_of(raw_v)
        st_ok, raw_ok, _ = http(base + "/checkout/api/send", "POST",
                                {"actor": "acct-ckd", "text": "plain city note"})
        accepted = json_of(raw_ok)
        calls2 = demo.counts["gate_calls"]
        decision = accepted.get("decision") or {}
        bad4 = (
            st_x != 403 or unpaid.get("error") != "E_ENTRANCE_REQUIRED"
            or calls1 != calls0
            or st_r != 422 or risky.get("error") != "E_CONTENT_REJECTED"
            or st_v != 422 or review.get("error") != "E_CONTENT_REVIEW"
            or st_ok != 200 or accepted.get("accepted") is not True
            or accepted.get("ai_generated") is not False
            or not decision.get("trace_id")
            or decision.get("suggest") != "pass"
            or calls2 != calls0 + 3
        )
        report("AC-CKD4 unpaid=%d/%s gate_before=%s risky=%d review=%d pass=%d gate_after=%d"
               % (st_x, unpaid.get("error"), calls1 == calls0, st_r, st_v, st_ok,
                  calls2 - calls0), bad4)

        # -- AC-CKD5: unknown order mutates nothing; 404/405 surface --------
        before = (len(demo.pay.orders), len(demo.pay.receipts),
                  len(demo.pay.entitlements))
        st_u, raw_u, _ = http(base + "/checkout/api/pay", "POST",
                              {"order_id": "sbx-order-does-not-exist"})
        unknown = json_of(raw_u)
        after = (len(demo.pay.orders), len(demo.pay.receipts),
                 len(demo.pay.entitlements))
        st_404, _, _ = http(base + "/checkout/nope")
        st_404p, _, _ = http(base + "/checkout/api/nope", "POST", {})
        st_405, _, _ = http(base + "/checkout/", "PUT", {})
        bad5 = (
            st_u != 404 or unknown.get("error") != "E_PAYMOCK_UNKNOWN_ORDER"
            or before != after
            or st_404 != 404 or st_404p != 404 or st_405 != 405
        )
        report("AC-CKD5 unknown=%d/%s untouched=%s 404=%d/%d put=%d"
               % (st_u, unknown.get("error"), before == after, st_404, st_404p,
                  st_405), bad5)

        # -- AC-CKD6: ASCII module, stdlib only, one registry row -----------
        with open(MODULE, "rb") as handle:
            src_bytes = handle.read()
        src = src_bytes.decode("ascii", "replace")
        ascii_ok = all(b < 128 for b in src_bytes)
        banned = ["urllib.request", "http.client", "socket", "requests",
                  "import time", "import datetime", "from datetime"]
        banned_hit = [b for b in banned if b in src]
        with open(PAGE, "rb") as handle:
            page_has_non_ascii = any(b > 127 for b in handle.read())
        with open(REGISTRY, "r", encoding="utf-8") as handle:
            registry = handle.read()
        row = '("os-lobby-checkout-demo", os.path.join("lobby", "test_checkout_demo.py"), 6)'
        bad6 = (
            not ascii_ok
            or banned_hit != []
            or not page_has_non_ascii
            or registry.count(row) != 1
        )
        report("AC-CKD6 ascii=%s banned=%s page_utf8=%s registry_row=%d"
               % (ascii_ok, banned_hit, page_has_non_ascii, registry.count(row)),
               bad6)
    finally:
        server.shutdown()
        server.server_close()

    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    digest = hashlib.sha256(
        "\n".join("%s:%s" % (n, "PASS" if ok else "FAIL") for n, ok in RESULTS).encode()
    ).hexdigest()[:32].upper()
    verdict = "SUITE PASS %d/%d" % (passed, total) if passed == total else \
        "SUITE FAIL %d/%d" % (passed, total)
    print("%s digest=%s" % (verdict, digest))
    return 0 if passed == total else 2


if __name__ == "__main__":
    raise SystemExit(main())