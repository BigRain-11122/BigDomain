"""Suite for the token ledger console (BigDomain R2469, P-47-2b).

Six criteria AC-LC1..AC-LC6 pre-registered in the R2469 backlog row BEFORE
this code existed. Every criterion is read off a REAL server started on port
0 (the OS assigns it) over the SHIPPED ledger and the SHIPPED reconcile
script, so nothing here proves a fixture instead of the product.

Two legs run in-process, each on its own temp database and its own bound
port, and their criterion digests must match; the run prints
EVIDENCE CAPTURE legs=2 identical=<bool>.

Usage: python test_ledger_page.py
Exit: 0 = SUITE PASS 6/6, 2 = FAIL.
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

sys.path.insert(0, HERE)

import ledger_page  # noqa: E402  (path wired above)
import reconcile as reconcile_script  # noqa: E402

PAGE = os.path.join(HERE, "ledger.html")
MODULE = os.path.join(HERE, "ledger_page.py")
CONFIG = os.path.join(HERE, "config.json")
REGISTRY = os.path.join(REPO, "src", "sandbox", "reconcile_all.py")

RESULTS = []

TRANSPORT_RETRIES = 3


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % (name, "FAIL" if bad else "PASS",
                       ("  " + detail) if detail else ""))
    return bad


def http(url, method="GET", body=None):
    """Read the response, retrying TRANSPORT failures only."""
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    for attempt in range(TRANSPORT_RETRIES):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                raw = res.read()
                if attempt:
                    print("  transport retries used=%d on %s" % (attempt, url))
                return res.status, raw, dict(res.headers)
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read(), dict(exc.headers)
        except (ConnectionError, OSError):
            if attempt == TRANSPORT_RETRIES - 1:
                raise
    raise AssertionError("unreachable")


def jload(raw):
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}


def balances(payload):
    return dict((row["account_id"], int(row["balance"]))
                for row in payload.get("accounts") or [])


def run_leg(tmpdir, tag):
    """One full pass over AC-LC1..AC-LC6 against a real server."""
    db_path = os.path.join(tmpdir, "ledger-" + tag + ".db")
    console = ledger_page.build_console(db_path, CONFIG)
    server = ledger_page.start_server("127.0.0.1", 0, console)
    port = server.server_address[1]
    base = "http://127.0.0.1:%d" % port
    try:
        with open(CONFIG, "r", encoding="utf-8") as handle:
            cfg = json.load(handle)
        tok = cfg["token"]

        # -- AC-LC1: the page on disk, offline, three standing surfaces ----
        with open(PAGE, "rb") as handle:
            page_bytes = handle.read()
        st_a, body_a, _ = http(base + "/ledger/")
        st_b, body_b, _ = http(base + "/ledger")
        ascii_label = tok["ai_label_text"].encode("utf-8")
        disclaimer = tok["disclaimer"].encode("utf-8")
        mock_line = "\u6ca1\u6709\u4efb\u4f55\u771f\u5b9e\u6263\u6b3e".encode("utf-8")
        no_cash_out = "\u4e0d\u53ef\u63d0\u73b0".encode("utf-8")
        ext = [tok_ for tok_ in (b"http://", b"https://", b'src="//', b"href='//")
               if tok_ in page_bytes]
        bad1 = (
            st_a != 200 or st_b != 200
            or body_a != page_bytes or body_b != page_bytes
            or len(page_bytes) <= 3000
            or ext != []
            or ascii_label not in page_bytes
            or disclaimer not in page_bytes
            or mock_line not in page_bytes
            or no_cash_out not in page_bytes
        )
        report("AC-LC1 bytes=%d same=%s external=%s notices=%s/%s/%s"
               % (len(page_bytes), body_a == page_bytes and body_b == page_bytes,
                  ext, ascii_label in page_bytes, disclaimer in page_bytes,
                  mock_line in page_bytes), bad1)

        # -- AC-LC2: state derived from the SHIPPED balance and checks -----
        st, raw, _ = http(base + "/ledger/api/state")
        state = jload(raw)
        acct_ok = isinstance(state.get("accounts"), list) and state["accounts"] != []
        derived = dict((row["account_id"], row["balance"])
                       for row in state.get("accounts") or [])
        disclaimer_block = state.get("disclaimer") or {}
        fresh_verdict = (state.get("reconcile") or {}).get("verdict")

        real_balance = console.ledger.balance
        moved = {"n": 0}

        def shifted(account_id):
            out = real_balance(account_id)
            moved["n"] += 1
            return {"account_id": out["account_id"],
                    "balance": int(out["balance"]) + 7}

        console.ledger.balance = shifted
        try:
            _, raw_shift, _ = http(base + "/ledger/api/state")
        finally:
            console.ledger.balance = real_balance
        shifted_state = jload(raw_shift)
        shifted_map = dict((row["account_id"], row["balance"])
                           for row in shifted_state.get("accounts") or [])
        moved_ok = (moved["n"] > 0 and shifted_map
                    and all(shifted_map[k] == derived[k] + 7 for k in derived))

        real_check = reconcile_script.check_lines

        def failing_checks(conn, config):
            return 3

        reconcile_script.check_lines = failing_checks
        try:
            _, raw_fake, _ = http(base + "/ledger/api/state")
        finally:
            reconcile_script.check_lines = real_check
        fake_block = (jload(raw_fake) or {}).get("reconcile") or {}
        seam_ok = fake_block.get("verdict") == "FAIL" and fake_block.get("failed") == 3

        bad2 = (
            st != 200 or not acct_ok or not moved_ok or not seam_ok
            or fresh_verdict != "PASS"
            or disclaimer_block.get("disclaimer") != tok["disclaimer"]
            or bool(disclaimer_block.get("persistent")) is not True
            or state.get("chargeable") is not False
        )
        report("AC-LC2 status=%d accounts=%d balance_seam=%s check_seam=%s verdict=%s"
               % (st, len(state.get("accounts") or []), moved_ok, seam_ok,
                  fresh_verdict), bad2)

        # -- AC-LC3: mint books, refusals book nothing ---------------------
        before = balances(jload(http(base + "/ledger/api/state")[1]))
        st_m, raw_m, _ = http(base + "/ledger/api/mint", "POST",
                              {"pool_id": "pool:reward", "amount": 100,
                               "ref": "suite-mint-" + tag})
        mid = jload(raw_m)
        after = balances(jload(http(base + "/ledger/api/state")[1]))
        total_after = sum(after.values())
        mint_ok = (
            st_m == 201
            and after.get("pool:reward") == before.get("pool:reward", 0) + 100
            and after.get("equity:auth") == before.get("equity:auth", 0) - 100
            and total_after == 0
            and (mid.get("reconcile") or {}).get("verdict") == "PASS"
            and mid.get("tx_id")
        )
        st_bad_pool, raw_bad_pool, _ = http(base + "/ledger/api/mint", "POST",
                                            {"pool_id": "pool:nope", "amount": 5,
                                             "ref": "suite-bad-pool-" + tag})
        st_bad_amt, raw_bad_amt, _ = http(base + "/ledger/api/mint", "POST",
                                          {"pool_id": "pool:reward", "amount": "abc",
                                           "ref": "suite-bad-amt-" + tag})
        after_refused = balances(jload(http(base + "/ledger/api/state")[1]))
        bad3 = not (
            mint_ok
            and st_bad_pool == 400 and jload(raw_bad_pool).get("error") == "E_BAD_ACCOUNT"
            and st_bad_amt == 400 and jload(raw_bad_amt).get("error") == "E_BAD_AMOUNT"
            and after_refused == after
        )
        report("AC-LC3 status=%d pool+%d equity%d total=%d verdict=%s refusals=%d/%s %d/%s"
               % (st_m, after.get("pool:reward", 0) - before.get("pool:reward", 0),
                  after.get("equity:auth", 0) - before.get("equity:auth", 0),
                  total_after, (mid.get("reconcile") or {}).get("verdict"),
                  st_bad_pool, jload(raw_bad_pool).get("error"),
                  st_bad_amt, jload(raw_bad_amt).get("error")), bad3)

        # -- AC-LC4: server-side source_ai, gate-before-pay ----------------
        usr = "usr:demo"
        pre4 = balances(jload(http(base + "/ledger/api/state")[1]))
        st_gate, raw_gate, _ = http(base + "/ledger/api/reward", "POST",
                                    {"account_id": usr, "action": "chat_mining",
                                     "ref": "suite-ev-nogate-" + tag})
        after_gate = balances(jload(http(base + "/ledger/api/state")[1]))
        gate_refused = (
            st_gate == 403
            and jload(raw_gate).get("error") == "E_GATE_REF"
            and after_gate == pre4
        )
        passed_ref = "suite-ev-pass-" + tag
        console.ledger.record_gate_pass(passed_ref)
        st_r, raw_r, _ = http(base + "/ledger/api/reward", "POST",
                              {"account_id": usr, "action": "chat_mining",
                               "ref": passed_ref, "source_ai": False})
        after_r = balances(jload(http(base + "/ledger/api/state")[1]))
        spec = cfg["actions"]["chat_mining"]
        reward_ok = (
            st_r == 201
            and after_r.get(usr) == pre4.get(usr, 0) + int(spec["score"])
            and after_r.get(spec["pool"]) == pre4.get(spec["pool"], 0) - int(spec["score"])
        )
        st_l, _, _ = http(base + "/ledger/api/reward", "POST",
                          {"account_id": usr, "action": "login",
                           "ref": "suite-ev-login-" + tag, "source_ai": False})
        _, raw_bill, _ = http(base + "/ledger/api/bill?account=" + usr)
        items = (jload(raw_bill) or {}).get("items") or []
        ai_rows = [it for it in items if it.get("source_ai") is True]
        server_authority_ok = (
            st_l == 201
            and bool(ai_rows)
            and all(it.get("ai_label") == tok["ai_label_text"] for it in ai_rows)
            and all(it.get("source_ai") is False
                    for it in items if it.get("action") == "login")
        )
        bad4 = not (gate_refused and reward_ok and server_authority_ok)
        report("AC-LC4 gate=%d/%s booked=%s ai_rows=%d server_ai=%s"
               % (st_gate, jload(raw_gate).get("error"), reward_ok, len(ai_rows),
                  server_authority_ok), bad4)

        # -- AC-LC5: overdraw refused, zero-sum survives ------------------
        pre5 = balances(jload(http(base + "/ledger/api/state")[1]))
        st_over, raw_over, _ = http(base + "/ledger/api/spend", "POST",
                                    {"account_id": usr, "amount": 9999,
                                     "ref": "suite-spend-over-" + tag})
        after_over = balances(jload(http(base + "/ledger/api/state")[1]))
        st_ok, raw_ok, _ = http(base + "/ledger/api/spend", "POST",
                                {"account_id": usr, "amount": 3,
                                 "ref": "suite-spend-ok-" + tag})
        after_ok = balances(jload(http(base + "/ledger/api/state")[1]))
        final_state = jload(http(base + "/ledger/api/state")[1])
        bad5 = not (
            st_over == 409
            and jload(raw_over).get("error") == "E_NEGATIVE_BALANCE"
            and after_over == pre5
            and sum(pre5.values()) == 0
            and st_ok == 201
            and after_ok.get(usr) == pre5.get(usr, 0) - 3
            and sum(after_ok.values()) == 0
            and (final_state.get("reconcile") or {}).get("verdict") == "PASS"
        )
        report("AC-LC5 overdraw=%d/%s untouched=%s spend=%d balance%d total=%d verdict=%s"
               % (st_over, jload(raw_over).get("error"), after_over == pre5, st_ok,
                  after_ok.get(usr, 0), sum(after_ok.values()),
                  (final_state.get("reconcile") or {}).get("verdict")), bad5)

        # -- AC-LC6: route surface, ASCII module, one registry row --------
        st_slash, body_slash, _ = http(base + "/ledger/")
        st_404, _, _ = http(base + "/ledger/api/nope")
        st_405, _, _ = http(base + "/ledger/api/mint")
        st_bill, raw_bill2, _ = http(base + "/ledger/api/bill?account=" + usr)
        with open(MODULE, "rb") as handle:
            src_bytes = handle.read()
        src = src_bytes.decode("ascii", "replace")
        ascii_ok = all(b < 128 for b in src_bytes)
        banned = ["urllib.request", "http.client", "socket", "requests",
                  "import time", "import datetime", "from datetime"]
        banned_hit = [b for b in banned if b in src]
        with open(REGISTRY, "r", encoding="utf-8") as handle:
            registry = handle.read()
        row = '("os-ledger-page", os.path.join("ledger", "test_ledger_page.py"), 6)'
        bill_items = (jload(raw_bill2) or {}).get("items") or []
        bad6 = not (
            st_slash == 200 and body_slash == page_bytes
            and st_404 == 404 and st_405 == 405
            and st_bill == 200 and bool(bill_items)
            and ascii_ok and banned_hit == []
            and registry.count(row) == 1
        )
        report("AC-LC6 same=%s 404=%d 405=%d bill=%d ascii=%s banned=%s row=%d"
               % (body_slash == page_bytes, st_404, st_405, len(bill_items),
                  ascii_ok, banned_hit, registry.count(row)), bad6)

        passed = sum(1 for _, ok in RESULTS if ok)
        total = len(RESULTS)
        digest = hashlib.sha256(
            "\n".join("%s:%s" % (n, "PASS" if ok else "FAIL")
                      for n, ok in RESULTS).encode()
        ).hexdigest()[:32].upper()
        return passed, total, digest
    finally:
        server.shutdown()
        server.server_close()
        console.close()


def main():
    legs = []
    for idx, tag in enumerate(("a", "b")):
        RESULTS[:] = []
        tmpdir = tempfile.mkdtemp(prefix="ledger-page-" + tag + "-")
        passed, total, digest = run_leg(tmpdir, tag)
        legs.append((passed, total, digest))
        if total != 6:
            print("FAIL leg %s criteria=%d, expected 6" % (tag, total))
    identical = legs[0][2] == legs[1][2] and legs[0][0] == legs[1][0]
    print("EVIDENCE CAPTURE legs=2 identical=%s digests=%s/%s"
          % (identical, legs[0][2], legs[1][2]))
    passed, total, digest = legs[-1]
    verdict = "SUITE PASS %d/%d" % (passed, total) if passed == total else \
        "SUITE FAIL %d/%d" % (passed, total)
    print("%s digest=%s" % (verdict, digest))
    return 0 if (passed == total and identical) else 2


if __name__ == "__main__":
    raise SystemExit(main())