"""Acceptance suite for the event-ticket session/check-in
board read-face family cross-restart persistence example window
(BigDomain R1930; canon = the tech-queue "eventtickets
session/check-in board read-face family cross-restart
persistence" row, the R1771/R1926 seed, claimed from the
tech-lane FIFO head). Asserts the pre-registered criteria
AC-SBP1..AC-SBP7 from the R1930 claim note (criteria were
registered in state/queue/tech.md before this code ran; honesty
law). Each criterion prints PASS/FAIL with evidence; the process
exits non-zero on any FAIL.

Covered semantics: the derived purity of the three session/read
faces -- session_board (per-session purchase audit trail),
attendees (per-session admission audit) and active_sessions
(schedule-window listing) -- across an instance restart. The
two-piece stack (Ledger -> EventTicketFace) closes fully in
reverse dependency order and reopens on the same db path and
config bytes; the ten pre-close board reads must replay
byte-identical from the fresh instance (zero in-memory drift in
the derived faces); a November purchase + check-in on the live
gala session plus a fresh newmo session registration via the
real product path must recalculate the touched boards (zero
cache) while every untouched board and every non-covering
schedule window stays byte-frozen (record-time / row-id
immutability); a third instance replays the post-injection
state byte-identically (two-instance sequential reads). Every
world row rides the real product path (register_session /
buy_ticket / admit) under a frozen clock - zero fixture
injection. Pure-read law and fail-closed negative probes are
asserted on the third instance. This test source stays pure
ASCII per the encoding discipline.

Usage: python test_eventtickets_sessionpersist.py
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
import eventtickets as T                # noqa: E402 (face under test)

RESULTS = []
EXPECTED = 7

DISCLAIMER = ("sandbox stand-in disclaimer: virtual event tickets"
             " grant admission only, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 15, 10, 0, 0)

# exact envelope contracts (the R1771 pin lists, reused
# verbatim: this suite adds zero keys to any read face)
SB_KEYS = sorted(["session_id", "disclaimer", "purchases"])
SB_ROW_KEYS = {"purchase_id", "buyer_id", "price_paid", "spend_tx",
               "purchase_window", "purchased_utc"}
AT_KEYS = sorted(["session_id", "disclaimer", "checkins"])
AT_ROW_KEYS = {"checkin_id", "account_id", "at_window",
               "checked_utc"}
AS_KEYS = sorted(["at_window", "disclaimer", "sessions"])
AS_ROW_KEYS = {"session_id", "session_key", "title", "start_window",
               "end_window", "ticket_price", "ai_label"}

# schedule probe windows (anchor world)
W_START_EDGE = 0       # gala start edge, inclusive
W_GALA = 15            # gala interior
W_BAND = 31            # empty band between gala (<=30) and meet (>=40)
W_MEET = 45            # meet interior
W_EMPTY = 200          # honest empty (late is 100..120)
W_NEWMO = 215          # post-injection newmo interior (210..230)


class _FrozenClock(object):
    """Deterministic UTC clock holder: _now_utc is patched onto
    the eventtickets module so every registration, purchase and
    check-in stamp moves only when the suite advances the
    clock."""

    def __init__(self):
        self.dt = BASE_DT

    def now_utc(self):
        return self.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds):
        self.dt = self.dt + datetime.timedelta(seconds=seconds)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def snap(env):
    return json.dumps(env, sort_keys=True)


def _count(conn, table, extra="", args=()):
    return int(conn.execute(
        "SELECT COUNT(*) FROM " + table + extra,
        tuple(args)).fetchone()[0])


def _open_stack(db_path, cfg):
    led = L.Ledger(db_path, cfg)
    face = T.EventTicketFace(led, DISCLAIMER)
    return led, face


def _close_stack(face, led):
    face.close()
    led.close()


def _manual_purchases(conn, sid):
    rows = conn.execute(
        "SELECT purchase_id, buyer_id, price_paid, spend_tx,"
        " purchase_window, purchased_utc FROM ticket_purchases"
        " WHERE session_id = ? ORDER BY purchase_id",
        (sid,)).fetchall()
    return [{"purchase_id": int(r[0]), "buyer_id": r[1],
             "price_paid": int(r[2]), "spend_tx": r[3],
             "purchase_window": int(r[4]),
             "purchased_utc": r[5]} for r in rows]


def _manual_checkins(conn, sid):
    rows = conn.execute(
        "SELECT checkin_id, account_id, at_window, checked_utc"
        " FROM ticket_checkins WHERE session_id = ?"
        " ORDER BY checkin_id", (sid,)).fetchall()
    return [{"checkin_id": int(r[0]), "account_id": r[1],
             "at_window": int(r[2]), "checked_utc": r[3]}
            for r in rows]


def _manual_active(conn, at_window):
    rows = conn.execute(
        "SELECT session_id, session_key, title, start_window,"
        " end_window, ticket_price, ai_label FROM"
        " ticket_sessions WHERE start_window <= ?"
        " AND end_window >= ? ORDER BY session_id",
        (at_window, at_window)).fetchall()
    return [{"session_id": int(r[0]), "session_key": r[1],
             "title": r[2], "start_window": int(r[3]),
             "end_window": int(r[4]), "ticket_price": int(r[5]),
             "ai_label": int(r[6])} for r in rows]


def _board_ok(env, keys, row_keys, row_field, manual):
    if sorted(env.keys()) != keys:
        return False
    if env["disclaimer"] != DISCLAIMER:
        return False
    rows = env[row_field]
    if not isinstance(rows, list):
        return False
    for r in rows:
        if set(r.keys()) != row_keys:
            return False
    return rows == manual


def main():
    tmp = tempfile.mkdtemp(prefix="eventtickets-sp-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    product_path = os.path.join(BASE, "eventtickets.py")
    with open(product_path, "rb") as handle:
        product_pre = handle.read()
    product_pre_sha = hashlib.sha256(product_pre).hexdigest()

    clock = _FrozenClock()
    real_now = T._now_utc

    T._now_utc = clock.now_utc

    try:
        led, face = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)

        # -- October anchor world (every row on the real product
        #    path under the frozen clock; zero injection) ------
        led.mint_to_pool("pool:reserve", 2000, "MINT-SBP",
                         "settlement")
        for who in ("alice", "bob", "dave"):
            led.ensure_account("usr:" + who,
                               census_avatar_id=who)
            led.adjust([("pool:reserve", "debit", 100),
                        ("usr:" + who, "credit", 100)],
                       "manual:fund-" + who,
                       "suite funding " + who)

        s_gala = face.register_session(
            "gala", "Gala Night", 0, 30, 5, 2, False)
        clock.advance(3)
        s_meet = face.register_session(
            "meet", "Meet Live", 40, 60, 3, 1, True)
        clock.advance(3)
        s_late = face.register_session(
            "late", "Late Session", 100, 120, 2, 1, False)
        clock.advance(3)

        sid_gala = s_gala["session_id"]
        sid_meet = s_meet["session_id"]
        sid_late = s_late["session_id"]

        face.buy_ticket("usr:alice", sid_gala, 10, "order:sbp-a1")
        clock.advance(7)
        face.buy_ticket("usr:alice", sid_gala, 12, "order:sbp-a2")
        clock.advance(7)
        face.buy_ticket("usr:bob", sid_gala, 11, "order:sbp-a3")
        clock.advance(7)
        face.buy_ticket("usr:bob", sid_meet, 45, "order:sbp-m1")
        clock.advance(7)
        face.admit("usr:alice", sid_gala, 12)
        clock.advance(7)

        anchor_counts = (_count(conn, "ticket_sessions"),
                         _count(conn, "ticket_purchases"),
                         _count(conn, "ticket_checkins"))

        # -- pre-close ten-read snapshot set --------------------
        sb_gala_pre = snap(face.session_board(sid_gala))
        sb_meet_pre = snap(face.session_board(sid_meet))
        sb_late_pre = snap(face.session_board(sid_late))
        at_gala_pre = snap(face.attendees(sid_gala))
        at_meet_pre = snap(face.attendees(sid_meet))
        as_edge_pre = snap(face.active_sessions(W_START_EDGE))
        as_gala_pre = snap(face.active_sessions(W_GALA))
        as_band_pre = snap(face.active_sessions(W_BAND))
        as_meet_pre = snap(face.active_sessions(W_MEET))
        as_empty_pre = snap(face.active_sessions(W_EMPTY))

        sbp1 = (
            anchor_counts == (3, 4, 1)
            and _board_ok(json.loads(sb_gala_pre), SB_KEYS,
                          SB_ROW_KEYS, "purchases",
                          _manual_purchases(conn, sid_gala))
            and _board_ok(json.loads(sb_meet_pre), SB_KEYS,
                          SB_ROW_KEYS, "purchases",
                          _manual_purchases(conn, sid_meet))
            and _board_ok(json.loads(sb_late_pre), SB_KEYS,
                          SB_ROW_KEYS, "purchases",
                          _manual_purchases(conn, sid_late))
            and _board_ok(json.loads(at_gala_pre), AT_KEYS,
                          AT_ROW_KEYS, "checkins",
                          _manual_checkins(conn, sid_gala))
            and _board_ok(json.loads(at_meet_pre), AT_KEYS,
                          AT_ROW_KEYS, "checkins",
                          _manual_checkins(conn, sid_meet))
            and _board_ok(json.loads(as_edge_pre), AS_KEYS,
                          AS_ROW_KEYS, "sessions",
                          _manual_active(conn, W_START_EDGE))
            and _board_ok(json.loads(as_gala_pre), AS_KEYS,
                          AS_ROW_KEYS, "sessions",
                          _manual_active(conn, W_GALA))
            and _board_ok(json.loads(as_band_pre), AS_KEYS,
                          AS_ROW_KEYS, "sessions",
                          _manual_active(conn, W_BAND))
            and _board_ok(json.loads(as_meet_pre), AS_KEYS,
                          AS_ROW_KEYS, "sessions",
                          _manual_active(conn, W_MEET))
            and _board_ok(json.loads(as_empty_pre), AS_KEYS,
                          AS_ROW_KEYS, "sessions",
                          _manual_active(conn, W_EMPTY))
            and json.loads(sb_gala_pre)["purchases"][0]["buyer_id"]
            == "usr:alice"
            and len(json.loads(sb_gala_pre)["purchases"]) == 3
            and len(json.loads(at_gala_pre)["checkins"]) == 1
            and [r["session_key"] for r in
                 json.loads(as_meet_pre)["sessions"]] == ["meet"]
            and json.loads(as_empty_pre)["sessions"] == []
            and json.loads(as_band_pre)["sessions"] == [])
        record("AC-SBP1", sbp1,
               "October anchor: 3 sessions + 4 real purchases + 1"
               " real check-in on the product path (counts"
               " sessions/purchases/checkins = %s); ten pre-close"
               " board reads pinned - session_board x3 (gala 3"
               " rows, meet 1, late honest-empty), attendees x2"
               " (gala 1 row, meet honest-empty), active_sessions"
               " x5 probe windows (%d edge-incl, %d gala, %d"
               " empty band, %d meet, %d honest empty); every"
               " board == manual SQL cross-derivation with exact"
               " key sets and resident disclaimer"
               % (anchor_counts, W_START_EDGE, W_GALA, W_BAND,
                  W_MEET, W_EMPTY))

        # -- AC-SBP2 cross-restart ten-read replay ----------------
        conn.close()
        _close_stack(face, led)
        led2, face2 = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)

        r_sb_gala = snap(face2.session_board(sid_gala))
        r_sb_gala2 = snap(face2.session_board(sid_gala))
        r_sb_meet = snap(face2.session_board(sid_meet))
        r_sb_late = snap(face2.session_board(sid_late))
        r_at_gala = snap(face2.attendees(sid_gala))
        r_at_meet = snap(face2.attendees(sid_meet))
        r_as_edge = snap(face2.active_sessions(W_START_EDGE))
        r_as_gala = snap(face2.active_sessions(W_GALA))
        r_as_band = snap(face2.active_sessions(W_BAND))
        r_as_meet = snap(face2.active_sessions(W_MEET))
        r_as_empty = snap(face2.active_sessions(W_EMPTY))
        sbp2 = (
            r_sb_gala == sb_gala_pre
            and r_sb_gala2 == sb_gala_pre
            and r_sb_meet == sb_meet_pre
            and r_sb_late == sb_late_pre
            and r_at_gala == at_gala_pre
            and r_at_meet == at_meet_pre
            and r_as_edge == as_edge_pre
            and r_as_gala == as_gala_pre
            and r_as_band == as_band_pre
            and r_as_meet == as_meet_pre
            and r_as_empty == as_empty_pre)
        record("AC-SBP2", sbp2,
               "two-piece stack close (face -> ledger, reverse"
               " dependency) -> reopen same db/config: all ten"
               " board reads byte-identical to the pre-close"
               " snapshots (session_board gala/meet/late=%s/%s/%s,"
               " attendees gala/meet=%s/%s, active_sessions 5"
               " windows=%s), second same-param read"
               " self-identical=%s - derived faces carry zero"
               " in-memory drift"
               % (r_sb_gala == sb_gala_pre,
                  r_sb_meet == sb_meet_pre,
                  r_sb_late == sb_late_pre,
                  r_at_gala == at_gala_pre,
                  r_at_meet == at_meet_pre,
                  (r_as_edge == as_edge_pre
                   and r_as_gala == as_gala_pre
                   and r_as_band == as_band_pre
                   and r_as_meet == as_meet_pre
                   and r_as_empty == as_empty_pre),
                  r_sb_gala2 == sb_gala_pre))

        # -- AC-SBP3 November real rows -> touched boards recalc --
        as_newmo_open = snap(face2.active_sessions(W_NEWMO))
        clock.advance(23 * 86400)
        s_newmo = face2.register_session(
            "newmo", "New Moon Session", 210, 230, 1, 1, True)
        clock.advance(5)
        face2.buy_ticket("usr:dave", sid_gala, 20, "order:sbp-n1")
        clock.advance(5)
        face2.admit("usr:bob", sid_gala, 20)
        sid_newmo = s_newmo["session_id"]

        sb_gala_new = json.loads(snap(face2.session_board(sid_gala)))
        at_gala_new = json.loads(snap(face2.attendees(sid_gala)))
        as_newmo_new = json.loads(
            snap(face2.active_sessions(W_NEWMO)))
        new_pur = sb_gala_new["purchases"][-1]
        new_chk = at_gala_new["checkins"][-1]
        sbp3 = (
            json.loads(as_newmo_open)["sessions"] == []
            and len(sb_gala_new["purchases"]) == 4
            and snap(sb_gala_new) != sb_gala_pre
            and len(at_gala_new["checkins"]) == 2
            and snap(at_gala_new) != at_gala_pre
            and set(new_pur.keys()) == SB_ROW_KEYS
            and new_pur["buyer_id"] == "usr:dave"
            and new_pur["price_paid"] == 5
            and new_pur["purchase_window"] == 20
            and isinstance(new_pur["spend_tx"], str)
            and new_pur["spend_tx"]
            and new_pur["purchase_id"]
            == max(r["purchase_id"]
                   for r in sb_gala_new["purchases"])
            and set(new_chk.keys()) == AT_ROW_KEYS
            and new_chk["account_id"] == "usr:bob"
            and new_chk["at_window"] == 20
            and sb_gala_new["purchases"]
            == _manual_purchases(conn, sid_gala)
            and at_gala_new["checkins"]
            == _manual_checkins(conn, sid_gala)
            and [r["session_key"] for r in
                 as_newmo_new["sessions"]] == ["newmo"]
            and as_newmo_new["sessions"]
            == _manual_active(conn, W_NEWMO)
            and as_newmo_new["sessions"][0]["ai_label"] == 1)
        record("AC-SBP3", sbp3,
               "frozen clock +23d -> 1 November purchase (dave on"
               " gala, 4th row, tail purchase_id order) + 1"
               " November check-in (bob on gala, 2nd row) + 1 new"
               " session registration (newmo 210..230) via the real"
               " product path: session_board(gala) recalculated"
               " byte-differs from the pre-close snapshot=%s"
               " (zero cache), attendees(gala) recalculated=%s,"
               " active_sessions(%d) empty-before=%s -> [newmo]"
               " recomputed with ai_label=1; new rows carry the"
               " full anchor key sets; every touched board =="
               " manual SQL"
               % (snap(sb_gala_new) != sb_gala_pre,
                  snap(at_gala_new) != at_gala_pre, W_NEWMO,
                  json.loads(as_newmo_open)["sessions"] == []))

        # -- AC-SBP4 untouched boards + non-covering windows ------
        p_sb_meet = snap(face2.session_board(sid_meet))
        p_sb_late = snap(face2.session_board(sid_late))
        p_at_meet = snap(face2.attendees(sid_meet))
        p_as_edge = snap(face2.active_sessions(W_START_EDGE))
        p_as_gala = snap(face2.active_sessions(W_GALA))
        p_as_band = snap(face2.active_sessions(W_BAND))
        p_as_meet = snap(face2.active_sessions(W_MEET))
        p_as_empty = snap(face2.active_sessions(W_EMPTY))
        tot = (_count(conn, "ticket_sessions"),
               _count(conn, "ticket_purchases"),
               _count(conn, "ticket_checkins"))
        a_s, a_p, a_c = anchor_counts
        sbp4 = (
            p_sb_meet == sb_meet_pre
            and p_sb_late == sb_late_pre
            and p_at_meet == at_meet_pre
            and p_as_edge == as_edge_pre
            and p_as_gala == as_gala_pre
            and p_as_band == as_band_pre
            and p_as_meet == as_meet_pre
            and p_as_empty == as_empty_pre
            and tot == (a_s + 1, a_p + 1, a_c + 1))
        record("AC-SBP4", sbp4,
               "after the November injection: untouched boards"
               " byte-frozen (session_board meet/late=%s/%s,"
               " attendees meet=%s, active_sessions 5 non-covering"
               " windows edge/gala/band/meet/empty all =="
               " pre-close=%s), table telescoping counts"
               " sessions %d+1==%d, purchases %d+1==%d, checkins"
               " %d+1==%d"
               % (p_sb_meet == sb_meet_pre,
                  p_sb_late == sb_late_pre,
                  p_at_meet == at_meet_pre,
                  (p_as_edge == as_edge_pre
                   and p_as_gala == as_gala_pre
                   and p_as_band == as_band_pre
                   and p_as_meet == as_meet_pre
                   and p_as_empty == as_empty_pre),
                  a_s, tot[0], a_p, tot[1], a_c, tot[2]))

        # -- AC-SBP5 two-instance sequential reads ----------------
        f2_set = (snap(face2.session_board(sid_gala)),
                  snap(face2.attendees(sid_gala)),
                  snap(face2.active_sessions(W_NEWMO)),
                  snap(face2.session_board(sid_meet)),
                  snap(face2.attendees(sid_meet)),
                  snap(face2.active_sessions(W_EMPTY)))
        conn.close()
        _close_stack(face2, led2)
        led3, face3 = _open_stack(db_path, cfg)
        f3_set = (snap(face3.session_board(sid_gala)),
                  snap(face3.attendees(sid_gala)),
                  snap(face3.active_sessions(W_NEWMO)),
                  snap(face3.session_board(sid_meet)),
                  snap(face3.attendees(sid_meet)),
                  snap(face3.active_sessions(W_EMPTY)))
        sbp5 = (
            f3_set == f2_set
            and snap(face3.session_board(sid_meet)) == sb_meet_pre
            and snap(face3.attendees(sid_meet)) == at_meet_pre
            and snap(face3.session_board(sid_late)) == sb_late_pre
            and snap(face3.active_sessions(W_EMPTY))
            == as_empty_pre)
        record("AC-SBP5", sbp5,
               "third instance on the same db: post-injection"
               " reads (touched gala boards + newmo window +"
               " untouched meet/empty boards) byte-identical to"
               " the second instance=%s, and the untouched boards"
               " still equal the original pre-close snapshots=%s"
               " (board reads survive restart x new-data"
               " unscratched)"
               % (f3_set == f2_set,
                  (snap(face3.session_board(sid_meet))
                   == sb_meet_pre
                   and snap(face3.attendees(sid_meet))
                   == at_meet_pre
                   and snap(face3.session_board(sid_late))
                   == sb_late_pre
                   and snap(face3.active_sessions(W_EMPTY))
                   == as_empty_pre)))

        # -- AC-SBP6 pure-read law + fail-closed probes -----------
        conn = sqlite3.connect(db_path)
        c0 = (_count(conn, "ticket_sessions"),
              _count(conn, "ticket_purchases"),
              _count(conn, "ticket_checkins"))
        for sid in (sid_gala, sid_meet, sid_late, sid_newmo):
            face3.session_board(sid)
            face3.attendees(sid)
        for w in (W_START_EDGE, W_GALA, W_BAND, W_MEET, W_EMPTY,
                  W_NEWMO):
            face3.active_sessions(w)
        codes = []
        for fn, args in ((face3.session_board, (999999,)),
                         (face3.attendees, (999999,)),
                         (face3.active_sessions, (-1,))):
            try:
                fn(*args)
                codes.append("NO-RAISE")
            except T.TicketError as exc:
                codes.append(exc.code)
        c1 = (_count(conn, "ticket_sessions"),
              _count(conn, "ticket_purchases"),
              _count(conn, "ticket_checkins"))
        sbp6 = (
            c0 == c1 == (4, 5, 2)
            and codes == [T.E_ET_UNKNOWN_SESSION,
                          T.E_ET_UNKNOWN_SESSION,
                          T.E_ET_BAD_ARGS])
        record("AC-SBP6", sbp6,
               "pure read: 10-form read battery (4 sessions x"
               " session_board+attendees + 6 active_sessions"
               " windows) on the third face moves zero rows"
               " (sessions/purchases/checkins %s == %s == 4/5/2),"
               " fail-closed negative probes across restart:"
               " session_board(unknown)=%s, attendees(unknown)=%s,"
               " active_sessions(-1)=%s"
               % (c0, c1, codes[0], codes[1], codes[2]))

        # -- AC-SBP7 hygiene --------------------------------------
        source = product_pre.decode("ascii")
        write_kw_total = 0
        for fname in ("session_board", "attendees",
                      "active_sessions"):
            idx = source.find("def " + fname)
            seg_end = source.find("    def ", idx + 20)
            if seg_end == -1:
                seg_end = len(source)
            seg = source[idx:seg_end]
            code_seg = re.sub(r'"""[\s\S]*?"""', '""', seg)
            code_seg = "\n".join(re.sub(r"#.*$", "", line)
                                for line in code_seg.splitlines())
            write_kw_total += len(re.findall(
                r"\b(INSERT|UPDATE|DELETE|REPLACE|CREATE)\b",
                code_seg))
        with open(product_path, "rb") as handle:
            product_post = handle.read()
        product_post_sha = hashlib.sha256(product_post).hexdigest()
        with open(os.path.join(BASE, "config.json"), "rb") as handle:
            cfg_bytes_end = handle.read()
        with open(os.path.abspath(__file__), "rb") as handle:
            me_bytes = handle.read()
        me_ascii = all(b < 128 for b in me_bytes)
        net_pat = re.compile(r"urllib|requests|socket|http")
        imports_net = [
            line for line in source.splitlines()
            if re.match(r"\s*(?:import|from)\s", line)
            and net_pat.search(line)]
        mine_net = [
            line for line in me_bytes.decode("ascii").splitlines()
            if re.match(r"\s*(?:import|from)\s", line)
            and net_pat.search(line)]
        runner_path = os.path.join(
            os.path.dirname(BASE), "reconcile_all.py")
        with open(runner_path, encoding="utf-8") as handle:
            runner_src = handle.read()
        sbp7 = (
            write_kw_total == 0
            and product_post == product_pre
            and product_pre_sha == product_post_sha
            and cfg_bytes_end == cfg_bytes
            and me_ascii and len(imports_net) == 0
            and len(mine_net) == 0
            and "ledger-eventtickets-sessionpersist"
            in runner_src
            and len(RESULTS) + 1 == EXPECTED)
        record("AC-SBP7", sbp7,
               "three read-face segments zero write keywords=%d,"
               " eventtickets.py sha256 stable=%s, config.json"
               " byte-stable=%s, sources pure-ASCII=%s, network"
               " imports 0/0=%s, reconcile_all SUITES row"
               " 'ledger-eventtickets-sessionpersist' registered,"
               " criteria drift self-check %d/%d"
               % (write_kw_total,
                  product_pre_sha == product_post_sha,
                  cfg_bytes_end == cfg_bytes, me_ascii,
                  len(imports_net) == 0 and len(mine_net) == 0,
                  len(RESULTS) + 1, EXPECTED))

        conn.close()
        _close_stack(face3, led3)

    finally:
        T._now_utc = real_now

    restored = T._now_utc is real_now
    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE eventtickets-sessionpersist: %d/%d criteria pass"
          % (passed, total), flush=True)
    print("clock restore probe: %s" % restored, flush=True)
    return 0 if (passed == total and total == EXPECTED
                 and restored) else 1


if __name__ == "__main__":
    sys.exit(main())
