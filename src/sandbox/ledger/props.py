"""City prop/cosmetic inventory face over the token ledger sandbox
(BigDomain explore queue #6, claimed round R599).

Two inventory domains ride on the P-47-2b token ledger, kept strictly
separate from the token domain (counts are never tokens):

  - kind 'cosmetic' : permanent entitlement, one row per account+item
  - kind 'prop'     : consumable count credits, re-purchasable

Domain-isolation law (counts-vs-tokens two-domain rule): the token
ledger is touched exactly once per purchase, by one spend booking;
granting or consuming count credits never books a token tx, and no
verb exists anywhere in this module that turns credits back into
tokens (the BLUEPRINT 5.4 structural-ban posture, extended to the
counts domain). Entitlements and credits bind to the purchasing
account; there is no verb that moves inventory between accounts (any
such face is a P1 item for CEO, approval-only).

Pre-registered criteria AC-PR1..AC-PR7 live in the R599 backlog row
and were written before this code existed (honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: one extra table in the same SQLite DB (WAL, single writer,
same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

E_PROP_DUP = "E_PROP_DUP"                    # AC-PR2
E_PROP_INSUFFICIENT = "E_PROP_INSUFFICIENT"  # AC-PR3
E_PROP_UNKNOWN = "E_PROP_UNKNOWN"
E_PROP_BAD_KIND = "E_PROP_BAD_KIND"          # AC-PR2 / AC-PR7
E_PROP_BAD_AMOUNT = "E_PROP_BAD_AMOUNT"
E_PROP_BAD_REF = "E_PROP_BAD_REF"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS props_inventory (
    inv_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('cosmetic','prop')),
    count_credits INTEGER NOT NULL DEFAULT 0 CHECK (count_credits >= 0),
    bound_spend_tx TEXT NOT NULL,
    granted_utc TEXT NOT NULL,
    UNIQUE (account_id, item_id)
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class PropError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class PropsFace:
    """Inventory face over one Ledger instance. Own connection and lock
    into the same DB file; every mutation runs inside BEGIN IMMEDIATE."""

    KINDS = ("cosmetic", "prop")

    def __init__(self, ledger):
        self.led = ledger
        self.db_path = ledger.db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- writer faces -------------------------------------------------------

    def buy_prop(self, account_id, item_id, kind, token_price, ref, count=0):
        """Purchase face: one token spend (the only token-domain touch),
        then the inventory grant bound to that spend tx. Cosmetic
        duplicates are rejected before the spend, so a rejected buy
        never charges; prop credits stack on re-purchase."""
        if kind not in self.KINDS:
            raise PropError(E_PROP_BAD_KIND, kind)
        if (not isinstance(token_price, int) or isinstance(token_price, bool)
                or token_price <= 0):
            raise PropError(E_PROP_BAD_AMOUNT, str(token_price))
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise PropError(E_PROP_BAD_AMOUNT, str(count))
        if kind == "prop" and count < 1:
            raise PropError(E_PROP_BAD_AMOUNT, "prop needs count >= 1")
        if not str(ref).strip():
            raise PropError(E_PROP_BAD_REF, "purchase ref required")
        if not account_id.startswith("usr:"):
            raise PropError(E_PROP_BAD_KIND, "purchases are usr:* only")
        # pre-check BEFORE the spend: a rejected duplicate must not charge
        with self._lock:
            row = self._conn.execute(
                "SELECT kind FROM props_inventory"
                " WHERE account_id = ? AND item_id = ?",
                (account_id, item_id)).fetchone()
        if row is not None:
            if kind != row[0]:
                raise PropError(E_PROP_BAD_KIND, "kind drift for held item")
            if kind == "cosmetic":
                raise PropError(E_PROP_DUP, item_id)
        self.led.ensure_account(account_id, census_avatar_id=account_id[4:])
        spend_tx = self.led.spend(account_id, token_price, str(ref), "order")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                if row is None:
                    self._conn.execute(
                        "INSERT INTO props_inventory (account_id, item_id,"
                        " kind, count_credits, bound_spend_tx, granted_utc)"
                        " VALUES (?,?,?,?,?,?)",
                        (account_id, item_id, kind, count, spend_tx, _now_utc()))
                    total = count
                else:
                    self._conn.execute(
                        "UPDATE props_inventory"
                        " SET count_credits = count_credits + ?"
                        " WHERE account_id = ? AND item_id = ?",
                        (count, account_id, item_id))
                    total = self._conn.execute(
                        "SELECT count_credits FROM props_inventory"
                        " WHERE account_id = ? AND item_id = ?",
                        (account_id, item_id)).fetchone()[0]
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"spend_tx_id": spend_tx, "item_id": item_id, "kind": kind,
                "count_credits": int(total)}

    def consume_prop(self, account_id, item_id, count=1):
        """Consume count credits. Zero token-ledger involvement (the
        counts-vs-tokens isolation law): the credit domain only ever
        goes down from here, and no verb converts credits back into
        tokens."""
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise PropError(E_PROP_BAD_AMOUNT, str(count))
        with self._lock:
            row = self._conn.execute(
                "SELECT kind, count_credits FROM props_inventory"
                " WHERE account_id = ? AND item_id = ?",
                (account_id, item_id)).fetchone()
            if row is None:
                raise PropError(E_PROP_UNKNOWN, item_id)
            kind, held = row[0], int(row[1])
            if kind != "prop":
                raise PropError(E_PROP_BAD_KIND,
                                "cosmetic entitlements are permanent")
            if held < count:
                raise PropError(E_PROP_INSUFFICIENT,
                                "%d held < %d asked" % (held, count))
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "UPDATE props_inventory"
                    " SET count_credits = count_credits - ?"
                    " WHERE account_id = ? AND item_id = ?",
                    (count, account_id, item_id))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"item_id": item_id, "count_credits": held - count}

    # -- read faces -----------------------------------------------------------

    def inventory(self, account_id):
        """Per-account inventory view: cosmetic entitlements plus prop
        credit balances, each row carrying its purchase provenance."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT item_id, kind, count_credits, bound_spend_tx"
                " FROM props_inventory WHERE account_id = ?"
                " ORDER BY item_id", (account_id,)).fetchall()
        cosmetics = [r[0] for r in rows if r[1] == "cosmetic"]
        props = [{"item_id": r[0], "count_credits": int(r[2])}
                 for r in rows if r[1] == "prop"]
        bindings = {r[0]: r[3] for r in rows}
        return {"account_id": account_id, "cosmetics": cosmetics,
                "props": props, "bound_spend_tx": bindings}
