"""Virtual-exhibition ad-slot schedule face over the venue + token
ledger sandbox (BigDomain R622; canon = BLUEPRINT sec-4 B3 virtual
exhibition / ad-slot price row: QUANT giant-screen carousel 2000
CNY/week, building naming rights 10000 CNY/year for street or metro
names, lobby splash ad 5000 CNY/week; claimed from the explore-lane
B3 row which pins the mechanism = schedule-window booking / carousel
rotation / exclusivity gate).

Three purchasable ad products, one booking per window span:

  kind 'quant_screen_carousel' : capacity-bounded concurrent rotation
      on a giant screen - rotation_slots advertisers share a window,
      the lineup order is the booking order
  kind 'building_naming'       : exclusive naming right on one
      building (street / metro name), single holder at a time
  kind 'lobby_splash'          : exclusive lobby splash ad, single
      holder at a time

Venue-reference law (the B3 row's "reference the venue structure, do
not double-build" clause): this module owns exactly one small table,
ad_units, which registers which ad kind a unit carries. Every WRITE
goes through the VenueFace public API (rent_venue for the carousel
capacity domain, lease_storefront for the exclusive domains), so all
occupancy rows, capacity gates, exclusivity gates and spend
provenance live in the venue structures - zero second occupancy
engine here. Read faces join those venue structures directly (same
DB file); the wrapped error surface is ad-domain (E_AD_*).

Occupancy-is-not-tokens isolation law (venue posture carried over):
each booking is exactly one token spend (windows x caller-supplied
price per window) and nothing else in this module ever touches the
token domain - lineup, holder and board faces move zero tokens, and
no verb converts a booking back into tokens or moves it between
accounts. Booking rows are immutable once written (no UPDATE surface
in this module); cancellation or fee reversal of any kind is a P1
[needs-CEO] approval face, not a mechanism here.

Prices are caller-supplied in the sandbox; the production price
points (2000 / 10000 / 5000 CNY anchors) and any launch gating are
a P1 item for CEO, approval-only ([needs-CEO]). No config keys are
added by this module.

Pre-registered criteria AC-AD1..AC-AD7 live in the R622 backlog row
and were written before this code existed (honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: one extra table in the same SQLite DB (WAL, single writer,
same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

E_AD_UNKNOWN = "E_AD_UNKNOWN"        # unit not in the ad registry
E_AD_FULL = "E_AD_FULL"              # carousel rotation slots full
E_AD_TAKEN = "E_AD_TAKEN"            # exclusive unit already held
E_AD_DUP = "E_AD_DUP"                # identical booking replay
E_AD_KIND_MISMATCH = "E_AD_KIND_MISMATCH"  # registry kind conflict
E_AD_BAD_ARGS = "E_AD_BAD_ARGS"

KINDS = ("quant_screen_carousel", "building_naming", "lobby_splash")
EXCLUSIVE_KINDS = ("building_naming", "lobby_splash")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ad_units (
    unit_id TEXT PRIMARY KEY,
    ad_kind TEXT NOT NULL CHECK (ad_kind IN
        ('quant_screen_carousel','building_naming','lobby_splash')),
    capacity INTEGER NOT NULL CHECK (capacity >= 1),
    registered_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return (isinstance(value, int) and not isinstance(value, bool))


class AdsError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class AdsFace:
    """Ad-slot schedule face over one Ledger + one VenueFace instance
    sharing the same DB file. Own connection and lock for the ad_units
    registry; every booking delegates to the venue public API."""

    def __init__(self, ledger, venue):
        self.led = ledger
        self.ven = venue
        if getattr(venue, "db_path", None) != ledger.db_path:
            raise AdsError(E_AD_BAD_ARGS,
                           "venue must share the ledger DB file")
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(ledger.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- internal helpers -------------------------------------------------

    def _kind_of(self, unit_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT ad_kind, capacity FROM ad_units WHERE unit_id = ?",
                (unit_id,)).fetchone()
        return row  # None or (ad_kind, capacity)

    def _wrap_venue(self, exc):
        """Map a VenueError onto the ad-domain error surface so callers
        of the ad face never need venue internals (reference law: the
        venue stays the engine, this module stays the API)."""
        mapping = {"E_VN_UNKNOWN": E_AD_UNKNOWN,
                   "E_VN_FULL": E_AD_FULL,
                   "E_VN_LEASE_ACTIVE": E_AD_TAKEN,
                   "E_VN_DUP": E_AD_DUP}
        code = mapping.get(getattr(exc, "code", ""), E_AD_BAD_ARGS)
        return AdsError(code, getattr(exc, "detail", ""))

    def _check_book_args(self, advertiser, start_window, windows,
                         price_per_window, ref):
        if not str(advertiser).startswith("usr:"):
            raise AdsError(E_AD_BAD_ARGS, "advertisers are usr:* only")
        if not _is_int(start_window) or start_window < 0:
            raise AdsError(E_AD_BAD_ARGS, "start_window must be int >= 0")
        if not _is_int(windows) or windows < 1:
            raise AdsError(E_AD_BAD_ARGS, "windows must be int >= 1")
        if not _is_int(price_per_window) or price_per_window <= 0:
            raise AdsError(E_AD_BAD_ARGS, "price_per_window must be int > 0")
        if not str(ref).strip():
            raise AdsError(E_AD_BAD_ARGS, "booking ref required")

    def _occ_of_spend(self, spend_tx):
        with self._lock:
            row = self._conn.execute(
                "SELECT occ_id, start_tick, end_tick FROM"
                " venue_occupancy WHERE bound_spend_tx = ?",
                (spend_tx,)).fetchone()
        return row

    # -- writer faces -------------------------------------------------------

    def register_ad_unit(self, unit_id, ad_kind, rotation_slots=None):
        """Mechanism registration of one ad unit under its product kind.
        Carousel units need rotation_slots >= 1 (that many advertisers
        share a window); exclusive kinds are inherently single-slot
        (capacity 1, rotation_slots must be None or 1). The unit's
        capacity is registered in the venue registry (same structure,
        no second registry); re-registering the same unit with the
        same kind and capacity is idempotent, a different kind is
        E_AD_KIND_MISMATCH, a different capacity is E_AD_BAD_ARGS."""
        unit_id = str(unit_id or "").strip()
        if not unit_id:
            raise AdsError(E_AD_BAD_ARGS, "unit_id required")
        if ad_kind not in KINDS:
            raise AdsError(E_AD_BAD_ARGS, "unknown ad kind")
        if ad_kind == "quant_screen_carousel":
            if not _is_int(rotation_slots) or rotation_slots < 1:
                raise AdsError(E_AD_BAD_ARGS,
                               "carousel needs rotation_slots int >= 1")
            capacity = rotation_slots
        else:
            if rotation_slots is not None and rotation_slots != 1:
                raise AdsError(E_AD_BAD_ARGS,
                               "exclusive kinds are single-slot")
            capacity = 1
        with self._lock:
            row = self._conn.execute(
                "SELECT ad_kind, capacity FROM ad_units WHERE unit_id = ?",
                (unit_id,)).fetchone()
            if row is not None:
                if row[0] != ad_kind:
                    raise AdsError(E_AD_KIND_MISMATCH,
                                   "%s already registered as %s"
                                   % (unit_id, row[0]))
                if int(row[1]) != capacity:
                    raise AdsError(E_AD_BAD_ARGS,
                                   "%s already registered with capacity %d"
                                   % (unit_id, int(row[1])))
                return {"unit_id": unit_id, "ad_kind": ad_kind,
                        "capacity": capacity, "idempotent": True}
        try:
            self.ven.register_venue(unit_id, capacity)
        except Exception as exc:  # venue raise -> ad surface
            if getattr(exc, "code", None):
                raise self._wrap_venue(exc)
            raise
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO ad_units (unit_id, ad_kind, capacity,"
                    " registered_utc) VALUES (?,?,?,?)",
                    (unit_id, ad_kind, capacity, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise AdsError(E_AD_KIND_MISMATCH, unit_id)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"unit_id": unit_id, "ad_kind": ad_kind,
                "capacity": capacity, "idempotent": False}

    def book(self, advertiser, unit_id, start_window, windows,
             price_per_window, ref):
        """Schedule-window booking face (advance booking: any future
        start_window). The unit's registered kind picks the venue verb:
        carousel -> rent_venue (capacity gate), exclusive kinds ->
        lease_storefront (exclusivity gate). Exactly one token spend
        per booking (windows x price), bound into the venue occupancy
        row; a rejected booking never charges. Receipt carries the
        occupancy row id and span as provenance."""
        self._check_book_args(advertiser, start_window, windows,
                              price_per_window, ref)
        row = self._kind_of(unit_id)
        if row is None:
            raise AdsError(E_AD_UNKNOWN, unit_id)
        kind, _capacity = row[0], int(row[1])
        try:
            if kind == "quant_screen_carousel":
                res = self.ven.rent_venue(advertiser, unit_id,
                                           start_window, windows,
                                           price_per_window, ref)
            else:
                res = self.ven.lease_storefront(advertiser, unit_id,
                                                start_window, windows,
                                                price_per_window, ref)
        except Exception as exc:  # venue raise -> ad surface
            if getattr(exc, "code", None):
                raise self._wrap_venue(exc)
            raise
        occ = self._occ_of_spend(res["spend_tx_id"])
        return {"unit_id": unit_id, "ad_kind": kind, "occ_id": int(occ[0]),
                "fee": res["fee"], "spend_tx": res["spend_tx_id"],
                "start_window": int(occ[1]), "end_window": int(occ[2])}

    # -- read faces -----------------------------------------------------------

    def _require_kind(self, unit_id, want_kind):
        row = self._kind_of(unit_id)
        if row is None:
            raise AdsError(E_AD_UNKNOWN, unit_id)
        if want_kind is not None and row[0] != want_kind:
            raise AdsError(E_AD_KIND_MISMATCH,
                           "%s is registered as %s" % (unit_id, row[0]))
        return row

    def carousel_lineup(self, screen_id, at_window):
        """Carousel rotation schedule: the advertisers whose booked
        windows cover at_window, in booking order (rotation order),
        with 1-based positions. Read-only, zero token movement."""
        if not _is_int(at_window) or at_window < 0:
            raise AdsError(E_AD_BAD_ARGS, "at_window must be int >= 0")
        kind_row = self._require_kind(screen_id, "quant_screen_carousel")
        with self._lock:
            rows = self._conn.execute(
                "SELECT occ_id, account_id, start_tick, end_tick,"
                " terminated_tick FROM venue_occupancy"
                " WHERE kind = 'venue' AND unit_id = ?"
                " ORDER BY occ_id", (screen_id,)).fetchall()
        advertisers = []
        for occ_id, account_id, r_start, r_end, r_term in rows:
            eff = r_end if r_term is None else min(r_end, r_term)
            if r_start <= at_window <= eff:
                advertisers.append({"position": len(advertisers) + 1,
                                    "occ_id": int(occ_id),
                                    "account_id": account_id,
                                    "start_window": int(r_start),
                                    "end_window": int(eff)})
        return {"screen_id": screen_id, "at_window": at_window,
                "rotation_slots": int(kind_row[1]),
                "advertisers": advertisers}

    def _exclusive_holder(self, unit_id, at_window, want_kind):
        if not _is_int(at_window) or at_window < 0:
            raise AdsError(E_AD_BAD_ARGS, "at_window must be int >= 0")
        self._require_kind(unit_id, want_kind)
        return self.ven.tenant_of(unit_id, at_window)

    def naming_holder(self, building_id, at_window):
        """The building naming-right holder at a window, or None
        (exclusivity: at most one). Read-only."""
        return self._exclusive_holder(building_id, at_window,
                                      "building_naming")

    def splash_owner(self, splash_id, at_window):
        """The lobby splash holder at a window, or None. Read-only."""
        return self._exclusive_holder(splash_id, at_window, "lobby_splash")

    def schedule_board(self, unit_id):
        """Schedule-window view of one unit: every booking row with
        its advertiser, span and bound spend tx (audit trail rides the
        venue occupancy ledger; read-only)."""
        kind_row = self._require_kind(unit_id, None)
        rows = self.ven.occupancy_ledger(unit_id)
        bookings = [{"account_id": r["account_id"],
                     "start_window": r["start_tick"],
                     "end_window": r["end_tick"],
                     "terminated_tick": r["terminated_tick"],
                     "spend_tx": r["bound_spend_tx"]} for r in rows]
        return {"unit_id": unit_id, "ad_kind": kind_row[0],
                "bookings": bookings}
