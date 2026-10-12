"""Acceptance suite for the event-ticket audit-board month-axis
telescoping example (BigDomain R1867 tech-queue claim row; seed =
the R1862 month-roll example + the telescoping example family
R1811 water-journal monthly-net-flow / R1858 freetrial
calls_by_* - the eventtickets board was the symmetric gap).
Asserts the pre-registered criteria AC-ETT1..AC-ETT6 from the
R1867 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

Carrier verdict (the R1862 dedicated-suite precedent): a fresh
isolated face instance in its own temp world, the eventtickets
module clock frozen (T._now_utc patched onto a deterministic
holder, restored in finally), all stamps riding the true
product write path - zero fixture injection.

World: BASE_DT 2026-10-15; sessions et-tel-a (price 30) and
et-tel-b (price 25), tick windows 10..900 so purchases stay
legal on both sides of the roll. October phase: 3 purchases
(a: alice + bob, b: carol) + 1 check-in (alice). The clock
advances +23d across the month boundary; November phase: 2 new
purchases (a: carol + dave) + 2 new check-ins (dave with his
November purchase, bob carrying his October purchase across
the roll - the cross-month pairing that makes no_show a
snapshot, never a telescoping sum).

Laws pinned:
- sold / admitted / revenue are additive flow faces: october
  window + november window == the default full-window value
  (the three-key telescoping law), because every immutable row
  lands in exactly one month cell (the row-set partition law).
- no_show is the end-of-window snapshot (purchases<=W minus
  check-ins<=W): windowed values do NOT telescope (R1862 world
  anchor: session a sums 1+1=2 while the full window reads 1)
  - snapshot semantics vs incremental semantics, honest note.
- admission_rate is a window-local ratio, never an additive
  face (0.5 + 1.0 != 0.75) - rates telescope nowhere.
- a zero-activity month window keeps the registry-driven dense
  rows with honest zeros (sold==0 revenue==0 rate==0.0).

Zero product bytes change: the board semantics already live in
eventtickets.py, this suite only pins them.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_eventtickets_telescope.py
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
EXPECTED = 6

DISCLAIMER = ("sandbox stand-in disclaimer: virtual event tickets"
             " grant admission only, not investment advice")

BASE_DT = datetime.datetime(2026, 10, 15, 10, 0, 0)
OLD_WIN = "2026-10"
NEW_WIN = "2026-11"
EMPTY_WIN = "2026-09"
OBS_MONTHS = (OLD_WIN, NEW_WIN)
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


def _month_counts(conn, table, col, skey):
    """Mirror SQL: per-month COUNT for one session's row family."""
    out = {}
    for m in OBS_MONTHS:
        out[m] = conn.execute(
            "SELECT COUNT(*) FROM " + table + " t, ticket_sessions"
            " s WHERE t.session_id = s.session_id"
            " AND s.session_key = ? AND substr(t." + col +
            ", 1, 7) = ?", (skey, m)).fetchone()[0]
    out["full"] = conn.execute(
        "SELECT COUNT(*) FROM " + table + " t, ticket_sessions"
        " s WHERE t.session_id = s.session_id"
        " AND s.session_key = ?", (skey,)).fetchone()[0]
    return out


def _month_revenue(conn, skey):
    """Mirror SQL: per-month SUM(price_paid) for one session."""
    out = {}
    for m in OBS_MONTHS:
        out[m] = conn.execute(
            "SELECT COALESCE(SUM(p.price_paid), 0) FROM"
            " ticket_purchases p, ticket_sessions s"
            " WHERE p.session_id = s.session_id"
            " AND s.session_key = ? AND substr(p.purchased_utc,"
            " 1, 7) = ?", (skey, m)).fetchone()[0]
    out["full"] = conn.execute(
        "SELECT COALESCE(SUM(p.price_paid), 0) FROM"
        " ticket_purchases p, ticket_sessions s"
        " WHERE p.session_id = s.session_id"
        " AND s.session_key = ?", (skey,)).fetchone()[0]
    return out


def _cumulative(conn, table, col, skey, w):
    """Mirror SQL: cumulative COUNT(month <= w) - the snapshot
    face behind the windowed no_show."""
    return conn.execute(
        "SELECT COUNT(*) FROM " + table + " t, ticket_sessions s"
        " WHERE t.session_id = s.session_id"
        " AND s.session_key = ? AND substr(t." + col +
        ", 1, 7) <= ?", (skey, w)).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="eventtickets-tel-")
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
        tf.register_session("et-tel-a", "Telescope Gala A", 10, 900,
                             30, 1, True)
        tf.register_session("et-tel-b", "Telescope Gala B", 10, 900,
                             25, 1, False)
        sids = conn.execute(
            "SELECT session_id FROM ticket_sessions"
            " ORDER BY session_key").fetchall()
        sid_a, sid_b = int(sids[0][0]), int(sids[1][0])
        led.mint_to_pool("pool:reserve", 2000, "SETUP-ETT-A",
                         "settlement")
        for who in ("alice", "bob", "carol", "dave"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
            led.adjust([("pool:reserve", "debit", 100),
                        ("usr:" + who, "credit", 100)],
                       "manual:fund-" + who,
                       "telescope suite funding " + who)

        # ---- October phase (frozen 2026-10-15) ---------------------------
        tf.buy_ticket("usr:alice", sid_a, 100, "oct-a1")
        tf.buy_ticket("usr:bob", sid_a, 100, "oct-b1")
        tf.buy_ticket("usr:carol", sid_b, 100, "oct-c1")
        tf.admit("usr:alice", sid_a, 120)

        # ---- the roll: clock +23d across the month boundary --------------
        clock.advance(23 * 86400)
        frozen_new_probe = T._now_utc()

        # ---- November phase (frozen 2026-11-07, live product path) -------
        tf.buy_ticket("usr:carol", sid_a, 200, "nov-c1")
        tf.buy_ticket("usr:dave", sid_a, 200, "nov-d1")
        tf.admit("usr:dave", sid_a, 210)
        tf.admit("usr:bob", sid_a, 220)

        # board faces
        b_oct = tf.event_audit_board(window=OLD_WIN)
        b_nov = tf.event_audit_board(window=NEW_WIN)
        b_full = tf.event_audit_board()

        world_ok = (
            frozen_new_probe == FROZEN_NEW
            and _count(conn, "ticket_sessions") == 2
            and _count(conn, "ticket_purchases") == 5
            and _count(conn, "ticket_checkins") == 3)
        if not world_ok:
            # the whole suite depends on the world shape
            record("AC-ETT1", False,
                   "world build failed: sessions/purchases/"
                   "checkins = %d/%d/%d" %
                   (_count(conn, "ticket_sessions"),
                    _count(conn, "ticket_purchases"),
                    _count(conn, "ticket_checkins")))
        else:
            # ==== AC-ETT1: three-key telescoping law ====================
            tel_ok = True
            ev = []
            for skey in ("et-tel-a", "et-tel-b"):
                ro = _row(b_oct, skey)
                rn = _row(b_nov, skey)
                rf = _row(b_full, skey)
                for key in ("sold", "admitted", "revenue"):
                    ssum = ro[key] + rn[key]
                    ok = ssum == rf[key]
                    tel_ok = tel_ok and ok
                    ev.append("%s %s %d+%d==%d" %
                              (skey, key, ro[key], rn[key], rf[key]))
            record("AC-ETT1", tel_ok,
                   "additive flow faces telescope: sold/admitted/"
                   "revenue october+november == full-window value"
                   " for both sessions (%s); every immutable row"
                   " lands in exactly one month cell because each"
                   " row family filters on its own record-time"
                   " stamp (substr month equality), the row-set"
                   " partition law pinned by the SQL mirror in"
                   " AC-ETT5" % "; ".join(ev))

            # ==== AC-ETT2: no_show snapshot, never telescoping ============
            ra_o = _row(b_oct, "et-tel-a")
            ra_n = _row(b_nov, "et-tel-a")
            ra_f = _row(b_full, "et-tel-a")
            rb_o = _row(b_oct, "et-tel-b")
            rb_n = _row(b_nov, "et-tel-b")
            rb_f = _row(b_full, "et-tel-b")
            sum_a = ra_o["no_show"] + ra_n["no_show"]
            sum_b = rb_o["no_show"] + rb_n["no_show"]
            snap_ok = (
                sum_a != ra_f["no_show"]
                and sum_b != rb_f["no_show"]
                and sum_a == 2 and ra_f["no_show"] == 1
                and _cumulative(conn, "ticket_purchases",
                                "purchased_utc", "et-tel-a",
                                OLD_WIN) == 2
                and _cumulative(conn, "ticket_checkins",
                                "checked_utc", "et-tel-a",
                                OLD_WIN) == 1
                and ra_o["no_show"] == 1
                and _cumulative(conn, "ticket_purchases",
                                "purchased_utc", "et-tel-a",
                                NEW_WIN) == 4
                and _cumulative(conn, "ticket_checkins",
                                "checked_utc", "et-tel-a",
                                NEW_WIN) == 3
                and ra_n["no_show"] == 1
                and ra_f["no_show"] ==
                ra_f["sold"] - ra_f["admitted"])
            record("AC-ETT2", snap_ok,
                   "no_show does NOT telescope (snapshot semantics,"
                   " honest note): session a windowed sum %d != full"
                   " %d (the R1862 world anchor - bob checks in"
                   " november against an october purchase, so the"
                   " november snapshot re-counts the pair); every"
                   " windowed no_show == the cumulative mirror SQL"
                   " (purchases<=W minus check-ins<=W: oct 2-1==1,"
                   " nov 4-3==1) while the full-window no_show is"
                   " the plain sold-admitted difference (4-3==1) -"
                   " snapshot vs incremental semantics, the"
                   " in-window net flow never masquerades under"
                   " the no_show field (AC-EAW4)" %
                   (sum_a, ra_f["no_show"]))

            # ==== AC-ETT3: admission_rate is a ratio, never additive ======
            rate_ok = (
                ra_o["admission_rate"] == 0.5
                and ra_n["admission_rate"] == 1.0
                and ra_f["admission_rate"] == 0.75
                and round(ra_o["admitted"] / ra_o["sold"], 4) == 0.5
                and round(ra_n["admitted"] / ra_n["sold"], 4) == 1.0
                and round(ra_f["admitted"] / ra_f["sold"], 4) == 0.75
                and rb_n["admission_rate"] == 0.0
                and rb_n["sold"] == 0)
            record("AC-ETT3", rate_ok,
                   "admission_rate is a window-local ratio, never"
                   " an additive face: a oct 0.5 + nov 1.0 != full"
                   " 0.75 - windowed rates telescope nowhere; each"
                   " windowed rate == round(windowed admitted /"
                   " windowed sold, 4) recomputed from its own"
                   " window cells (0.5 / 1.0 / 0.75 all pinned);"
                   " zero-sold guard stays honest (b november"
                   " sold==0 -> rate==0.0, no division)")

            # ==== AC-ETT4: zero-activity month window honest zeros =========
            b_emp = tf.event_audit_board(window=EMPTY_WIN)
            re_a = _row(b_emp, "et-tel-a")
            re_b = _row(b_emp, "et-tel-b")
            zero_ok = (
                b_emp.get("window") == EMPTY_WIN
                and re_a is not None and re_b is not None
                and re_a["sold"] == 0 and re_a["admitted"] == 0
                and re_a["revenue"] == 0
                and re_a["admission_rate"] == 0.0
                and re_a["no_show"] == 0
                and re_b["sold"] == 0 and re_b["revenue"] == 0
                and re_b["admission_rate"] == 0.0
                and rb_n["sold"] == 0 and rb_n["revenue"] == 0
                and rb_n["admission_rate"] == 0.0
                and len(b_emp["event_audit_board"]) == 2)
            record("AC-ETT4", zero_ok,
                   "zero-activity month window %s: the registry-"
                   "driven dense board keeps both session rows"
                   " with honest zeros (sold==0 revenue==0 rate=="
                   "0.0, no_show snapshot of an empty past == 0) -"
                   " rows stay carried, no phantom, no omission;"
                   " in-world zero-activity cell also pinned: b"
                   " november row sold==0 revenue==0 rate==0.0"
                   " present (rate==0.0 zero-sold guard)" %
                   EMPTY_WIN)

            # ==== AC-ETT5: SQL third-path mirror + partition law ===========
            mir_ok = True
            ev5 = []
            for skey in ("et-tel-a", "et-tel-b"):
                pm = _month_counts(conn, "ticket_purchases",
                                   "purchased_utc", skey)
                cm = _month_counts(conn, "ticket_checkins",
                                  "checked_utc", skey)
                rv = _month_revenue(conn, skey)
                part_p = pm[OLD_WIN] + pm[NEW_WIN] == pm["full"]
                part_c = cm[OLD_WIN] + cm[NEW_WIN] == cm["full"]
                ro = _row(b_oct, skey)
                rn = _row(b_nov, skey)
                rf = _row(b_full, skey)
                for env, m in ((ro, OLD_WIN), (rn, NEW_WIN)):
                    mir_ok = mir_ok and (
                        env["sold"] == pm[m]
                        and env["admitted"] == cm[m]
                        and env["revenue"] == rv[m])
                mir_ok = mir_ok and (
                    rf["sold"] == pm["full"]
                    and rf["admitted"] == cm["full"]
                    and rf["revenue"] == rv["full"]
                    and part_p and part_c)
                ev5.append("%s purchases %d+%d==%d checkins %d+%d"
                           "==%d revenue %d+%d==%d" %
                           (skey, pm[OLD_WIN], pm[NEW_WIN],
                            pm["full"], cm[OLD_WIN], cm[NEW_WIN],
                            cm["full"], rv[OLD_WIN], rv[NEW_WIN],
                            rv["full"]))
            tot_ok = (_count(conn, "ticket_purchases") == 5
                      and _count(conn, "ticket_checkins") == 3)
            record("AC-ETT5", mir_ok and tot_ok,
                   "SQL third path (independent ro connection"
                   " semantics on the same db): per session per"
                   " month per key, the windowed board values =="
                   " direct COUNT/SUM mirror (%s); the row-set"
                   " partition law holds per family: observed-month"
                   " counts sum == the all-window count (every"
                   " immutable row lands in exactly one month cell"
                   " - the structural basis of the AC-ETT1"
                   " telescoping); whole-world counters 5 purchases"
                   " + 3 check-ins constant" % "; ".join(ev5))
    finally:
        T._now_utc = orig_now

    # ==== AC-ETT6: pure-read law + hygiene ==============================
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
    record("AC-ETT6", hyg_ok,
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
    print("SUITE PASS (6/6)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
