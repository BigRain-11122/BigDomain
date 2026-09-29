"""Studio onboarding annual-fee face over the venue + token ledger
sandbox (BigDomain R625; canon = BLUEPRINT sec-4 B-side price rows
B1 game-studio onboarding 9,800 CNY/year and B2 quant-studio /
researcher onboarding 19,800 CNY/year; claimed from the explore-lane
B1 row which pins the B2 row's same-structure joint-delivery note,
combined into one piece; adjacency check = venue storefront occupancy
domain, reference-not-double-build).

Two studio kinds in one registry:

  kind 'game_studio'  : idea-pool access + player-traffic boost +
                        virtual studio floor (three-benefit bundle)
  kind 'quant_studio' : stock-inspiration feed + co-create
                        observation entry + QUANT city screen
                        spotlight (three-benefit bundle)

Reference law (identity.py / ads.py posture carried over): this
module owns exactly one small table, studio_products, which
registers which kind a studio carries. Every WRITE goes through
the VenueFace public API - the annual onboarding rides
VenueFace.lease_storefront with a one-window year lease (one window
index = one subscription year), so the occupancy row, the
exclusivity gates and the spend provenance live in the venue
structures. Zero second occupancy engine here (the module source
has no INSERT INTO those structures). Read faces join those
structures directly (same DB file); the wrapped error surface is
studio-domain (E_ST_*).

Annual-fee window semantics: same studio re-onboarded in the same
year window is rejected E_ST_DUP before the spend (zero charge); a
different account hitting the same studio-year is rejected
E_ST_TAKEN (the venue exclusivity gate); renewal = onboarding a
later year window (advance booking). The two kinds are independent
products - one account may hold a game-studio seat and a
quant-studio seat in the same year, and several studios of the same
kind may be onboarded in parallel (each = its own unit).

Onboarding-is-not-tokens isolation law: each onboarding is exactly
one token spend and nothing else in this module ever touches the
token domain - registry, benefit, tenant and profile faces move
zero tokens, and no verb turns a subscription back into tokens or
moves it between accounts. Registry rows are immutable once
written (no row-mutation surface in this module); cancellation,
fee reversal of any kind is a P1 [needs-CEO] approval face, not a
mechanism here.

Prices are caller-supplied in the sandbox; the production price
points (9,800 / 19,800 CNY per year anchors) and any launch gating
are a P1 item for CEO, approval-only ([needs-CEO]). No config keys
are added by this module.

Pre-registered criteria AC-SB1..AC-SB7 live in the R625 backlog
row and were written before this code existed (honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: one extra table in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

E_ST_UNKNOWN = "E_ST_UNKNOWN"          # studio not in the registry
E_ST_KIND_MISMATCH = "E_ST_KIND_MISMATCH"  # registry kind conflict
E_ST_DUP = "E_ST_DUP"                 # same studio-year replay
E_ST_TAKEN = "E_ST_TAKEN"             # studio-year held by another
E_ST_BAD_ARGS = "E_ST_BAD_ARGS"

KINDS = ("game_studio", "quant_studio")

# Canon three-benefit bundles per kind (BLUEPRINT sec-4 B1/B2 rows).
BENEFITS = {
    "game_studio": ("idea_pool_access", "player_traffic_boost",
                    "studio_floor"),
    "quant_studio": ("stock_inspiration_feed",
                     "co_create_observation_entry",
                     "quant_screen_spotlight"),
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS studio_products (
    studio_id TEXT PRIMARY KEY,
    st_kind TEXT NOT NULL CHECK (st_kind IN
        ('game_studio','quant_studio')),
    registered_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return (isinstance(value, int) and not isinstance(value, bool))


class StudioError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class StudioFace:
    """Studio onboarding face over one Ledger + one VenueFace sharing
    the same DB file. Own connection and lock for the studio_products
    registry; every onboarding delegates to the venue public API."""

    def __init__(self, ledger, venue):
        self.led = ledger
        self.ven = venue
        if getattr(venue, "db_path", None) != ledger.db_path:
            raise StudioError(E_ST_BAD_ARGS,
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

    def _kind_of(self, studio_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT st_kind FROM studio_products"
                " WHERE studio_id = ?", (studio_id,)).fetchone()
        return row  # None or (st_kind,)

    def _wrap(self, exc):
        """Map a Venue error onto the studio-domain surface so callers
        of this face never need engine internals (reference law: the
        venue stays the engine, this module is the API)."""
        mapping = {"E_VN_UNKNOWN": E_ST_UNKNOWN,
                   "E_VN_LEASE_ACTIVE": E_ST_TAKEN,
                   "E_VN_DUP": E_ST_DUP,
                   "E_VN_BAD_ARGS": E_ST_BAD_ARGS}
        code = mapping.get(getattr(exc, "code", ""), E_ST_BAD_ARGS)
        return StudioError(code, getattr(exc, "detail", ""))

    def _check_buy_args(self, account_id, price, year_index, ref):
        if not str(account_id).startswith("usr:"):
            raise StudioError(E_ST_BAD_ARGS, "owners are usr:* only")
        if not _is_int(price) or price <= 0:
            raise StudioError(E_ST_BAD_ARGS, "price must be int > 0")
        if not _is_int(year_index) or year_index < 0:
            raise StudioError(E_ST_BAD_ARGS, "year_index must be int >= 0")
        if not str(ref).strip():
            raise StudioError(E_ST_BAD_ARGS, "onboarding ref required")

    # -- writer faces -------------------------------------------------------

    def register_studio(self, studio_id, st_kind):
        """Mechanism registration of one studio product under its kind
        (the benefit bundle is canon-static per kind, not a registry
        column). Re-registering the same studio with the same kind is
        idempotent; a different kind is E_ST_KIND_MISMATCH."""
        studio_id = str(studio_id or "").strip()
        if not studio_id:
            raise StudioError(E_ST_BAD_ARGS, "studio_id required")
        if st_kind not in KINDS:
            raise StudioError(E_ST_BAD_ARGS, "unknown studio kind")
        with self._lock:
            row = self._conn.execute(
                "SELECT st_kind FROM studio_products"
                " WHERE studio_id = ?", (studio_id,)).fetchone()
            if row is not None:
                if row[0] != st_kind:
                    raise StudioError(E_ST_KIND_MISMATCH,
                                      "%s already registered as %s"
                                      % (studio_id, row[0]))
                return {"studio_id": studio_id, "st_kind": st_kind,
                        "idempotent": True}
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO studio_products (studio_id, st_kind,"
                    " registered_utc) VALUES (?,?,?)",
                    (studio_id, st_kind, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise StudioError(E_ST_KIND_MISMATCH, studio_id)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"studio_id": studio_id, "st_kind": st_kind,
                "idempotent": False}

    def onboard_studio(self, account_id, studio_id, year_index,
                       annual_price, ref):
        """Annual onboarding: the registered kind carries the benefit
        bundle; the seat rides VenueFace.lease_storefront as one
        exclusive year window [year_index, year_index] with exactly
        one token spend (1 x annual_price) bound into the occupancy
        row. A rejected onboarding never charges. Renewal = onboarding
        a later year window (advance booking); a second account in the
        same studio-year is rejected E_ST_TAKEN by the venue
        exclusivity gate."""
        self._check_buy_args(account_id, annual_price, year_index, ref)
        row = self._kind_of(studio_id)
        if row is None:
            raise StudioError(E_ST_UNKNOWN, studio_id)
        try:
            res = self.ven.lease_storefront(account_id, studio_id,
                                            year_index, 1,
                                            annual_price, ref)
        except Exception as exc:
            if getattr(exc, "code", None):
                raise self._wrap(exc)
            raise
        return {"studio_id": studio_id, "st_kind": row[0],
                "year": year_index, "fee": res["fee"],
                "spend_tx": res["spend_tx_id"],
                "window": [res["start_tick"], res["end_tick"]]}

    # -- read faces -----------------------------------------------------------

    def studio_benefits(self, studio_id):
        """The canon three-benefit bundle of a registered studio,
        derived from its registry kind. Read-only, zero token
        movement."""
        row = self._kind_of(studio_id)
        if row is None:
            raise StudioError(E_ST_UNKNOWN, studio_id)
        return {"studio_id": studio_id, "st_kind": row[0],
                "benefits": list(BENEFITS[row[0]])}

    def studio_tenant(self, studio_id, at_year):
        """The effective studio-seat holder in a year window, or None.
        Read-only, zero token movement."""
        if not _is_int(at_year) or at_year < 0:
            raise StudioError(E_ST_BAD_ARGS, "at_year must be int >= 0")
        row = self._kind_of(studio_id)
        if row is None:
            raise StudioError(E_ST_UNKNOWN, studio_id)
        return self.ven.tenant_of(studio_id, at_year)

    def studio_profile(self, account_id, at_year):
        """Derived onboarding view of one account at a year anchor:
        every registered studio whose occupancy window covers at_year
        (joined from the venue occupancy structure through the studio
        registry, so foreign storefront units never leak in), each row
        carrying its kind, canon benefit bundle and purchase spend tx.
        Read-only, zero token movement."""
        if not str(account_id).startswith("usr:"):
            raise StudioError(E_ST_BAD_ARGS, "profiles are usr:* only")
        if not _is_int(at_year) or at_year < 0:
            raise StudioError(E_ST_BAD_ARGS, "at_year must be int >= 0")
        with self._lock:
            occ = self._conn.execute(
                "SELECT vo.unit_id, vo.start_tick, vo.end_tick,"
                " vo.terminated_tick, vo.bound_spend_tx"
                " FROM venue_occupancy vo JOIN studio_products sp"
                " ON vo.unit_id = sp.studio_id"
                " WHERE vo.account_id = ?"
                " ORDER BY vo.start_tick, vo.occ_id",
                (account_id,)).fetchall()
        subscriptions = []
        for unit_id, r_start, r_end, r_term, tx in occ:
            eff = r_end if r_term is None else min(r_end, r_term)
            if r_start <= at_year <= eff:
                kind = self._kind_of(unit_id)
                subscriptions.append({
                    "studio_id": unit_id, "st_kind": (kind[0] if kind
                                                      else None),
                    "benefits": list(BENEFITS[kind[0]]) if kind else [],
                    "year": int(r_start), "spend_tx": tx})
        return {"account_id": account_id, "at_year": at_year,
                "subscriptions": subscriptions}
