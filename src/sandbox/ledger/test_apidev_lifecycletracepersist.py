"""Acceptance suite for the apidev lifecycle_trace windowed
read restart-persistence example window (BigDomain R1909; canon =
the tech-queue "apidev lifecycle_trace windowed read
cross-restart persistence" row, the R1904 seed, claimed from the
tech-lane FIFO oldest claimable row). Asserts the
pre-registered criteria AC-TRW8..AC-TRW14 from the R1909 claim
note (criteria were registered in state/queue/tech.md before
this code ran; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Covered semantics: the derived purity of the single-key
lifecycle event-sequence audit read face across an instance
restart -- the three-piece stack (Ledger -> MeteredFace ->
DevKeyFace) closes fully in reverse dependency order and
reopens on the same db path and config bytes; the October
windowed envelope (window echo + the key's own event trail)
must replay byte-identical from the fresh instance (zero
in-memory drift in the derived face); one November rotation on
chain-b -- the very key whose October windowed read is pinned
-- lands through the real product path (the only lifecycle
write a non-terminal key still accepts; revoke and rotate
both fail E_AD_ALREADY on a terminal key, so an active key's
rotation is the unique live row path) and recalculates the
default full-trail read via the real product path (zero
cache) while the October windowed read's TRAIL block stays
byte-frozen; a third instance replays the post-injection
state byte-identically (two-instance sequential reads).

Comparison-surface ruling (the claim ruling 3): the
lifecycle_trace windowed envelope carries full-derived key
facts (status + both pair links derive from the key's FULL
event set even under the window lens -- the R1875 law: a
window never redefines the key's state, so the state itself
re-derives when new lifecycle rows land). Under the same-key
November injection the October windowed read therefore
freezes at the TRAIL-block level (eight fields: api_key,
dev_account, key_name, key_id, events, total, window,
disclaimer) while the three key-fact fields re-derive to
their designed values (status active -> rotated_out,
rotated_to None -> successor id) -- the honest comparison
face. The lone-e terminal key (October revoke, E_AD_ALREADY
closed chain = zero new rows ever reachable) keeps the FULL
envelope byte-frozen across the injection. The pure-restart
faces (1) (2) and the third-instance face (4) carry zero
clock moves, so full-envelope byte comparison is structurally
reachable there.

This face moves zero tokens, so the suite needs no funding.
This test source stays pure ASCII per the encoding discipline.

Usage: python test_apidev_lifecycletracepersist.py
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
ACCT = "usr:ltp"

# exact envelope contracts (the R1824/R1875 pin lists, reused
# verbatim: this suite adds zero keys to lifecycle_trace)
TRACE_KEYS = sorted([
    "api_key", "dev_account", "key_name", "key_id", "status",
    "rotated_from_key_id", "rotated_to_key_id", "events", "total",
    "disclaimer"])
WIN_KEYS = sorted(TRACE_KEYS + ["window"])
EVENT_KEYS = sorted(["event_id", "event", "pair_key_id", "event_utc"])
# the claim ruling-3 trail block: every envelope field except the
# three full-derived key facts
FACT_KEYS = ("status", "rotated_from_key_id", "rotated_to_key_id")


class _FrozenClock(object):
    """Deterministic UTC clock holder patched onto the apidev
    module (the R1845 recipe): event stamps and window keys roll
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


def trail_of(env):
    """The claim ruling-3 trail block: the envelope minus the
    three full-derived key-fact fields."""
    return json.dumps({k: v for k, v in env.items()
                       if k not in FACT_KEYS}, sort_keys=True)


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


def main():
    tmp = tempfile.mkdtemp(prefix="apidev-ltp-ac-")
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

        # -- AC-TRW8 October anchor world + pre-close snapshots --
        # chain-a -> rotate -> chain-b (the pinned ACTIVE middle
        # key: its only October row is a real-product rotate_in);
        # lone-e issued + revoked in October (terminal key, the
        # E_AD_ALREADY closed chain = zero new rows ever
        # reachable = the full-envelope freeze face)
        ka = dk.issue_key(ACCT, "chain-a", 5, ["backtest"], True)
        clock.advance(3)
        kb = dk.rotate_key(ka["api_key"], "chain-b")
        clock.advance(3)
        ke = dk.issue_key(ACCT, "lone-e", 5, ["backtest"], False)
        dk.revoke_key(ke["api_key"])

        def key_id_of(api_key):
            return conn.execute(
                "SELECT key_id FROM api_dev_keys WHERE api_key = ?",
                (api_key,)).fetchone()[0]

        id_a = key_id_of(ka["api_key"])
        id_b = key_id_of(kb["api_key"])
        id_e = key_id_of(ke["api_key"])
        # month-abstraction law: W derives from the pinned key's
        # real rotate_in row record-time stamp, never hardcoded
        W = lcconn.execute(
            "SELECT substr(event_utc, 1, 7) FROM key_events"
            " WHERE key_id = ? AND event = 'rotate_in'"
            " ORDER BY event_utc, event_id LIMIT 1",
            (id_b,)).fetchone()[0]

        e_oct_b = _count(
            lcconn, "key_events",
            " WHERE substr(event_utc, 1, 7) = '2026-10'"
            " AND key_id = ?", (id_b,))
        e_oct_all = _count(
            lcconn, "key_events",
            " WHERE substr(event_utc, 1, 7) = '2026-10'")
        oct_win = dk.lifecycle_trace(kb["api_key"], W)
        oct_def = dk.lifecycle_trace(kb["api_key"])
        lone_win = dk.lifecycle_trace(ke["api_key"], W)
        lone_def = dk.lifecycle_trace(ke["api_key"])

        s_oct_win = snap(oct_win)
        s_oct_def = snap(oct_def)
        s_lone_win = snap(lone_win)
        s_lone_def = snap(lone_def)
        t_oct_win_pre = trail_of(oct_win)

        # manual SQL cross: the windowed trail == the ascending
        # record-time window slice of the key's own rows
        sql_rows = lcconn.execute(
            "SELECT event_id, event, pair_key_id, event_utc"
            " FROM key_events WHERE key_id = ?"
            " AND substr(event_utc, 1, 7) = ?"
            " ORDER BY event_utc, event_id",
            (id_b, W)).fetchall()
        manual = [{"event_id": r[0], "event": r[1],
                   "pair_key_id": r[2], "event_utc": r[3]}
                  for r in sql_rows]
        shapes_ok = all(sorted(e.keys()) == EVENT_KEYS
                        for env in (oct_win, oct_def, lone_win,
                                    lone_def)
                        for e in env["events"])
        brief = lambda env: [(e["event"], e["pair_key_id"])
                             for e in env["events"]]
        # lone-e default-vs-window: the window key is additive
        # only (trail + status + total identical)
        lone_def_keys_ok = (sorted(lone_def.keys()) == TRACE_KEYS
                            and lone_def["events"]
                            == lone_win["events"]
                            and lone_def["status"]
                            == lone_win["status"]
                            and lone_def["total"]
                            == lone_win["total"])
        trw8 = (
            W == "2026-10" and e_oct_b == 1 and e_oct_all == 3
            and sorted(oct_win.keys()) == WIN_KEYS
            and len(WIN_KEYS) == 11 and oct_win["window"] == W
            and sorted(oct_def.keys()) == TRACE_KEYS
            and len(TRACE_KEYS) == 10
            and oct_win["api_key"] == kb["api_key"]
            and oct_win["dev_account"] == ACCT
            and oct_win["key_name"] == "chain-b"
            and oct_win["key_id"] == id_b
            and oct_win["disclaimer"] == DISCLAIMER
            and oct_win["total"] == 1 and oct_def["total"] == 1
            and oct_win["events"] == manual
            and oct_def["events"] == manual
            and shapes_ok and len(EVENT_KEYS) == 4
            and brief(oct_win) == [("rotate_in", id_a)]
            and oct_win["status"] == "active"
            and oct_win["rotated_from_key_id"] == id_a
            and oct_win["rotated_to_key_id"] is None
            and brief(lone_win) == [("revoke", None)]
            and lone_win["status"] == "revoked"
            and lone_win["total"] == 1
            and lone_def_keys_ok)
        record("AC-TRW8", trw8,
               "October anchor: chain-b one real rotate_in row"
               " record-time W=%s (SQL window count==%d, whole-db"
               " oct rows==%d), windowed envelope 11 keys /"
               " default 10 keys pinned, windowed trail == manual"
               " SQL ascending window slice=%s, chain-b"
               " status=active pairs=(from %s, to None), lone-e"
               " terminal [revoke] status=revoked, event rows 4"
               " keys=%s, lone-e default==window (additive key"
               " only)=%s"
               % (W, e_oct_b, e_oct_all,
                  oct_win["events"] == manual, id_a, shapes_ok,
                  lone_def_keys_ok))

        # -- AC-TRW9 restart replay: windowed envelope ----------
        conn.close()
        lcconn.close()
        rjconn.close()
        _close_stack(dk, metered, led)
        led2, metered2, dk2 = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)
        rjconn = sqlite3.connect(rj_path)

        replay = snap(dk2.lifecycle_trace(kb["api_key"], W))
        replay2 = snap(dk2.lifecycle_trace(kb["api_key"], W))
        trw9 = (replay == s_oct_win and replay2 == s_oct_win)
        record("AC-TRW9", trw9,
               "full stack close (reverse order) -> reopen same"
               " db/config: October windowed envelope"
               " byte-identical to the pre-close snapshot=%s,"
               " second same-param read self-identical=%s"
               % (replay == s_oct_win, replay2 == s_oct_win))

        # -- AC-TRW10 default + lone-e replay (clock unmoved) ---
        r_oct_def = snap(dk2.lifecycle_trace(kb["api_key"]))
        r_lone_win = snap(dk2.lifecycle_trace(ke["api_key"], W))
        r_lone_def = snap(dk2.lifecycle_trace(ke["api_key"]))
        trw10 = (r_oct_def == s_oct_def
                 and r_lone_win == s_lone_win
                 and r_lone_def == s_lone_def)
        record("AC-TRW10", trw10,
               "default full-trail read replayed byte-identical"
               "=%s (10 keys, 1 row), lone-e windowed=%s (11"
               " keys), lone-e default=%s (10 keys) -- the"
               " derived face carries zero in-memory state"
               " across the restart"
               % (r_oct_def == s_oct_def,
                  r_lone_win == s_lone_win,
                  r_lone_def == s_lone_def))

        # -- AC-TRW11 November rotation on the pinned key -----
        clock.advance(23 * 86400)
        kc = dk2.rotate_key(kb["api_key"], "chain-c")
        id_c = key_id_of(kc["api_key"])
        nov_b = _count(
            lcconn, "key_events",
            " WHERE substr(event_utc, 1, 7) = '2026-11'"
            " AND key_id = ?", (id_b,))
        nov_c = _count(
            lcconn, "key_events",
            " WHERE substr(event_utc, 1, 7) = '2026-11'"
            " AND key_id = ?", (id_c,))
        r_def_nov = json.loads(
            snap(dk2.lifecycle_trace(kb["api_key"])))
        r_nov_win = json.loads(
            snap(dk2.lifecycle_trace(kb["api_key"], NEW_WIN)))
        trw11 = (
            nov_b == 1 and nov_c == 1
            and snap(r_def_nov) != s_oct_def
            and r_def_nov["total"] == 2
            and [(e["event"], e["pair_key_id"])
                 for e in r_def_nov["events"]]
            == [("rotate_in", id_a), ("rotate_out", id_c)]
            and r_def_nov["status"] == "rotated_out"
            and r_def_nov["rotated_from_key_id"] == id_a
            and r_def_nov["rotated_to_key_id"] == id_c
            and r_nov_win["window"] == NEW_WIN
            and r_nov_win["total"] == 1
            and [(e["event"], e["pair_key_id"])
                 for e in r_nov_win["events"]]
            == [("rotate_out", id_c)]
            and all(e["event_utc"][:7] == NEW_WIN
                    for e in r_nov_win["events"])
            and r_nov_win["status"] == "rotated_out"
            and r_nov_win["rotated_to_key_id"] == id_c)
        record("AC-TRW11", trw11,
               "frozen clock +23d -> one November rotation on"
               " chain-b (the very key the October windowed read"
               " pins) via the real product path (same-"
               " transaction same-stamp pair: chain-b rotate_out"
               " + chain-c rotate_in, record-time 2026-11 SQL"
               " count==%d/%d): default full-trail read"
               " recalculated (total 1->%s, byte-differs from"
               " the pre-close default snapshot=%s = zero cache,"
               " status active->%s, rotated_to None->%s),"
               " November windowed read carries the new"
               " rotate_out row exactly"
               % (nov_b, nov_c, r_def_nov["total"],
                  snap(r_def_nov) != s_oct_def,
                  r_def_nov["status"], id_c))

        # -- AC-TRW12 old-window zero permeation ------------------
        p_oct_win = json.loads(
            snap(dk2.lifecycle_trace(kb["api_key"], W)))
        p_lone_win = snap(dk2.lifecycle_trace(ke["api_key"], W))
        # closed-chain probes: both keys are terminal now, the
        # double revoke must reject E_AD_ALREADY with zero new
        # rows (the mechanical guarantee behind the freeze)
        probe_ok = True
        ev_pre_probe = _count(lcconn, "key_events")
        for probe in (kb["api_key"], ke["api_key"]):
            try:
                dk2.revoke_key(probe)
                probe_ok = False
            except D.ApiDevError as exc:
                if exc.code != D.E_AD_ALREADY:
                    probe_ok = False
        ev_post_probe = _count(lcconn, "key_events")
        b_all = _count(lcconn, "key_events",
                       " WHERE key_id = ?", (id_b,))
        b_oct = _count(
            lcconn, "key_events",
            " WHERE key_id = ? AND substr(event_utc, 1, 7)"
            " = '2026-10'", (id_b,))
        b_nov = _count(
            lcconn, "key_events",
            " WHERE key_id = ? AND substr(event_utc, 1, 7)"
            " = '2026-11'", (id_b,))
        all_rows = _count(lcconn, "key_events")
        all_oct = _count(
            lcconn, "key_events",
            " WHERE substr(event_utc, 1, 7) = '2026-10'")
        all_nov = _count(
            lcconn, "key_events",
            " WHERE substr(event_utc, 1, 7) = '2026-11'")
        fact_shift_ok = (
            p_oct_win["status"] == "rotated_out"
            and p_oct_win["rotated_from_key_id"] == id_a
            and p_oct_win["rotated_to_key_id"] == id_c)
        trw12 = (
            trail_of(p_oct_win) == t_oct_win_pre
            and p_oct_win["total"] == 1
            and [(e["event"], e["pair_key_id"])
                 for e in p_oct_win["events"]]
            == [("rotate_in", id_a)]
            and p_lone_win == s_lone_win
            and fact_shift_ok and probe_ok
            and ev_post_probe == ev_pre_probe
            and b_all == 2 and b_oct == 1 and b_nov == 1
            and b_oct + b_nov == b_all
            and all_rows == 5 and all_oct == 3 and all_nov == 2
            and all_oct + all_nov == all_rows)
        record("AC-TRW12", trw12,
               "after the November injection on the same pinned"
               " key: October windowed read TRAIL block"
               " byte-frozen=%s (events/total/window echo + five"
               " static fields; key_events rows are record-time"
               " immutable), the three full-derived key facts"
               " re-derived to their designed values=%s (the"
               " R1875 window-lens law, honest note), lone-e"
               " October windowed read FULL-envelope"
               " byte-frozen=%s (terminal key), closed-chain"
               " double-revoke probes both E_AD_ALREADY with"
               " zero new rows=%s, telescoping chain-b all-time"
               " %d == oct %d + nov %d, whole-db %d == %d + %d"
               " immutable rows never lost"
               % (trail_of(p_oct_win) == t_oct_win_pre,
                  fact_shift_ok, p_lone_win == s_lone_win,
                  probe_ok, b_all, b_oct, b_nov,
                  all_rows, all_oct, all_nov))

        # -- AC-TRW13 third-instance sequential reads ------------
        f2_a = snap(dk2.lifecycle_trace(kb["api_key"], W))
        f2_b = snap(dk2.lifecycle_trace(kb["api_key"]))
        f2_c = snap(dk2.lifecycle_trace(kb["api_key"], NEW_WIN))
        f2_d = snap(dk2.lifecycle_trace(ke["api_key"], W))
        conn.close()
        lcconn.close()
        rjconn.close()
        _close_stack(dk2, metered2, led2)
        led3, metered3, dk3 = _open_stack(db_path, cfg)
        f3_a = json.loads(
            snap(dk3.lifecycle_trace(kb["api_key"], W)))
        f3_b = json.loads(
            snap(dk3.lifecycle_trace(kb["api_key"])))
        f3_c = json.loads(
            snap(dk3.lifecycle_trace(kb["api_key"], NEW_WIN)))
        f3_d = json.loads(snap(dk3.lifecycle_trace(ke["api_key"],
                                                  W)))
        trw13 = (snap(f3_a) == f2_a and snap(f3_b) == f2_b
                 and snap(f3_c) == f2_c and snap(f3_d) == f2_d
                 and trail_of(f3_a) == t_oct_win_pre)
        record("AC-TRW13", trw13,
               "third instance on the same db: all four"
               " post-injection reads byte-identical to the"
               " second instance (%s/%s/%s/%s), and the October"
               " windowed read's TRAIL block still equals the"
               " ORIGINAL pre-close trail=%s (windowed read"
               " survives restart x new-data unscratched at the"
               " trail level)"
               % (snap(f3_a) == f2_a, snap(f3_b) == f2_b,
                  snap(f3_c) == f2_c, snap(f3_d) == f2_d,
                  trail_of(f3_a) == t_oct_win_pre))

        # -- AC-TRW14 pure-read law + hygiene -------------------
        conn = sqlite3.connect(db_path)
        lcconn = sqlite3.connect(lc_path)
        rjconn = sqlite3.connect(rj_path)
        calls_before = _count(conn, "api_calls")
        keys_before = _count(conn, "api_dev_keys")
        ev_before = _count(lcconn, "key_events")
        rj_before = _count(rjconn, "reject_events")
        for w in (None, W, NEW_WIN, "2030-01"):
            dk3.lifecycle_trace(kb["api_key"], w)
            dk3.lifecycle_trace(ke["api_key"], w)
        bad_ok = True
        for bad in ("2026-13", "2026", 2026):
            try:
                dk3.lifecycle_trace(kb["api_key"], bad)
                bad_ok = False
            except D.ApiDevError as exc:
                if exc.code != D.E_AD_BAD_ARGS:
                    bad_ok = False
        unknown_gate = False
        try:
            dk3.lifecycle_trace("sk-nonexistent", W)
        except D.ApiDevError as exc:
            unknown_gate = exc.code == D.E_AD_UNKNOWN_KEY
        calls_after = _count(conn, "api_calls")
        keys_after = _count(conn, "api_dev_keys")
        ev_after = _count(lcconn, "key_events")
        rj_after = _count(rjconn, "reject_events")

        source = product_pre.decode("ascii")
        idx = source.find("def lifecycle_trace")
        seg_end = source.find("    def ", idx + 20)
        trace_seg = source[idx:seg_end]
        # strip docstrings and comments before the write-keyword
        # scan (the R1888 AC-LG7 code-strip precedent)
        code_seg = re.sub(r'"""[\s\S]*?"""', '""', trace_seg)
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
        runner_path = os.path.join(
            os.path.dirname(BASE), "reconcile_all.py")
        with open(runner_path, encoding="utf-8") as handle:
            runner_src = handle.read()
        row_wired = ("ledger-apidev-lifecycletracepersist"
                     in runner_src)
        trw14 = (calls_after == calls_before
                 and keys_after == keys_before
                 and ev_after == ev_before
                 and rj_after == rj_before
                 and bad_ok and unknown_gate
                 and len(write_kw) == 0
                 and product_post == product_pre
                 and product_pre_sha == product_post_sha
                 and cfg_bytes_end == cfg_bytes
                 and me_ascii and len(imports_net) == 0
                 and len(mine_net) == 0 and row_wired)
        record("AC-TRW14", trw14,
               "pure read: 8-form read battery across both keys"
               " plus bad-window x3 and unknown-key gate probes"
               " (bad_ok=%s, unknown fired=%s) moves zero rows"
               " (api_calls %d==%d, api_dev_keys %d==%d,"
               " key_events %d==%d, reject_events %d==%d),"
               " lifecycle_trace segment zero write keywords=%d,"
               " apidev.py sha256 stable=%s, config.json"
               " byte-stable=%s, sources pure-ASCII=%s, network"
               " imports 0/0=%s, runner row wired=%s"
               % (bad_ok, unknown_gate, calls_after, calls_before,
                  keys_after, keys_before, ev_after, ev_before,
                  rj_after, rj_before, len(write_kw),
                  product_pre_sha == product_post_sha,
                  cfg_bytes_end == cfg_bytes, me_ascii,
                  len(imports_net) == 0 and len(mine_net) == 0,
                  row_wired))

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
    print("SUITE apidev-lifecycletracepersist: %d/%d criteria"
          " pass" % (passed, total), flush=True)
    print("clock restore probe: %s" % restored, flush=True)
    return 0 if (passed == total and total == 7
                 and restored) else 1


if __name__ == "__main__":
    sys.exit(main())
