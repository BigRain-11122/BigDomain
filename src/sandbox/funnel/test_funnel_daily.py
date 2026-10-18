"""Acceptance suite for funnel_daily (FUNNEL-LOOP v0.1, R2032).

Pre-registered criteria AC-FN1..AC-FN7 live in
docs/ops/FUNNEL-AUTOMATION-PLAN-v1.md section 4 and were written
BEFORE this code existed (honesty law). Pure ASCII source: the
injected banned word uses a unicode escape so no non-ASCII literal
enters this file (coding law).
"""

import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import funnel_daily as fd  # noqa: E402


def _mk_inbox(root, name, rows):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    for i, row in enumerate(rows):
        with open(os.path.join(d, "%03d.json" % i), "w", encoding="utf-8") as h:
            json.dump(row, h, ensure_ascii=False)
    return d


def _empty_inbox(root, name):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    return d


def _write_config(path, banned, standing):
    with open(path, "w", encoding="utf-8") as h:
        json.dump({"banned_words": banned, "standing_lines": standing}, h, ensure_ascii=False)


def _dump(env):
    return json.dumps(env, ensure_ascii=False, sort_keys=True)


def _count(db_path, table):
    con = sqlite3.connect(db_path)
    n = con.execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0]
    con.close()
    return n


def case_fn1(tmp):
    """AC-FN1: four-ring series + determinism - same inputs, same day,
    two independent carriers produce byte-identical envelopes."""
    leads = [{"lead_id": "L1", "source": "s", "text": "I want a game demo level"}]
    orders = [{"order_id": "O1", "sku": "compute-pack-19.9", "amount_cent": 1990}]
    flows = [
        {"flow_id": "F1", "account": "u1", "kind": "grant", "amount": 100},
        {"flow_id": "F2", "account": "u1", "kind": "spend", "amount": 30},
    ]
    envs = []
    for run in ("a", "b"):
        root = os.path.join(tmp, "fn1-" + run)
        os.makedirs(root)
        li = _mk_inbox(root, "leads", leads)
        oi = _mk_inbox(root, "orders", orders)
        fi = _mk_inbox(root, "flows", flows)
        f = fd.FunnelDaily(os.path.join(root, "funnel.db"))
        out = f.run_daily(li, oi, fi, "2026-10-19")
        envs.append(_dump(out["envelope"]))
        f.close()
    assert envs[0] == envs[1], "AC-FN1 determinism broken"
    env = json.loads(envs[0])
    assert env["gate"] == "PASS", "AC-FN1 clean run must gate PASS"
    assert env["counts"]["leads_day"] == 1
    assert env["counts"]["dispatches_day"] == 1
    assert env["counts"]["orders_day"] == 1
    assert env["counts"]["token_granted_day"] == 100
    assert env["counts"]["token_spent_day"] == 30
    assert env["counts"]["token_outstanding_total"] == 70


def case_fn2(tmp):
    """AC-FN2: honest zero-book on empty inboxes; domain
    pre-classification when leads exist."""
    root = os.path.join(tmp, "fn2")
    os.makedirs(root)
    li = _empty_inbox(root, "leads")
    oi = _empty_inbox(root, "orders")
    fi = _empty_inbox(root, "flows")
    db = os.path.join(root, "funnel.db")
    f = fd.FunnelDaily(db)
    out = f.run_daily(li, oi, fi, "2026-10-19")
    env = out["envelope"]
    assert env["counts"]["leads_day"] == 0, "AC-FN2 empty must stay zero"
    assert env["verdict_line"].startswith("flat:"), "AC-FN2 honest flat verdict"
    assert _count(db, "leads") == 0, "AC-FN2 zero rows on zero input"
    f.close()

    li2 = _mk_inbox(
        root,
        "leads2",
        [
            {"lead_id": "L1", "text": "I want a game demo"},
            {"lead_id": "L2", "text": "a strategy backtest idea"},
            {"lead_id": "L3", "text": "totally unmatched words"},
        ],
    )
    f = fd.FunnelDaily(db)
    f.scan_leads(li2, "2026-10-20")
    rows = f.db.execute(
        "SELECT lead_id, domain FROM leads ORDER BY lead_id"
    ).fetchall()
    f.close()
    assert rows == [
        ("L1", "game"),
        ("L2", "quant"),
        ("L3", "other"),
    ], "AC-FN2 classification mismatch: %r" % (rows,)


def case_fn3(tmp):
    """AC-FN3: six-domain routing; no-match leads route to unrouted
    honest archive, never dropped."""
    root = os.path.join(tmp, "fn3")
    os.makedirs(root)
    li = _mk_inbox(
        root,
        "leads",
        [
            {"lead_id": "L1", "text": "build me a game level"},
            {"lead_id": "L2", "text": "quant factor idea"},
            {"lead_id": "L3", "text": "nothing matches here"},
        ],
    )
    db = os.path.join(root, "funnel.db")
    f = fd.FunnelDaily(db)
    f.scan_leads(li, "2026-10-19")
    out = f.dispatch_leads("2026-10-19")
    f.close()
    assert out["dispatches_new"] == 3, "AC-FN3 dispatch count"
    assert out["routes"] == {"game": 1, "quant": 1, "unrouted": 1}, (
        "AC-FN3 routes mismatch: %r" % (out["routes"],)
    )
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT lead_id, route FROM dispatches ORDER BY lead_id"
    ).fetchall()
    con.close()
    assert rows == [
        ("L1", "game"),
        ("L2", "quant"),
        ("L3", "unrouted"),
    ], "AC-FN3 archive mismatch: %r" % (rows,)


def case_fn4(tmp):
    """AC-FN4: order idempotency - a replayed inbox books nothing new;
    empty inbox books an honest zero."""
    root = os.path.join(tmp, "fn4")
    os.makedirs(root)
    oi = _mk_inbox(
        root, "orders", [{"order_id": "O1", "sku": "compute-pack-19.9", "amount_cent": 1990}]
    )
    ei = _empty_inbox(root, "orders-empty")
    db = os.path.join(root, "funnel.db")
    f = fd.FunnelDaily(db)
    a = f.book_orders(oi, "2026-10-19")
    b = f.book_orders(oi, "2026-10-19")
    c = f.book_orders(ei, "2026-10-20")
    f.close()
    assert a["orders_new"] == 1 and b["orders_new"] == 0, "AC-FN4 replay must be idempotent"
    assert c["orders_new"] == 0, "AC-FN4 empty stays zero"
    assert _count(db, "orders") == 1, "AC-FN4 exactly one order row"


def case_fn5(tmp):
    """AC-FN5: three-face daily account + the outstanding identity
    across days; flow idempotency."""
    root = os.path.join(tmp, "fn5")
    os.makedirs(root)
    day1 = _mk_inbox(
        root,
        "flows1",
        [
            {"flow_id": "F1", "account": "u1", "kind": "grant", "amount": 100},
            {"flow_id": "F2", "account": "u1", "kind": "spend", "amount": 30},
        ],
    )
    day2 = _mk_inbox(
        root, "flows2", [{"flow_id": "F3", "account": "u2", "kind": "grant", "amount": 50}]
    )
    ei = _empty_inbox(root, "flows-empty")
    db = os.path.join(root, "funnel.db")
    f = fd.FunnelDaily(db)
    f.book_token_flows(day1, "2026-10-19")
    env1 = f.rollup("2026-10-19")
    f.book_token_flows(day2, "2026-10-20")
    env2 = f.rollup("2026-10-20")
    replay = f.book_token_flows(day1, "2026-10-21")
    f.close()
    assert env1["counts"]["token_granted_day"] == 100
    assert env1["counts"]["token_spent_day"] == 30
    assert env1["counts"]["token_outstanding_total"] == 70
    assert env2["counts"]["token_outstanding_total"] == 120, (
        "AC-FN5 cross-day identity: 150 granted - 30 spent = 120"
    )
    assert replay["flows_new"] == 0, "AC-FN5 replay must be idempotent"
    assert _count(db, "flows") == 3, "AC-FN5 exactly three flow rows"


def case_fn6(tmp):
    """AC-FN6: gate fail-closed - a banned word reaching the
    presented envelope means gate=FAIL with the hit list persisted;
    the shipped config stays clean."""
    root = os.path.join(tmp, "fn6")
    os.makedirs(root)
    ei = _empty_inbox(root, "leads")
    db = os.path.join(root, "funnel.db")
    bad = os.path.join(root, "bad-config.json")
    # "\u5347\u503c" = the banned word injected through the standing-line
    # (presented-face copy channel) - unicode escape keeps this file ASCII.
    _write_config(bad, ["\u5347\u503c"], {"aigc": "x \u5347\u503c y"})
    f = fd.FunnelDaily(db, config_path=bad)
    f.scan_leads(ei, "2026-10-19")
    env = f.rollup("2026-10-19")
    f.close()
    assert env["gate"] == "FAIL", "AC-FN6 banned word must fail the gate"
    assert "\u5347\u503c" in env["hits"], "AC-FN6 hit list must persist"

    db2 = os.path.join(root, "funnel2.db")
    f2 = fd.FunnelDaily(db2, config_path=fd.DEFAULT_CONFIG)
    f2.scan_leads(ei, "2026-10-19")
    env2 = f2.rollup("2026-10-19")
    f2.close()
    assert env2["gate"] == "PASS" and env2["hits"] == [], "AC-FN6 shipped config stays clean"


def case_fn7(tmp):
    """AC-FN7: rollup carries the four-ring counts, the prev-day
    delta, the verdict line, the focus (positioning-law) line, the
    standing AIGC line, gate and hits."""
    root = os.path.join(tmp, "fn7")
    os.makedirs(root)
    li = _mk_inbox(root, "leads", [{"lead_id": "L1", "text": "game demo"}])
    fi = _mk_inbox(
        root, "flows", [{"flow_id": "F1", "account": "u1", "kind": "grant", "amount": 10}]
    )
    ei = _empty_inbox(root, "orders")
    db = os.path.join(root, "funnel.db")
    f = fd.FunnelDaily(db)
    env1 = f.run_daily(li, ei, fi, "2026-10-19")["envelope"]
    env2 = f.run_daily(li, ei, fi, "2026-10-20")["envelope"]
    f.close()
    for env in (env1, env2):
        for key in ("day", "counts", "delta_prev_day", "verdict_line", "focus",
                    "standing_lines", "gate", "hits"):
            assert key in env, "AC-FN7 missing key %s" % key
        for key in fd._COUNT_KEYS:
            assert key in env["counts"], "AC-FN7 missing count %s" % key
        assert env["standing_lines"].get("aigc"), "AC-FN7 standing AIGC line required"
        assert env["focus"].startswith("business=commercialization-funnel"), (
            "AC-FN7 focus/positioning line required"
        )
    assert env1["delta_prev_day"] is None, "AC-FN7 first day has no prev delta"
    assert env2["delta_prev_day"] is not None, "AC-FN7 second day must carry delta"
    assert env2["delta_prev_day"]["leads_day"] == -1, (
        "AC-FN7 delta is a day-over-day diff: day1 booked 1 new lead, "
        "the replayed inbox books 0 on day2, so delta = 0 - 1 = -1"
    )


def case_bad_args(tmp):
    """Zero-row rejection: a bad inbox argument or a bad file raises
    E_FN_BAD_ARGS and leaves zero new rows (fail-closed)."""
    root = os.path.join(tmp, "bad")
    os.makedirs(root)
    li = _mk_inbox(root, "leads", [{"lead_id": "L1", "text": "ok"}])
    badf = _mk_inbox(root, "leads-bad", [{"text": "missing lead_id"}])
    ei = _empty_inbox(root, "orders")
    fi = _empty_inbox(root, "flows")
    db = os.path.join(root, "funnel.db")
    f = fd.FunnelDaily(db)
    for call in (
        lambda: f.run_daily(os.path.join(root, "no-such-dir"), ei, fi, "2026-10-19"),
        lambda: f.run_daily(li, ei, fi, "2026-99-99"),
        lambda: f.scan_leads(badf, "2026-10-19"),
        lambda: f.book_orders(ei, "bad-day"),
    ):
        try:
            call()
        except fd.FunnArgError as exc:
            assert str(exc) == fd.E_FN_BAD_ARGS
        else:
            raise AssertionError("bad args must raise E_FN_BAD_ARGS")
    assert _count(db, "leads") == 0, (
        "no call above ever booked the good inbox, so zero rows so far"
    )
    # zero-row rejection with survivors: book the good inbox, then let a
    # bad file reject - the good row stays, the bad ring books nothing.
    f.scan_leads(li, "2026-10-19")
    try:
        f.scan_leads(badf, "2026-10-19")
    except fd.FunnArgError:
        pass
    else:
        raise AssertionError("bad inbox file must raise E_FN_BAD_ARGS")
    assert _count(db, "leads") == 1, (
        "the good lead row survives; the bad file books zero new rows"
    )
    f.close()


def main():
    tmp = tempfile.mkdtemp(prefix="funnel-v01-")
    cases = [
        ("AC-FN1 four-ring series + determinism", case_fn1),
        ("AC-FN2 honest zero-book + classification", case_fn2),
        ("AC-FN3 six-domain routing + unrouted archive", case_fn3),
        ("AC-FN4 order idempotency + empty honesty", case_fn4),
        ("AC-FN5 three-face account + identity", case_fn5),
        ("AC-FN6 gate fail-closed + clean shipped config", case_fn6),
        ("AC-FN7 rollup full envelope + delta", case_fn7),
        ("zero-row rejection on bad args/files", case_bad_args),
    ]
    failed = 0
    for name, fn in cases:
        try:
            fn(tmp)
            print("PASS %s" % name)
        except AssertionError as exc:
            failed += 1
            print("FAIL %s :: %s" % (name, exc))
    shutil.rmtree(tmp, ignore_errors=True)
    total = len(cases)
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL", total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
