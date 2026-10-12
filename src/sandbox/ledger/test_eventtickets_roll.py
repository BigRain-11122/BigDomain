"""Acceptance suite for the event-ticket audit-board cross-month
month-roll fidelity example (BigDomain R1862 tech-queue claim
row; seed = the R1826 window parameterization + the R1840
read-cap parameterization - the month-roll example family
R1730/R1738/R1739/R1839/R1845/R1854/R1858 had no eventtickets
seat). Asserts the pre-registered criteria AC-ETR1..AC-ETR7
from the R1862 tech.md claim line (criteria were registered
before this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any
FAIL.

Carrier verdict (the R1845 devboard_roll / R1858 callroll
dedicated-suite precedent): the existing
test_eventtickets_boardwin suite world pins historical months
through fixture injection, so a true month roll rides this
dedicated suite - a fresh isolated face instance in its own
temp world with the eventtickets module clock frozen
(T._now_utc patched onto a deterministic holder, restored in
finally; the R1678/R1858 frozen-clock precedent).

World (all stamps ride the frozen clock, the live product
write path - zero fixture injection for the roll scenario):
BASE_DT 2026-10-15; sessions et-roll-a (price 30) and
et-roll-b (price 25), tick windows 10..900 so purchases stay
legal on both sides of the roll. October phase: 3 purchases
(a: alice + bob, b: carol) + 1 check-in (alice). The clock
advances +23d across the month boundary; November phase: 2
new purchases (a: carol + dave) + 2 new check-ins (dave with
his November purchase, bob carrying his October purchase
across the roll - the cross-month check-in anchor). Every
window slices rows by their own record-time stamp
(purchased_utc / checked_utc), and the windowed no_show stays
the end-of-window snapshot (the AC-EAW4 law). Zero product
bytes change: the roll semantics already live in the board,
this suite only pins them.

This test source stays pure ASCII per the encoding
discipline.

Usage: python test_eventtickets_roll.py
"""

import ast
import datetime
import hashlib
import inspect
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
import eventtickets as T                # noqa: E402 (R1767 face)

RESULTS = []
EXPECTED = 7

DISCLAIMER = ("sandbox stand-in disclaimer: virtual event tickets"
             " grant admission only, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 15, 10, 0, 0)
OLD_WIN = "2026-10"
NEW_WIN = "2026-11"
FROZEN_OLD = BASE_DT.strftime("%Y-%m-%dT%H:%M:%SZ")
FROZEN_NEW = (BASE_DT +
              datetime.timedelta(days=23)).strftime("%Y-%m-%dT%H:%M:%SZ")

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")

WRITE_STMT_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|CREATE|DROP)\b")


class _FrozenClock(object):
    """Deterministic UTC clock holder: the eventtickets module
    _now_utc is patched onto this holder so session/purchase/
    check-in stamps roll only when the suite moves the clock."""

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


def _row(board_env, key):
    for row in board_env["event_audit_board"]:
        if row["session_key"] == key:
            return row
    return None


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " +
                        table).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="eventtickets-roll-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg_sha = hashlib.sha256(cfg_bytes).hexdigest()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(BASE, "eventtickets.py"), "rb") as handle:
        face_bytes = handle.read()
    face_sha = hashlib.sha256(face_bytes).hexdigest()
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    tf = T.EventTicketFace(led, DISCLAIMER)
    conn = sqlite3.connect(db_path)

    clock = _FrozenClock()
    orig_now = T._now_utc
    T._now_utc = clock.now_utc
    try:
        # ---- world build: sessions, funding ------------------------------
        sa = tf.register_session("et-roll-a", "Roll Gala A", 10, 900,
                                 30, 1, True)
        sb = tf.register_session("et-roll-b", "Roll Gala B", 10, 900,
                                 25, 1, False)
        sid_a = sa["session_id"]
        sid_b = sb["session_id"]
        led.mint_to_pool("pool:reserve", 2000, "SETUP-ETR-A",
                         "settlement")
        for who in ("alice", "bob", "carol", "dave"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
            led.adjust([("pool:reserve", "debit", 100),
                        ("usr:" + who, "credit", 100)],
                       "manual:fund-" + who,
                       "roll suite funding " + who)

        # ---- October phase (frozen 2026-10-15) ---------------------------
        tf.buy_ticket("usr:alice", sid_a, 100, "oct-a1")
        tf.buy_ticket("usr:bob", sid_a, 100, "oct-b1")
        tf.buy_ticket("usr:carol", sid_b, 100, "oct-c1")
        tf.admit("usr:alice", sid_a, 120)

        # pre-roll snapshots (four faces)
        oct_pre = tf.event_audit_board(window=OLD_WIN)
        default_pre = tf.event_audit_board()
        counts_pre = {"sessions": _count(conn, "ticket_sessions"),
                      "purchases": _count(conn, "ticket_purchases"),
                      "checkins": _count(conn, "ticket_checkins")}
        purch_ids_pre = set(
            r["purchase_id"] for s in (sid_a, sid_b)
            for r in tf.session_board(s)["purchases"])
        check_ids_pre = set(
            r["checkin_id"] for s in (sid_a, sid_b)
            for r in tf.attendees(s)["checkins"])
        view_a_pre = tf.session_view(sid_a)
        view_b_pre = tf.session_view(sid_b)

        # ---- the roll: clock +23d across the month boundary --------------
        clock.advance(23 * 86400)
        frozen_new_probe = T._now_utc()

        # ---- November phase (frozen 2026-11-07, live product path) -------
        tf.buy_ticket("usr:carol", sid_a, 200, "nov-c1")
        tf.buy_ticket("usr:dave", sid_a, 200, "nov-d1")
        tf.admit("usr:dave", sid_a, 210)
        tf.admit("usr:bob", sid_a, 220)

        # ==== AC-ETR1: frozen-clock cross-month world, live path =========
        world_ok = (
            frozen_new_probe == FROZEN_NEW
            and counts_pre["sessions"] == 2
            and counts_pre["purchases"] == 3
            and counts_pre["checkins"] == 1
            and _count(conn, "ticket_purchases") == 5
            and _count(conn, "ticket_checkins") == 3
            and len(purch_ids_pre) == 3
            and len(check_ids_pre) == 1
            and view_a_pre["ticket_count"] == 2
            and view_a_pre["attendee_count"] == 1)
        record("AC-ETR1", world_ok,
               "frozen clock patched (T._now_utc=%s -> %s after +23d);"
               " oct phase 2 sessions + 3 purchases + 1 check-in via"
               " true gates (zero fixture injection); nov phase 2"
               " purchases + 2 check-ins via true gates; all stamps"
               " ride the frozen clock (purchased_utc/checked_utc"
               " pre=%s new=%s); post-roll counts purchases 3->5"
               " checkins 1->3" %
               (FROZEN_OLD, frozen_new_probe, FROZEN_OLD, FROZEN_NEW))

        # ==== AC-ETR2: new-month window landing ===========================
        b11 = tf.event_audit_board(window=NEW_WIN)
        row_a = _row(b11, "et-roll-a")
        row_b = _row(b11, "et-roll-b")
        sql_pur_new = conn.execute(
            "SELECT COUNT(*) FROM ticket_purchases"
            " WHERE substr(purchased_utc, 1, 7) = ?",
            (NEW_WIN,)).fetchone()[0]
        sql_chk_new = conn.execute(
            "SELECT COUNT(*) FROM ticket_checkins"
            " WHERE substr(checked_utc, 1, 7) = ?",
            (NEW_WIN,)).fetchone()[0]
        sql_a_sold_new = conn.execute(
            "SELECT COUNT(*) FROM ticket_purchases p,"
            " ticket_sessions s WHERE p.session_id = s.session_id"
            " AND s.session_key = ? AND substr(p.purchased_utc,"
            " 1, 7) = ?", ("et-roll-a", NEW_WIN)).fetchone()[0]
        net_flow_a = row_a["sold"] - row_a["admitted"]
        land_ok = (
            b11.get("window") == NEW_WIN
            and row_a["sold"] == 2 and row_a["admitted"] == 2
            and row_a["revenue"] == 60
            and row_b["sold"] == 0 and row_b["admitted"] == 0
            and row_b["revenue"] == 0
            and row_b["admission_rate"] == 0.0
            and sql_pur_new == 2 and sql_chk_new == 2
            and sql_a_sold_new == 2
            and row_a["no_show"] == 1 and row_b["no_show"] == 1
            and net_flow_a == 0)
        record("AC-ETR2", land_ok,
               "explicit %s board: a sold==2 admitted==2 revenue==60"
               " (both new purchases + both new check-ins land in"
               " the new-month cell); b sold==0 admitted==0"
               " revenue==0 rate==0.0 (zero-activity honest zeros);"
               " SQL third path: nov purchases==%d nov checkins==%d"
               " a-nov-sold==%d (record-time attribution, each row"
               " family on its own stamp); windowed no_show ="
               " end-of-window snapshot (a: 4-3==1, b: 1-0==1);"
               " in-window net flow %d deliberately NOT surfaced"
               " under the no_show field (AC-EAW4)" %
               (NEW_WIN, sql_pur_new, sql_chk_new, sql_a_sold_new,
                net_flow_a))

        # ==== AC-ETR3: old-month byte preservation ========================
        oct_post = tf.event_audit_board(window=OLD_WIN)
        oct_pre_txt = json.dumps(oct_pre, sort_keys=True)
        oct_post_txt = json.dumps(oct_post, sort_keys=True)
        pa = _row(oct_pre, "et-roll-a")
        pb = _row(oct_pre, "et-roll-b")
        pa_post = _row(oct_post, "et-roll-a")
        keep_ok = (
            oct_pre_txt == oct_post_txt
            and pa["sold"] == 2 and pa["admitted"] == 1
            and pa["admission_rate"] == 0.5
            and pb["sold"] == 1
            and pa_post is not None
            and pa_post["no_show"] == pa["no_show"])
        record("AC-ETR3", keep_ok,
               "post-roll explicit %s board == pre-roll october"
               " snapshot byte-identical (full envelope json.dumps"
               " compare); a sold==2 admitted==1 rate==0.5, b"
               " sold==1; november rows never leak into the october"
               " window (zero-valued nov b-row + byte compare ="
               " two-window mutual non-penetration); october"
               " no_show snapshot stays frozen under the november"
               " check-ins (checked_utc %s > %s, string-ordered,"
               " never back-flows)" %
               (OLD_WIN, NEW_WIN, OLD_WIN))

        # ==== AC-ETR4: default all-window read ===========================
        d_post = tf.event_audit_board()
        da = _row(d_post, "et-roll-a")
        db_ = _row(d_post, "et-roll-b")
        default_ok = (
            "window" not in d_post
            and da["sold"] == 4 and da["admitted"] == 3
            and da["revenue"] == 120 and da["no_show"] == 1
            and db_["sold"] == 1 and db_["revenue"] == 25
            and db_["admitted"] == 0)
        record("AC-ETR4", default_ok,
               "default window=None board after the roll: a sold==4"
               " admitted==3 revenue==120, b sold==1 revenue==25 -"
               " the cross-month rows all appear in the default"
               " read; default envelope carries no window key"
               " (AC-EAW1 byte-stability law); honest note: the"
               " eventtickets default is the ALL-window semantics,"
               " unlike the current-month-default family"
               " (apidev dev_board / freetrial calls_by_* whose"
               " default reads the clock's current month)")

        # ==== AC-ETR5: immutable rows never lost ========================
        purch_ids_post = set(
            r["purchase_id"] for s in (sid_a, sid_b)
            for r in tf.session_board(s)["purchases"])
        check_ids_post = set(
            r["checkin_id"] for s in (sid_a, sid_b)
            for r in tf.attendees(s)["checkins"])
        view_a_post = tf.session_view(sid_a)
        view_b_post = tf.session_view(sid_b)
        loss_ok = (
            _count(conn, "ticket_sessions") == 2
            and _count(conn, "ticket_purchases") == 5
            and _count(conn, "ticket_checkins") == 3
            and purch_ids_pre <= purch_ids_post
            and len(purch_ids_post - purch_ids_pre) == 2
            and check_ids_pre <= check_ids_post
            and len(check_ids_post - check_ids_pre) == 2
            and view_a_post["ticket_count"] == 4
            and view_a_post["attendee_count"] == 3
            and view_b_post["ticket_count"] == 1
            and view_b_post["attendee_count"] == 0)
        record("AC-ETR5", loss_ok,
               "three-table all-window counts across the roll:"
               " sessions 2==2 constant, purchases 3->5 (delta"
               " exactly the 2 new rows), checkins 1->3 (delta"
               " exactly the 2 new rows); every pre-roll"
               " purchase_id/checkin_id still present (session_board"
               "/attendees product faces, ID-set superset, %d new"
               " purchase ids + %d new checkin ids); session_view"
               " COUNT faces see all rows (a ticket_count 2->4,"
               " attendee_count 1->3; b ticket_count 1) - zero"
               " rows lost, zero cached counters" %
               (len(purch_ids_post - purch_ids_pre),
                len(check_ids_post - check_ids_pre)))

        # ==== AC-ETR6: read-hat x cross-month orthogonality =============
        b11_full = tf.event_audit_board(window=NEW_WIN)
        b11_l1 = tf.event_audit_board(window=NEW_WIN, limit=1)
        b11_l5 = tf.event_audit_board(window=NEW_WIN, limit=5)
        b10_l1 = tf.event_audit_board(window=OLD_WIN, limit=1)
        oct_full = tf.event_audit_board(window=OLD_WIN)
        bad_win = None
        try:
            tf.event_audit_board(window="2026-13", limit=1)
        except T.TicketError as exc:
            bad_win = exc.code
        b11_after_bad = tf.event_audit_board(window=NEW_WIN)
        hat_ok = (
            b11_l1.get("total") == 2
            and b11_l1.get("returned") == 1
            and b11_l1.get("truncated") is True
            and b11_l1.get("limit") == 1
            and b11_l1["event_audit_board"] ==
            b11_full["event_audit_board"][-1:]
            and b11_l1["event_audit_board"][0]["session_key"] ==
            "et-roll-b"
            and b11_l5.get("returned") == 2
            and b11_l5.get("truncated") is False
            and b11_l5["event_audit_board"] ==
            b11_full["event_audit_board"]
            and b10_l1.get("total") == 2
            and b10_l1["event_audit_board"] ==
            oct_full["event_audit_board"][-1:]
            and b10_l1["event_audit_board"][0]["sold"] == 1
            and bad_win == T.E_ET_BAD_ARGS
            and json.dumps(b11_after_bad, sort_keys=True) ==
            json.dumps(b11_full, sort_keys=True))
        record("AC-ETR6", hat_ok,
               "board(%s,1): total==2 (in-window full count - the"
               " windowed board lists every session row, never the"
               " post-truncation 1), returned==1, truncated==True,"
               " returned row == full windowed board tail-1"
               " (et-roll-b) byte-equal; board(%s,5): returned==2,"
               " truncated==False, rows == full windowed board;"
               " board(%s,1) old-month combo: total==2, returned"
               " row == october windowed board tail (b sold==1) -"
               " window filtering runs before the cap across the"
               " roll (R1840 orthogonality law); malformed window"
               " %s refuses %s fail-closed with zero side effects"
               " (post-bad windowed read byte-identical)" %
               (NEW_WIN, NEW_WIN, OLD_WIN, "2026-13", bad_win))
    finally:
        T._now_utc = orig_now

    # ==== AC-ETR7: pure-read law + hygiene ==============================
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_sha_post = hashlib.sha256(handle.read()).hexdigest()
    with open(os.path.join(BASE, "eventtickets.py"), "rb") as handle:
        face_sha_post = hashlib.sha256(handle.read()).hexdigest()
    with open(os.path.abspath(__file__), "rb") as handle:
        own_bytes = handle.read()
    own_ascii = max(own_bytes) < 128
    imported = set()
    for node in ast.walk(ast.parse(own_bytes.decode("ascii"))):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])
    net_hits = sorted(name for name in imported
                      if name in NET_LIBS)
    board_src = inspect.getsource(
        T.EventTicketFace.event_audit_board)
    write_hits = sorted(WRITE_STMT_RE.findall(board_src))
    restored_probe = T._now_utc()
    clock_restored = (
        T._now_utc == orig_now
        and restored_probe != FROZEN_OLD
        and restored_probe != FROZEN_NEW)

    tf.close()
    conn.close()
    led.close()
    shutil.rmtree(tmp, ignore_errors=True)
    tmp_gone = not os.path.exists(tmp)
    tmp_outside = not os.path.abspath(
        tmp).startswith(os.path.dirname(BASE))
    hyg_ok = (
        not write_hits and own_ascii and not net_hits
        and cfg_sha_post == cfg_sha and face_sha_post == face_sha
        and clock_restored and tmp_gone and tmp_outside)
    record("AC-ETR7", hyg_ok,
           "event_audit_board read-face source inspect: zero write"
           " statements (%s); eventtickets.py + config.json zero"
           " bytes changed (sha256 pre==post); suite source pure"
           " ASCII (%s); true import statement lines carry zero"
           " network libs (%s); frozen clock restored in finally"
           " (identity probe + restored value != frozen stamps);"
           " temp world outside the repo and cleaned (%s, %s)" %
           (write_hits or "none", own_ascii,
            net_hits or "none", tmp_gone, tmp_outside))

    failed = [ac for ac, ok in RESULTS if not ok]
    if len(RESULTS) != EXPECTED:
        print("SUITE FAIL (recorded %d of %d criteria)" %
              (len(RESULTS), EXPECTED), flush=True)
        return 1
    if failed:
        print("SUITE FAIL (%d failed: %s)" %
              (len(failed), ", ".join(failed)), flush=True)
        return 1
    print("SUITE PASS (7/7)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
