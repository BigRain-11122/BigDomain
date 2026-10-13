"""Cross-restart persistence window for the trading-hall
value-added expedite face (BigDomain R1937; the expedite seat of
the R1886 persist-family lineage - the R1935-seeded row, criteria
pre-registered in the R1937 tech.md claim row before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Three-instance world on the real product path: anchor world ->
close both pieces -> reopen the same db/config -> byte-identical
read replay -> restart-surviving gate probes (zero drift) ->
post-restart real-path continuation -> frozen faces + idempotent
replay across restart -> pure-read law -> third instance
stability. queue_snapshot and credits_view rows carry
purchased_utc / consumed_utc / submitted_utc and bound spend_tx
(persisted values, not clock echoes), so full-dump byte-identity
holds without clock freezing; the evidence digests mask those
fields (banded projection, R1902 law) so the suite stdout stays
deterministic across double runs.

Usage: python test_expedite_persist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L          # noqa: E402  (P-47-2b core)
import expedite as X        # noqa: E402  (R620 extension face)

RESULTS = []

_TS_RE = re.compile(
    r'"(?:purchased_utc|consumed_utc|submitted_utc)": "[^"]*"')
_SPEND_RE = re.compile(r'"spend_tx": "[^"]*"')


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_x_error(fn, *codes):
    try:
        fn()
    except X.ExpediteError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def masked(text):
    out = _SPEND_RE.sub('"spend_tx": "<tx>"', text)
    return _TS_RE.sub('"ts": "<ts>"', out)


def evidence_digest(snap):
    parts = []
    for key in sorted(snap):
        val = snap[key]
        if isinstance(val, int):
            parts.append("%s=%s" % (key, val))
        else:
            parts.append("%s=%s" % (key, masked(val)))
    return sha16("\n".join(parts))


def table_counts(db_path):
    out = {}
    conn = sqlite3.connect(db_path)
    for tbl in ("expedite_credits", "expedite_jobs", "ledger_tx",
                "ledger_entries"):
        out[tbl] = int(conn.execute(
            "SELECT COUNT(*) FROM " + tbl).fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    conn.close()
    return out


def spend_cross(db_path, tx_id, account_id):
    """SQL cross: the bound spend tx is a real ledger spend row
    with a debit leg on the buying account."""
    conn = sqlite3.connect(db_path)
    head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                        (tx_id,)).fetchone()
    leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = ? AND direction = 'debit'",
        (tx_id, account_id)).fetchone()
    conn.close()
    return (head[0] if head else None), (leg[0] if leg else None)


def read_battery(ef, led):
    return {
        "queue": dump(ef.queue_snapshot()),
        "cr_alice": dump(ef.credits_view("usr:alice")),
        "cr_bob": dump(ef.credits_view("usr:bob")),
        "cr_carol": dump(ef.credits_view("usr:carol")),
        "bal_alice": led.balance("usr:alice")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_pool": led.balance("pool:reserve")["balance"],
    }


def battery_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    tmp = tempfile.mkdtemp(prefix="expedite-persist-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    expmod_sha_before = sha16(io_read(os.path.join(BASE, "expedite.py")))
    ledmod_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    db_path = os.path.join(tmp, "ledger.db")

    # ---- instance 1: anchor world on the real product path -------
    led = L.Ledger(db_path, cfg)
    ef = X.ExpediteFace(led)
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-EPP-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    led.adjust([("pool:reserve", "debit", 2000),
                ("usr:alice", "credit", 2000)],
               "manual:epp-fund-alice", "persist window funding alice")
    led.adjust([("pool:reserve", "debit", 600),
                ("usr:bob", "credit", 600)],
               "manual:epp-fund-bob", "persist window funding bob")
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:carol", "credit", 400)],
               "manual:epp-fund-carol", "persist window funding carol")

    # alice buys five credits (one ref replayed idempotently)
    pa1 = ef.purchase("usr:alice", "demo_queuejump", 50, "order:epp-a1")
    pa1r = ef.purchase("usr:alice", "demo_queuejump", 50, "order:epp-a1")
    pa1b = ef.purchase("usr:alice", "demo_queuejump", 12, "order:epp-a1b")
    pa2 = ef.purchase("usr:alice", "submit_expedite", 10, "order:epp-a2")
    pa3 = ef.purchase("usr:alice", "backtest_expedite", 20, "order:epp-a3")
    pa4 = ef.purchase("usr:alice", "resident_dialogue", 5, "order:epp-a4")
    pb1 = ef.purchase("usr:bob", "demo_queuejump", 30, "order:epp-b1")

    # job spectrum: one normal, two expedited, one more normal
    jb9 = ef.submit("usr:bob", "demo:build-9")
    je3 = ef.submit("usr:alice", "demo:build-3",
                    expedite_kind="demo_queuejump")
    jt2 = ef.submit("usr:alice", "idea:tower-mk2")
    je4 = ef.submit("usr:alice", "demo:build-4",
                    expedite_kind="demo_queuejump")

    # -- AC-EPP1 control anchor: world pinned + gate probes -----
    bal1 = read_battery(ef, led)
    cnt1 = table_counts(db_path)
    ok_world = (
        pa1["idempotent"] is False and pa1r["idempotent"] is True
        and pa1["credit_id"] == pa1r["credit_id"]
        and pa1["spend_tx"] == pa1r["spend_tx"] and not pa1r["consumed"]
        and [jb9["position"], je3["position"], jt2["position"],
             je4["position"]] == [1, 1, 3, 2]
        and not jb9["expedited"] and je3["expedited"]
        and not jt2["expedited"] and je4["expedited"]
        and je3["used_credit"] == pa1["credit_id"]
        and je4["used_credit"] == pa1b["credit_id"]
        and bal1["bal_alice"] == 1903 and bal1["bal_bob"] == 570
        and bal1["bal_carol"] == 400 and bal1["bal_pool"] == 17127
        and cnt1["expedite_credits"] == 6
        and cnt1["expedite_jobs"] == 4 and cnt1["spend_tx"] == 6)
    probe_specs = (
        ("no-credit", lambda: ef.submit(
            "usr:alice", "demo:build-5",
            expedite_kind="demo_queuejump"), X.E_EXP_NO_CREDIT),
        ("kind-mismatch", lambda: ef.submit(
            "usr:alice", "demo:build-6",
            expedite_kind="submit_expedite"), X.E_EXP_KIND_MISMATCH),
        ("bad-kind", lambda: ef.submit(
            "usr:alice", "idea:y", expedite_kind="magic"),
         X.E_EXP_BAD_KIND),
        ("bad-account", lambda: ef.submit("svc:x", "idea:y"),
         X.E_EXP_BAD_ACCOUNT),
        ("empty-subject", lambda: ef.submit("usr:alice", "  "),
         X.E_EXP_BAD_SUBJECT))
    probes1 = []
    for label, fn, code in probe_specs:
        ok_one, got = expect_x_error(fn, code)
        probes1.append("%s=%s" % (label, got) if ok_one else
                      "%s NOT-RAISED(%s)" % (label, got))
    ok_probes1 = all("NOT-RAISED" not in p for p in probes1)
    ok_probe_drift1 = (table_counts(db_path) == cnt1
                       and read_battery(ef, led) == bal1)
    cr_a = ef.credits_view("usr:alice")["credits"]
    demo_rows = [c for c in cr_a if c["kind"] == "demo_queuejump"]
    ok_credits = (
        len(cr_a) == 5
        and all(c["consumed"] for c in demo_rows)
        and all(c["consumed_job"] in (je3["job_id"], je4["job_id"])
                for c in demo_rows)
        and not any(c["consumed"] for c in cr_a
                    if c["kind"] != "demo_queuejump")
        and len(ef.credits_view("usr:bob")["credits"]) == 1
        and not ef.credits_view("usr:bob")["credits"][0]["consumed"]
        and ef.credits_view("usr:carol")["credits"] == [])
    queue1 = ef.queue_snapshot()["jobs"]
    ok_queue = ([(j["subject"], j["expedited"]) for j in queue1] ==
                [("demo:build-3", True), ("demo:build-4", True),
                 ("demo:build-9", False), ("idea:tower-mk2", False)]
                and [j["position"] for j in queue1] == [1, 2, 3, 4])
    ok1 = (ok_world and ok_probes1 and ok_probe_drift1 and ok_credits
           and ok_queue)
    record("AC-EPP1", ok1, "anchor world pinned (alice five credits"
          " demo x2 consumed->jobs %s/%s, submit/backtest/resident"
          " unconsumed; bob one unconsumed; carol empty spine);"
          " queue two-tier order [build-3 exp, build-4 exp, build-9"
          " norm, tower-mk2 norm] positions 1-4; five gate probes"
          " rejected (%s); counts credits=%d jobs=%d spend-tx=%d"
          " frozen across probes; balances 1903/570/400/17127;"
          " digest=%s" % (je3["job_id"], je4["job_id"],
                          "; ".join(probes1), cnt1["expedite_credits"],
                          cnt1["expedite_jobs"], cnt1["spend_tx"],
                          evidence_digest(bal1)))

    # -- AC-EPP2 cross-restart byte-identical replay -------------
    ef.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    ef2 = X.ExpediteFace(led2)
    bal2 = read_battery(ef2, led2)
    diffs2 = battery_diffs(bal1, bal2)
    ok2 = not diffs2
    record("AC-EPP2", ok2, "two-piece close->reopen (ef.close ->"
          " led.close -> Ledger same db/cfg + ExpediteFace fresh):"
          " read battery byte-identical to pre-close snapshot"
          " (queue + credits_view x3 + four balances), diffs=%s;"
          " persisted timestamps and spend_tx values replay with"
          " zero in-memory drift; digest=%s" %
          (diffs2 or "none", evidence_digest(bal2)))

    # -- AC-EPP3 gates survive restart, zero drift ---------------
    probes2 = []
    for label, fn, code in probe_specs:
        fn2 = None
        if label == "no-credit":
            def fn2(_ef=ef2):
                _ef.submit("usr:alice", "demo:build-5",
                           expedite_kind="demo_queuejump")
        elif label == "kind-mismatch":
            def fn2(_ef=ef2):
                _ef.submit("usr:alice", "demo:build-6",
                           expedite_kind="submit_expedite")
        elif label == "bad-kind":
            def fn2(_ef=ef2):
                _ef.submit("usr:alice", "idea:y", expedite_kind="magic")
        elif label == "bad-account":
            def fn2(_ef=ef2):
                _ef.submit("svc:x", "idea:y")
        else:
            def fn2(_ef=ef2):
                _ef.submit("usr:alice", "  ")
        ok_one, got = expect_x_error(fn2, code)
        probes2.append("%s=%s" % (label, got) if ok_one else
                       "%s NOT-RAISED(%s)" % (label, got))
    ok_probes2 = all("NOT-RAISED" not in p for p in probes2)
    ok_drift2 = (table_counts(db_path) == cnt1
                 and read_battery(ef2, led2) == bal2)
    ok3 = ok_probes2 and ok_drift2
    record("AC-EPP3", ok3, "restart-surviving gates: five probes"
          " all rejected with identical codes on instance 2 (%s);"
          " counts and balances frozen across the probe batch"
          " (credits/jobs/spend-tx %d/%d/%d unchanged, zero"
          " charge, zero rows)" % ("; ".join(probes2),
                                   cnt1["expedite_credits"],
                                   cnt1["expedite_jobs"],
                                   cnt1["spend_tx"]))

    # -- AC-EPP4 post-restart real-path continuation --------------
    pc1 = ef2.purchase("usr:carol", "demo_queuejump", 25, "order:epp-c1")
    head, leg = spend_cross(db_path, pc1["spend_tx"], "usr:carol")
    jc10 = ef2.submit("usr:carol", "demo:build-10",
                      expedite_kind="demo_queuejump")
    bal4 = read_battery(ef2, led2)
    cnt4 = table_counts(db_path)
    queue4 = ef2.queue_snapshot()["jobs"]
    c10 = [c for c in ef2.credits_view("usr:carol")["credits"]
           if c["purchase_ref"] == "order:epp-c1"][0]
    ok4 = (
        pc1["idempotent"] is False and head == "spend" and leg == "debit"
        and jc10["expedited"] and jc10["position"] == 3
        and jc10["used_credit"] == pc1["credit_id"]
        and c10["consumed"] and c10["consumed_job"] == jc10["job_id"]
        and cnt4["expedite_jobs"] == 5 and cnt4["spend_tx"] == 7
        and bal4["bal_carol"] == 375 and bal4["bal_bob"] == 570
        and [(j["subject"], j["expedited"]) for j in queue4] ==
        [("demo:build-3", True), ("demo:build-4", True),
         ("demo:build-10", True), ("demo:build-9", False),
         ("idea:tower-mk2", False)]
        and [j["position"] for j in queue4] == [1, 2, 3, 4, 5])
    record("AC-EPP4", ok4, "post-restart continuation: carol fresh"
          " purchase order:epp-c1 binds a real spend tx (SQL cross"
          " type=%s, debit leg=%s, tx_id not echoed); carol jumps"
          " demo:build-10 consuming that credit, expedited-tier"
          " FIFO lands position 3 behind the two earlier expedited"
          " jobs; derived faces recompute zero-cache (jobs 4->5,"
          " spend-tx 6->7, carol 400->375, bob 570 frozen); digest=%s"
          % (head, leg, evidence_digest(bal4)))

    # -- AC-EPP5 frozen faces + idempotent replay across restart --
    cr_bob_now = ef2.credits_view("usr:bob")["credits"]
    cr_bob_before = json.loads(bal1["cr_bob"])["credits"]
    old_by_id = {j["job_id"]: j for j in queue1}
    now_by_id = {j["job_id"]: j for j in queue4}
    frozen_fields = ("subject", "account_id", "expedited", "base_seq",
                     "used_credit")
    frozen_ok = all(
        all(old_by_id[jid][f] == now_by_id[jid][f]
            for f in frozen_fields) for jid in old_by_id)
    pos_shift = (now_by_id[jb9["job_id"]]["position"] == 4
                 and now_by_id[jt2["job_id"]]["position"] == 5)
    replay = ef2.purchase("usr:alice", "demo_queuejump", 50, "order:epp-a1")
    replay_bad, _ = expect_x_error(
        lambda: ef2.submit("usr:alice", "demo:build-5",
                           expedite_kind="demo_queuejump"),
        X.E_EXP_NO_CREDIT)
    bal5 = read_battery(ef2, led2)
    ok5 = (
        dump(cr_bob_now) == dump(cr_bob_before) and frozen_ok
        and pos_shift and replay["idempotent"] is True
        and replay["credit_id"] == pa1["credit_id"]
        and replay["spend_tx"] == pa1["spend_tx"]
        and replay["consumed"] is True
        and bal5["bal_alice"] == 1903 and replay_bad
        and table_counts(db_path)["expedite_credits"] == 7)
    record("AC-EPP5", ok5, "frozen faces: bob credits_view byte-"
          "identical to pre-close; the four pre-existing jobs keep"
          " every persisted field (subject/account/expedited/"
          "base_seq/used_credit) with only the derived position"
          " honestly shifted (normal jobs 3->4, 4->5); old ref"
          " order:epp-a1 replays idempotent across restart (same"
          " credit #%d, same spend tx, zero new row, zero second"
          " charge, alice still 1903); consumed credits cannot be"
          " resurrected - third demo jump still rejected" %
          replay["credit_id"])

    # -- AC-EPP6 pure-read law ------------------------------------
    bat_a = read_battery(ef2, led2)
    bat_b = read_battery(ef2, led2)
    ok6 = (bat_a == bat_b and battery_diffs(bat_a, bat_b) == []
           and table_counts(db_path) == cnt4)
    record("AC-EPP6", ok6, "pure-read law: full battery read twice"
          " back-to-back - queue + credits_view x3 + four balances"
          " byte-identical between the two reads and table counts"
          " constant (read faces have zero side effects)")

    # -- AC-EPP7 third instance stability + hygiene --------------
    ef2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    ef3 = X.ExpediteFace(led3)
    bal3 = read_battery(ef3, led3)
    diffs3 = battery_diffs(bal5, bal3)
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in
                          ("urllib", "requests", "socket", "http"))]
    ok7 = (not diffs3
           and sha16(io_read(cfg_path)) == cfg_sha_before
           and sha16(io_read(os.path.join(BASE, "expedite.py")))
           == expmod_sha_before
           and sha16(io_read(os.path.join(BASE, "ledger.py")))
           == ledmod_sha_before
           and non_ascii == 0 and not net_imports
           and os.path.realpath(tmp).startswith(
               os.path.realpath(tempfile.gettempdir()))
           and not os.path.realpath(tmp).startswith(repo_root))
    record("AC-EPP7", ok7, "third instance: close -> reopen same db"
          " once more - battery byte-identical to instance-2"
          " terminal state (diffs=%s, replay faces and new-write"
          " faces both stable across a second restart); shipped"
          " files untouched (config/expedite/ledger sha16 stable);"
          " suite source pure ASCII (%d non-ascii), zero network"
          " imports (%d hits), world tmp outside repo (%s)" %
          (diffs3 or "none", non_ascii, len(net_imports),
           "yes" if not os.path.realpath(tmp).startswith(repo_root)
           else "NO"))

    ef3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
