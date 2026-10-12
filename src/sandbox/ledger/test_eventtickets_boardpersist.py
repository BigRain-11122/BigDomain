"""Acceptance suite for the event-ticket audit-board capped-
windowed read restart-persistence example window (BigDomain
R1898; canon = the tech-queue "eventtickets event_audit_board
cap-window read cross-restart persistence" row, the R1894 seed,
claimed from the tech-lane FIFO head oldest claimable row).
Asserts the pre-registered criteria AC-EAW8..AC-EAW14 from the
R1898 claim note (criteria were registered in
state/queue/tech.md before this code ran; honesty law). Each
criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Covered semantics: the derived purity of the event_audit_board
read face across an instance restart -- the two-piece stack
(Ledger -> EventTicketFace) closes fully in reverse
dependency order and reopens on the same db path and config
bytes; the October capped-windowed board envelope (window echo
+ overflow block) must replay byte-identical from the fresh
instance (zero in-memory drift in the derived face); a
November purchase + check-in on the live tail-slice session
"delta" via the real product path must recalculate the
default board and the default capped read (zero cache) while
the October windowed reads stay byte-frozen (purchase and
check-in rows are record-time immutable; the injection lands
inside the very tail slice the October capped read pins - a
stronger double-hijack face than the R1896 isolated-key
injection, per the claim ruling); a third instance replays
the post-injection state byte-identically (two-instance
sequential reads).

Every world row rides the real product path (register_session
/ buy_ticket / admit) under a frozen clock - zero fixture
injection. W is derived from the first purchase row's
purchased_utc record-time prefix (the R1813 month-abstraction
law; this domain carries no window column). This test source
stays pure ASCII per the encoding discipline.

Usage: python test_eventtickets_boardpersist.py
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
NEW_WIN = "2026-11"
CAP = 2

# exact envelope contracts (the R1826/R1840 pin lists, reused
# verbatim: this suite adds zero keys to any read face)
COMBO_KEYS = sorted([
    "event_audit_board", "disclaimer", "window",
    "limit", "total", "returned", "truncated"])
WINBARE_KEYS = sorted(["event_audit_board", "disclaimer",
                       "window"])
DEFAULT_KEYS = sorted(["event_audit_board", "disclaimer"])
DEFCAP_KEYS = sorted([
    "event_audit_board", "disclaimer", "limit", "total",
    "returned", "truncated"])

ROW_KEYS = {"session_key", "title", "ai_label", "sold",
            "admitted", "no_show", "revenue", "admission_rate"}


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


def _cells(conn, sid, w=None):
    """Manual SQL cross-derivation of one board cell: sold/
    admitted/revenue filtered by the record-time columns (w =
    None means the full window); noshow computed both ways."""
    if w is None:
        sold = _count(conn, "ticket_purchases",
                      " WHERE session_id = ?", (sid,))
        adm = _count(conn, "ticket_checkins",
                     " WHERE session_id = ?", (sid,))
        rev = int(conn.execute(
            "SELECT COALESCE(SUM(price_paid), 0) FROM"
            " ticket_purchases WHERE session_id = ?",
            (sid,)).fetchone()[0])
        noshow = sold - adm
    else:
        sold = _count(
            conn, "ticket_purchases",
            " WHERE session_id = ? AND substr(purchased_utc, 1, 7)"
            " = ?", (sid, w))
        adm = _count(
            conn, "ticket_checkins",
            " WHERE session_id = ? AND substr(checked_utc, 1, 7)"
            " = ?", (sid, w))
        rev = int(conn.execute(
            "SELECT COALESCE(SUM(price_paid), 0) FROM"
            " ticket_purchases WHERE session_id = ?"
            " AND substr(purchased_utc, 1, 7) = ?",
            (sid, w)).fetchone()[0])
        p_le = _count(
            conn, "ticket_purchases",
            " WHERE session_id = ? AND substr(purchased_utc, 1, 7)"
            " <= ?", (sid, w))
        c_le = _count(
            conn, "ticket_checkins",
            " WHERE session_id = ? AND substr(checked_utc, 1, 7)"
            " <= ?", (sid, w))
        noshow = p_le - c_le
    rate = round(adm / sold, 4) if sold else 0.0
    return {"sold": sold, "admitted": adm, "revenue": rev,
            "no_show": noshow, "admission_rate": rate}


def _row_eq(board_row, cells):
    return (board_row["sold"] == cells["sold"]
            and board_row["admitted"] == cells["admitted"]
            and board_row["no_show"] == cells["no_show"]
            and board_row["revenue"] == cells["revenue"]
            and board_row["admission_rate"]
            == cells["admission_rate"])


def main():
    tmp = tempfile.mkdtemp(prefix="eventtickets-bp-")
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
        led.mint_to_pool("pool:reserve", 2000, "MINT-EAW-BP",
                         "settlement")
        for who in ("alice", "bob", "dave"):
            led.ensure_account("usr:" + who,
                               census_avatar_id=who)
            led.adjust([("pool:reserve", "debit", 100),
                        ("usr:" + who, "credit", 100)],
                       "manual:fund-" + who,
                       "suite funding " + who)

        s_alpha = face.register_session(
            "alpha-gala", "Alpha Gala Night", 0, 30, 5, 2,
            False)
        clock.advance(3)
        s_beta = face.register_session(
            "beta-night", "Beta Night Live", 0, 30, 3, 1, True,
            capacity=5)
        clock.advance(3)
        s_charity = face.register_session(
            "charity", "Charity Stream", 0, 30, 4, 1, False)
        clock.advance(3)
        s_delta = face.register_session(
            "delta", "Delta Session", 0, 30, 2, 1, True)

        face.buy_ticket("usr:alice", s_alpha["session_id"], 10,
                        "order:eawbp-a1")
        clock.advance(7)
        face.buy_ticket("usr:alice", s_alpha["session_id"], 12,
                        "order:eawbp-a2")
        clock.advance(7)
        face.buy_ticket("usr:bob", s_alpha["session_id"], 11,
                        "order:eawbp-a3")
        clock.advance(7)
        face.buy_ticket("usr:dave", s_beta["session_id"], 4,
                        "order:eawbp-b1")
        clock.advance(7)
        face.buy_ticket("usr:alice", s_charity["session_id"], 3,
                        "order:eawbp-c1")
        clock.advance(7)
        face.admit("usr:alice", s_alpha["session_id"], 12)
        clock.advance(7)
        face.admit("usr:alice", s_charity["session_id"], 3)
        clock.advance(7)

        def _sid(key):
            return int(conn.execute(
                "SELECT session_id FROM ticket_sessions"
                " WHERE session_key = ?", (key,)).fetchone()[0])

        # W derivation (R1813 month-abstraction law): from the
        # first purchase row's record-time prefix, never
        # hardcoded
        W = conn.execute(
            "SELECT substr(purchased_utc, 1, 7) FROM"
            " ticket_purchases ORDER BY purchased_utc,"
            " purchase_id LIMIT 1").fetchone()[0]
        oct_pur = _count(
            conn, "ticket_purchases",
            " WHERE substr(purchased_utc, 1, 7) = ?", (W,))
        oct_chk = _count(
            conn, "ticket_checkins",
            " WHERE substr(checked_utc, 1, 7) = ?", (W,))

        # -- pre-close four-read snapshot set ------------------
        s_oct_combo = snap(face.event_audit_board(W, CAP))
        s_oct_win = snap(face.event_audit_board(W))
        s_default = snap(face.event_audit_board())
        s_def_cap = snap(face.event_audit_board(None, CAP))

        combo = json.loads(s_oct_combo)
        winbare = json.loads(s_oct_win)
        default = json.loads(s_default)
        defcap = json.loads(s_def_cap)

        keys_pin = (
            sorted(combo.keys()) == COMBO_KEYS
            and len(COMBO_KEYS) == 7
            and sorted(winbare.keys()) == WINBARE_KEYS
            and len(WINBARE_KEYS) == 3
            and sorted(default.keys()) == DEFAULT_KEYS
            and len(DEFAULT_KEYS) == 2
            and sorted(defcap.keys()) == DEFCAP_KEYS
            and len(DEFCAP_KEYS) == 6)
        block_pin = (
            combo["window"] == W
            and combo["disclaimer"] == DISCLAIMER
            and combo["limit"] == CAP and combo["total"] == 4
            and combo["returned"] == CAP
            and combo["truncated"] is True
            and [r["session_key"] for r in
                combo["event_audit_board"]]
            == ["charity", "delta"]
            and all(set(r.keys()) == ROW_KEYS
                    for r in combo["event_audit_board"]))
        default_pin = (
            [r["session_key"] for r in
             default["event_audit_board"]]
            == ["alpha-gala", "beta-night", "charity",
                "delta"]
            and all(set(r.keys()) == ROW_KEYS
                    for r in default["event_audit_board"]))
        # manual SQL cross-derivation: every full-board cell and
        # every combo tail cell (October world == full window)
        manual_ok = True
        for r in default["event_audit_board"]:
            manual_ok = manual_ok and _row_eq(
                r, _cells(conn, _sid(r["session_key"])))
            manual_ok = manual_ok and _row_eq(
                r, _cells(conn, _sid(r["session_key"]), W))
        for r in combo["event_audit_board"]:
            manual_ok = manual_ok and _row_eq(
                r, _cells(conn, _sid(r["session_key"]), W))
        slice_ok = (
            combo["event_audit_board"]
            == default["event_audit_board"][-CAP:])
        eaw8 = (W == "2026-10" and oct_pur == 5
                and oct_chk == 2 and keys_pin and block_pin
                and default_pin and manual_ok and slice_ok)
        record("AC-EAW8", eaw8,
               "October anchor: %d real purchases + %d real"
               " check-ins on the product path, W=%s derived"
               " from the first purchase row's record-time"
               " prefix; four pre-close snapshots pinned"
               " (combo 7 keys with window echo + overflow"
               " block l/t/r/tr=%s/%s/%s/%s tail"
               " [charity,delta]; window-bare 3 keys;"
               " default 2 keys; default-cap 6 keys);"
               " board order [alpha-gala, beta-night,"
               " charity, delta]; every cell == manual SQL"
               " (full + windowed + snapshot no_show)=%s;"
               " combo == default tail slice=%s"
               % (oct_pur, oct_chk, W, combo["limit"],
                  combo["total"], combo["returned"],
                  combo["truncated"], manual_ok, slice_ok))

        # -- AC-EAW9 cross-restart combo replay -----------------
        conn.close()
        _close_stack(face, led)
        led2, face2 = _open_stack(db_path, cfg)
        conn = sqlite3.connect(db_path)

        replay = snap(face2.event_audit_board(W, CAP))
        replay2 = snap(face2.event_audit_board(W, CAP))
        eaw9 = (replay == s_oct_combo
                and replay2 == s_oct_combo)
        record("AC-EAW9", eaw9,
               "two-piece stack close (face -> ledger, reverse"
               " dependency) -> reopen same db/config: October"
               " capped-windowed envelope byte-identical to the"
               " pre-close snapshot=%s, second same-param read"
               " self-identical=%s"
               % (replay == s_oct_combo,
                  replay2 == s_oct_combo))

        # -- AC-EAW10 default / window-bare / default-cap replay -
        r_default = snap(face2.event_audit_board())
        r_oct_win = snap(face2.event_audit_board(W))
        r_def_cap = snap(face2.event_audit_board(None, CAP))
        eaw10 = (r_default == s_default
                 and r_oct_win == s_oct_win
                 and r_def_cap == s_def_cap)
        record("AC-EAW10", eaw10,
               "default 2-key read replayed byte-identical=%s"
               " (no window echo on the default face),"
               " window-bare 3-key=%s, default-cap 6-key=%s"
               " (derived face zero in-memory drift)"
               % (r_default == s_default,
                  r_oct_win == s_oct_win,
                  r_def_cap == s_def_cap))

        # -- AC-EAW11 November real rows -> recalc faces ---------
        clock.advance(23 * 86400)
        face2.buy_ticket("usr:bob", s_delta["session_id"], 5,
                         "order:eawbp-n1")
        clock.advance(7)
        face2.admit("usr:bob", s_delta["session_id"], 6)
        nov_pur = _count(
            conn, "ticket_purchases",
            " WHERE substr(purchased_utc, 1, 7) = ?",
            (NEW_WIN,))
        nov_chk = _count(
            conn, "ticket_checkins",
            " WHERE substr(checked_utc, 1, 7) = ?",
            (NEW_WIN,))
        r_def = json.loads(snap(face2.event_audit_board()))
        r_defcap = json.loads(
            snap(face2.event_audit_board(None, CAP)))
        r_nov_combo = json.loads(
            snap(face2.event_audit_board(NEW_WIN, CAP)))
        d_row = {r["session_key"]: r for r in
                 r_def["event_audit_board"]}["delta"]
        n_delta = {r["session_key"]: r for r in
                   r_nov_combo["event_audit_board"]}["delta"]
        n_charity = {r["session_key"]: r for r in
                     r_nov_combo["event_audit_board"]}["charity"]
        eaw11 = (
            nov_pur == 1 and nov_chk == 1
            and d_row["sold"] == 1 and d_row["admitted"] == 1
            and d_row["no_show"] == 0
            and d_row["revenue"] == 2
            and d_row["admission_rate"] == 1.0
            and snap(r_def) != s_default
            and snap(r_defcap) != s_def_cap
            and [r["session_key"] for r in
                 r_defcap["event_audit_board"]]
            == ["charity", "delta"]
            and {r["session_key"]: r for r in
                 r_defcap["event_audit_board"]}["delta"]
            ["sold"] == 1
            and r_nov_combo["window"] == NEW_WIN
            and r_nov_combo["total"] == 4
            and r_nov_combo["returned"] == CAP
            and r_nov_combo["truncated"] is True
            and n_delta["sold"] == 1
            and n_delta["admitted"] == 1
            and n_delta["no_show"] == 0
            and n_delta["revenue"] == 2
            and n_delta["admission_rate"] == 1.0
            and n_charity["sold"] == 0
            and n_charity["admitted"] == 0
            and n_charity["no_show"] == 0
            and _row_eq(
                n_delta,
                _cells(conn, _sid("delta"), NEW_WIN))
            and _row_eq(
                n_charity,
                _cells(conn, _sid("charity"), NEW_WIN)))
        record("AC-EAW11", eaw11,
               "frozen clock +23d -> 1 November purchase + 1"
               " November check-in on the live tail-slice"
               " session delta via the real product path"
               " (record-time SQL counts nov pur=%d chk=%d):"
               " default board recalculated (delta sold"
               " 0->1, admitted 0->1, byte-differs from the"
               " pre-close default snapshot=%s = zero cache),"
               " default-cap recalculated with delta inside"
               " the tail slice=%s, November combo carries the"
               " new rows (window echo=%s, delta sold_w=1"
               " admitted_w=1, charity end-of-window snapshot"
               " no_show==0 absorbing the October pair, both"
               " cells == manual SQL)=%s"
               % (nov_pur, nov_chk, snap(r_def) != s_default,
                  snap(r_defcap) != s_def_cap,
                  r_nov_combo["window"], True))

        # -- AC-EAW12 old-window zero penetration ---------------
        p_oct_combo = snap(face2.event_audit_board(W, CAP))
        p_oct_win = snap(face2.event_audit_board(W))
        tot_pur = _count(conn, "ticket_purchases")
        tot_chk = _count(conn, "ticket_checkins")
        tot_sess = _count(conn, "ticket_sessions")
        eaw12 = (p_oct_combo == s_oct_combo
                 and p_oct_win == s_oct_win
                 and tot_pur == 6 and tot_chk == 3
                 and tot_sess == 4
                 and oct_pur + nov_pur == tot_pur
                 and oct_chk + nov_chk == tot_chk)
        record("AC-EAW12", eaw12,
               "after the November injection on the tail-slice"
               " session: October capped-windowed read still"
               " byte-identical to the pre-close snapshot=%s,"
               " window-bare=%s (purchase/check-in rows are"
               " record-time immutable), table counts pinned"
               " sessions=%d purchases=%d checkins=%d,"
               " telescoping purchases oct %d + nov %d =="
               " all-time %d (checkins %d + %d == %d)"
               % (p_oct_combo == s_oct_combo,
                  p_oct_win == s_oct_win, tot_sess,
                  tot_pur, tot_chk, oct_pur, nov_pur,
                  tot_pur, oct_chk, nov_chk, tot_chk))

        # -- AC-EAW13 two-instance sequential reads --------------
        f2_a = snap(face2.event_audit_board(W, CAP))
        f2_b = snap(face2.event_audit_board(W))
        f2_c = snap(face2.event_audit_board(NEW_WIN, CAP))
        f2_d = snap(face2.event_audit_board())
        f2_e = snap(face2.event_audit_board(None, CAP))
        conn.close()
        _close_stack(face2, led2)
        led3, face3 = _open_stack(db_path, cfg)
        f3_a = snap(face3.event_audit_board(W, CAP))
        f3_b = snap(face3.event_audit_board(W))
        f3_c = snap(face3.event_audit_board(NEW_WIN, CAP))
        f3_d = snap(face3.event_audit_board())
        f3_e = snap(face3.event_audit_board(None, CAP))
        eaw13 = (f3_a == f2_a and f3_b == f2_b
                 and f3_c == f2_c and f3_d == f2_d
                 and f3_e == f2_e
                 and f3_a == s_oct_combo)
        record("AC-EAW13", eaw13,
               "third instance on the same db: all five"
               " post-injection reads byte-identical to the"
               " second instance (%s/%s/%s/%s/%s) and the"
               " October capped-windowed read still equals"
               " the original pre-close snapshot=%s"
               " (windowed read survives restart x new-data"
               " unscratched)"
               % (f3_a == f2_a, f3_b == f2_b, f3_c == f2_c,
                  f3_d == f2_d, f3_e == f2_e,
                  f3_a == s_oct_combo))

        # -- AC-EAW14 pure-read law + hygiene --------------------
        conn = sqlite3.connect(db_path)
        c0 = (_count(conn, "ticket_sessions"),
              _count(conn, "ticket_purchases"),
              _count(conn, "ticket_checkins"))
        for w, lmt in ((None, 0), (W, 0), (W, CAP), (W, 1),
                       (None, CAP), (NEW_WIN, CAP),
                       (NEW_WIN, 0), (None, 1)):
            face3.event_audit_board(w, lmt)
        c1 = (_count(conn, "ticket_sessions"),
              _count(conn, "ticket_purchases"),
              _count(conn, "ticket_checkins"))

        source = product_pre.decode("ascii")
        idx = source.find("def event_audit_board")
        seg_end = source.find("    def ", idx + 20)
        if seg_end == -1:
            seg_end = len(source)
        board_seg = source[idx:seg_end]
        # strip docstrings and comments before the write-keyword
        # scan (the R1888 AC-LG7 / R1896 AC-LG29 / R1897 AC-LU21
        # code-strip precedent: the naive scan hits the
        # segment's own hygiene sentences)
        code_seg = re.sub(r'"""[\s\S]*?"""', '""', board_seg)
        code_seg = "\n".join(re.sub(r"#.*$", "", line)
                            for line in code_seg.splitlines())
        write_kw = re.findall(
            r"\b(INSERT|UPDATE|DELETE|REPLACE|CREATE)\b",
            code_seg)
        with open(product_path, "rb") as handle:
            product_post = handle.read()
        product_post_sha = hashlib.sha256(product_post).hexdigest()
        with open(os.path.join(BASE, "config.json"),
                  "rb") as handle:
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
        eaw14 = (c0 == c1
                 and len(write_kw) == 0
                 and product_post == product_pre
                 and product_pre_sha == product_post_sha
                 and cfg_bytes_end == cfg_bytes
                 and me_ascii and len(imports_net) == 0
                 and len(mine_net) == 0
                 and "ledger-eventtickets-boardpersist"
                 in runner_src
                 and len(RESULTS) + 1 == EXPECTED)
        record("AC-EAW14", eaw14,
               "pure read: 8-form read battery on the third face"
               " moves zero rows (sessions/purchases/checkins"
               " %s == %s), event_audit_board segment zero write"
               " keywords=%d, eventtickets.py sha256 stable=%s,"
               " config.json byte-stable=%s, sources pure-ASCII"
               "=%s, network imports 0/0=%s, reconcile_all"
               " SUITES row 'ledger-eventtickets-boardpersist'"
               " registered, criteria drift self-check %d/%d"
               % (c0, c1, len(write_kw),
                  product_pre_sha == product_post_sha,
                  cfg_bytes_end == cfg_bytes, me_ascii,
                  len(imports_net) == 0 and len(mine_net) == 0,
                  len(RESULTS), EXPECTED))

        conn.close()
        _close_stack(face3, led3)

    finally:
        T._now_utc = real_now

    restored = T._now_utc is real_now
    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE eventtickets-boardpersist: %d/%d criteria pass"
          % (passed, total), flush=True)
    print("clock restore probe: %s" % restored, flush=True)
    return 0 if (passed == total and total == EXPECTED
                 and restored) else 1


if __name__ == "__main__":
    sys.exit(main())
