"""Acceptance suite for the apidev lineage chain-usage read face
(BigDomain R1833; canon = tech-queue "apidev lineage chain usage
one-shot aggregate read face" row, the R1825 audit_lineage
successor, claimed from the tech-lane FIFO oldest open row). The
pre-registered criteria AC-LU1..AC-LU7 live in the R1833 tech
claim note (criteria were registered before this code ran; the
AC-CU prefix was taken by the R1751 curation family so the claim
switched to AC-LU per the R1811 prefix-switch precedent).

Covered semantics: chain_usage(api_key, window=None) is the
pure-read one-shot chain usage face over the immutable call rows
-- the chain walked exactly the way audit_lineage walks it
(cross-face zero-drift pinned by this suite), per-member exact-key
counts, two alignment invariants (prefix sum over ancestors plus
queried == the quota ring's ancestry-only anti-evasion effective
count == key_view quota_used for the current window; chain_total ==
that prefix plus the descendants' own rows), the 14-form bad-window
family fail-closed, historical/future month semantics on the
record-time window column, dead keys fully readable, embedded faces
untouched.

The metered face is the real product injected by reference (no
copy). This test source stays pure ASCII per the encoding
discipline.

Usage: python test_apidev_chainusage.py
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
import apidev as D                      # noqa: E402 (R1700+R1833)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the open API is a compute"
             " + visualization interface, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 15, 10, 0, 0)
CUR_WIN = "2026-10"
HIST_WIN = "2026-09"
FUT_WIN = "2026-12"

# exact envelope contracts (the AC-RJW4 law pins -- same pin
# lists as the R1825 lineage suite: this round adds zero keys to
# key_view / dev_board)
CHAIN_USAGE_KEYS = sorted([
    "api_key", "dev_account", "key_name", "key_id", "window",
    "by_member", "chain_total", "effective_upto_queried",
    "chain_size", "queried_index", "disclaimer"])
MEMBER_KEYS = sorted(["key_id", "key_name", "own_calls"])
KEY_VIEW_KEYS = sorted([
    "api_key", "dev_account", "key_name", "metered_client",
    "window_cap", "enabled_kinds", "ai_label", "minute_cap",
    "status", "rotated_from_key_id", "window", "quota_used",
    "quota_remaining", "minute_window", "minute_used",
    "reject_tally", "usage_kind_tally", "disclaimer"])
BOARD_KEYS = sorted([
    "dev_account", "keys", "window", "reject_tally_total",
    "usage_kind_tally_total", "disclaimer"])
BOARD_ROW_KEYS = sorted([
    "key_name", "api_key", "metered_client", "window_cap",
    "enabled_kinds", "ai_label", "minute_cap", "status",
    "rotated_from_key_id", "quota_used", "minute_window",
    "minute_used", "reject_tally", "usage_kind_tally", "billing"])

BAD_WINDOWS = ("2026-13", "2026-00", "2026-1", "2026/10", "2026",
               "202610", "abcd", "", 2026, True, 2.5,
               "2026-10\n", "2026-10 ", "2026-10\r")


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


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _key_id(conn, api_key):
    return conn.execute(
        "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
        (api_key,)).fetchone()[0]


def _manual_own(conn, key_id, window):
    return conn.execute(
        "SELECT COUNT(*) FROM api_calls"
        " WHERE key_id = ? AND window = ?",
        (key_id, window)).fetchone()[0]


def _manual_in_list(conn, key_ids, window):
    marks = ",".join("?" for _ in key_ids)
    return conn.execute(
        "SELECT COUNT(*) FROM api_calls"
        " WHERE window = ? AND key_id IN (" + marks + ")",
        [window] + list(key_ids)).fetchone()[0]


def _make_calls(dk, clock, api_key, prefix, n, kind, start=1):
    for i in range(start, start + n):
        ref = "%s-%02d" % (prefix, i)
        dk.call(api_key, kind, ref, "engine:%s" % ref)
        clock.advance(7)


def _member_ids(env):
    return [m["key_id"] for m in env["by_member"]]


def _own_map(env):
    return {m["key_id"]: m["own_calls"] for m in env["by_member"]}


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-cu-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    lc_path = os.path.join(tmp, "api_lifecycle.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    conn = sqlite3.connect(db_path)
    lcconn = sqlite3.connect(lc_path)
    clock = _FrozenClock()
    real_now = D._now_utc
    real_minute = D._minute_utc
    real_window = D._window_utc

    try:
        D._now_utc = clock.now_utc
        D._minute_utc = clock.minute_utc
        D._window_utc = clock.window_utc

        # world: one funded 3-key rotate chain A->B->C on usr:lin
        # (A 3 calls, B 2 calls, C 4 calls, then C revoked ->
        # all-terminal chain), one plain-revoked singleton with 2
        # calls, one zero-call fresh key, and one out-of-chain key
        # on a second developer with 5 calls (scope isolation).
        led.mint_to_pool("pool:reserve", 5000, "MINT-LU", "settlement")
        led.ensure_account("usr:lin", census_avatar_id="lin")
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:lin", "credit", 300)],
                   "manual:fund-lin-cu", "suite funding lin")
        led.ensure_account("usr:zoe", census_avatar_id="zoe")
        led.adjust([("pool:reserve", "debit", 100),
                    ("usr:zoe", "credit", 100)],
                   "manual:fund-zoe-cu", "suite funding zoe")

        ka = dk.issue_key("usr:lin", "chain-a", 50,
                          ["backtest", "visualize"], True)
        dk.buy_credits(ka["api_key"], 40, 1, "PACK-LU-A")
        _make_calls(dk, clock, ka["api_key"], "LU-A", 3, "backtest")
        kb = dk.rotate_key(ka["api_key"], "chain-b")
        _make_calls(dk, clock, kb["api_key"], "LU-B", 2, "visualize")
        kc = dk.rotate_key(kb["api_key"], "chain-c")
        _make_calls(dk, clock, kc["api_key"], "LU-C", 4, "backtest")
        dk.revoke_key(kc["api_key"])   # all-terminal chain world

        rk = dk.issue_key("usr:lin", "plain-revoked", 10,
                          ["backtest"], False)
        dk.buy_credits(rk["api_key"], 10, 1, "PACK-LU-R")
        _make_calls(dk, clock, rk["api_key"], "LU-R", 2, "backtest")
        dk.revoke_key(rk["api_key"])

        fk = dk.issue_key("usr:lin", "fresh-zero", 10,
                          ["backtest"], False)
        ko = dk.issue_key("usr:zoe", "other-chain", 20,
                          ["backtest"], False)
        dk.buy_credits(ko["api_key"], 20, 1, "PACK-LU-O")
        _make_calls(dk, clock, ko["api_key"], "LU-O", 5, "backtest")

        id_a = _key_id(conn, ka["api_key"])
        id_b = _key_id(conn, kb["api_key"])
        id_c = _key_id(conn, kc["api_key"])

        # fixture-injected rows for the historical month on chain
        # ancestor A: 2 backtest rows (the product record path
        # stamps the window at record time, so a past month needs
        # the direct honest INSERT -- the R1730 family fixture
        # precedent, noted here per the honesty law)
        for call_ref, called_utc in (
                ("LU-H-01", "2026-09-05T08:00:00Z"),
                ("LU-H-02", "2026-09-12T09:30:00Z")):
            conn.execute(
                "INSERT INTO api_calls (call_ref, key_id, kind,"
                " engine_ref, window, called_utc)"
                " VALUES (?,?,?,?,?,?)",
                (call_ref, id_a, "backtest",
                 "engine:%s" % call_ref, HIST_WIN, called_utc))
        conn.commit()

        source = open(os.path.join(BASE, "apidev.py"), "r",
                     encoding="ascii").read()

        # -- AC-LU1 contract + default current-month --------------------
        ok_unk, code_unk, _d1 = expect_ad_error(
            lambda: dk.chain_usage("sk-nonexistent"), D.E_AD_UNKNOWN_KEY)
        ok_empty, code_empty, _d2 = expect_ad_error(
            lambda: dk.chain_usage(""), D.E_AD_UNKNOWN_KEY)
        ok_unk_badwin, code_unk_badwin, _d3 = expect_ad_error(
            lambda: dk.chain_usage("sk-nonexistent", "2026-13"),
            D.E_AD_UNKNOWN_KEY)
        t_def = dk.chain_usage(kb["api_key"])
        lg_b = dk.audit_lineage(kb["api_key"])
        member_shapes = all(
            sorted(m.keys()) == MEMBER_KEYS for m in t_def["by_member"])
        lu1 = (ok_unk and ok_empty and ok_unk_badwin
               and sorted(t_def.keys()) == CHAIN_USAGE_KEYS
               and t_def["window"] == CUR_WIN
               and t_def["api_key"] == kb["api_key"]
               and t_def["dev_account"] == "usr:lin"
               and t_def["key_name"] == "chain-b"
               and t_def["key_id"] == id_b
               and t_def["disclaimer"] == DISCLAIMER
               and member_shapes
               and _member_ids(t_def) == [id_a, id_b, id_c]
               and _member_ids(t_def) ==
                   [m["key_id"] for m in lg_b["chain"]]
               and [m["key_name"] for m in t_def["by_member"]] ==
                   ["chain-a", "chain-b", "chain-c"]
               and _own_map(t_def) == {id_a: 3, id_b: 2, id_c: 4}
               and t_def["chain_total"] == 9
               and t_def["effective_upto_queried"] == 5
               and t_def["chain_size"] == 3
               and t_def["queried_index"] == 1)
        record("AC-LU1", lu1,
               "key gate first: unknown/empty/unknown+bad-window ->"
               " %s/%s/%s; envelope 11 keys exact=%s, window=%s,"
               " member rows 3-key exact=%s, chain order"
               " [A,B,C]==audit_lineage order=%s, own map=%s,"
               " chain_total=%d, effective_upto_queried=%d,"
               " queried_index=%d"
               % (code_unk, code_empty, code_unk_badwin,
                  sorted(t_def.keys()) == CHAIN_USAGE_KEYS,
                  t_def["window"], member_shapes,
                  _member_ids(t_def) ==
                  [m["key_id"] for m in lg_b["chain"]],
                  _own_map(t_def), t_def["chain_total"],
                  t_def["effective_upto_queried"],
                  t_def["queried_index"]))

        # -- AC-LU2 bad window shapes fail-closed -----------------------
        calls_before = _count(conn, "api_calls")
        keys_before = _count(conn, "api_dev_keys")
        ev_before = _count(lcconn, "key_events")
        codes = []
        oks = []
        for bad in BAD_WINDOWS:
            ok_bad, code_bad, _d4 = expect_ad_error(
                lambda b=bad: dk.chain_usage(kb["api_key"], b),
                D.E_AD_BAD_ARGS)
            oks.append(ok_bad)
            codes.append(code_bad)
        calls_after = _count(conn, "api_calls")
        keys_after = _count(conn, "api_dev_keys")
        ev_after = _count(lcconn, "key_events")
        lu2 = (all(oks) and codes == [D.E_AD_BAD_ARGS] * 14
               and calls_after == calls_before
               and keys_after == keys_before
               and ev_after == ev_before)
        record("AC-LU2", lu2,
               "14 bad shapes -> %s (api_calls %d==%d,"
               " api_dev_keys %d==%d, key_events %d==%d, zero read"
               " side effects); only None is the default sentinel"
               % (codes, calls_after, calls_before,
                  keys_after, keys_before, ev_after, ev_before))

        # -- AC-LU3 cross-face zero drift + query-point invariance ------
        t_a = dk.chain_usage(ka["api_key"])
        t_b = dk.chain_usage(kb["api_key"])
        t_c = dk.chain_usage(kc["api_key"])
        lg_a = dk.audit_lineage(ka["api_key"])
        lg_c = dk.audit_lineage(kc["api_key"])
        drift_free = all(
            _member_ids(tx) ==
            [m["key_id"] for m in lgx["chain"]]
            for tx, lgx in ((t_a, lg_a), (t_b, lg_b), (t_c, lg_c)))
        point_indep = (
            _own_map(t_a) == _own_map(t_b) == _own_map(t_c)
            == {id_a: 3, id_b: 2, id_c: 4}
            and t_a["chain_total"] == t_b["chain_total"]
            == t_c["chain_total"] == 9
            and t_a["chain_size"] == t_b["chain_size"]
            == t_c["chain_size"] == 3
            and (t_a["queried_index"], t_b["queried_index"],
                 t_c["queried_index"]) == (0, 1, 2))
        lu3 = drift_free and point_indep
        record("AC-LU3", lu3,
               "by_member id order == audit_lineage chain order from"
               " every query point=%s; point invariance (own map /"
               " chain_total=9 / chain_size=3 equal, queried_index"
               " 0/1/2 by point)=%s"
               % (drift_free, point_indep))

        # -- AC-LU4 manual SQL cross + semantic alignment ----------------
        manual_own = {kid: _manual_own(conn, kid, CUR_WIN)
                      for kid in (id_a, id_b, id_c)}
        manual_chain = _manual_in_list(
            conn, [id_a, id_b, id_c], CUR_WIN)
        manual_prefix_b = _manual_in_list(
            conn, [id_a, id_b], CUR_WIN)
        manual_prefix_c = _manual_in_list(
            conn, [id_a, id_b, id_c], CUR_WIN)
        eff_b = dk._effective_window_count(id_b, CUR_WIN)
        eff_c = dk._effective_window_count(id_c, CUR_WIN)
        view_b = dk.key_view(kb["api_key"])
        view_c = dk.key_view(kc["api_key"])
        desc_b = _manual_in_list(conn, [id_c], CUR_WIN)
        desc_c = 0
        lu4 = (manual_own == {id_a: 3, id_b: 2, id_c: 4}
               and manual_chain == 9
               and t_b["chain_total"] == manual_chain
               and t_b["effective_upto_queried"] == manual_prefix_b
               == eff_b == view_b["quota_used"] == 5
               and t_c["effective_upto_queried"] == manual_prefix_c
               == eff_c == view_c["quota_used"] == 9
               and t_b["chain_total"] ==
                   t_b["effective_upto_queried"] + desc_b
               and t_c["chain_total"] ==
                   t_c["effective_upto_queried"] + desc_c
               and t_a["effective_upto_queried"] == 3
               and dk._effective_window_count(id_a, CUR_WIN) == 3)
        record("AC-LU4", lu4,
               "per-member own == manual SQL=%s; chain_total==manual"
               " IN-list==%d; effective(B)==manual prefix==product"
               " _effective_window_count==key_view quota_used==%d;"
               " effective(C)==%d; split law"
               " chain_total==effective+descendants (%d==5+4,"
               " %d==9+0)=%s"
               % (manual_own, manual_chain, eff_b, eff_c,
                  t_b["chain_total"], t_c["chain_total"], lu4))

        # -- AC-LU5 window semantics (record-time column) ----------------
        t_hist_a = dk.chain_usage(ka["api_key"], window=HIST_WIN)
        t_hist_c = dk.chain_usage(kc["api_key"], window=HIST_WIN)
        t_fut = dk.chain_usage(kb["api_key"], window=FUT_WIN)
        t_def_again = dk.chain_usage(kb["api_key"])
        lu5 = (t_hist_a["window"] == HIST_WIN
               and _own_map(t_hist_a) ==
                   {id_a: 2, id_b: 0, id_c: 0}
               and t_hist_a["chain_total"] == 2
               and t_hist_a["effective_upto_queried"] == 2
               and t_hist_c["chain_total"] == 2
               and t_hist_c["effective_upto_queried"] == 2
               and _own_map(t_fut) == {id_a: 0, id_b: 0, id_c: 0}
               and t_fut["chain_total"] == 0
               and t_fut["effective_upto_queried"] == 0
               and t_fut["window"] == FUT_WIN
               and json.dumps(t_def_again, sort_keys=True) ==
                   json.dumps(t_def, sort_keys=True))
        record("AC-LU5", lu5,
               "hist window: A own==2 (fixture-injected rows, direct"
               " INSERT noted), B/C zero, chain_total==2, effective"
               " through C==2 (ancestor hist rows carry); future"
               " window: all-zero honest empty; default read"
               " re-read byte-stable (zero hist penetration)=%s"
               % lu5)

        # -- AC-LU6 pure-read law + dead-key readability -----------------
        t_rk = dk.chain_usage(rk["api_key"])
        t_fk = dk.chain_usage(fk["api_key"])
        env1 = json.dumps(dk.chain_usage(kb["api_key"]),
                          sort_keys=True)
        env2 = json.dumps(dk.chain_usage(kb["api_key"]),
                          sort_keys=True)
        ins1 = json.dumps(dk.chain_usage(kb["api_key"]))
        ins2 = json.dumps(dk.chain_usage(kb["api_key"]))
        calls_end = _count(conn, "api_calls")
        keys_end = _count(conn, "api_dev_keys")
        ev_end = _count(lcconn, "key_events")
        # method-source write-statement scan (docstring/comment
        # strip first: the R1678 self-referential false-positive
        # family lesson)
        m = re.search(
            r"    def chain_usage\(self.*?(?=\n    def |\n    # --)",
            source, re.S)
        method_src = m.group(0) if m else ""
        code_only = re.sub(r'"""[\s\S]*?"""', '""', method_src)
        code_only = "\n".join(re.sub(r"#.*$", "", line)
                              for line in code_only.splitlines())
        writes = re.search(r"\bINSERT\b|\bUPDATE\b|\bDELETE\b",
                           code_only)
        lu6 = (t_rk["chain_size"] == 1
               and t_rk["queried_index"] == 0
               and _own_map(t_rk) == {_key_id(conn,
                                              rk["api_key"]): 2}
               and t_rk["chain_total"] == 2
               and t_rk["effective_upto_queried"] == 2
               and t_fk["chain_total"] == 0
               and t_c["chain_size"] == 3
               and _own_map(t_c) == {id_a: 3, id_b: 2, id_c: 4}
               and env1 == env2 and ins1 == ins2
               and calls_end == calls_before
               and keys_end == keys_before
               and ev_end == ev_before
               and method_src != "" and writes is None)
        record("AC-LU6", lu6,
               "revoked singleton readable (own==2), zero-call"
               " fresh key honest zero, all-terminal 3-key chain"
               " readable (A rotated_out/B rotated_out/C revoked,"
               " own map==%s); double-call json byte-identical"
               " (sorted + insertion order); table counts stable"
               " (%d/%d/%d); chain_usage source write-statement"
               " scan=%s"
               % (_own_map(t_c), calls_end, keys_end, ev_end,
                  writes is None))

        # -- AC-LU7 embedded faces + hygiene -----------------------------
        view_fk = dk.key_view(fk["api_key"])
        board_lin = dk.dev_board("usr:lin")
        row0 = board_lin["keys"][0]
        with open(os.path.join(BASE, "config.json"), "rb") as handle:
            cfg_bytes_end = handle.read()
        imports_net = [line for line in source.splitlines()
                       if re.match(r"\s*(?:import|from)\s", line)
                       and re.search(r"urllib|requests|socket|http",
                                     line)]
        is_ascii = all(ord(ch) < 128 for ch in source)
        module_code = re.sub(r'"""[\s\S]*?"""', '""', source)
        module_code = "\n".join(re.sub(r"#.*$", "", line)
                               for line in module_code.splitlines())
        has_update = re.search(r"\bUPDATE\b", module_code) is not None
        has_rng = re.search(r"\brandom\b", source) is not None
        has_face = "def chain_usage" in source
        lu7 = (sorted(view_fk.keys()) == KEY_VIEW_KEYS
               and sorted(board_lin.keys()) == BOARD_KEYS
               and sorted(row0.keys()) == BOARD_ROW_KEYS
               and cfg_bytes_end == cfg_bytes and is_ascii
               and not has_update and not has_rng
               and len(imports_net) == 0 and has_face)
        record("AC-LU7", lu7,
               "key_view keys exact (%d), dev_board keys exact"
               " (%d), board row keys exact (%d) -- zero"
               " chain_usage embedding=%s; config.json"
               " byte-stable=%s, source pure-ASCII=%s, zero"
               " UPDATE=%s, zero RNG=%s, net-imports=%d,"
               " chain_usage present=%s"
               % (len(KEY_VIEW_KEYS), len(BOARD_KEYS),
                  len(BOARD_ROW_KEYS),
                  sorted(view_fk.keys()) == KEY_VIEW_KEYS,
                  cfg_bytes_end == cfg_bytes, is_ascii,
                  not has_update, not has_rng, len(imports_net),
                  has_face))

    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute
        D._window_utc = real_window

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE apidev-chainusage: %d/%d criteria pass"
          % (passed, total), flush=True)
    lcconn.close()
    conn.close()
    dk.close()
    metered.close()
    led.close()
    return 0 if passed == total == 7 else 1


if __name__ == "__main__":
    sys.exit(main())
