"""Acceptance suite for the apidev key_view explicit historical
window read (BigDomain R1868; canon = tech-queue "apidev key_view
explicit historical window read face" row, the R1863 reseed,
claimed from the tech-lane FIFO oldest open row; the tasks.md
P1 mirror row 23). The pre-registered criteria AC-KVW1..AC-KVW7
live in the R1868 tech claim note (criteria were registered
before this code ran; the AC-KVW prefix was verified unowned by
a whole-repo scan on claim).

Covered semantics: key_view(api_key) is the single-key panel
that always read the current _window_utc month. It gains an
optional window=None tail parameter: the default keeps the
current-month behavior byte-stable, an explicit "YYYY-MM"
string re-domains the quota panel (quota_used /
quota_remaining / reject_tally / usage_kind_tally) to that
record-time month with the quota counter keeping its
rotation-chain ancestry semantics (anti-evasion: a rotate never
resets an explicit month either), the minute ring stays
clock-orthogonal, a historical month stays readable forever
and a future month is an honest all-zero panel, and a bad
window shape rejects the dedicated E_AD_BAD_WINDOW fail-closed
(the panel-class code the dev_board window face owns) after
the key gate. The three-face single-key interlock carries the
R1863 AC-ANW family to key_view: key_view(key, window=W)
quota_used == dev_board(window=W) board row == chain_usage(key,
window=W) effective_upto_queried, in the anchor month and
across the roll.

The metered face is the real product injected by reference (no
copy). This test source stays pure ASCII per the encoding
discipline.

Usage: python test_apidev_keyviewwin.py
"""

import datetime
import json
import os
import re
import shutil
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
FUT_WIN = "2026-12"

# the R1824 key_view pin list (18 keys, reused verbatim: this
# suite adds zero keys to the envelope)
VIEW_KEYS = sorted([
    "api_key", "dev_account", "key_name", "metered_client",
    "window_cap", "enabled_kinds", "ai_label", "minute_cap",
    "status", "rotated_from_key_id", "window", "quota_used",
    "quota_remaining", "minute_window", "minute_used",
    "reject_tally", "usage_kind_tally", "disclaimer"])

# minute ring is clock-orthogonal (R1857 AC-DBL13 / R1863 AC-ANW5
# ruling): byte comparisons over an explicit historical window use
# the window-scoped projection (minute fields stripped)
MINUTE_FIELDS = ("minute_window", "minute_used")

# the 14 bad-window forms (R1856 in-register tuple, reused)
BADS14 = ("2026-13", "2026-00", "2026-1", "2026/10", "2026",
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


def dumps(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def project(view):
    """Window-scoped projection: the envelope minus the two
    clock-orthogonal minute fields (the AC-KVW4 comparison
    caliber; premise honestly noted per the R1863 AC-ANW5
    two-first-run-red precedent)."""
    return dumps({k: v for k, v in view.items()
                  if k not in MINUTE_FIELDS})


def _key_id(conn, api_key):
    return conn.execute(
        "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
        (api_key,)).fetchone()[0]


def _own_oct_count(conn, id_b):
    return conn.execute(
        "SELECT COUNT(*) FROM api_calls"
        " WHERE window = ? AND key_id = ?",
        (OLD_WIN, id_b)).fetchone()[0]


def _make_calls(dk, clock, api_key, prefix, n, kind, start=1):
    for i in range(start, start + n):
        ref = "%s-%02d" % (prefix, i)
        dk.call(api_key, kind, ref, "engine:%s" % ref)
        clock.advance(7)


def _board_row(dk, dev_account, key_name, window):
    board = dk.dev_board(dev_account, window=window)
    for row in board["keys"]:
        if row["key_name"] == key_name:
            return row
    return None


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-kvw-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    conn = sqlite3.connect(db_path)
    rjconn = sqlite3.connect(os.path.join(tmp, "api_rejects.db"))
    src_path = os.path.join(BASE, "test_apidev_keyviewwin.py")
    with open(src_path, "rb") as fh:
        suite_src = fh.read().decode("ascii")
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
        # rejects E_AD_QUOTA (zero new api_calls rows, one
        # reject_events row record-time stamped window 2026-10
        # attributed to roll-b). All calls land inside one frozen
        # minute (clock.advance(7) per call).
        led.mint_to_pool("pool:reserve", 5000, "MINT-KVW", "settlement")
        led.ensure_account("usr:rex", census_avatar_id="rex")
        led.adjust([("pool:reserve", "debit", 100),
                    ("usr:rex", "credit", 100)],
                   "manual:fund-rex-roll", "suite funding rex roll")
        kp = dk.issue_key("usr:rex", "roll-p", 3, ["backtest"], True)
        dk.buy_credits(kp["api_key"], 10, 1, "PACK-KVW-P")
        _make_calls(dk, clock, kp["api_key"], "KVW-P", 2, "backtest")
        kb = dk.rotate_key(kp["api_key"], "roll-b")
        _make_calls(dk, clock, kb["api_key"], "KVW-B", 1, "backtest")
        ok_rej, code_rej, _d0 = expect_ad_error(
            lambda: dk.call(kb["api_key"], "backtest",
                            "KVW-B-02", "engine:KVW-B-02"),
            D.E_AD_QUOTA)
        assert ok_rej, "quota reject anchor failed: %s" % code_rej
        id_b = _key_id(conn, kb["api_key"])

        # -- AC-KVW1 default fidelity triple identity ----------
        v_def = dk.key_view(kb["api_key"])
        v_none = dk.key_view(kb["api_key"], window=None)
        same = dumps(v_def) == dumps(v_none)
        keys_ok = sorted(v_def.keys()) == VIEW_KEYS
        win_ok = v_def["window"] == OLD_WIN
        used_ok = v_def["quota_used"] == 3
        rem_ok = v_def["quota_remaining"] == 0
        record("AC-KVW1", same and keys_ok and win_ok and used_ok
               and rem_ok,
               "default==window=None byte-identical=%s; 18-key"
               " envelope pin=%s; window=%s quota_used=%d/%d"
               " remaining=%d"
               % (same, keys_ok, v_def["window"], v_def["quota_used"],
                  kp["window_cap"], v_def["quota_remaining"]))

        # -- AC-KVW2 October anchor three-face interlock --------
        kv_oct_b = dk.key_view(kb["api_key"], window=OLD_WIN)
        board_row_b = _board_row(dk, "usr:rex", "roll-b", OLD_WIN)
        chain_oct_b = dk.chain_usage(kb["api_key"], window=OLD_WIN)
        face_a = kv_oct_b["quota_used"]
        face_b = board_row_b["quota_used"] if board_row_b else -1
        face_c = chain_oct_b["effective_upto_queried"]
        inter = face_a == face_b == face_c == 3
        kv_oct_p = dk.key_view(kp["api_key"], window=OLD_WIN)
        chain_oct_p = dk.chain_usage(kp["api_key"], window=OLD_WIN)
        p_ok = kv_oct_p["quota_used"] == 2 \
            == chain_oct_p["effective_upto_queried"]
        own_sql = _own_oct_count(conn, id_b)
        disc = own_sql == 1 and face_a != own_sql
        record("AC-KVW2", inter and p_ok and disc,
               "roll-b three faces kv=%d board=%d chain=%d (== 3,"
               " ancestry 2 + own 1); roll-p reverse %d (ancestors"
               " never inherit); own-only SQL mirror 1 != 3"
               % (face_a, face_b, face_c, kv_oct_p["quota_used"]))

        # -- AC-KVW3 new/future month honest zero panel ---------
        v_nov_pre = dk.key_view(kb["api_key"], window=NEW_WIN)
        v_fut = dk.key_view(kb["api_key"], window=FUT_WIN)
        nov_ok = v_nov_pre["quota_used"] == 0 \
            and v_nov_pre["quota_remaining"] == 3 \
            and v_nov_pre["reject_tally"] == {} \
            and v_nov_pre["usage_kind_tally"] == {} \
            and v_nov_pre["window"] == NEW_WIN
        fut_ok = v_fut["quota_used"] == 0 \
            and v_fut["reject_tally"] == {} \
            and v_fut["window"] == FUT_WIN
        record("AC-KVW3", nov_ok and fut_ok,
               "pre-roll %s zero panel used=0 remaining=3 tallies"
               " empty; future %s honest zero too"
               % (NEW_WIN, FUT_WIN))

        # -- AC-KVW4 cross-roll old-window preservation ---------
        s_oct = project(dk.key_view(kb["api_key"], window=OLD_WIN))
        clock.advance(23 * 24 * 3600)     # +23d -> 2026-11-07
        _make_calls(dk, clock, kb["api_key"], "KVW-N", 2, "backtest")
        kv_oct_post = dk.key_view(kb["api_key"], window=OLD_WIN)
        old_ok = project(kv_oct_post) == s_oct
        v_def_nov = dk.key_view(kb["api_key"])
        v_exp_nov = dk.key_view(kb["api_key"], window=NEW_WIN)
        newdef_ok = dumps(v_def_nov) == dumps(v_exp_nov)
        nov_face_a = v_exp_nov["quota_used"]
        nov_row = _board_row(dk, "usr:rex", "roll-b", NEW_WIN)
        nov_chain = dk.chain_usage(kb["api_key"], window=NEW_WIN)
        nov_inter = nov_face_a == (nov_row["quota_used"]
                                   if nov_row else -1) \
            == nov_chain["effective_upto_queried"] == 2
        record("AC-KVW4", old_ok and newdef_ok and nov_inter,
               "old-window projection byte-preserved=%s (minute"
               " fields clock-orthogonal, premise per R1863"
               " AC-ANW5); new-month default==explicit=%s; November"
               " three faces %d/%s/%d == 2"
               % (old_ok, newdef_ok, nov_face_a,
                  nov_row["quota_used"] if nov_row else -1,
                  nov_chain["effective_upto_queried"]))

        # -- AC-KVW5 bad-window fail-closed (14 forms) ---------
        calls_pre = conn.execute(
            "SELECT COUNT(*) FROM api_calls").fetchone()[0]
        rej_pre = rjconn.execute(
            "SELECT COUNT(*) FROM reject_events").fetchone()[0]
        rejects14 = []
        for bad in BADS14:
            got, code, _d1 = expect_ad_error(
                lambda b=bad: dk.key_view(kb["api_key"], window=b),
                D.E_AD_BAD_WINDOW)
            rejects14.append((bad, code))
        all14 = all(code == D.E_AD_BAD_WINDOW for _b, code in rejects14)
        calls_post = conn.execute(
            "SELECT COUNT(*) FROM api_calls").fetchone()[0]
        rej_post = rjconn.execute(
            "SELECT COUNT(*) FROM reject_events").fetchone()[0]
        side_ok = calls_pre == calls_post and rej_pre == rej_post
        ok_key_gate, code_gate, _d2 = expect_ad_error(
            lambda: dk.key_view("no-such-key", window="2026-13"),
            D.E_AD_UNKNOWN_KEY)
        record("AC-KVW5", all14 and side_ok and ok_key_gate,
               "bads14 all rejected E_AD_BAD_WINDOW (dedicated"
               " panel code, dev_board precedent; not the"
               " E_AD_BAD_ARGS audit family)=%s; zero side effects"
               " calls %d==%d rejects %d==%d; key gate first=%s"
               " (%s)"
               % (all14, calls_pre, calls_post, rej_pre, rej_post,
                  ok_key_gate, code_gate))

        # -- AC-KVW6 minute ring clock orthogonality -----------
        minute_now = clock.minute_utc()
        orth = kv_oct_post["minute_window"] == minute_now \
            and kv_oct_post["minute_used"] == 2
        record("AC-KVW6", orth,
               "explicit %s read keeps minute ring on the clock:"
               " minute_window=%s (frozen %s) minute_used=%d"
               " (the two November calls; ancestry rows sit in the"
               " October minute and never leak)"
               % (OLD_WIN, kv_oct_post["minute_window"], minute_now,
                  kv_oct_post["minute_used"]))

        # -- AC-KVW7 hygiene -----------------------------------
        ascii_ok = True
        try:
            suite_src.encode("ascii")
        except UnicodeEncodeError:
            ascii_ok = False
        net_pat = re.compile(
            r'^\s*(import|from)\s+(socket|http|urllib|requests)'
            r'\b', re.M)
        net_free = not net_pat.search(suite_src)
        cfg_now = open(os.path.join(BASE, "config.json"),
                       "rb").read()
        cfg_ok = cfg_now == cfg_bytes
        record("AC-KVW7", ascii_ok and net_free and cfg_ok,
               "suite source pure ASCII=%s; zero network imports"
               "=%s; shipped config.json bytes unchanged=%s"
               % (ascii_ok, net_free, cfg_ok))

    finally:
        D._now_utc = real_now
        D._minute_utc = real_minute
        D._window_utc = real_window
        conn.close()
        rjconn.close()
        shutil.rmtree(tmp, ignore_errors=True)

    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s: %d/%d criteria"
          % ("PASS" if not fails else "FAIL",
             sum(1 for _a, ok in RESULTS if ok), len(RESULTS)),
          flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
