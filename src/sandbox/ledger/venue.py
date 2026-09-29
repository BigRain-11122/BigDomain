"""City venue rental + storefront tenancy face over the token ledger
sandbox (BigDomain explore queue #2, claimed round R605).

Two occupancy domains ride on the P-47-2b token ledger:

  - kind 'venue'      : capacity-bounded concurrent scene rental in
                        integer tick windows (a rental occupies one
                        capacity slot for [start, start+term-1])
  - kind 'storefront' : exclusive single-tenant lease per storefront
                        (tenant branding slot; early termination ends
                        occupancy without moving tokens)

Occupancy-is-not-tokens isolation law: each rental/lease books
exactly one token spend (term x caller-supplied price, integer) and
nothing else in this module ever touches the token domain -
capacity checks, activation, expiry, termination and read faces move
zero tokens, and no verb converts occupancy back into tokens or
moves an occupancy between accounts. Pricing values, term limits
and any fee-reversal or compensation face are P1 [needs-CEO]
approval items; no config keys are added by this module (prices
arrive as caller arguments only).

Pre-registered criteria AC-VN1..AC-VN7 live in the R605 backlog row
and were written before this code existed (honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: one extra table pair in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

E_VN_UNKNOWN = "E_VN_UNKNOWN"          # venue not registered
E_VN_FULL = "E_VN_FULL"                # AC-VN2 capacity gate
E_VN_DUP = "E_VN_DUP"                  # AC-VN4 identical rental
E_VN_LEASE_ACTIVE = "E_VN_LEASE_ACTIVE"  # AC-VN5 storefront exclusivity
E_VN_NO_LEASE = "E_VN_NO_LEASE"        # terminate on nothing active
E_VN_BAD_ARGS = "E_VN_BAD_ARGS"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS venue_registry (
    venue_id TEXT PRIMARY KEY,
    capacity INTEGER NOT NULL CHECK (capacity >= 1)
);
CREATE TABLE IF NOT EXISTS venue_occupancy (
    occ_id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL CHECK (kind IN ('venue','storefront')),
    unit_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    start_tick INTEGER NOT NULL,
    end_tick INTEGER NOT NULL,
    bound_spend_tx TEXT NOT NULL,
    terminated_tick INTEGER,
    created_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return (isinstance(value, int) and not isinstance(value, bool))


class VenueError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class VenueFace:
    """Venue rental + storefront tenancy face over one Ledger instance.
    Own connection and lock into the same DB file; every mutation
    runs inside BEGIN IMMEDIATE."""

    def __init__(self, ledger):
        self.led = ledger
        self.db_path = ledger.db_path
        # RLock: lease_storefront auto-registers the storefront unit via
        # register_venue() while already holding this lock (reentrancy)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- internal helpers -------------------------------------------------

    def _check_common(self, account_id, start_tick, term_windows,
                      rent_per_window, ref):
        if not account_id.startswith("usr:"):
            raise VenueError(E_VN_BAD_ARGS, "tenants are usr:* only")
        if not _is_int(start_tick) or start_tick < 0:
            raise VenueError(E_VN_BAD_ARGS, "start_tick must be int >= 0")
        if not _is_int(term_windows) or term_windows < 1:
            raise VenueError(E_VN_BAD_ARGS, "term_windows must be int >= 1")
        if (not _is_int(rent_per_window) or rent_per_window <= 0):
            raise VenueError(E_VN_BAD_ARGS,
                             "rent_per_window must be int > 0")
        if not str(ref).strip():
            raise VenueError(E_VN_BAD_ARGS, "rental ref required")

    def _effective_end(self, row_end, terminated_tick):
        if terminated_tick is None:
            return row_end
        return terminated_tick if terminated_tick < row_end else row_end

    def _overlap_active(self, kind, unit_id, start, end):
        """Occupancy rows of one unit still effective inside [start, end].
        A terminated row stops counting from terminated_tick + 1."""
        rows = self._conn.execute(
            "SELECT start_tick, end_tick, terminated_tick"
            " FROM venue_occupancy WHERE kind = ? AND unit_id = ?",
            (kind, unit_id)).fetchall()
        hits = []
        for r_start, r_end, r_term in rows:
            eff = self._effective_end(r_end, r_term)
            if eff >= start and r_start <= end:
                hits.append((r_start, r_end, r_term))
        return hits

    # -- writer faces -------------------------------------------------------

    def register_venue(self, venue_id, capacity):
        """Mechanism registration of a rentable venue with its concurrent
        capacity (>= 1). Re-registering the same id with the same
        capacity is idempotent; a different capacity is rejected."""
        if not _is_int(capacity) or capacity < 1:
            raise VenueError(E_VN_BAD_ARGS, "capacity must be int >= 1")
        if not str(venue_id).strip():
            raise VenueError(E_VN_BAD_ARGS, "venue_id required")
        with self._lock:
            row = self._conn.execute(
                "SELECT capacity FROM venue_registry WHERE venue_id = ?",
                (venue_id,)).fetchone()
            if row is None:
                self._conn.execute("BEGIN IMMEDIATE")
                try:
                    self._conn.execute(
                        "INSERT INTO venue_registry (venue_id, capacity)"
                        " VALUES (?,?)", (venue_id, capacity))
                    self._conn.execute("COMMIT")
                except BaseException:
                    self._conn.execute("ROLLBACK")
                    raise
            elif int(row[0]) != capacity:
                raise VenueError(E_VN_BAD_ARGS,
                                 "venue already registered with capacity %d"
                                 % int(row[0]))
        return {"venue_id": venue_id, "capacity": capacity}

    def rent_venue(self, account_id, venue_id, start_tick, term_windows,
                   rent_per_window, ref):
        """Venue rental: pre-checks run BEFORE the spend (a rejected
        rental never charges), then exactly one token spend books the
        whole-window fee, then the occupancy row binds that spend tx."""
        self._check_common(account_id, start_tick, term_windows,
                           rent_per_window, ref)
        end_tick = start_tick + term_windows - 1
        with self._lock:
            row = self._conn.execute(
                "SELECT capacity FROM venue_registry WHERE venue_id = ?",
                (venue_id,)).fetchone()
            if row is None:
                raise VenueError(E_VN_UNKNOWN, venue_id)
            capacity = int(row[0])
            dup = self._conn.execute(
                "SELECT COUNT(*) FROM venue_occupancy"
                " WHERE kind = 'venue' AND unit_id = ? AND account_id = ?"
                " AND start_tick = ? AND end_tick = ?",
                (venue_id, account_id, start_tick, end_tick)).fetchone()[0]
            if dup:
                raise VenueError(E_VN_DUP, venue_id)
            active = self._overlap_active("venue", venue_id,
                                          start_tick, end_tick)
            if len(active) >= capacity:
                raise VenueError(E_VN_FULL,
                                 "%d/%d slots taken" % (len(active), capacity))
        self.led.ensure_account(account_id,
                                census_avatar_id=account_id[4:])
        fee = term_windows * rent_per_window
        spend_tx = self.led.spend(account_id, fee, str(ref), "order")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO venue_occupancy"
                    " (kind, unit_id, account_id, start_tick, end_tick,"
                    "  bound_spend_tx, created_utc)"
                    " VALUES ('venue',?,?,?,?,?,?)",
                    (venue_id, account_id, start_tick, end_tick,
                     spend_tx, _now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"venue_id": venue_id, "fee": fee, "spend_tx_id": spend_tx,
                "start_tick": start_tick, "end_tick": end_tick}

    def lease_storefront(self, tenant_account, storefront_id, start_tick,
                         term_windows, rent_per_window, ref):
        """Storefront tenancy: a storefront is an exclusive unit
        (implicit capacity 1, auto-registered on first lease). One
        active tenant at a time inside overlapping windows."""
        self._check_common(tenant_account, start_tick, term_windows,
                           rent_per_window, ref)
        end_tick = start_tick + term_windows - 1
        with self._lock:
            self.register_venue(storefront_id, 1)
            dup = self._conn.execute(
                "SELECT COUNT(*) FROM venue_occupancy"
                " WHERE kind = 'storefront' AND unit_id = ?"
                " AND account_id = ? AND start_tick = ? AND end_tick = ?",
                (storefront_id, tenant_account, start_tick, end_tick)
                ).fetchone()[0]
            if dup:
                raise VenueError(E_VN_DUP, storefront_id)
            active = self._overlap_active("storefront", storefront_id,
                                          start_tick, end_tick)
            if active:
                raise VenueError(E_VN_LEASE_ACTIVE, storefront_id)
        self.led.ensure_account(tenant_account,
                                census_avatar_id=tenant_account[4:])
        fee = term_windows * rent_per_window
        spend_tx = self.led.spend(tenant_account, fee, str(ref), "order")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO venue_occupancy"
                    " (kind, unit_id, account_id, start_tick, end_tick,"
                    "  bound_spend_tx, created_utc)"
                    " VALUES ('storefront',?,?,?,?,?,?)",
                    (storefront_id, tenant_account, start_tick, end_tick,
                     spend_tx, _now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"storefront_id": storefront_id, "fee": fee,
                "spend_tx_id": spend_tx, "start_tick": start_tick,
                "end_tick": end_tick}

    def terminate_lease(self, storefront_id, at_tick):
        """Early termination: ends the active storefront lease AT
        at_tick (occupancy stays effective through at_tick, free from
        at_tick + 1). Zero token-ledger involvement - fee reversal of
        any kind is a P1 [needs-CEO] approval face, not a mechanism
        here."""
        if not _is_int(at_tick) or at_tick < 0:
            raise VenueError(E_VN_BAD_ARGS, "at_tick must be int >= 0")
        with self._lock:
            rows = self._conn.execute(
                "SELECT occ_id, account_id, start_tick, end_tick,"
                " terminated_tick FROM venue_occupancy"
                " WHERE kind = 'storefront' AND unit_id = ?", (storefront_id,)
                ).fetchall()
            victim = None
            for r in rows:
                eff = self._effective_end(r[3], r[4])
                if r[2] <= at_tick <= eff:
                    victim = r
                    break
            if victim is None:
                raise VenueError(E_VN_NO_LEASE, storefront_id)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "UPDATE venue_occupancy SET terminated_tick = ?"
                    " WHERE occ_id = ?", (at_tick, victim[0]))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"storefront_id": storefront_id,
                "terminated_for": victim[1], "terminated_at": at_tick}

    # -- read faces -----------------------------------------------------------

    def is_rented(self, venue_id, account_id, at_tick):
        """Is this account's venue rental effective at this tick?"""
        with self._lock:
            rows = self._conn.execute(
                "SELECT start_tick, end_tick, terminated_tick"
                " FROM venue_occupancy WHERE kind = 'venue'"
                " AND unit_id = ? AND account_id = ?",
                (venue_id, account_id)).fetchall()
        for r_start, r_end, r_term in rows:
            eff = self._effective_end(r_end, r_term)
            if r_start <= at_tick <= eff:
                return True
        return False

    def tenant_of(self, storefront_id, at_tick):
        """The effective tenant of a storefront at a tick, or None."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT account_id, start_tick, end_tick, terminated_tick"
                " FROM venue_occupancy WHERE kind = 'storefront'"
                " AND unit_id = ?", (storefront_id,)).fetchall()
        for account_id, r_start, r_end, r_term in rows:
            eff = self._effective_end(r_end, r_term)
            if r_start <= at_tick <= eff:
                return account_id
        return None

    def occupancy_ledger(self, unit_id):
        """Full occupancy history of one unit with provenance (audit
        trail: rows survive expiry and termination)."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT kind, account_id, start_tick, end_tick,"
                " terminated_tick, bound_spend_tx"
                " FROM venue_occupancy WHERE unit_id = ?"
                " ORDER BY start_tick, occ_id", (unit_id,)).fetchall()
        return [{"kind": r[0], "account_id": r[1], "start_tick": int(r[2]),
                 "end_tick": int(r[3]),
                 "terminated_tick": (int(r[4]) if r[4] is not None else None),
                 "bound_spend_tx": r[5]} for r in rows]
