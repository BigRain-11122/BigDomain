"""City solar-term / festival limited-event engine face over the
token ledger + collectibles sandbox (BigDomain R1693; canon =
explore-queue city solar-term / festival limited-event engine
line: the mechanism reuses the ads/venue schedule-window
convention - a limited event = window-spanned item sales +
per-account purchase-limit gate + event-commemorative collectibles
linkage; seeds = the collectibles (R619) and ads (R622) faces
already in the ledger).

Three domains ride on the P-47-2b token ledger:

  events  : a platform-registered limited event (a solar term or a
            festival) spans an integer-tick window, the ads/venue
            schedule-window convention (start_window..end_window,
            end strictly after start, purchase valid on both
            edges). The registry is platform-side: no
            resident-authored text enters this module (the
            ads/collectibles platform-side posture - event titles
            are platform copy and purchases carry no text, so no
            content gate is wired here; any future resident-text
            face built on this engine wires the SecGate pre-gate
            first, the companion/tmarket posture). The declared
            AIGC label persists on the event row and every view
            surfaces it.
  sales   : a resident buys the limited item only while the event
            window covers the purchase tick - one tick outside
            refuses fail-closed with zero charge (E_FE_WINDOW).
            Exactly one spend per purchase, bound to its tx; the
            price paid is an immutable copy of the registered
            price. The per-account purchase-limit gate rejects a
            buyer already at per_account_limit purchases BEFORE
            the spend; the optional event-wide edition cap
            rejects at total_cap BEFORE the spend; a same
            (buyer, purchase_ref) replay is rejected BEFORE the
            spend.
  linkage : the FIRST purchase of an event by an account grants
            the event commemorative collectible through the
            CollectiblesFace public API (issue_certificate - the
            collectibles product is referenced, never copied; this
            module writes zero collectibles rows directly). The
            award itself moves zero tokens (the purchase already
            spent); the collectibles UNIQUE (account, kind,
            event_ref) is the structural one-per-account-event
            backstop - a pre-awarded account (platform direct
            award before any purchase) buys legally without a
            double award.

Event and purchase rows are immutable once written (zero UPDATE
surface: window, limit and cap enforcement read COUNT faces,
they never mutate counters). Counts stay counts and tokens stay
tokens: the only token-domain touch in this module is the one
spend per purchase.

Prices, per-account limits and edition caps are caller-supplied
in the sandbox; every production parameter value (festival item
price points, purchase limits, edition sizes) is a P1 item for
CEO, approval-only ([needs-CEO]). No config keys are added by
this module.

Pre-registered criteria AC-FE1..AC-FE7 live in the R1693
explore-queue row and were written before this code existed
(honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: two extra tables in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

E_FE_BAD_ARGS = "E_FE_BAD_ARGS"              # AC-FE2 / AC-FE7
E_FE_BAD_ACCOUNT = "E_FE_BAD_ACCOUNT"         # AC-FE7
E_FE_BAD_PRICE = "E_FE_BAD_PRICE"             # AC-FE1 / AC-FE7
E_FE_BAD_EVENT = "E_FE_BAD_EVENT"             # AC-FE1 / AC-FE7
E_FE_DUP_EVENT = "E_FE_DUP_EVENT"             # AC-FE1
E_FE_UNKNOWN_EVENT = "E_FE_UNKNOWN_EVENT"     # AC-FE2 / AC-FE6
E_FE_WINDOW = "E_FE_WINDOW"                   # AC-FE2 (window gate)
E_FE_LIMIT = "E_FE_LIMIT"                     # AC-FE3 (purchase limit)
E_FE_SOLD_OUT = "E_FE_SOLD_OUT"               # AC-FE4 (edition cap)
E_FE_DUP_PURCHASE = "E_FE_DUP_PURCHASE"        # AC-FE3 (ref replay)
E_FE_NO_DISCLAIMER = "E_FE_NO_DISCLAIMER"     # AC-FE6
E_FE_NO_COLLECTIBLES = "E_FE_NO_COLLECTIBLES"  # AC-FE5 (wiring)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS festival_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    start_window INTEGER NOT NULL CHECK (start_window >= 0),
    end_window INTEGER NOT NULL CHECK (end_window > start_window),
    token_price INTEGER NOT NULL CHECK (token_price > 0),
    per_account_limit INTEGER NOT NULL CHECK (per_account_limit >= 1),
    edition_cap INTEGER CHECK (edition_cap IS NULL OR edition_cap >= 1),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0, 1)),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS festival_purchases (
    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    buyer_id TEXT NOT NULL,
    purchase_ref TEXT NOT NULL,
    price_paid INTEGER NOT NULL CHECK (price_paid > 0),
    spend_tx TEXT NOT NULL,
    purchase_window INTEGER NOT NULL CHECK (purchase_window >= 0),
    commemorative INTEGER NOT NULL CHECK (commemorative IN (0, 1)),
    purchased_utc TEXT NOT NULL,
    UNIQUE (buyer_id, purchase_ref)
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


class FestivalError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class FestivalFace:
    """Solar-term / festival limited-event face over one Ledger and
    one CollectiblesFace sharing the same DB file. Own connection
    and lock for the event + purchase tables; the commemorative
    award goes through the collectibles public API (reference law -
    never a second collectibles engine here). Every mutation runs
    inside BEGIN IMMEDIATE; rows are immutable once written. A
    missing collectibles face or an empty disclaimer refuses
    construction - no linkage, no door; no disclaimer, no door."""

    def __init__(self, ledger, collectibles, disclaimer):
        self.led = ledger
        if (collectibles is None or not callable(
                getattr(collectibles, "issue_certificate", None))):
            raise FestivalError(E_FE_NO_COLLECTIBLES,
                                "collectibles face required")
        if getattr(collectibles, "db_path", None) != ledger.db_path:
            raise FestivalError(E_FE_NO_COLLECTIBLES,
                               "collectibles must share the ledger DB file")
        self.col = collectibles
        text = str(disclaimer or "").strip()
        if not text:
            raise FestivalError(E_FE_NO_DISCLAIMER,
                                "resident disclaimer required")
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

    # -- event registry domain ---------------------------------------------

    def register_event(self, event_key, title, start_window, end_window,
                       token_price, per_account_limit, ai_generated,
                       edition_cap=None):
        """Register one limited event: an integer-tick window (the
        ads/venue schedule convention, end strictly after start),
        a token price for the limited item, a per-account purchase
        limit and an optional event-wide edition cap (None =
        uncapped). Exactly one row per event_key - a repeat is
        rejected with zero rows (AC-FE1). The declared AIGC label
        persists on the row and every view surfaces it (AC-FE6)."""
        key = str(event_key or "").strip()
        if not key:
            raise FestivalError(E_FE_BAD_EVENT, "event key required")
        if not str(title or "").strip():
            raise FestivalError(E_FE_BAD_EVENT, "title required")
        if not _is_int(start_window) or start_window < 0:
            raise FestivalError(E_FE_BAD_EVENT, "start_window must be"
                                                      " int >= 0")
        if not _is_int(end_window) or end_window <= start_window:
            raise FestivalError(E_FE_BAD_EVENT, "end_window must be"
                                                 " > start_window")
        if not _is_int(token_price) or token_price <= 0:
            raise FestivalError(E_FE_BAD_PRICE, str(token_price))
        if not _is_int(per_account_limit) or per_account_limit < 1:
            raise FestivalError(E_FE_BAD_EVENT,
                                "per_account_limit must be int >= 1")
        if edition_cap is not None and (not _is_int(edition_cap)
                                        or edition_cap < 1):
            raise FestivalError(E_FE_BAD_EVENT,
                                "edition_cap must be int >= 1 or None")
        if not isinstance(ai_generated, bool):
            raise FestivalError(E_FE_BAD_EVENT,
                                "ai_generated must be bool")
        label = 1 if ai_generated else 0
        with self._lock:
            row = self._conn.execute(
                "SELECT event_id FROM festival_events WHERE event_key = ?",
                (key,)).fetchone()
            if row is not None:
                raise FestivalError(E_FE_DUP_EVENT, key)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO festival_events (event_key, title,"
                    " start_window, end_window, token_price,"
                    " per_account_limit, edition_cap, ai_label,"
                    " registered_utc) VALUES (?,?,?,?,?,?,?,?,?)",
                    (key, str(title), start_window, end_window,
                     token_price, per_account_limit, edition_cap, label,
                     _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise FestivalError(E_FE_DUP_EVENT, key)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"event_id": cur.lastrowid, "event_key": key,
                "title": str(title), "start_window": start_window,
                "end_window": end_window, "token_price": token_price,
                "per_account_limit": per_account_limit,
                "edition_cap": edition_cap, "ai_label": label}

    def _require_event(self, event_id):
        """Validation + lookup under no lock (caller holds it).
        Returns the full event row."""
        if not _is_int(event_id) or event_id <= 0:
            raise FestivalError(E_FE_BAD_ARGS, str(event_id))
        row = self._conn.execute(
            "SELECT event_id, event_key, start_window, end_window,"
            " token_price, per_account_limit, edition_cap, ai_label"
            " FROM festival_events WHERE event_id = ?",
            (event_id,)).fetchone()
        if row is None:
            raise FestivalError(E_FE_UNKNOWN_EVENT, str(event_id))
        return row

    # -- sales domain --------------------------------------------------------

    def _award_commemorative(self, account_id, event_key):
        """Grant the event commemorative through the collectibles
        public API on the account's first purchase of the event
        (AC-FE5). A pre-awarded account (platform direct award
        before any purchase) hits the collectibles UNIQUE backstop
        (E_CL_DUP): the purchase stays legal with no double award -
        this row simply did not grant it. Returns 1 when this call
        granted, 0 when the account already held it; any other
        collectibles failure propagates (fail-closed, no silent
        award loss)."""
        event_ref = "festival:" + event_key
        try:
            self.col.issue_certificate(account_id, event_ref, event_ref)
            return 1
        except Exception as exc:  # noqa: BLE001 (collectibles surface)
            if getattr(exc, "code", "") == "E_CL_DUP":
                return 0
            raise

    def buy_event_item(self, buyer_id, event_id, at_window, ref):
        """Buy the limited event item at one window tick. The event
        window must cover the tick - both edges inclusive - and one
        tick outside refuses with zero charge (AC-FE2); the replay
        gate, the per-account purchase limit and the edition cap all
        reject BEFORE the spend so a rejected buy never charges
        (AC-FE3/AC-FE4). Exactly one spend per purchase, bound to
        its tx; the first purchase per (account, event) grants the
        event commemorative collectible through the collectibles
        public API (AC-FE5). Returns the full provenance envelope
        with the declared AIGC label and the resident disclaimer
        (AC-FE6)."""
        if not str(buyer_id or "").startswith("usr:"):
            raise FestivalError(E_FE_BAD_ACCOUNT, buyer_id)
        r = str(ref or "").strip()
        if not r:
            raise FestivalError(E_FE_BAD_ARGS, "purchase ref required")
        if not _is_int(at_window) or at_window < 0:
            raise FestivalError(E_FE_BAD_ARGS, "at_window must be"
                                                " int >= 0")
        with self._lock:
            ev = self._require_event(event_id)
            e_key, e_start, e_end = ev[1], int(ev[2]), int(ev[3])
            price, limit, cap = int(ev[4]), int(ev[5]), ev[6]
            if not (e_start <= at_window <= e_end):
                raise FestivalError(E_FE_WINDOW,
                                    "%s: tick %d outside %d..%d"
                                    % (e_key, at_window, e_start, e_end))
            row = self._conn.execute(
                "SELECT purchase_id FROM festival_purchases"
                " WHERE buyer_id = ? AND purchase_ref = ?",
                (buyer_id, r)).fetchone()
            if row is not None:
                raise FestivalError(E_FE_DUP_PURCHASE,
                                    "%s/%s" % (buyer_id, r))
            n_buyer = self._conn.execute(
                "SELECT COUNT(*) FROM festival_purchases"
                " WHERE buyer_id = ? AND event_id = ?",
                (buyer_id, event_id)).fetchone()[0]
            if n_buyer >= limit:
                raise FestivalError(E_FE_LIMIT,
                                    "%s at limit %d on %s"
                                    % (buyer_id, limit, e_key))
            if cap is not None:
                n_all = self._conn.execute(
                    "SELECT COUNT(*) FROM festival_purchases"
                    " WHERE event_id = ?", (event_id,)).fetchone()[0]
                if n_all >= int(cap):
                    raise FestivalError(E_FE_SOLD_OUT,
                                        "%s cap %d reached"
                                        % (e_key, cap))
            self.led.ensure_account(buyer_id,
                                    census_avatar_id=buyer_id[4:])
            spend_tx = self.led.spend(buyer_id, price, r, "order")
            commemorative = 0
            if n_buyer == 0:
                commemorative = self._award_commemorative(
                    buyer_id, e_key)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO festival_purchases (event_id, buyer_id,"
                    " purchase_ref, price_paid, spend_tx, purchase_window,"
                    " commemorative, purchased_utc) VALUES (?,?,?,?,?,?,?,?)",
                    (event_id, buyer_id, r, price, spend_tx, at_window,
                     commemorative, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise FestivalError(E_FE_DUP_PURCHASE,
                                    "%s/%s" % (buyer_id, r))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"purchase_id": cur.lastrowid, "event_id": event_id,
                "event_key": e_key, "buyer_id": buyer_id,
                "price_paid": price, "spend_tx": spend_tx,
                "purchase_window": at_window,
                "commemorative": commemorative,
                "ai_label": int(ev[7]),
                "disclaimer": self.disclaimer}

    # -- read faces ----------------------------------------------------------

    def event_view(self, event_id):
        """One event surface: window, params, declared AIGC label,
        purchase/participant counts; the envelope carries the
        resident non-advisory disclaimer (AC-FE6). Pure read."""
        with self._lock:
            row = self._conn.execute(
                "SELECT event_id, event_key, title, start_window,"
                " end_window, token_price, per_account_limit,"
                " edition_cap, ai_label, registered_utc"
                " FROM festival_events WHERE event_id = ?",
                (event_id,)).fetchone()
            if row is None:
                raise FestivalError(E_FE_UNKNOWN_EVENT, str(event_id))
            n_buy, n_people = self._conn.execute(
                "SELECT COUNT(*), COUNT(DISTINCT buyer_id) FROM"
                " festival_purchases WHERE event_id = ?",
                (event_id,)).fetchone()
        return {"event_id": int(row[0]), "event_key": row[1],
                "title": row[2], "start_window": int(row[3]),
                "end_window": int(row[4]), "token_price": int(row[5]),
                "per_account_limit": int(row[6]),
                "edition_cap": None if row[7] is None else int(row[7]),
                "ai_label": int(row[8]), "registered_utc": row[9],
                "purchase_count": int(n_buy),
                "participant_count": int(n_people),
                "disclaimer": self.disclaimer}

    def active_events(self, at_window):
        """Schedule-window listing face: every event whose window
        covers at_window (inclusive on both edges - the ads/venue
        coverage convention), each row carrying its declared AIGC
        label; the envelope carries the resident disclaimer
        (AC-FE6). Pure read, zero token movement."""
        if not _is_int(at_window) or at_window < 0:
            raise FestivalError(E_FE_BAD_ARGS, "at_window must be"
                                               " int >= 0")
        with self._lock:
            rows = self._conn.execute(
                "SELECT event_id, event_key, title, start_window,"
                " end_window, token_price, ai_label FROM"
                " festival_events WHERE start_window <= ?"
                " AND end_window >= ? ORDER BY event_id",
                (at_window, at_window)).fetchall()
        return {"at_window": at_window,
                "disclaimer": self.disclaimer,
                "events": [{"event_id": int(r[0]), "event_key": r[1],
                            "title": r[2], "start_window": int(r[3]),
                            "end_window": int(r[4]),
                            "token_price": int(r[5]),
                            "ai_label": int(r[6])} for r in rows]}

    def festival_board(self, event_id):
        """Per-event purchase ledger view: every purchase row with
        its buyer, immutable price copy, bound spend tx, window
        tick and commemorative flag - the audit trail of the
        limited sale (AC-FE5/AC-FE6). Pure read."""
        with self._lock:
            self._require_event(event_id)
            rows = self._conn.execute(
                "SELECT purchase_id, buyer_id, price_paid, spend_tx,"
                " purchase_window, commemorative, purchased_utc FROM"
                " festival_purchases WHERE event_id = ?"
                " ORDER BY purchase_id", (event_id,)).fetchall()
        return {"event_id": event_id, "disclaimer": self.disclaimer,
                "purchases": [{"purchase_id": int(r[0]),
                               "buyer_id": r[1], "price_paid": int(r[2]),
                               "spend_tx": r[3],
                               "purchase_window": int(r[4]),
                               "commemorative": int(r[5]),
                               "purchased_utc": r[6]} for r in rows]}
