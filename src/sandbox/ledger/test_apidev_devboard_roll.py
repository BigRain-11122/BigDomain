"""Acceptance suite for the apidev dev_board month-rollover
re-domain fidelity (BigDomain R1845; canon = tech-queue
"apidev dev_board month-roll panel re-domain fidelity example
window" row, the R1839 reseed, claimed from the tech-lane FIFO
oldest open row). The pre-registered criteria AC-DBR1..AC-DBR7
live in the R1845 tech claim note (criteria were registered
before this code ran; the AC-DBR prefix was verified unowned by
a whole-repo scan on claim).

Covered semantics: dev_board(dev_account) is the account-level
no-window-param panel that always reads the current _window_utc
key. When the frozen clock crosses the month boundary the panel
re-domains honestly: the window key rolls with the clock, every
per-key face (quota_used / minute_used / reject_tally /
usage_kind_tally) and both total keys come back all-zero for the
new month BEFORE any new call, a pre-roll October quota reject
row (record-time stamped in reject_events) does not leak into
the new-month panel tally, the old month keeps its values as an
explicit window read (chain_usage window='2026-10' plus the
window-scoped tally faces), a new November call succeeds (the
quota ring rolled) and the panel re-computes, and no immutable
row is ever lost. This is the account-level panel symmetric
case closing the month-roll family after the R1730 rejectwin /
R1738 usagekind / R1739 usagewin / R1839 chain_usage precedents.

The metered face is the real product injected by reference (no
copy). Zero product bytes change: the roll semantics already
live in dev_board, this suite only pins them. This test source
stays pure ASCII per the encoding discipline.

Usage: python test_apidev_devboard_roll.py
"""

import datetime
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                      # noqa: E402 (P-47-2b core)
import metered as M                     # noqa: E402 (R626 product)
import apidev as D                      # noqa: E402 (R1700+ face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the open API is a compute"
             " + visualization interface, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 15, 10, 0, 0)
OLD_WIN = "2026-10"
NEW_WIN = "2026-11"

# exact envelope contracts (the R1825 pin lists, reused verbatim:
# this suite adds zero keys to dev_board)
BOARD_KEYS = sorted([
    "dev_account", "keys", "window", "reject_tally_total",
    "usage_kind_tally_total", "disclaimer"])
BOARD_ROW_KEYS = sorted([
    "key_name", "api_key", "metered_client", "window_cap",
    "enabled_kinds", "ai_label", "minute_cap", "status",
    "rotated_from_key_id", "quota_used", "minute_window",
    "minute_used", "reject_tally", "usage_kind_tally", "billing"])


class _FrozenClock(object):
    """Deterministic UTC clock holder: _now_utc/_minute_utc/
    _window_utc are patched onto the apidev module so the window
    and minute keys roll only when the suite moves the clock."""

    def __init__(self):
        self.dt = BASE_DT

    def now_utc(self):
        return self.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def minute_utc(self):
        return self.dt.strftime("%Y-%m-%dT%H:%M")

    def window_utc(self):
        return self.dt.strftime("%Y-%m")

    def advance(self, seconds):
        self.dt = self.dt + datetime.timedelta(seconds=seconds)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_ad_error(fn, code):
    try:
        fn()
    except D.ApiDevError as exc:
        return exc.code == code, exc.code, exc.detail
    return False, "no-error-raised", ""


def _key_id(conn, api_key):
    return conn.execute(
        "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
        (api_key,)).fetchone()[0]


def _pair_count(conn, marks_pair, id_p, id_b, extra="", args=()):
    return conn.execute(
        "SELECT COUNT(*) FROM api_calls"
        " WHERE key_id IN (" + marks_pair + ")" + extra,
        (id_p, id_b) + tuple(args)).fetchone()[0]


def _make_calls(dk, clock, api_key, prefix, n, kind, start=1):
    for i in range(start, start + n):
        ref = "%s-%02d" % (prefix, i)
        dk.call(api_key, kind, ref, "engine:%s" % ref)
        clock.advance(7)


def _row_by_name(board, key_name):
    for row in board["keys"]:
        if row["key_name"] == key_name:
            return row
    return None


def _own_map(env):
    return {m["key_id"]: m["own_calls"] for m in env["by_member"]}


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-dbr-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    conn = sqlite3.connect(db_path)
    rjconn = sqlite3.connect(os.path.join(tmp, "api_rejects.db"))
    product_pre = open(os.path.join(BASE, "apidev.py"), "rb").read()
    clock = _FrozenClock()
    real_now = D._now_utc
    real_minute = D._minute_utc
    real_window = D._window_utc

    try:
        D._now_utc = clock.now_utc
        D._minute_utc = clock.minute_utc
        D._window_utc = clock.window_utc

        # world: one funded two-key rotate chain on usr:rex --
        # roll-p cap 3 spends 2 calls, rotates to roll-b which
        # spends 1 -> effective 3 == cap, so the 4th October call
        # rejects E_AD_QUOTA (the capped-out anchor, zero new
        # api_calls rows, one reject_events row record-time
        # stamped window 2026-10 attributed to roll-b). All calls
        # land inside one frozen minute (clock.advance(7) per
        # call) so the minute ring reads 2 / 3 per key row.
        led.mint_to_pool("pool:reserve", 5000, "MINT-DBR", "settlement")
        led.ensure_account("usr:rex", census_avatar_id="rex")
        led.adjust([("pool:reserve", "debit", 100),
                    ("usr:rex", "credit", 100)],
                   "manual:fund-rex-roll", "suite funding rex roll")
        kp = dk.issue_key("usr:rex", "roll-p", 3, ["backtest"], True)
        dk.buy_credits(kp["api_key"], 10, 1, "PACK-DBR-P")
        _make_calls(dk, clock, kp["api_key"], "DBR-P", 2, "backtest")
        kb = dk.rotate_key(kp["api_key"], "roll-b")
        _make_calls(dk, clock, kb["api_key"], "DBR-B", 1, "backtest")
        ok_oct_q, code_oct_q, _d1 = expect_ad_error(
            lambda: dk.call(kb["api_key"], "backtest",
                            "DBR-B-02", "engine:DBR-B-02"),
            D.E_AD_QUOTA)
        id_p = _key_id(conn, kp["api_key"])
        id_b = _key_id(conn, kb["api_key"])
        marks_pair = ",".join("?" for _ in (id_p, id_b))
        pre_all = _pair_count(conn, marks_pair, id_p, id_b)
        rej_oct = rjconn.execute(
            "SELECT COUNT(*) FROM reject_events"
            " WHERE window = ?", (OLD_WIN,)).fetchone()[0]

        # -- AC-DBR1 pre-roll panel anchor ---------------------------
        t_pre = dk.chain_usage(kb["api_key"], window=OLD_WIN)
        board_pre = dk.dev_board("usr:rex")
        row_p_pre = _row_by_name(board_pre, "roll-p")
        row_b_pre = _row_by_name(board_pre, "roll-b")
        dbr1 = (ok_oct_q and code_oct_q == D.E_AD_QUOTA
                and pre_all == 3 and rej_oct == 1
                and sorted(board_pre.keys()) == BOARD_KEYS
                and sorted(row_p_pre.keys()) == BOARD_ROW_KEYS
                and sorted(row_b_pre.keys()) == BOARD_ROW_KEYS
                and board_pre["window"] == OLD_WIN
                and board_pre["dev_account"] == "usr:rex"
                and board_pre["disclaimer"] == DISCLAIMER
                and len(board_pre["keys"]) == 2
                and row_p_pre["status"] == "rotated_out"
                and row_b_pre["status"] == "active"
                and row_p_pre["rotated_from_key_id"] is None
                and row_b_pre["rotated_from_key_id"] == id_p
                and row_p_pre["quota_used"] == 2
                and row_b_pre["quota_used"] == 3
                and row_p_pre["minute_used"] == 2
                and row_b_pre["minute_used"] == 3
                and row_p_pre["reject_tally"] == {}
                and row_b_pre["reject_tally"] == {"E_AD_QUOTA": 1}
                and row_p_pre["usage_kind_tally"] == {"backtest": 2}
                and row_b_pre["usage_kind_tally"] == {"backtest": 1}
                and board_pre["reject_tally_total"] == {"E_AD_QUOTA": 1}
                and board_pre["usage_kind_tally_total"] ==
                    {"backtest": 3}
                and t_pre["window"] == OLD_WIN
                and _own_map(t_pre) == {id_p: 2, id_b: 1}
                and t_pre["chain_total"] == 3
                and t_pre["effective_upto_queried"] == 3)
        record("AC-DBR1", dbr1,
               "pre-roll anchor: 4th call -> %s (api_calls pair=%d,"
               " reject_events 2026-10=%d); board window=%s"
               " envelope exact=%s row envelope exact=%s/%s;"
               " rows=%d status %s/%s rotated_from %s/%s;"
               " quota_used %d/%d (ancestry inheritance visible),"
               " minute_used %d/%d (one frozen minute);"
               " reject_tally %s/%s, kind_tally %s/%s;"
               " totals %s + %s; explicit old-window read"
               " own=%s chain_total=%d effective=%d"
               % (code_oct_q, pre_all, rej_oct, board_pre["window"],
                  sorted(board_pre.keys()) == BOARD_KEYS,
                  sorted(row_p_pre.keys()) == BOARD_ROW_KEYS,
                  sorted(row_b_pre.keys()) == BOARD_ROW_KEYS,
                  len(board_pre["keys"]), row_p_pre["status"],
                  row_b_pre["status"],
                  row_p_pre["rotated_from_key_id"],
                  row_b_pre["rotated_from_key_id"],
                  row_p_pre["quota_used"], row_b_pre["quota_used"],
                  row_p_pre["minute_used"], row_b_pre["minute_used"],
                  row_p_pre["reject_tally"], row_b_pre["reject_tally"],
                  row_p_pre["usage_kind_tally"],
                  row_b_pre["usage_kind_tally"],
                  board_pre["reject_tally_total"],
                  board_pre["usage_kind_tally_total"],
                  _own_map(t_pre), t_pre["chain_total"],
                  t_pre["effective_upto_queried"]))

        # -- AC-DBR2 window key rolls with the clock ------------------
        clock.advance(23 * 86400)
        board_rolled = dk.dev_board("usr:rex")
        row_p_r = _row_by_name(board_rolled, "roll-p")
        row_b_r = _row_by_name(board_rolled, "roll-b")
        dbr2 = (board_rolled["window"] == NEW_WIN
                and row_p_r["minute_window"] == clock.minute_utc()
                and row_b_r["minute_window"] == clock.minute_utc()
                and board_rolled["dev_account"] == "usr:rex")
        record("AC-DBR2", dbr2,
               "frozen clock +23d: panel window rolls %s -> %s"
               " (no-window-param face always reads current"
               " _window_utc); minute_window follows the clock"
               " ==%s on both rows"
               % (board_pre["window"], board_rolled["window"],
                  clock.minute_utc()))

        # -- AC-DBR3 re-domain honest board, zero-penetration --------
        rej_oct_after = rjconn.execute(
            "SELECT COUNT(*) FROM reject_events"
            " WHERE window = ?", (OLD_WIN,)).fetchone()[0]
        rej_nov = rjconn.execute(
            "SELECT COUNT(*) FROM reject_events"
            " WHERE window = ?", (NEW_WIN,)).fetchone()[0]
        dbr3 = (rej_oct_after == 1 and rej_nov == 0
                and row_p_r["quota_used"] == 0
                and row_b_r["quota_used"] == 0
                and row_p_r["minute_used"] == 0
                and row_b_r["minute_used"] == 0
                and row_p_r["reject_tally"] == {}
                and row_b_r["reject_tally"] == {}
                and row_p_r["usage_kind_tally"] == {}
                and row_b_r["usage_kind_tally"] == {}
                and sorted(board_rolled.keys()) == BOARD_KEYS
                and sorted(row_p_r.keys()) == BOARD_ROW_KEYS
                and sorted(row_b_r.keys()) == BOARD_ROW_KEYS)
        record("AC-DBR3", dbr3,
               "honest re-domain BEFORE any new call: per-key"
               " quota_used %d/%d, minute_used %d/%d,"
               " reject_tally %s/%s, kind_tally %s/%s all zero"
               " in %s; October quota reject row stays in the"
               " store (reject_events window 2026-10 COUNT=%d,"
               " 2026-11 COUNT=%d) yet never penetrates the new"
               " month panel tally (record-time attribution)"
               % (row_p_r["quota_used"], row_b_r["quota_used"],
                  row_p_r["minute_used"], row_b_r["minute_used"],
                  row_p_r["reject_tally"], row_b_r["reject_tally"],
                  row_p_r["usage_kind_tally"],
                  row_b_r["usage_kind_tally"], NEW_WIN,
                  rej_oct_after, rej_nov))

        # -- AC-DBR4 total keys reset with the re-domain -------------
        dbr4 = (board_rolled["reject_tally_total"] == {}
                and board_rolled["usage_kind_tally_total"] == {})
        record("AC-DBR4", dbr4,
               "panel total keys reset with the re-domain:"
               " reject_tally_total=%s, usage_kind_tally_total=%s"
               " (window-scoped aggregation like the per-key"
               " faces, not lifetime counters)"
               % (board_rolled["reject_tally_total"],
                  board_rolled["usage_kind_tally_total"]))

        # -- AC-DBR5 old-month truth preservation ---------------------
        t_old = dk.chain_usage(kb["api_key"], window=OLD_WIN)
        tally_rej_b_old = dk._reject_tally(id_b, OLD_WIN)
        tally_kinds_p_old = dk._usage_kind_tally(id_p, OLD_WIN)
        post_all_rolled = _pair_count(conn, marks_pair, id_p, id_b)
        dbr5 = (json.dumps(t_old, sort_keys=True) ==
                json.dumps(t_pre, sort_keys=True)
                and post_all_rolled == pre_all == 3
                and tally_rej_b_old == {"E_AD_QUOTA": 1}
                and tally_kinds_p_old == {"backtest": 2})
        record("AC-DBR5", dbr5,
               "old-month preservation: explicit chain_usage"
               " window=%s byte-equal across the roll=%s"
               " (own=%s chain_total=%d); window-scoped tally"
               " faces keep their values (_reject_tally"
               " roll-b 2026-10=%s, _usage_kind_tally roll-p"
               " 2026-10=%s); immutable rows all preserved"
               " (api_calls pair=%d == pre-roll %d)"
               % (OLD_WIN,
                  json.dumps(t_old, sort_keys=True) ==
                  json.dumps(t_pre, sort_keys=True),
                  _own_map(t_old), t_old["chain_total"],
                  tally_rej_b_old, tally_kinds_p_old,
                  post_all_rolled, pre_all))

        # -- AC-DBR6 new-month re-compute face ------------------------
        dk.call(kb["api_key"], "backtest", "DBR-N-01",
                "engine:DBR-N-01")
        stamp_nov = conn.execute(
            "SELECT COUNT(*) FROM api_calls"
            " WHERE key_id IN (" + marks_pair + ")"
            " AND window = ? AND call_ref = ?",
            (id_p, id_b, NEW_WIN, "DBR-N-01")).fetchone()[0]
        board_new = dk.dev_board("usr:rex")
        row_p_n = _row_by_name(board_new, "roll-p")
        row_b_n = _row_by_name(board_new, "roll-b")
        t_old2 = dk.chain_usage(kb["api_key"], window=OLD_WIN)
        post_all_new = _pair_count(conn, marks_pair, id_p, id_b)
        dbr6 = (stamp_nov == 1
                and board_new["window"] == NEW_WIN
                and row_b_n["quota_used"] == 1
                and row_b_n["minute_used"] == 1
                and row_b_n["usage_kind_tally"] == {"backtest": 1}
                and row_b_n["reject_tally"] == {}
                and row_p_n["quota_used"] == 0
                and row_p_n["minute_used"] == 0
                and row_p_n["usage_kind_tally"] == {}
                and row_p_n["reject_tally"] == {}
                and board_new["reject_tally_total"] == {}
                and board_new["usage_kind_tally_total"] ==
                    {"backtest": 1}
                and post_all_new == 4
                and json.dumps(t_old2, sort_keys=True) ==
                    json.dumps(t_pre, sort_keys=True))
        record("AC-DBR6", dbr6,
               "new-month re-compute: November call succeeds"
               " (quota ring rolled, no E_AD_QUOTA), record-time"
               " stamp window=%s COUNT=%d; panel recomputes"
               " roll-b quota_used=%d minute_used=%d"
               " kind_tally=%s, roll-p stays all-zero (%d/%d"
               " %s); totals follow: kinds=%s rejects=%s;"
               " all-time rows=%d; October explicit read still"
               " byte-equal=%s (two windows non-penetrating)"
               % (NEW_WIN, stamp_nov, row_b_n["quota_used"],
                  row_b_n["minute_used"],
                  row_b_n["usage_kind_tally"],
                  row_p_n["quota_used"], row_p_n["minute_used"],
                  row_p_n["usage_kind_tally"],
                  board_new["usage_kind_tally_total"],
                  board_new["reject_tally_total"], post_all_new,
                  json.dumps(t_old2, sort_keys=True) ==
                  json.dumps(t_pre, sort_keys=True)))

        # -- AC-DBR7 suite-side hygiene -------------------------------
        product_post = open(os.path.join(BASE, "apidev.py"),
                            "rb").read()
        with open(os.path.join(BASE, "config.json"), "rb") as handle:
            cfg_bytes_end = handle.read()
        own_path = os.path.abspath(__file__)
        own_source = open(own_path, "r", encoding="ascii").read()
        imports_net = [line for line in own_source.splitlines()
                      if re.match(r"\s*(?:import|from)\s", line)
                      and re.search(r"urllib|requests|socket|http",
                                    line)]
        own_ascii = all(ord(ch) < 128 for ch in own_source)
        dbr7 = (product_post == product_pre
                and cfg_bytes_end == cfg_bytes
                and "def dev_board" in product_post.decode("ascii")
                and own_ascii and len(imports_net) == 0)
        record("AC-DBR7", dbr7,
               "hygiene: apidev.py byte-stable across the run=%s"
               " (dev_board face present=%s), config.json"
               " byte-stable=%s, suite source pure-ASCII=%s,"
               " net-imports=%d (double-run byte-identity and"
               " the RUNNER / matrix / sentinel faces live in"
               " the round evidence log)"
               % (product_post == product_pre,
                  "def dev_board" in product_post.decode("ascii"),
                  cfg_bytes_end == cfg_bytes, own_ascii,
                  len(imports_net)))

    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute
        D._window_utc = real_window

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-devboard-roll: %d/%d criteria pass"
          % (passed, total), flush=True)
    rjconn.close()
    conn.close()
    dk.close()
    metered.close()
    led.close()
    return 0 if passed == total == 7 else 1


if __name__ == "__main__":
    sys.exit(main())
