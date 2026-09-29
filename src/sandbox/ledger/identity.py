"""Metaverse identity paid face over the props + venue + token ledger
sandbox (BigDomain R624; canon = BLUEPRINT sec-4 C5 identity price
row: private room 9.9 CNY/month, avatar skin 29.9 CNY permanent,
creator plaque 49.9 CNY permanent, premium floor plaque 199 CNY
permanent; claimed from the explore-lane C5 row which pins the
adjacency check = props cosmetic domain + venue occupancy domain,
reference-not-double-build).

Four identity products in one registry:

  kind 'private_room'   : exclusive monthly room window - one
      tenant per room per month window, renewal = a later window
  kind 'avatar_skin'    : permanent cosmetic entitlement
  kind 'creator_plaque' : permanent cosmetic entitlement
  kind 'floor_plaque'   : permanent cosmetic entitlement

Reference law (the C5 row's check-then-build clause, ads.py
posture carried over): this module owns exactly one small table,
identity_products, which registers which identity kind a product
carries. Every WRITE goes through the PropsFace / VenueFace public
APIs - permanent kinds ride PropsFace.buy_prop(kind='cosmetic')
so entitlement rows live in props_inventory; private rooms ride
VenueFace.lease_storefront so occupancy rows, exclusivity gates
and spend provenance live in the venue structures. Zero second
entitlement or occupancy engine here (the module source has no
INSERT INTO those structures). Read faces join those structures
directly (same DB file); the wrapped error surface is
identity-domain (E_ID_*).

Identity-is-not-tokens isolation law (props/venue posture carried
over): each purchase is exactly one token spend and nothing else
in this module ever touches the token domain - registry, holder
and profile faces move zero tokens, and no verb converts an
entitlement or occupancy back into tokens or moves it between
accounts. Registry rows are immutable once written (no UPDATE
surface in this module); cancellation, fee reversal or transfer
of any kind is a P1 [needs-CEO] approval face, not a mechanism
here.

Prices are caller-supplied in the sandbox; the production price
points (9.9 / 29.9 / 49.9 / 199 CNY anchors) and any launch
gating are a P1 item for CEO, approval-only ([needs-CEO]). No
config keys are added by this module.

Pre-registered criteria AC-ID1..AC-ID7 live in the R624 backlog
row and were written before this code existed (honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: one extra table in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

E_ID_UNKNOWN = "E_ID_UNKNOWN"          # product not in the registry
E_ID_KIND_MISMATCH = "E_ID_KIND_MISMATCH"  # registry kind conflict
E_ID_DUP = "E_ID_DUP"                  # identical purchase replay
E_ID_TAKEN = "E_ID_TAKEN"              # room window held by someone
E_ID_BAD_ARGS = "E_ID_BAD_ARGS"

KINDS = ("private_room", "avatar_skin", "creator_plaque", "floor_plaque")
PERMANENT_KINDS = ("avatar_skin", "creator_plaque", "floor_plaque")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS identity_products (
    product_id TEXT PRIMARY KEY,
    id_kind TEXT NOT NULL CHECK (id_kind IN
        ('private_room','avatar_skin','creator_plaque','floor_plaque')),
    registered_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return (isinstance(value, int) and not isinstance(value, bool))


class IdentityError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class IdentityFace:
    """Identity paid face over one Ledger + one VenueFace + one
    PropsFace sharing the same DB file. Own connection and lock for
    the identity_products registry; every purchase delegates to the
    props/venue public APIs."""

    def __init__(self, ledger, venue, props):
        self.led = ledger
        self.ven = venue
        self.prp = props
        if getattr(venue, "db_path", None) != ledger.db_path:
            raise IdentityError(E_ID_BAD_ARGS,
                                "venue must share the ledger DB file")
        if getattr(props, "db_path", None) != ledger.db_path:
            raise IdentityError(E_ID_BAD_ARGS,
                                "props must share the ledger DB file")
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(ledger.db_path, check_same_thread=False,
                                      isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- internal helpers -------------------------------------------------

    def _kind_of(self, product_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT id_kind FROM identity_products"
                " WHERE product_id = ?", (product_id,)).fetchone()
        return row  # None or (id_kind,)

    def _wrap(self, exc):
        """Map a Props/Venue error onto the identity-domain surface so
        callers of this face never need engine internals (reference
        law: props/venue stay the engines, this module is the API)."""
        mapping = {"E_VN_UNKNOWN": E_ID_UNKNOWN,
                   "E_VN_LEASE_ACTIVE": E_ID_TAKEN,
                   "E_VN_DUP": E_ID_DUP,
                   "E_VN_BAD_ARGS": E_ID_BAD_ARGS,
                   "E_PROP_DUP": E_ID_DUP,
                   "E_PROP_BAD_KIND": E_ID_KIND_MISMATCH,
                   "E_PROP_BAD_AMOUNT": E_ID_BAD_ARGS,
                   "E_PROP_UNKNOWN": E_ID_UNKNOWN}
        code = mapping.get(getattr(exc, "code", ""), E_ID_BAD_ARGS)
        return IdentityError(code, getattr(exc, "detail", ""))

    def _check_buy_args(self, account_id, price, ref):
        if not str(account_id).startswith("usr:"):
            raise IdentityError(E_ID_BAD_ARGS, "buyers are usr:* only")
        if not _is_int(price) or price <= 0:
            raise IdentityError(E_ID_BAD_ARGS, "price must be int > 0")
        if not str(ref).strip():
            raise IdentityError(E_ID_BAD_ARGS, "purchase ref required")

    # -- writer faces -------------------------------------------------------

    def register_identity_product(self, product_id, id_kind):
        """Mechanism registration of one identity product under its
        kind. A private-room product auto-registers its room unit in
        the venue registry with capacity 1 (the venue public API, no
        second registry). Re-registering the same product with the
        same kind is idempotent; a different kind is
        E_ID_KIND_MISMATCH."""
        product_id = str(product_id or "").strip()
        if not product_id:
            raise IdentityError(E_ID_BAD_ARGS, "product_id required")
        if id_kind not in KINDS:
            raise IdentityError(E_ID_BAD_ARGS, "unknown identity kind")
        with self._lock:
            row = self._conn.execute(
                "SELECT id_kind FROM identity_products"
                " WHERE product_id = ?", (product_id,)).fetchone()
            if row is not None:
                if row[0] != id_kind:
                    raise IdentityError(E_ID_KIND_MISMATCH,
                                        "%s already registered as %s"
                                        % (product_id, row[0]))
                return {"product_id": product_id, "id_kind": id_kind,
                        "idempotent": True}
        if id_kind == "private_room":
            try:
                self.ven.register_venue(product_id, 1)
            except Exception as exc:
                if getattr(exc, "code", None):
                    raise self._wrap(exc)
                raise
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO identity_products (product_id, id_kind,"
                    " registered_utc) VALUES (?,?,?)",
                    (product_id, id_kind, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise IdentityError(E_ID_KIND_MISMATCH, product_id)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"product_id": product_id, "id_kind": id_kind,
                "idempotent": False}

    def rent_private_room(self, account_id, room_id, month_index,
                          price_per_month, ref):
        """Monthly private-room rental: the registered room kind must
        be private_room; the rental rides VenueFace.lease_storefront
        as one exclusive month window [month_index, month_index].
        Exactly one token spend per month window (1 x price), bound
        into the venue occupancy row; a rejected rental never
        charges. Renewal = renting a later month window (advance
        booking); a second account in the same month window is
        rejected E_ID_TAKEN by the venue exclusivity gate."""
        self._check_buy_args(account_id, price_per_month, ref)
        if not _is_int(month_index) or month_index < 0:
            raise IdentityError(E_ID_BAD_ARGS, "month_index must be int >= 0")
        row = self._kind_of(room_id)
        if row is None:
            raise IdentityError(E_ID_UNKNOWN, room_id)
        if row[0] != "private_room":
            raise IdentityError(E_ID_KIND_MISMATCH,
                                 "%s is registered as %s" % (room_id, row[0]))
        try:
            res = self.ven.lease_storefront(account_id, room_id,
                                            month_index, 1,
                                            price_per_month, ref)
        except Exception as exc:
            if getattr(exc, "code", None):
                raise self._wrap(exc)
            raise
        return {"room_id": room_id, "month": month_index, "fee": res["fee"],
                "spend_tx": res["spend_tx_id"],
                "window": [res["start_tick"], res["end_tick"]]}

    def claim_permanent(self, account_id, product_id, price, ref):
        """Permanent identity product (avatar skin / creator plaque /
        floor plaque): the registered kind must be one of the three
        permanent kinds; the claim rides PropsFace.buy_prop with
        kind 'cosmetic' so the permanent entitlement row (one per
        account, immutable) lives in props_inventory. Exactly one
        token spend per claim; a duplicate claim is rejected by the
        props cosmetic gate before the spend (zero charge)."""
        self._check_buy_args(account_id, price, ref)
        row = self._kind_of(product_id)
        if row is None:
            raise IdentityError(E_ID_UNKNOWN, product_id)
        if row[0] not in PERMANENT_KINDS:
            raise IdentityError(E_ID_KIND_MISMATCH,
                                 "%s is registered as %s" % (product_id,
                                                             row[0]))
        try:
            res = self.prp.buy_prop(account_id, product_id, "cosmetic",
                                    price, ref)
        except Exception as exc:
            if getattr(exc, "code", None):
                raise self._wrap(exc)
            raise
        return {"product_id": product_id, "id_kind": row[0],
                "spend_tx": res["spend_tx_id"]}

    # -- read faces -----------------------------------------------------------

    def room_holder(self, room_id, at_month):
        """The effective tenant of a registered private room in a
        month window, or None. Read-only, zero token movement."""
        if not _is_int(at_month) or at_month < 0:
            raise IdentityError(E_ID_BAD_ARGS, "at_month must be int >= 0")
        row = self._kind_of(room_id)
        if row is None:
            raise IdentityError(E_ID_UNKNOWN, room_id)
        if row[0] != "private_room":
            raise IdentityError(E_ID_KIND_MISMATCH,
                                 "%s is registered as %s" % (room_id, row[0]))
        return self.ven.tenant_of(room_id, at_month)

    def identity_profile(self, account_id, at_month):
        """Derived identity view of one account at a month anchor:
        the private rooms whose window covers at_month (joined from
        the venue occupancy structure through the identity registry,
        so foreign venue/storefront units never leak in) plus the
        held permanent identity products (joined from the props
        inventory through the registry). Every row carries its
        purchase spend tx. Read-only, zero token movement."""
        if not str(account_id).startswith("usr:"):
            raise IdentityError(E_ID_BAD_ARGS, "profiles are usr:* only")
        if not _is_int(at_month) or at_month < 0:
            raise IdentityError(E_ID_BAD_ARGS, "at_month must be int >= 0")
        with self._lock:
            occ = self._conn.execute(
                "SELECT vo.unit_id, vo.start_tick, vo.end_tick,"
                " vo.terminated_tick, vo.bound_spend_tx"
                " FROM venue_occupancy vo JOIN identity_products ip"
                " ON vo.unit_id = ip.product_id"
                " WHERE ip.id_kind = 'private_room' AND vo.account_id = ?"
                " ORDER BY vo.start_tick, vo.occ_id",
                (account_id,)).fetchall()
        rooms = []
        for unit_id, r_start, r_end, r_term, tx in occ:
            eff = r_end if r_term is None else min(r_end, r_term)
            if r_start <= at_month <= eff:
                rooms.append({"room_id": unit_id, "month": int(r_start),
                              "spend_tx": tx})
        inv = self.prp.inventory(account_id)
        held = {item for item in inv["cosmetics"]
                if (lambda r: r is not None and r[0] in PERMANENT_KINDS)(
                    self._kind_of(item))}
        permanents = [{"product_id": item, "spend_tx": inv[
            "bound_spend_tx"][item]} for item in sorted(held)]
        return {"account_id": account_id, "at_month": at_month,
                "rooms": rooms, "permanents": permanents}
