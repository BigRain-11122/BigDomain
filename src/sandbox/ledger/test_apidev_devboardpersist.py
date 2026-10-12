"""Acceptance suite for the apidev dev_board capped-windowed
read restart-persistence example window (BigDomain R1902; canon =
the tech-queue "apidev dev_board cap-window read cross-restart
persistence" row, the R1896 seed, claimed from the tech-lane FIFO
oldest claimable row). Asserts the pre-registered criteria
AC-DBL15..AC-DBL21 from the R1902 claim note (criteria were
registered in state/queue/tech.md before this code ran; honesty
law). Each criterion prints PASS/FAIL with evidence; the process
exits non-zero on any FAIL.

Covered semantics: the derived purity of the dev_board read face
across an instance restart -- the three-piece stack (Ledger ->
MeteredFace -> DevKeyFace) closes fully in reverse dependency
order and reopens on the same db path and config bytes; the
October windowed capped envelope (window re-domained panel x cap
tail-slice, window echo + overflow block) must replay
byte-identical from the fresh instance (zero in-memory drift in
the derived face); two November calls on chain-c -- the very key
the October capped read pins in its tail slice -- recalculate
the default capped read via the real product path (zero cache)
while the October windowed reads stay window-frozen
(api_calls rows are record-time immutable; the injection lands
on the very key whose October capped read is pinned -- a
stronger hijack face than the R1896 isolated-key injection, per
the R1897 claim ruling); a third instance replays the
post-injection state byte-identically (two-instance sequential
reads).

Cross-clock comparisons (after the +23d frozen-clock move) use
the window-scoped projection that strips the two clock-following
minute fields and the lifetime billing block from every key row
(the R1863 AC-DBL13 minute-ring-orthogonal + billing-lifetime
rulings); zero-clock-move comparisons (a pure restart) compare
the FULL envelope byte-for-byte -- a stronger face than the
banded projection.

The metered face is the real product injected by reference (no
copy); the two November calls spend real credits from the same
pack the October calls spent (the suite funds each client once).
This test source stays pure ASCII per the encoding discipline.

Usage: python test_apidev_devboardpersist.py
"""

import datetime
import hashlib
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
NEW_WIN = "2026-11"
ACCT = "usr:dbp"

# exact envelope contracts (the R1825/R1845/R1852/R1857 pin lists,
# reused verbatim: this suite adds zero keys to dev_board)
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
    module (the R1845 recipe): the window and minute keys roll
    only when the suite moves the clock, so double-run stdout is
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


def snap(env):
    return json.dumps(env, sort_keys=True)


def _win_projection(board):
    """Window-scoped projection of a dev_board envelope: strips
    the two clock-following minute fields and the billing block
    (the lifetime metered ring face) from every key row. The
    minute ring is orthogonal to the month window (the R1857
    AC-DBL13 ruling) and billing is a lifetime face whose
    consumed_calls/remaining_credits legitimately advance with
    new spend -- so a cross-clock byte-comparison of the full
    envelope is structurally unreachable; the window-scoped
    projection is the honest comparison surface (the R1863
    ancestry-suite precedent, reused verbatim)."""
    proj = {k: v for k, v in board.items() if k != "keys"}
    proj["keys"] = [{f: v for f, v in row.items()
                     if f not in ("minute_window", "minute_used",
                                  "billing")}
                    for row in board["keys"]]
    return proj


def _count(conn, table, extra="", args=()):
    return conn.execute(
        "SELECT COUNT(*) FROM " + table + extra,
        tuple(args)).fetchone()[0]


def _open_stack(db_path, cfg):
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    return led, metered, dk


def _close_stack(dk, metered, led):
    dk.close()
    metered.close()
    led.close()


def _make_calls(dk, clock, api_key, prefix, n, kind, start=1):
    for i in range(start, start + n):
        ref = "%s-%02d" % (prefix, i)
        dk.call(api_key, kind, ref, "engine:%s" % ref)
        clock.advance(3)


def _row_by_name(board, key_name):
    for row in board["keys"]:
        if row["key_name"] == key_name:
            return row
    return None


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-dbp-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    lc_path = os.path.join(tmp, "api_lifecycle.db")
    rj_path = os.path.join(tmp, "api_rejects.db")

    product_path = os.path.join(BASE, "apidev.py")
    with open(product_path, "rb") as handle:
        product_pre = handle.read()
    product_pre_sha = hashlib.sha256(product_pre).hexdigest()

    clock = _FrozenClock()
    real_now = D._now_utc
    real_minute = D._minute_utc
    real_window = D._window_utc

    D._now_utc = clock.now_utc
    D._minute_utc = clock.minute_utc
    D._window_utc = clock.window_utc

    try:
        led, metered, dk = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)
        rjconn = sqlite3.connect(rj_path)

        # -- AC-DBL15 October anchor world + pre-close snapshots ---
        led.mint_to_pool("pool:reserve", 5000, "MINT-DBP",
                         "settlement")
        led.ensure_account(ACCT, census_avatar_id="dbp")
        led.adjust([("pool:reserve", "debit", 300),
                    (ACCT, "credit", 300)],
                   "manual:fund-dbp", "suite funding dbp")

        ka = dk.issue_key(ACCT, "chain-a", 50,
                          ["backtest", "visualize"], True)
        dk.buy_credits(ka["api_key"], 40, 1, "PACK-DBP-A")
        _make_calls(dk, clock, ka["api_key"], "DBP-A", 3, "backtest")
        kb = dk.rotate_key(ka["api_key"], "chain-b")
        _make_calls(dk, clock, kb["api_key"], "DBP-B", 2,
                    "visualize")
        kc = dk.rotate_key(kb["api_key"], "chain-c")
        _make_calls(dk, clock, kc["api_key"], "DBP-C", 2,
                    "backtest")
        kd = dk.issue_key(ACCT, "lone-d", 50, ["backtest"], True)
        dk.buy_credits(kd["api_key"], 20, 1, "PACK-DBP-D")
        _make_calls(dk, clock, kd["api_key"], "DBP-D", 2,
                    "backtest")
        kind_rejected = False
        try:
            dk.call(kd["api_key"], "visualize", "DBP-D-BAD",
                    "engine:DBP-D-BAD")
        except D.ApiDevError as exc:
            kind_rejected = exc.code == D.E_AD_KIND
        clock.advance(3)

        def key_id_of(api_key):
            return conn.execute(
                "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
                (api_key,)).fetchone()[0]

        id_a = key_id_of(ka["api_key"])
        id_b = key_id_of(kb["api_key"])
        id_c = key_id_of(kc["api_key"])
        id_d = key_id_of(kd["api_key"])
        marks4 = ",".join("?" for _ in (id_a, id_b, id_c, id_d))
        oct_calls = _count(
            conn, "api_calls",
            " WHERE window = '2026-10' AND key_id IN (" + marks4
            + ")", (id_a, id_b, id_c, id_d))
        # month-abstraction law (R1813): W derives from a real
        # call row's record-time window column, never hardcoded
        W = conn.execute(
            "SELECT window FROM api_calls WHERE key_id = ?"
            " ORDER BY called_utc, call_ref LIMIT 1",
            (id_a,)).fetchone()[0]
        oct_rejects = _count(
            rjconn, "reject_events",
            " WHERE window = '2026-10' AND key_id = ?",
            (id_d,))

        s_oct_capwin = snap(dk.dev_board(ACCT, 2, W))
        s_oct_bare = snap(dk.dev_board(ACCT, 0, W))
        s_default = snap(dk.dev_board(ACCT))
        s_def_cap = snap(dk.dev_board(ACCT, 2))
        p_oct_capwin_pre = snap(_win_projection(
            json.loads(s_oct_capwin)))
        p_oct_bare_pre = snap(_win_projection(
            json.loads(s_oct_bare)))

        oc = json.loads(s_oct_capwin)
        ob = json.loads(s_oct_bare)
        quota_map = {r["key_name"]: r["quota_used"]
                     for r in ob["keys"]}
        status_map = {r["key_name"]: r["status"]
                      for r in ob["keys"]}
        rot_map = {r["key_name"]: r["rotated_from_key_id"]
                   for r in ob["keys"]}
        row_keys_ok = all(sorted(r.keys()) == BOARD_ROW_KEYS
                          for r in ob["keys"])
        row_c = _row_by_name(oc, "chain-c")
        row_d = _row_by_name(oc, "lone-d")
        dbp15 = (
            kind_rejected
            and oct_calls == 9 and W == "2026-10"
            and oct_rejects == 1
            and sorted(oc.keys()) == CAPPED_KEYS
            and len(CAPPED_KEYS) == 10
            and sorted(ob.keys()) == BOARD_KEYS
            and len(BOARD_KEYS) == 6
            and row_keys_ok and len(BOARD_ROW_KEYS) == 15
            and oc["dev_account"] == ACCT
            and oc["window"] == W
            and oc["disclaimer"] == DISCLAIMER
            and oc["limit"] == 2 and oc["total"] == 4
            and oc["returned"] == 2 and oc["truncated"] is True
            and [r["key_name"] for r in oc["keys"]]
            == ["chain-c", "lone-d"]
            and quota_map == {"chain-a": 3, "chain-b": 5,
                              "chain-c": 7, "lone-d": 2}
            and status_map == {"chain-a": "rotated_out",
                                "chain-b": "rotated_out",
                                "chain-c": "active",
                                "lone-d": "active"}
            and rot_map == {"chain-a": None, "chain-b": id_a,
                            "chain-c": id_b, "lone-d": None}
            and oc["usage_kind_tally_total"]
            == {"backtest": 7, "visualize": 2}
            and oc["reject_tally_total"] == {"E_AD_KIND": 1}
            and row_c["usage_kind_tally"] == {"backtest": 2}
            and row_d["reject_tally"] == {"E_AD_KIND": 1}
            and ob["usage_kind_tally_total"]
            == {"backtest": 7, "visualize": 2}
            and ob["reject_tally_total"] == {"E_AD_KIND": 1}
            and json.loads(s_default)["window"] == W
            and s_default == s_oct_bare)
        record("AC-DBL15", dbp15,
               "October anchor: 9 real call rows window=2026-10"
               " over the 4-key world (SQL count==%d), 1"
               " E_AD_KIND reject row, W=%s from the first call"
               " row's window column; four snapshots anchored"
               " (capped-win 10 keys overflow l/t/r/tr=%s/%s/%s"
               "/%s tail=%s; bare/default 6 keys; default=="
               "oct-bare byte-equal=%s), quota map %s (chain"
               " ancestry carried), statuses %s, world"
               " aggregates full-world under truncation"
               " kinds=%s tally=%s, row pin 15 keys=%s"
               % (oct_calls, W, oc["limit"], oc["total"],
                  oc["returned"], oc["truncated"],
                  [r["key_name"] for r in oc["keys"]],
                  s_default == s_oct_bare, quota_map, status_map,
                  oc["usage_kind_tally_total"],
                  oc["reject_tally_total"], row_keys_ok))

        # -- AC-DBL16 restart replay: capped-windowed envelope ------
        conn.close()
        lcconn.close()
        rjconn.close()
        _close_stack(dk, metered, led)
        led2, metered2, dk2 = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)

        replay = snap(dk2.dev_board(ACCT, 2, W))
        replay2 = snap(dk2.dev_board(ACCT, 2, W))
        dbp16 = (replay == s_oct_capwin
                 and replay2 == s_oct_capwin)
        record("AC-DBL16", dbp16,
               "full stack close (reverse order) -> reopen same"
               " db/config: October windowed capped envelope"
               " byte-identical to the pre-close snapshot=%s,"
               " second same-param read self-identical=%s"
               % (replay == s_oct_capwin,
                  replay2 == s_oct_capwin))

        # -- AC-DBL17 default / bare-window / default-cap replay ------
        r_default = snap(dk2.dev_board(ACCT))
        r_oct_bare = snap(dk2.dev_board(ACCT, 0, W))
        r_def_cap = snap(dk2.dev_board(ACCT, 2))
        dbp17 = (r_default == s_default
                 and r_oct_bare == s_oct_bare
                 and r_def_cap == s_def_cap)
        record("AC-DBL17", dbp17,
               "default read replayed byte-identical=%s (window"
               " echo stays %s), oct bare-window=%s, default-cap"
               "=%s (derived face carries zero in-memory state"
               " across the restart)"
               % (r_default == s_default,
                  json.loads(r_default)["window"],
                  r_oct_bare == s_oct_bare,
                  r_def_cap == s_def_cap))

        # -- AC-DBL18 November calls on the pinned key -> recalc -----
        clock.advance(23 * 86400)
        _make_calls(dk2, clock, kc["api_key"], "DBP-N", 2,
                    "backtest")
        nov_calls = _count(
            conn, "api_calls",
            " WHERE window = '2026-11' AND key_id IN (" + marks4
            + ")", (id_a, id_b, id_c, id_d))
        r_def_cap_nov = json.loads(snap(dk2.dev_board(ACCT, 2)))
        r_nov_capwin = json.loads(snap(dk2.dev_board(ACCT, 2,
                                                    NEW_WIN)))
        dbp18 = (
            nov_calls == 2
            and snap(r_def_cap_nov) != s_def_cap
            and r_def_cap_nov["window"] == NEW_WIN
            and {r["key_name"]: r["quota_used"]
                 for r in r_def_cap_nov["keys"]}
            == {"chain-c": 2, "lone-d": 0}
            and r_def_cap_nov["usage_kind_tally_total"]
            == {"backtest": 2}
            and r_def_cap_nov["reject_tally_total"] == {}
            and r_nov_capwin["window"] == NEW_WIN
            and r_nov_capwin["limit"] == 2
            and r_nov_capwin["total"] == 4
            and r_nov_capwin["truncated"] is True
            and {r["key_name"]: r["quota_used"]
                 for r in r_nov_capwin["keys"]}
            == {"chain-c": 2, "lone-d": 0}
            and r_nov_capwin["usage_kind_tally_total"]
            == {"backtest": 2}
            and r_nov_capwin["reject_tally_total"] == {})
        record("AC-DBL18", dbp18,
               "frozen clock +23d -> 2 November calls on chain-c"
               " (the very key the October capped read pins in"
               " its tail slice) via the real product path"
               " (record-time window=2026-11 SQL count==%d):"
               " default capped read recalculated (window echo"
               " %s, quota map %s, byte-differs from the"
               " pre-close default-cap snapshot=%s = zero"
               " cache), November windowed capped read carries"
               " the new rows kinds=%s tally=%s honest-empty"
               % (nov_calls, r_def_cap_nov["window"],
                  {r["key_name"]: r["quota_used"]
                   for r in r_def_cap_nov["keys"]},
                  snap(r_def_cap_nov) != s_def_cap,
                  r_nov_capwin["usage_kind_tally_total"],
                  r_nov_capwin["reject_tally_total"]))

        # -- AC-DBL19 old-window zero permeation ----------------------
        p_oct_capwin_post = snap(_win_projection(
            json.loads(snap(dk2.dev_board(ACCT, 2, W)))))
        p_oct_bare_post = snap(_win_projection(
            json.loads(snap(dk2.dev_board(ACCT, 0, W)))))
        total_rows = _count(conn, "api_calls")
        oct_total = _count(conn, "api_calls",
                           " WHERE window = '2026-10'")
        nov_total = _count(conn, "api_calls",
                           " WHERE window = '2026-11'")
        dbp19 = (p_oct_capwin_post == p_oct_capwin_pre
                 and p_oct_bare_post == p_oct_bare_pre
                 and total_rows == 11
                 and oct_total == 9 and nov_total == 2
                 and oct_total + nov_total == total_rows)
        record("AC-DBL19", dbp19,
               "after the November injection on the same pinned"
               " key: October windowed reads stay window-frozen"
               " under the window-scoped projection (capped=%s,"
               " bare=%s; record-time window column immutable),"
               " api_calls total %d == oct %d + nov %d immutable"
               " rows never lost"
               % (p_oct_capwin_post == p_oct_capwin_pre,
                  p_oct_bare_post == p_oct_bare_pre,
                  total_rows, oct_total, nov_total))

        # -- AC-DBL20 two-instance sequential reads --------------------
        f2_a = snap(dk2.dev_board(ACCT, 2, W))
        f2_b = snap(dk2.dev_board(ACCT, 0, W))
        f2_c = snap(dk2.dev_board(ACCT, 2, NEW_WIN))
        f2_d = snap(dk2.dev_board(ACCT, 2))
        p2_oct = snap(_win_projection(
            json.loads(snap(dk2.dev_board(ACCT, 2, W)))))
        conn.close()
        _close_stack(dk2, metered2, led2)
        led3, metered3, dk3 = _open_stack(db_path, cfg)
        f3_a = snap(dk3.dev_board(ACCT, 2, W))
        f3_b = snap(dk3.dev_board(ACCT, 0, W))
        f3_c = snap(dk3.dev_board(ACCT, 2, NEW_WIN))
        f3_d = snap(dk3.dev_board(ACCT, 2))
        p3_oct = snap(_win_projection(
            json.loads(snap(dk3.dev_board(ACCT, 2, W)))))
        dbp20 = (f3_a == f2_a and f3_b == f2_b
                 and f3_c == f2_c and f3_d == f2_d
                 and p3_oct == p2_oct
                 and p3_oct == p_oct_capwin_pre)
        record("AC-DBL20", dbp20,
               "third instance on the same db: all four"
               " post-injection reads byte-identical to the"
               " second instance (%s/%s/%s/%s), and the October"
               " capped-windowed projection still equals the"
               " original pre-close projection=%s (windowed read"
               " survives restart x new-data unscratched)"
               % (f3_a == f2_a, f3_b == f2_b, f3_c == f2_c,
                  f3_d == f2_d, p3_oct == p_oct_capwin_pre))

        # -- AC-DBL21 pure-read law + hygiene -------------------------
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)
        rjconn = sqlite3.connect(rj_path)
        calls_before = _count(conn, "api_calls")
        keys_before = _count(conn, "api_dev_keys")
        ev_before = _count(lcconn, "key_events")
        rj_before = _count(rjconn, "reject_events")
        for lmt, w in ((0, None), (2, W), (1, NEW_WIN),
                       (2, None), (0, W), (1, W), (2, NEW_WIN),
                       (0, NEW_WIN)):
            dk3.dev_board(ACCT, lmt, w)
        calls_after = _count(conn, "api_calls")
        keys_after = _count(conn, "api_dev_keys")
        ev_after = _count(lcconn, "key_events")
        rj_after = _count(rjconn, "reject_events")

        source = product_pre.decode("ascii")
        idx = source.find("def dev_board")
        seg_end = source.find("    def ", idx + 20)
        board_seg = source[idx:seg_end]
        # strip docstrings and comments before the write-keyword
        # scan (the R1888 AC-LG7 code-strip precedent: the naive
        # scan hits the segment's own hygiene sentences)
        code_seg = re.sub(r'"""[\s\S]*?"""', '""', board_seg)
        code_seg = "\n".join(re.sub(r"#.*$", "", line)
                            for line in code_seg.splitlines())
        write_kw = re.findall(
            r"\b(INSERT|UPDATE|DELETE|REPLACE|CREATE)\b",
            code_seg)
        with open(product_path, "rb") as handle:
            product_post = handle.read()
        product_post_sha = hashlib.sha256(product_post).hexdigest()
        with open(os.path.join(BASE, "config.json"), "rb") as handle:
            cfg_bytes_end = handle.read()
        with open(os.path.abspath(__file__), "rb") as handle:
            me_bytes = handle.read()
        me_ascii = all(b < 128 for b in me_bytes)
        imports_net = [
            line for line in source.splitlines()
            if re.match(r"\s*(?:import|from)\s", line)
            and re.search(r"urllib|requests|socket|http", line)]
        mine_net = [
            line for line in
            me_bytes.decode("ascii").splitlines()
            if re.match(r"\s*(?:import|from)\s", line)
            and re.search(r"urllib|requests|socket|http", line)]
        dbp21 = (calls_after == calls_before
                 and keys_after == keys_before
                 and ev_after == ev_before
                 and rj_after == rj_before
                 and len(write_kw) == 0
                 and product_post == product_pre
                 and product_pre_sha == product_post_sha
                 and cfg_bytes_end == cfg_bytes
                 and me_ascii and len(imports_net) == 0
                 and len(mine_net) == 0)
        record("AC-DBL21", dbp21,
               "pure read: 8-form read battery on the third face"
               " moves zero rows (api_calls %d==%d,"
               " api_dev_keys %d==%d, key_events %d==%d,"
               " reject_events %d==%d), dev_board segment zero"
               " write keywords=%d, apidev.py sha256 stable=%s,"
               " config.json byte-stable=%s, sources pure-ASCII"
               "=%s, network imports 0/0=%s"
               % (calls_after, calls_before, keys_after,
                  keys_before, ev_after, ev_before,
                  rj_after, rj_before, len(write_kw),
                  product_pre_sha == product_post_sha,
                  cfg_bytes_end == cfg_bytes, me_ascii,
                  len(imports_net) == 0 and len(mine_net) == 0))

        conn.close()
        lcconn.close()
        rjconn.close()
        _close_stack(dk3, metered3, led3)

    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute
        D._window_utc = real_window

    restored = (D._now_utc is real_now
                and D._minute_utc is real_minute
                and D._window_utc is real_window)
    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-devboardpersist: %d/%d criteria pass"
          % (passed, total), flush=True)
    print("clock restore probe: %s" % restored, flush=True)
    return 0 if (passed == total and total == 7
                 and restored) else 1


if __name__ == "__main__":
    sys.exit(main())
