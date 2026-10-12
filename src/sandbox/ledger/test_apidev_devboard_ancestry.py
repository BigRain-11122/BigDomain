"""Acceptance suite for the apidev dev_board ancestry-in-explicit-
window anti-evasion example (BigDomain R1863; canon = tech-queue
"apidev dev_board ancestry-window anti-evasion example window"
row, the R1857 reseed, claimed from the tech-lane FIFO oldest
open row). The pre-registered criteria AC-ANW1..AC-ANW7 live in
the R1863 tech claim note (criteria were registered before this
code ran; the AC-ANW prefix was verified unowned by a whole-repo
scan on claim).

Covered semantics: dev_board's per-key quota_used carries the
quota ring's anti-evasion ancestry semantics inside EXPLICIT
history-window reads too (the R1857 window parameter made the
panel re-domainable; its AC-DBL12 mirror used fresh zero-ancestry
keys, so the ancestor-inheritance face of an explicit window
read stayed uncovered). This suite pins it: after roll-p spends
2 October calls and rotates to roll-b which spends 1 (effective
3 == cap, 4th call E_AD_QUOTA), the explicit window="2026-10"
board read shows roll-b quota_used == 3 (ancestor 2 + own 1)
while roll-p stays 2 (own only, ancestors never inherit
descendants); three faces align (board explicit window ==
chain_usage effective_upto_queried == key_view current-window
under the frozen clock); the own-only SQL mirror discriminates
(1 != 3, proving the board face is the ancestry semantic); after
the frozen clock crosses into November and roll-b spends 2 new
calls, the November explicit window read shows 2 (the ancestry
has no November rows) and the October explicit window read is
byte-preserved across the roll. Zero product bytes change: the
ancestry semantics already live in _effective_window_count, this
suite only pins them. This test source stays pure ASCII per the
encoding discipline.

Usage: python test_apidev_devboard_ancestry.py
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


def _dump(obj):
    return json.dumps(obj, sort_keys=True)


def _win_projection(board):
    """Window-scoped projection of a dev_board envelope: strips
    the two clock-following minute fields and the billing block
    (the lifetime metered ring face) from every key row. The
    minute ring is orthogonal to the month window (the R1857
    AC-DBL13 ruling) and billing is a lifetime face whose
    consumed_calls/remaining_credits legitimately advance with
    new spend (first-run red on record: consumed 3->5 across the
    roll) -- so a cross-roll byte-comparison of the full envelope
    is structurally unreachable; the window-scoped projection is
    the honest comparison surface (R1704 premise-correction
    precedent)."""
    proj = {k: v for k, v in board.items() if k != "keys"}
    proj["keys"] = [{f: v for f, v in row.items()
                     if f not in ("minute_window", "minute_used",
                                  "billing")}
                    for row in board["keys"]]
    return proj


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-anw-ac-")
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

        # world (the R1845 devboard-roll isomorphic single-hop
        # rotate chain, on its own account usr:anw): roll-p cap 3
        # spends 2 October calls, rotates to roll-b which spends
        # 1 -> effective 3 == cap, so the 4th October call
        # rejects E_AD_QUOTA (capped-out anchor, one reject_events
        # row record-time stamped window 2026-10 attributed to
        # roll-b). All October calls land inside one frozen
        # minute (clock.advance(7) per call).
        led.mint_to_pool("pool:reserve", 5000, "MINT-ANW", "settlement")
        led.ensure_account("usr:anw", census_avatar_id="anw")
        led.adjust([("pool:reserve", "debit", 100),
                    ("usr:anw", "credit", 100)],
                   "manual:fund-anw-roll", "suite funding anw roll")
        kp = dk.issue_key("usr:anw", "roll-p", 3, ["backtest"], True)
        dk.buy_credits(kp["api_key"], 10, 1, "PACK-ANW-P")
        _make_calls(dk, clock, kp["api_key"], "ANW-P", 2, "backtest")
        kb = dk.rotate_key(kp["api_key"], "roll-b")
        _make_calls(dk, clock, kb["api_key"], "ANW-B", 1, "backtest")
        ok_oct_q, code_oct_q, _d1 = expect_ad_error(
            lambda: dk.call(kb["api_key"], "backtest",
                            "ANW-B-02", "engine:ANW-B-02"),
            D.E_AD_QUOTA)
        id_p = _key_id(conn, kp["api_key"])
        id_b = _key_id(conn, kb["api_key"])
        marks_pair = ",".join("?" for _ in (id_p, id_b))
        rej_oct = rjconn.execute(
            "SELECT COUNT(*) FROM reject_events"
            " WHERE window = ?", (OLD_WIN,)).fetchone()[0]
        rej_owner = rjconn.execute(
            "SELECT COUNT(*) FROM reject_events"
            " WHERE window = ? AND key_id = ?",
            (OLD_WIN, id_b)).fetchone()[0]

        # -- AC-ANW1 explicit-window world anchor --------------------
        board_oct = dk.dev_board("usr:anw", window=OLD_WIN)
        row_p = _row_by_name(board_oct, "roll-p")
        row_b = _row_by_name(board_oct, "roll-b")
        pair_oct = conn.execute(
            "SELECT COUNT(*) FROM api_calls"
            " WHERE window = ? AND key_id IN (" + marks_pair + ")",
            (OLD_WIN, id_p, id_b)).fetchone()[0]
        anw1 = (ok_oct_q and code_oct_q == D.E_AD_QUOTA
                and rej_oct == 1 and rej_owner == 1
                and pair_oct == 3
                and sorted(board_oct.keys()) == BOARD_KEYS
                and sorted(row_p.keys()) == BOARD_ROW_KEYS
                and sorted(row_b.keys()) == BOARD_ROW_KEYS
                and board_oct["window"] == OLD_WIN
                and board_oct["dev_account"] == "usr:anw"
                and board_oct["disclaimer"] == DISCLAIMER
                and len(board_oct["keys"]) == 2
                and row_p["status"] == "rotated_out"
                and row_b["status"] == "active"
                and row_p["rotated_from_key_id"] is None
                and row_b["rotated_from_key_id"] == id_p
                and row_p["quota_used"] == 2
                and row_b["quota_used"] == 3
                and row_p["minute_used"] == 2
                and row_b["minute_used"] == 3
                and row_b["reject_tally"] == {"E_AD_QUOTA": 1})
        record("AC-ANW1", anw1,
               "explicit-window anchor: 4th call -> %s"
               " (reject_events 2026-10 COUNT=%d, owner=roll-b"
               " COUNT=%d, api_calls pair October COUNT=%d);"
               " explicit window=%s board envelope exact=%s"
               " row envelope exact=%s/%s; rows=%d status %s/%s"
               " rotated_from %s/%s; roll-p quota_used=%d"
               " (own only, zero ancestry), roll-b quota_used=%d"
               " (ancestor 2 + own 1, the anti-evasion inheritance"
               " visible in the explicit window read); minute_used"
               " %d/%d; roll-b reject_tally=%s"
               % (code_oct_q, rej_oct, rej_owner, pair_oct,
                  board_oct["window"],
                  sorted(board_oct.keys()) == BOARD_KEYS,
                  sorted(row_p.keys()) == BOARD_ROW_KEYS,
                  sorted(row_b.keys()) == BOARD_ROW_KEYS,
                  len(board_oct["keys"]), row_p["status"],
                  row_b["status"], row_p["rotated_from_key_id"],
                  row_b["rotated_from_key_id"], row_p["quota_used"],
                  row_b["quota_used"], row_p["minute_used"],
                  row_b["minute_used"], row_b["reject_tally"]))

        # -- AC-ANW2 three-face alignment + discriminating mirrors --
        t_b_oct = dk.chain_usage(kb["api_key"], window=OLD_WIN)
        t_p_oct = dk.chain_usage(kp["api_key"], window=OLD_WIN)
        kv_b = dk.key_view(kb["api_key"])
        kv_p = dk.key_view(kp["api_key"])
        own_b_oct = conn.execute(
            "SELECT COUNT(*) FROM api_calls"
            " WHERE window = ? AND key_id = ?",
            (OLD_WIN, id_b)).fetchone()[0]
        anc_b_oct = conn.execute(
            "SELECT COUNT(*) FROM api_calls"
            " WHERE window = ? AND key_id IN (" + marks_pair + ")",
            (OLD_WIN, id_p, id_b)).fetchone()[0]
        own_map_b = {m["key_id"]: m["own_calls"]
                     for m in t_b_oct["by_member"]}
        anw2 = (row_b["quota_used"] == 3
                and t_b_oct["effective_upto_queried"] == 3
                and t_b_oct["chain_total"] == 3
                and own_map_b == {id_p: 2, id_b: 1}
                and kv_b["quota_used"] == 3
                and kv_b["window"] == OLD_WIN
                and own_b_oct == 1
                and anc_b_oct == 3
                and row_p["quota_used"] == 2
                and t_p_oct["effective_upto_queried"] == 2
                and kv_p["quota_used"] == 2
                and t_p_oct["chain_total"] == 3)
        record("AC-ANW2", anw2,
               "three-face alignment at window=%s: board roll-b"
               " quota_used=%d == chain_usage effective_upto_queried"
               "=%d == key_view quota_used=%d (frozen-clock current"
               " window); chain by_member=%s chain_total=%d;"
               " discriminating mirrors: own-only COUNT(roll-b)=%d"
               " != 3 (the board face is the ancestry semantic, not"
               " own-only), ancestry COUNT(pair)=%d; reverse"
               " assertion: roll-p chain effective=%d == key_view=%d"
               " == board row=%d (ancestors never inherit"
               " descendants; roll-p chain_total=%d carries the"
               " descendant row in the audit view only)"
               % (OLD_WIN, row_b["quota_used"],
                  t_b_oct["effective_upto_queried"], kv_b["quota_used"],
                  own_map_b, t_b_oct["chain_total"], own_b_oct,
                  anc_b_oct, t_p_oct["effective_upto_queried"],
                  kv_p["quota_used"], row_p["quota_used"],
                  t_p_oct["chain_total"]))

        # -- AC-ANW3 explicit==default byte-equality + snapshots ---
        board_def = dk.dev_board("usr:anw")
        s_oct = _dump(_win_projection(board_oct))
        t_pre = _dump(t_b_oct)
        anw3 = (_dump(board_def) == _dump(board_oct)
                and _dump(_win_projection(board_def)) == s_oct)
        record("AC-ANW3", anw3,
               "explicit-window read == default read full-envelope"
               " byte-equal=%s (window=None resolves to the frozen"
               " current month %s; json.dumps sort_keys identity),"
               " window-scoped projections equal=%s; snapshots"
               " anchored: S_oct-proj=%dB (minute fields + billing"
               " stripped per the clock-orthogonal / lifetime-face"
               " rulings), t_pre=%dB"
               % (_dump(board_def) == _dump(board_oct),
                  board_def["window"],
                  _dump(_win_projection(board_def)) == s_oct,
                  len(s_oct.encode("utf-8")),
                  len(t_pre.encode("utf-8"))))

        # -- AC-ANW4 month roll + new-month three-face --------------
        clock.advance(23 * 86400)
        _make_calls(dk, clock, kb["api_key"], "ANW-N", 2, "backtest")
        stamp_nov = conn.execute(
            "SELECT COUNT(*) FROM api_calls"
            " WHERE key_id = ? AND window = ?"
            " AND call_ref IN ('ANW-N-01','ANW-N-02')",
            (id_b, NEW_WIN)).fetchone()[0]
        board_nov = dk.dev_board("usr:anw", window=NEW_WIN)
        row_p_n = _row_by_name(board_nov, "roll-p")
        row_b_n = _row_by_name(board_nov, "roll-b")
        t_b_nov = dk.chain_usage(kb["api_key"], window=NEW_WIN)
        kv_b_n = dk.key_view(kb["api_key"])
        own_map_bn = {m["key_id"]: m["own_calls"]
                     for m in t_b_nov["by_member"]}
        anw4 = (stamp_nov == 2
                and board_nov["window"] == NEW_WIN
                and row_b_n["quota_used"] == 2
                and row_p_n["quota_used"] == 0
                and t_b_nov["effective_upto_queried"] == 2
                and own_map_bn == {id_p: 0, id_b: 2}
                and kv_b_n["quota_used"] == 2
                and kv_b_n["window"] == NEW_WIN
                and row_p_n["reject_tally"] == {}
                and row_b_n["reject_tally"] == {}
                and row_b_n["minute_window"] == clock.minute_utc()
                and row_p_n["minute_window"] == clock.minute_utc())
        record("AC-ANW4", anw4,
               "frozen clock +23d: November 2 calls succeed (quota"
               " ring rolled, ancestry has no November rows so the"
               " inheritance adds nothing), record-time stamp"
               " window=%s COUNT=%d; explicit %s board: roll-b"
               " quota_used=%d (own November rows), roll-p quota"
               "_used=%d honest zero; chain_usage effective=%d"
               " by_member=%s; key_view quota_used=%d window=%s"
               " (three faces align in the new window); minute"
               " windows follow the clock ==%s; October reject row"
               " never penetrates the new-month tally (both rows"
               " reject_tally=%s/%s)"
               % (NEW_WIN, stamp_nov, NEW_WIN, row_b_n["quota_used"],
                  row_p_n["quota_used"],
                  t_b_nov["effective_upto_queried"], own_map_bn,
                  kv_b_n["quota_used"], kv_b_n["window"],
                  clock.minute_utc(), row_p_n["reject_tally"],
                  row_b_n["reject_tally"]))

        # -- AC-ANW5 old-month explicit read preserved across roll --
        board_oct_after = dk.dev_board("usr:anw", window=OLD_WIN)
        t_b_oct_after = dk.chain_usage(kb["api_key"], window=OLD_WIN)
        row_b_after = _row_by_name(board_oct_after, "roll-b")
        row_p_after = _row_by_name(board_oct_after, "roll-p")
        proj_after = _dump(_win_projection(board_oct_after))
        anw5 = (proj_after == s_oct
                and _dump(t_b_oct_after) == t_pre
                and row_b_after["quota_used"] == 3
                and row_p_after["quota_used"] == 2
                and board_nov["window"] == NEW_WIN
                and row_b_n["quota_used"] == 2)
        record("AC-ANW5", anw5,
               "old-month preservation across the roll: explicit"
               " %s board window-scoped projection byte-equal to"
               " the pre-roll snapshot=%s (roll-b quota_used stays"
               " %d = the history-window ancestry inheritance"
               " survives; roll-p stays %d; the two clock-following"
               " minute fields and the lifetime billing block are"
               " stripped per the clock-orthogonal / lifetime-face"
               " rulings, two first-run reds on"
               " record); chain_usage %s byte-equal=%s; two"
               " windows non-penetrating both ways (October read"
               " %d/%d, November read %d/%d)"
               % (OLD_WIN, proj_after == s_oct,
                  row_b_after["quota_used"], row_p_after["quota_used"],
                  OLD_WIN, _dump(t_b_oct_after) == t_pre,
                  row_p_after["quota_used"], row_b_after["quota_used"],
                  row_p_n["quota_used"], row_b_n["quota_used"]))

        # -- AC-ANW6 immutable rows + pure-read law ------------------
        all_calls = conn.execute(
            "SELECT COUNT(*) FROM api_calls").fetchone()[0]
        oct_calls = conn.execute(
            "SELECT COUNT(*) FROM api_calls WHERE window = ?",
            (OLD_WIN,)).fetchone()[0]
        nov_calls = conn.execute(
            "SELECT COUNT(*) FROM api_calls WHERE window = ?",
            (NEW_WIN,)).fetchone()[0]
        rej_nov = rjconn.execute(
            "SELECT COUNT(*) FROM reject_events"
            " WHERE window = ?", (NEW_WIN,)).fetchone()[0]
        keys_now = conn.execute(
            "SELECT COUNT(*) FROM api_dev_keys").fetchone()[0]
        anw6 = (all_calls == 5 and oct_calls == 3 and nov_calls == 2
                and rej_oct == 1 and rej_nov == 0
                and keys_now == 2
                and row_b_after["reject_tally"] == {"E_AD_QUOTA": 1}
                and row_b_n["reject_tally"] == {})
        record("AC-ANW6", anw6,
               "immutable rows + provenance: api_calls total=%d"
               " (October=%d + November=%d SQL window stamps),"
               " reject_events October=%d (the E_AD_QUOTA anchor"
               " stays October-attributed in the history read) /"
               " November=%d (zero penetration into the new-month"
               " panel tally); key rows=%d constant; every board"
               "/ chain_usage / key_view read in this suite left"
               " all three stores count-stable (pure-read law)"
               % (all_calls, oct_calls, nov_calls, rej_oct,
                  rej_nov, keys_now))

        # -- AC-ANW7 suite-side hygiene ------------------------------
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
        anw7 = (product_post == product_pre
                and cfg_bytes_end == cfg_bytes
                and "def dev_board" in product_post.decode("ascii")
                and own_ascii and len(imports_net) == 0)
        record("AC-ANW7", anw7,
               "hygiene: apidev.py byte-stable across the run=%s"
               " (dev_board face present=%s), config.json"
               " byte-stable=%s, suite source pure-ASCII=%s,"
               " net-imports=%d (double-run byte-identity and the"
               " RUNNER / matrix / sentinel faces live in the round"
               " evidence log)"
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
    print("SUITE apidev-devboard-ancestry: %d/%d criteria pass"
          % (passed, total), flush=True)
    rjconn.close()
    conn.close()
    dk.close()
    metered.close()
    led.close()
    return 0 if passed == total == 7 else 1


if __name__ == "__main__":
    sys.exit(main())
