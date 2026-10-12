"""Acceptance suite for the apidev dev_board read-cap parameter
window (BigDomain R1852; canon = tech-queue "apidev dev_board
read-cap parameter window" row, the R1845 reseed, claimed from the
tech-lane FIFO oldest open row). The pre-registered criteria
AC-DBL1..AC-DBL8 live in the R1852 tech claim note (criteria
were registered before this code ran; the AC-DBL prefix was
verified unowned by a whole-repo scan on claim).

Covered semantics: dev_board(dev_account, limit=0) gains an
additive read cap. limit=0 (the default) keeps the full-board
envelope byte-stable for every existing consumer; limit>0 bounds
the keys list to the most recent limit rows (the highest key_ids,
a tail-window slice of the board's ascending key_id order) and
adds an overflow block -- limit/total/returned/truncated -- where
total is the full key-row count, never the truncated count, and
the world aggregates (reject_tally_total /
usage_kind_tally_total) stay full-world counts over every key of
the account: truncation only cuts the keys list. Five bad limit
forms reject the dedicated E_AD_BAD_LIMIT code fail-closed before
any read; the dev_account form gate stays outermost. The capped
read stays honest across the month rollover (orthogonal to the
R1845 roll panel: window key rolls with the frozen clock, the
new-month panel re-domains all-zero before any new call, a
November call re-computes under the cap, the October
explicit-window read never moves). Mirror SQL (independent
mode=ro connection, ORDER BY key_id DESC LIMIT N reversed back to
ascending) is the third path for the tail slice.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_apidev_devboard_limit.py
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

# exact envelope contracts (the R1825/R1845 pin lists, reused
# verbatim for the uncapped face; the capped face adds exactly
# the four overflow keys)
BOARD_KEYS = sorted([
    "dev_account", "keys", "window", "reject_tally_total",
    "usage_kind_tally_total", "disclaimer"])
CAPPED_KEYS = sorted(BOARD_KEYS +
                     ["limit", "total", "returned", "truncated"])
BOARD_ROW_KEYS = sorted([
    "key_name", "api_key", "metered_client", "window_cap",
    "enabled_kinds", "ai_label", "minute_cap", "status",
    "rotated_from_key_id", "quota_used", "minute_window",
    "minute_used", "reject_tally", "usage_kind_tally", "billing"])


class _FrozenClock(object):
    """Deterministic UTC clock holder patched onto the apidev
    module (R1845 recipe): the window and minute keys roll only
    when the suite moves the clock, so double-run stdout is
    byte-identical (zero real-time leakage)."""

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


def _row_by_name(board, key_name):
    for row in board["keys"]:
        if row["key_name"] == key_name:
            return row
    return None


def _dumps(obj):
    return json.dumps(obj, sort_keys=True)


def _scoped_counts(conn, rjconn, marks, key_ids):
    keys_n = conn.execute(
        "SELECT COUNT(*) FROM api_dev_keys"
        " WHERE dev_account = ?", ("usr:limit",)).fetchone()[0]
    calls_n = conn.execute(
        "SELECT COUNT(*) FROM api_calls"
        " WHERE key_id IN (" + marks + ")",
        tuple(key_ids)).fetchone()[0]
    rejects_n = rjconn.execute(
        "SELECT COUNT(*) FROM reject_events"
        " WHERE key_id IN (" + marks + ")",
        tuple(key_ids)).fetchone()[0]
    return keys_n, calls_n, rejects_n


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-dbl-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    conn = sqlite3.connect(db_path)
    rjconn = sqlite3.connect(os.path.join(tmp, "api_rejects.db"))
    ro = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    clock = _FrozenClock()
    real_now = D._now_utc
    real_minute = D._minute_utc
    real_window = D._window_utc

    try:
        D._now_utc = clock.now_utc
        D._minute_utc = clock.minute_utc
        D._window_utc = clock.window_utc

        # ---- main world: six keys on usr:limit ------------------
        # k1 cap 1 spends 1 call then rejects E_AD_QUOTA on the
        # second; k2/k3/k4 are issued only; k5/k6 spend 1 call
        # each. Totals: reject_tally_total {E_AD_QUOTA:1},
        # usage_kind_tally_total {backtest:3}. All calls land in
        # the frozen 2026-10 window.
        led.mint_to_pool("pool:reserve", 5000, "MINT-DBL", "settlement")
        led.ensure_account("usr:limit", census_avatar_id="limit")
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:limit", "credit", 300)],
                   "manual:fund-limit", "suite funding limit world")
        issued = []
        for idx, cap in ((1, 1), (2, 3), (3, 3), (4, 3), (5, 3),
                        (6, 3)):
            k = dk.issue_key("usr:limit", "k%d" % idx, cap,
                             ["backtest"], True)
            dk.buy_credits(k["api_key"], 10, 1,
                           "PACK-DBL-%d" % idx)
            issued.append(k)
        dk.call(issued[0]["api_key"], "backtest", "L1-01",
                "engine:L1-01")
        clock.advance(7)
        ok_k1_rej, code_k1_rej, _d0 = expect_ad_error(
            lambda: dk.call(issued[0]["api_key"], "backtest",
                            "L1-02", "engine:L1-02"),
            D.E_AD_QUOTA)
        clock.advance(7)
        dk.call(issued[4]["api_key"], "backtest", "L5-01",
                "engine:L5-01")
        clock.advance(7)
        dk.call(issued[5]["api_key"], "backtest", "L6-01",
                "engine:L6-01")
        clock.advance(7)
        key_ids = [conn.execute(
            "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
            (k["api_key"],)).fetchone()[0] for k in issued]
        marks = ",".join("?" for _ in key_ids)
        pre_counts = _scoped_counts(conn, rjconn, marks, key_ids)
        schema_pre = set(r[0] for r in conn.execute(
            "SELECT sql FROM sqlite_master"
            " WHERE sql IS NOT NULL").fetchall())

        # -- AC-DBL1 default fidelity -------------------------------
        board_noarg = dk.dev_board("usr:limit")
        board_zero = dk.dev_board("usr:limit", 0)
        dbl1 = (ok_k1_rej and code_k1_rej == D.E_AD_QUOTA
                and pre_counts == (6, 3, 1)
                and _dumps(board_noarg) == _dumps(board_zero)
                and sorted(board_noarg.keys()) == BOARD_KEYS
                and len(board_noarg["keys"]) == 6
                and all(sorted(r.keys()) == BOARD_ROW_KEYS
                        for r in board_noarg["keys"])
                and [r["key_name"] for r in board_noarg["keys"]] ==
                    ["k1", "k2", "k3", "k4", "k5", "k6"])
        record("AC-DBL1", dbl1,
               "default fidelity: no-arg == explicit limit=0"
               " byte-identical=%s; envelope keys == 6-pin=%s;"
               " rows=%d all 15-pin=%s; issue order"
               " k1..k6=%s; world anchor (6 keys / 3 calls /"
               " 1 reject, 2nd k1 call -> %s)"
               % (_dumps(board_noarg) == _dumps(board_zero),
                  sorted(board_noarg.keys()) == BOARD_KEYS,
                  len(board_noarg["keys"]),
                  all(sorted(r.keys()) == BOARD_ROW_KEYS
                      for r in board_noarg["keys"]),
                  [r["key_name"] for r in board_noarg["keys"]] ==
                  ["k1", "k2", "k3", "k4", "k5", "k6"],
                  code_k1_rej))

        # -- AC-DBL2 five bad forms fail-closed ---------------------
        bad_forms = [-1, True, "2", 2.5, None]
        rejects = []
        for bad in bad_forms:
            ok_b, code_b, _d1 = expect_ad_error(
                lambda b=bad: dk.dev_board("usr:limit", b),
                D.E_AD_BAD_LIMIT)
            rejects.append((ok_b, code_b))
        ok_form, code_form, _d2 = expect_ad_error(
            lambda: dk.dev_board("not-usr", -1), D.E_AD_BAD_ARGS)
        mid_counts = _scoped_counts(conn, rjconn, marks, key_ids)
        dbl2 = (all(ok_b for ok_b, _c in rejects)
                and all(code_b == D.E_AD_BAD_LIMIT
                        for _ok, code_b in rejects)
                and mid_counts == pre_counts
                and ok_form and code_form == D.E_AD_BAD_ARGS)
        record("AC-DBL2", dbl2,
               "five bad forms reject=%d/5 codes=%s;"
               " counts stable across rejects=%s"
               " (keys/calls/rejects %s -> %s); double-bad"
               " ('not-usr', -1) -> %s (dev_account form gate"
               " fires first); sentinel is 0 only, None rejects"
               % (sum(1 for ok_b, _c in rejects if ok_b),
                  sorted(set(code_b for _ok, code_b in rejects)),
                  mid_counts == pre_counts, pre_counts, mid_counts,
                  code_form))

        # -- AC-DBL3 tail-window truncation fidelity ----------------
        full_rows = board_noarg["keys"]
        cap2 = dk.dev_board("usr:limit", 2)
        cap4 = dk.dev_board("usr:limit", 4)
        seq2 = [r["key_name"] for r in cap2["keys"]]
        seq4 = [r["key_name"] for r in cap4["keys"]]
        rows_byte2 = ([_dumps(r) for r in cap2["keys"]] ==
                      [_dumps(r) for r in full_rows[-2:]])
        rows_byte4 = ([_dumps(r) for r in cap4["keys"]] ==
                      [_dumps(r) for r in full_rows[-4:]])
        dbl3 = (seq2 == ["k5", "k6"] and seq4 ==
                ["k3", "k4", "k5", "k6"]
                and rows_byte2 and rows_byte4
                and all(sorted(r.keys()) == BOARD_ROW_KEYS
                        for r in cap2["keys"] + cap4["keys"]))
        record("AC-DBL3", dbl3,
               "tail-window fidelity: limit=2 -> %s,"
               " limit=4 -> %s; per-row dumps byte-equal to"
               " full[-N:]=%s/%s; every returned row keeps the"
               " 15-key field set; ascending key_id order kept"
               % (seq2, seq4, rows_byte2, rows_byte4))

        # -- AC-DBL4 envelope overflow block ------------------------
        env_keys_capped = sorted(cap2.keys())
        total_mirror = ro.execute(
            "SELECT COUNT(*) FROM api_dev_keys"
            " WHERE dev_account = ?", ("usr:limit",)).fetchone()[0]
        dbl4 = (env_keys_capped == CAPPED_KEYS
                and cap2["limit"] == 2 and cap2["total"] == 6
                and total_mirror == 6
                and cap2["returned"] == 2
                and cap2["truncated"] is True
                and cap4["returned"] == 4 and cap4["truncated"] is True
                and _dumps(cap2["reject_tally_total"]) ==
                    _dumps(board_noarg["reject_tally_total"])
                and _dumps(cap2["usage_kind_tally_total"]) ==
                    _dumps(board_noarg["usage_kind_tally_total"])
                and cap2["reject_tally_total"] == {"E_AD_QUOTA": 1}
                and cap2["usage_kind_tally_total"] ==
                    {"backtest": 3}
                and cap2["window"] == OLD_WIN
                and cap2["dev_account"] == "usr:limit"
                and cap2["disclaimer"] == DISCLAIMER)
        record("AC-DBL4", dbl4,
               "overflow block: capped envelope keys == 6+4=%s;"
               " limit=%s total=%s (== mirror COUNT=%s)"
               " returned=%s truncated=%s; world aggregates"
               " full-world stable capped vs uncapped=%s/%s"
               " (reject=%s kinds=%s); truncation only cuts the"
               " keys list"
               % (env_keys_capped == CAPPED_KEYS, cap2["limit"],
                  cap2["total"], total_mirror, cap2["returned"],
                  cap2["truncated"],
                  _dumps(cap2["reject_tally_total"]) ==
                  _dumps(board_noarg["reject_tally_total"]),
                  _dumps(cap2["usage_kind_tally_total"]) ==
                  _dumps(board_noarg["usage_kind_tally_total"]),
                  cap2["reject_tally_total"],
                  cap2["usage_kind_tally_total"]))

        # -- AC-DBL5 mirror SQL third path --------------------------
        mirror_matches = []
        for n in (2, 4):
            prod_rows = dk.dev_board("usr:limit", n)["keys"]
            desc = ro.execute(
                "SELECT api_key, key_name FROM api_dev_keys"
                " WHERE dev_account = ?"
                " ORDER BY key_id DESC LIMIT ?",
                ("usr:limit", n)).fetchall()
            mirror = list(reversed(desc))
            same = (len(mirror) == len(prod_rows)
                    and all(mirror[i][0] == prod_rows[i]["api_key"]
                            and mirror[i][1] ==
                            prod_rows[i]["key_name"]
                            for i in range(len(mirror))))
            mirror_matches.append(same)
        dbl5 = all(mirror_matches)
        record("AC-DBL5", dbl5,
               "mirror SQL third path (mode=ro, ORDER BY key_id"
               " DESC LIMIT N reversed): limit=2 %s, limit=4 %s"
               " -- api_key/key_name field-level equality with"
               " the product tail slice"
               % (mirror_matches[0], mirror_matches[1]))

        # -- AC-DBL6 boundary states --------------------------------
        cap_exact = dk.dev_board("usr:limit", 6)
        cap_over = dk.dev_board("usr:limit", 50)
        cap_one = dk.dev_board("usr:limit", 1)
        cap_ghost = dk.dev_board("usr:ghost", 2)
        dbl6 = (cap_exact["truncated"] is False
                and cap_exact["returned"] == cap_exact["total"] == 6
                and cap_over["truncated"] is False
                and len(cap_over["keys"]) == 6
                and cap_one["returned"] == 1
                and [r["key_name"] for r in cap_one["keys"]] ==
                    ["k6"]
                and cap_ghost["keys"] == []
                and cap_ghost["total"] == 0
                and cap_ghost["returned"] == 0
                and cap_ghost["truncated"] is False
                and cap_ghost["reject_tally_total"] == {}
                and cap_ghost["usage_kind_tally_total"] == {}
                and sorted(cap_ghost.keys()) == CAPPED_KEYS)
        record("AC-DBL6", dbl6,
               "boundary states: exact-fit limit==6"
               " (truncated=%s returned==total==%s), over 50"
               " (rows=%d truncated=%s), single tail limit=1 ->"
               " %s, zero-key world usr:ghost (rows=0 total=0"
               " truncated=%s, tallies %s/%s, all four overflow"
               " keys carried)"
               % (cap_exact["truncated"], cap_exact["returned"],
                  len(cap_over["keys"]), cap_over["truncated"],
                  [r["key_name"] for r in cap_one["keys"]],
                  cap_ghost["truncated"],
                  cap_ghost["reject_tally_total"],
                  cap_ghost["usage_kind_tally_total"]))

        # ---- roll world: read-cap x month-roll orthogonality -----
        # R1845 recipe: roll-p cap 3 spends 2 calls, rotates to
        # roll-b which spends 1 -> effective 3 == cap, the 4th
        # October call rejects E_AD_QUOTA (reject row
        # record-time stamped 2026-10, attributed to roll-b).
        led.ensure_account("usr:rollx", census_avatar_id="rollx")
        led.adjust([("pool:reserve", "debit", 100),
                    ("usr:rollx", "credit", 100)],
                   "manual:fund-rollx", "suite funding rollx world")
        kp = dk.issue_key("usr:rollx", "roll-p", 3, ["backtest"],
                          True)
        dk.buy_credits(kp["api_key"], 10, 1, "PACK-DBL-RP")
        dk.call(kp["api_key"], "backtest", "DBL-RP-01",
                "engine:DBL-RP-01")
        clock.advance(7)
        dk.call(kp["api_key"], "backtest", "DBL-RP-02",
                "engine:DBL-RP-02")
        clock.advance(7)
        kb = dk.rotate_key(kp["api_key"], "roll-b")
        dk.buy_credits(kb["api_key"], 10, 1, "PACK-DBL-RB")
        dk.call(kb["api_key"], "backtest", "DBL-RB-01",
                "engine:DBL-RB-01")
        clock.advance(7)
        ok_roll_rej, code_roll_rej, _d3 = expect_ad_error(
            lambda: dk.call(kb["api_key"], "backtest",
                            "DBL-RB-02", "engine:DBL-RB-02"),
            D.E_AD_QUOTA)
        t_oct_pre = dk.chain_usage(kb["api_key"], window=OLD_WIN)

        # -- AC-DBL7 capped read across the month roll --------------
        clock.advance(23 * 86400)
        roll_capped = dk.dev_board("usr:rollx", 2)
        roll_full = dk.dev_board("usr:rollx")
        row_p_r = _row_by_name(roll_capped, "roll-p")
        row_b_r = _row_by_name(roll_capped, "roll-b")
        ids_roll = [conn.execute(
            "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
            (k,)).fetchone()[0] for k in (kp["api_key"],
                                          kb["api_key"])]
        marks_roll = ",".join("?" for _ in ids_roll)
        roll_counts_pre_call = (
            conn.execute("SELECT COUNT(*) FROM api_dev_keys"
                         " WHERE dev_account = ?",
                         ("usr:rollx",)).fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM api_calls"
                         " WHERE key_id IN (" + marks_roll + ")",
                         tuple(ids_roll)).fetchone()[0],
            rjconn.execute("SELECT COUNT(*) FROM reject_events"
                           " WHERE key_id IN (" + marks_roll + ")",
                           tuple(ids_roll)).fetchone()[0])
        dk.call(kb["api_key"], "backtest", "DBL-N-01",
                "engine:DBL-N-01")
        clock.advance(7)
        roll_capped2 = dk.dev_board("usr:rollx", 2)
        row_b_n = _row_by_name(roll_capped2, "roll-b")
        row_p_n = _row_by_name(roll_capped2, "roll-p")
        t_oct_post = dk.chain_usage(kb["api_key"], window=OLD_WIN)
        roll_counts_post_call = (
            conn.execute("SELECT COUNT(*) FROM api_dev_keys"
                         " WHERE dev_account = ?",
                         ("usr:rollx",)).fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM api_calls"
                         " WHERE key_id IN (" + marks_roll + ")",
                         tuple(ids_roll)).fetchone()[0],
            rjconn.execute("SELECT COUNT(*) FROM reject_events"
                           " WHERE key_id IN (" + marks_roll + ")",
                           tuple(ids_roll)).fetchone()[0])
        dbl7 = (ok_roll_rej and code_roll_rej == D.E_AD_QUOTA
                and roll_counts_pre_call == (2, 3, 1)
                and roll_capped["window"] == NEW_WIN
                and roll_capped["total"] == 2
                and roll_capped["returned"] == 2
                and roll_capped["truncated"] is False
                and [r["key_name"] for r in roll_capped["keys"]]
                    == ["roll-p", "roll-b"]
                and row_p_r["quota_used"] == 0
                and row_b_r["quota_used"] == 0
                and roll_capped["reject_tally_total"] == {}
                and roll_capped["usage_kind_tally_total"] == {}
                and _dumps(roll_capped["reject_tally_total"]) ==
                    _dumps(roll_full["reject_tally_total"])
                and _dumps(roll_capped["usage_kind_tally_total"])
                    == _dumps(roll_full["usage_kind_tally_total"])
                and row_b_n["quota_used"] == 1
                and row_b_n["usage_kind_tally"] == {"backtest": 1}
                and row_p_n["quota_used"] == 0
                and roll_capped2["usage_kind_tally_total"] ==
                    {"backtest": 1}
                and roll_capped2["reject_tally_total"] == {}
                and _dumps(t_oct_post) == _dumps(t_oct_pre)
                and roll_counts_post_call == (2, 4, 1))
        record("AC-DBL7", dbl7,
               "month-roll orthogonality: frozen clock +23d ->"
               " capped read window=%s rows=%s total=%d"
               " truncated=%s (tail rows all returned); new-month"
               " re-domain honest (roll-p/roll-b quota_used"
               " %d/%d, totals %s/%s); capped totals byte-equal"
               " uncapped=%s; November call re-computes under"
               " the cap (roll-b quota_used=%d kinds=%s, totals"
               " %s); October explicit read never moves=%s;"
               " counts %s -> %s (the +1 call is the AC fixture"
               " write, zero movement from any read)"
               % (roll_capped["window"],
                  [r["key_name"] for r in roll_capped["keys"]],
                  roll_capped["total"], roll_capped["truncated"],
                  row_p_r["quota_used"], row_b_r["quota_used"],
                  roll_capped["reject_tally_total"],
                  roll_capped["usage_kind_tally_total"],
                  _dumps(roll_capped["reject_tally_total"]) ==
                  _dumps(roll_full["reject_tally_total"]) and
                  _dumps(roll_capped["usage_kind_tally_total"])
                  == _dumps(roll_full["usage_kind_tally_total"]),
                  row_b_n["quota_used"],
                  row_b_n["usage_kind_tally"],
                  roll_capped2["usage_kind_tally_total"],
                  _dumps(t_oct_post) == _dumps(t_oct_pre),
                  roll_counts_pre_call, roll_counts_post_call))

        # -- AC-DBL8 pure-read law + determinism + hygiene ----------
        end_counts = _scoped_counts(conn, rjconn, marks, key_ids)
        fn_src = None
        with open(os.path.join(BASE, "apidev.py"), "r",
                  encoding="ascii") as handle:
            product_src = handle.read()
        m = re.search(r"    def dev_board\(self.*?(?=\n    def )",
                      product_src, re.DOTALL)
        fn_src = m.group(0) if m else ""
        dml_hits = re.findall(
            r"\b(INSERT|UPDATE|DELETE|REPLACE|DROP|CREATE)\b",
            fn_src)
        again_a = dk.dev_board("usr:limit", 2)
        again_b = dk.dev_board("usr:limit", 2)
        with open(os.path.join(BASE, "config.json"), "rb") as handle:
            cfg_bytes_end = handle.read()
        own_path = os.path.abspath(__file__)
        own_source = open(own_path, "r", encoding="ascii").read()
        imports_net = [line for line in own_source.splitlines()
                      if re.match(r"\s*(?:import|from)\s", line)
                      and re.search(r"urllib|requests|socket|http",
                                    line)]
        own_ascii = all(ord(ch) < 128 for ch in own_source)
        with open(os.path.join(
                os.path.dirname(BASE), "reconcile_all.py"), "r",
                encoding="ascii") as handle:
            reg_src = handle.read()
        reg_row_pos = reg_src.find('"ledger-apidev-devboard-limit"')
        reg_chunk = reg_src[reg_row_pos:reg_row_pos + 300]
        reg_row = (reg_row_pos >= 0
                   and "test_apidev_devboard_limit.py" in reg_chunk
                   and "8)," in reg_chunk)
        schema_end = set(r[0] for r in conn.execute(
            "SELECT sql FROM sqlite_master"
            " WHERE sql IS NOT NULL").fetchall())
        dbl8 = (end_counts == pre_counts
                and len(dml_hits) == 0
                and _dumps(again_a) == _dumps(again_b)
                and cfg_bytes_end == cfg_bytes
                and own_ascii and len(imports_net) == 0
                and schema_end == schema_pre
                and reg_row)
        record("AC-DBL8", dbl8,
               "pure-read + hygiene: main-world counts stable"
               " across every read %s == %s; dev_board source DML"
               " verbs=%d; double-call byte-identical (back-to-back"
               " fresh reads at the rolled clock, window=%s)=%s;"
               " config.json byte-stable=%s; suite pure-ASCII=%s;"
               " net-imports=%d; schema frozen=%s; registry row +"
               " criteria=8=%s"
               % (pre_counts, end_counts, len(dml_hits),
                  again_a["window"],
                  _dumps(again_a) == _dumps(again_b),
                  cfg_bytes_end == cfg_bytes, own_ascii,
                  len(imports_net), schema_end == schema_pre,
                  reg_row))

    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute
        D._window_utc = real_window

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-devboard-limit: %d/%d criteria pass"
          % (passed, total), flush=True)
    ro.close()
    rjconn.close()
    conn.close()
    dk.close()
    metered.close()
    led.close()
    return 0 if passed == total == 8 else 1


if __name__ == "__main__":
    sys.exit(main())
