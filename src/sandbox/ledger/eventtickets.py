"""Virtual event ticket face (BigDomain R1767; canon =
explore-queue virtual event ticket line: the liveroom paid-
admission variant over the festival schedule-window convention -
seeds = liveroom.py R608 + festival.py R1693).

Design verdicts (registered before the code, in the R1767
explore-queue row):

  - carrier: EventTicketFace rides the same SQLite file as the
    ledger (the festival R1693 pattern) with three own tables -
    ticket_sessions / ticket_purchases / ticket_checkins - on a
    private connection and lock; the ledger schema is untouched,
    so the schema fingerprint sentinel stays clean.
  - structure reuse, not a second engine: the three purchase
    gates are the festival AC-FE2/FE3/FE4 judgements reused -
    the schedule window (int tick, inclusive on both edges, one
    tick outside refuses fail-closed), the per-account purchase
    limit and the session-wide capacity cap all reject BEFORE the
    one spend. The paid-admission check-in gate is the liveroom
    R608 unattended-admission law turned into a ticket reader:
    no ticket, no entry (E_ET_NO_TICKET, fail-closed, zero rows,
    zero token movement).
  - platform-side posture: session registration, ticket
    purchase and admission carry no resident free text, so no
    content gate is wired here (the festival/ads/showroom
    precedent); any successor resident-text surface (a seat
    dedication note, say) wires the SecGate pre-gate first.
  - caller-supplied parameters: ticket prices, per-account limits
    and capacities are caller-supplied in the sandbox; production
    values are a [needs-CEO] batch - the shipped config.json is
    untouched.

Domains:

  - session registry: platform-registered virtual event sessions
    (a live-room show, a city gala) with an int-tick window (the
    ads/venue/festival convention), a ticket price, a
    per-account purchase limit and an optional session-wide
    capacity (None = uncapped); the declared AIGC label persists
    on the row and every view surfaces it.
  - ticket sales: a resident buys tickets only while the session
    window covers the purchase tick. Exactly one spend per
    purchase, bound to its tx; the price paid is an immutable
    copy of the registered price. Replay, per-account limit and
    capacity all reject before the spend, so a rejected buy
    never charges.
  - admission: the check-in gate admits only ticket holders -
    one append-only check-in row per (session, account); a
    re-check-in is rejected; admission moves zero tokens (the
    ticket already spent).

Hard laws:

  - append-only: session/purchase/check-in rows are INSERT-only;
    the module source carries zero UPDATE statements (window,
    limit, capacity and has-ticket enforcement all read COUNT
    faces, they never mutate counters);
  - zero RNG, zero network imports, pure ASCII source; counts
    stay counts and tokens stay tokens - the only token-domain
    touch is the one spend per ticket purchase.

AIGC labeling: registry rows carry a persistent ai_label (0/1,
DB CHECK) shown on every listing surface; a resident standing
disclaimer is required at construction and rides every envelope
(non-advisory law).

Pre-registered criteria AC-ET1..AC-ET7 live in the R1767
explore-queue row and were written before this code existed
(honesty law).
"""

import datetime
import sqlite3
import threading

E_ET_BAD_ARGS = "E_ET_BAD_ARGS"              # AC-ET2 / AC-ET5 / AC-ET7
E_ET_BAD_ACCOUNT = "E_ET_BAD_ACCOUNT"        # AC-ET7
E_ET_BAD_PRICE = "E_ET_BAD_PRICE"            # AC-ET1 / AC-ET7
E_ET_BAD_SESSION = "E_ET_BAD_SESSION"        # AC-ET1 / AC-ET7
E_ET_DUP_SESSION = "E_ET_DUP_SESSION"        # AC-ET1
E_ET_UNKNOWN_SESSION = "E_ET_UNKNOWN_SESSION"  # AC-ET1 / AC-ET7
E_ET_WINDOW = "E_ET_WINDOW"                  # AC-ET2 / AC-ET5
E_ET_LIMIT = "E_ET_LIMIT"                    # AC-ET3
E_ET_SOLD_OUT = "E_ET_SOLD_OUT"              # AC-ET4
E_ET_DUP_TICKET = "E_ET_DUP_TICKET"           # AC-ET3 (ref replay)
E_ET_NO_TICKET = "E_ET_NO_TICKET"            # AC-ET5 (admission gate)
E_ET_DUP_CHECKIN = "E_ET_DUP_CHECKIN"        # AC-ET5
E_ET_NO_DISCLAIMER = "E_ET_NO_DISCLAIMER"    # AC-ET6

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ticket_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    start_window INTEGER NOT NULL CHECK (start_window >= 0),
    end_window INTEGER NOT NULL CHECK (end_window > start_window),
    ticket_price INTEGER NOT NULL CHECK (ticket_price > 0),
    per_account_limit INTEGER NOT NULL CHECK (per_account_limit >= 1),
    capacity INTEGER CHECK (capacity IS NULL OR capacity >= 1),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0, 1)),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ticket_purchases (
    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    purchase_ref TEXT NOT NULL,
    price_paid INTEGER NOT NULL CHECK (price_paid > 0),
    spend_tx TEXT NOT NULL,
    purchase_window INTEGER NOT NULL CHECK (purchase_window >= 0),
    purchased_utc TEXT NOT NULL,
    UNIQUE (buyer_id, purchase_ref)
);
CREATE TABLE IF NOT EXISTS ticket_checkins (
    checkin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    account_id TEXT NOT NULL,
    at_window INTEGER NOT NULL CHECK (at_window >= 0),
    checked_utc TEXT NOT NULL,
    UNIQUE (session_id, account_id)
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


class TicketError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class EventTicketFace:
    """Virtual event ticket face over one Ledger sharing the same
    DB file. Own connection and lock for the session/purchase/
    check-in tables; the one spend per purchase goes through the
    ledger public API. Every mutation runs inside BEGIN IMMEDIATE;
    rows are immutable once written. An empty disclaimer refuses
    construction - no disclaimer, no door."""

    def __init__(self, ledger, disclaimer):
        if ledger is None:
            raise TicketError(E_ET_BAD_ARGS, "ledger required")
        text = str(disclaimer or "").strip()
        if not text:
            raise TicketError(E_ET_NO_DISCLAIMER,
                              "resident disclaimer required")
        self.led = ledger
        self.disclaimer = text
        self.db_path = ledger.db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- session registry domain --------------------------------------------

    def register_session(self, session_key, title, start_window,
                         end_window, ticket_price, per_account_limit,
                         ai_generated, capacity=None):
        """Register one virtual event session: an integer-tick
        window (the ads/venue/festival convention, end strictly
        after start), a ticket price, a per-account purchase limit
        and an optional session-wide capacity (None = uncapped).
        Exactly one row per session_key - a repeat is rejected with
        zero rows (AC-ET1). The declared AIGC label persists on
        the row and every view surfaces it (AC-ET6)."""
        key = str(session_key or "").strip()
        if not key:
            raise TicketError(E_ET_BAD_SESSION, "session key required")
        if not str(title or "").strip():
            raise TicketError(E_ET_BAD_SESSION, "title required")
        if not _is_int(start_window) or start_window < 0:
            raise TicketError(E_ET_BAD_SESSION,
                              "start_window must be int >= 0")
        if not _is_int(end_window) or end_window <= start_window:
            raise TicketError(E_ET_BAD_SESSION,
                              "end_window must be > start_window")
        if not _is_int(ticket_price) or ticket_price <= 0:
            raise TicketError(E_ET_BAD_PRICE, str(ticket_price))
        if not _is_int(per_account_limit) or per_account_limit < 1:
            raise TicketError(E_ET_BAD_SESSION,
                              "per_account_limit must be int >= 1")
        if capacity is not None and (not _is_int(capacity)
                                     or capacity < 1):
            raise TicketError(E_ET_BAD_SESSION,
                              "capacity must be int >= 1 or None")
        if not isinstance(ai_generated, bool):
            raise TicketError(E_ET_BAD_SESSION,
                              "ai_generated must be bool")
        label = 1 if ai_generated else 0
        with self._lock:
            row = self._conn.execute(
                "SELECT session_id FROM ticket_sessions"
                " WHERE session_key = ?", (key,)).fetchone()
            if row is not None:
                raise TicketError(E_ET_DUP_SESSION, key)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO ticket_sessions (session_key, title,"
                    " start_window, end_window, ticket_price,"
                    " per_account_limit, capacity, ai_label,"
                    " registered_utc) VALUES (?,?,?,?,?,?,?,?,?)",
                    (key, str(title), start_window, end_window,
                     ticket_price, per_account_limit, capacity, label,
                     _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise TicketError(E_ET_DUP_SESSION, key)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"session_id": cur.lastrowid, "session_key": key,
                "title": str(title), "start_window": start_window,
                "end_window": end_window,
                "ticket_price": ticket_price,
                "per_account_limit": per_account_limit,
                "capacity": capacity, "ai_label": label,
                "disclaimer": self.disclaimer}

    def _require_session(self, session_id):
        """Validation + lookup (caller holds the lock). Returns the
        full session row."""
        if not _is_int(session_id) or session_id <= 0:
            raise TicketError(E_ET_BAD_ARGS, str(session_id))
        row = self._conn.execute(
            "SELECT session_id, session_key, start_window, end_window,"
            " ticket_price, per_account_limit, capacity, ai_label"
            " FROM ticket_sessions WHERE session_id = ?",
            (session_id,)).fetchone()
        if row is None:
            raise TicketError(E_ET_UNKNOWN_SESSION, str(session_id))
        return row

    # -- ticket sales domain --------------------------------------------------

    def buy_ticket(self, buyer_id, session_id, at_window, ref):
        """Buy one ticket at a window tick. The session window must
        cover the tick - both edges inclusive - and one tick
        outside refuses with zero charge (AC-ET2); the replay gate,
        the per-account purchase limit and the session capacity all
        reject BEFORE the spend so a rejected buy never charges
        (AC-ET3/AC-ET4). Exactly one spend per purchase, bound to
        its tx. Returns the provenance envelope with the declared
        AIGC label and the resident disclaimer (AC-ET6)."""
        if not str(buyer_id or "").startswith("usr:"):
            raise TicketError(E_ET_BAD_ACCOUNT, buyer_id)
        r = str(ref or "").strip()
        if not r:
            raise TicketError(E_ET_BAD_ARGS, "purchase ref required")
        if not _is_int(at_window) or at_window < 0:
            raise TicketError(E_ET_BAD_ARGS, "at_window must be"
                                              " int >= 0")
        with self._lock:
            sess = self._require_session(session_id)
            s_key, s_start, s_end = sess[1], int(sess[2]), int(sess[3])
            price, limit, cap = int(sess[4]), int(sess[5]), sess[6]
            if not (s_start <= at_window <= s_end):
                raise TicketError(E_ET_WINDOW,
                                  "%s: tick %d outside %d..%d"
                                  % (s_key, at_window, s_start, s_end))
            row = self._conn.execute(
                "SELECT purchase_id FROM ticket_purchases"
                " WHERE buyer_id = ? AND purchase_ref = ?",
                (buyer_id, r)).fetchone()
            if row is not None:
                raise TicketError(E_ET_DUP_TICKET,
                                  "%s/%s" % (buyer_id, r))
            n_buyer = self._conn.execute(
                "SELECT COUNT(*) FROM ticket_purchases"
                " WHERE buyer_id = ? AND session_id = ?",
                (buyer_id, session_id)).fetchone()[0]
            if n_buyer >= limit:
                raise TicketError(E_ET_LIMIT,
                                  "%s at limit %d on %s"
                                  % (buyer_id, limit, s_key))
            if cap is not None:
                n_all = self._conn.execute(
                    "SELECT COUNT(*) FROM ticket_purchases"
                    " WHERE session_id = ?", (session_id,)).fetchone()[0]
                if n_all >= int(cap):
                    raise TicketError(E_ET_SOLD_OUT,
                                      "%s capacity %d reached"
                                      % (s_key, cap))
            self.led.ensure_account(buyer_id,
                                    census_avatar_id=buyer_id[4:])
            spend_tx = self.led.spend(buyer_id, price, r, "order")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO ticket_purchases (session_id,"
                    " buyer_id, purchase_ref, price_paid, spend_tx,"
                    " purchase_window, purchased_utc)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (session_id, buyer_id, r, price, spend_tx,
                     at_window, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise TicketError(E_ET_DUP_TICKET,
                                  "%s/%s" % (buyer_id, r))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"purchase_id": cur.lastrowid, "session_id": session_id,
                "session_key": s_key, "buyer_id": buyer_id,
                "price_paid": price, "spend_tx": spend_tx,
                "purchase_window": at_window,
                "ai_label": int(sess[7]),
                "disclaimer": self.disclaimer}

    # -- admission domain ------------------------------------------------------

    def admit(self, account_id, session_id, at_window):
        """Paid-admission check-in gate (the liveroom R608 law
        turned into a ticket reader). Gate order: account shape,
        session known, window (inclusive both edges - one tick
        outside refuses with zero rows), then the ticket gate -
        an account with zero purchases on this session is
        refused E_ET_NO_TICKET fail-closed (no ticket, no entry;
        zero rows, zero token movement). A pass appends exactly
        one check-in row per (session, account) - a re-check-in
        is rejected E_ET_DUP_CHECKIN (AC-ET5). Admission moves
        zero tokens: the ticket already spent."""
        if not str(account_id or "").startswith("usr:"):
            raise TicketError(E_ET_BAD_ACCOUNT, account_id)
        if not _is_int(at_window) or at_window < 0:
            raise TicketError(E_ET_BAD_ARGS, "at_window must be"
                                             " int >= 0")
        with self._lock:
            sess = self._require_session(session_id)
            s_key, s_start, s_end = sess[1], int(sess[2]), int(sess[3])
            if not (s_start <= at_window <= s_end):
                raise TicketError(E_ET_WINDOW,
                                  "%s: tick %d outside %d..%d"
                                  % (s_key, at_window, s_start, s_end))
            n_tickets = self._conn.execute(
                "SELECT COUNT(*) FROM ticket_purchases"
                " WHERE session_id = ? AND buyer_id = ?",
                (session_id, account_id)).fetchone()[0]
            if n_tickets == 0:
                raise TicketError(E_ET_NO_TICKET,
                                  "%s holds no ticket on %s"
                                  % (account_id, s_key))
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO ticket_checkins (session_id,"
                    " account_id, at_window, checked_utc)"
                    " VALUES (?,?,?,?)",
                    (session_id, account_id, at_window, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise TicketError(E_ET_DUP_CHECKIN,
                                  "%s on %s" % (account_id, s_key))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"session_id": session_id, "session_key": s_key,
                "account_id": account_id, "at_window": at_window,
                "tickets_held": int(n_tickets),
                "ai_label": int(sess[7]),
                "disclaimer": self.disclaimer}

    # -- read faces ------------------------------------------------------------

    def session_view(self, session_id):
        """One session surface: window, params, declared AIGC
        label, ticket and attendee counts (COUNT faces, zero
        cached state); the envelope carries the resident
        non-advisory disclaimer (AC-ET6). Pure read."""
        with self._lock:
            row = self._conn.execute(
                "SELECT session_id, session_key, title, start_window,"
                " end_window, ticket_price, per_account_limit,"
                " capacity, ai_label, registered_utc"
                " FROM ticket_sessions WHERE session_id = ?",
                (session_id,)).fetchone()
            if row is None:
                raise TicketError(E_ET_UNKNOWN_SESSION, str(session_id))
            n_tickets, n_buyers = self._conn.execute(
                "SELECT COUNT(*), COUNT(DISTINCT buyer_id) FROM"
                " ticket_purchases WHERE session_id = ?",
                (session_id,)).fetchone()
            n_in = self._conn.execute(
                "SELECT COUNT(*) FROM ticket_checkins"
                " WHERE session_id = ?", (session_id,)).fetchone()[0]
        return {"session_id": int(row[0]), "session_key": row[1],
                "title": row[2], "start_window": int(row[3]),
                "end_window": int(row[4]),
                "ticket_price": int(row[5]),
                "per_account_limit": int(row[6]),
                "capacity": None if row[7] is None else int(row[7]),
                "ai_label": int(row[8]), "registered_utc": row[9],
                "ticket_count": int(n_tickets),
                "ticket_buyers": int(n_buyers),
                "attendee_count": int(n_in),
                "disclaimer": self.disclaimer}

    def session_board(self, session_id):
        """Per-session ticket audit trail: every purchase row with
        its buyer, immutable price copy, bound spend tx and window
        tick (AC-ET6). Pure read."""
        with self._lock:
            self._require_session(session_id)
            rows = self._conn.execute(
                "SELECT purchase_id, buyer_id, price_paid, spend_tx,"
                " purchase_window, purchased_utc FROM"
                " ticket_purchases WHERE session_id = ?"
                " ORDER BY purchase_id", (session_id,)).fetchall()
        return {"session_id": session_id, "disclaimer": self.disclaimer,
                "purchases": [{"purchase_id": int(r[0]),
                               "buyer_id": r[1], "price_paid": int(r[2]),
                               "spend_tx": r[3],
                               "purchase_window": int(r[4]),
                               "purchased_utc": r[5]} for r in rows]}

    def attendees(self, session_id):
        """Per-session admission audit: every check-in row in
        arrival order (the append-only admission ledger, AC-ET5).
        Pure read."""
        with self._lock:
            self._require_session(session_id)
            rows = self._conn.execute(
                "SELECT checkin_id, account_id, at_window, checked_utc"
                " FROM ticket_checkins WHERE session_id = ?"
                " ORDER BY checkin_id", (session_id,)).fetchall()
        return {"session_id": session_id, "disclaimer": self.disclaimer,
                "checkins": [{"checkin_id": int(r[0]),
                              "account_id": r[1],
                              "at_window": int(r[2]),
                              "checked_utc": r[3]} for r in rows]}

    def active_sessions(self, at_window):
        """Schedule-window listing face: every session whose window
        covers at_window (inclusive on both edges - the ads/venue
        coverage convention), each row carrying its declared AIGC
        label; the envelope carries the resident disclaimer
        (AC-ET6). Pure read, zero token movement."""
        if not _is_int(at_window) or at_window < 0:
            raise TicketError(E_ET_BAD_ARGS, "at_window must be"
                                             " int >= 0")
        with self._lock:
            rows = self._conn.execute(
                "SELECT session_id, session_key, title, start_window,"
                " end_window, ticket_price, ai_label FROM"
                " ticket_sessions WHERE start_window <= ?"
                " AND end_window >= ? ORDER BY session_id",
                (at_window, at_window)).fetchall()
        return {"at_window": at_window,
                "disclaimer": self.disclaimer,
                "sessions": [{"session_id": int(r[0]),
                              "session_key": r[1], "title": r[2],
                              "start_window": int(r[3]),
                              "end_window": int(r[4]),
                              "ticket_price": int(r[5]),
                              "ai_label": int(r[6])} for r in rows]}
