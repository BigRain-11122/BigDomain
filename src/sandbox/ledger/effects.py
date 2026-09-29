"""Trading-hall value-added effects consumables face over the token
ledger sandbox (BigDomain R629; canon = BLUEPRINT sec-4 hall
value-added line, C3 price row effects residual; claimed from the
explore-lane replenish under the zero-idle night order
O-2026-0929-027, R619 lane-restock precedent).

Four one-shot effect products ride on the P-47-2b token ledger,
one effect credit per purchase, each bound to exactly one token
spend:

  kind 'dynamic_emoji'  : dynamic emoji on one hall message
  kind 'limit_up_effect': limit-up celebration on one hall message
  kind 'flood_effect'   : screen-flood effect on one hall message
  kind 'message_pin'    : single-message highlight pin (one-shot
                          consumable; distinct from the mayor-tier
                          persistent chat_highlight privilege owned
                          by the member face - reference, no
                          double-build)

Division of authority (reference law): the lobby ingress owns the
msgSecCheck front-gate - message_ref here references an
already-gated hall message and this module adds no second content
channel; presentation authority is server-side per
integration-deepening-spec IF-9 (member -> lobby envelope), the
client carries zero say.

Mechanism (pre-registered criteria AC-LE1..AC-LE7 live in the R629
backlog row and were written before this code existed; honesty
law):

  - purchase is idempotent on the caller ref: a repeated ref
    returns the existing credit with no second charge (AC-LE1);
    every credit row binds its real spend tx and the spend is the
    module's only token touch (AC-LE2).
  - use consumes exactly one unconsumed credit of the matching
    kind inside the same transaction that inserts the effect row,
    so a failed use leaves zero rows (AC-LE3/AC-LE4). use is
    idempotent on use_ref: a replay returns the existing effect
    row with no second consumption (AC-LE5).
  - a consumed credit is consumed once and binds the effect row
    it paid for (AC-LE6). Consumption marking on credit rows is
    the single UPDATE surface in this module; effect rows are
    immutable and no verb moves a credit between accounts.

Counts stay counts and tokens stay tokens (props posture).
Prices are caller-supplied in the sandbox; the production price
points (canon anchors 9.9 / 19.9 / 9.9 / 4.9 yuan tiers) and any
launch gating are a P1 item for CEO, approval-only ([needs-CEO]).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: two extra tables in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

E_EFF_BAD_ACCOUNT = "E_EFF_BAD_ACCOUNT"    # AC-LE7
E_EFF_BAD_KIND = "E_EFF_BAD_KIND"           # AC-LE4 / AC-LE7
E_EFF_BAD_AMOUNT = "E_EFF_BAD_AMOUNT"       # AC-LE7
E_EFF_BAD_REF = "E_EFF_BAD_REF"             # AC-LE7
E_EFF_BAD_MESSAGE = "E_EFF_BAD_MESSAGE"     # AC-LE7
E_EFF_NO_CREDIT = "E_EFF_NO_CREDIT"         # AC-LE3 / AC-LE6
E_EFF_DUP_USE = "E_EFF_DUP_USE"             # AC-LE5 (cross-account ref)

EFFECT_KINDS = ("dynamic_emoji", "limit_up_effect",
                "flood_effect", "message_pin")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS effect_credits (
    credit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN
        ('dynamic_emoji','limit_up_effect','flood_effect',
         'message_pin')),
    purchase_ref TEXT NOT NULL UNIQUE,
    token_price INTEGER NOT NULL CHECK (token_price > 0),
    bound_spend_tx TEXT NOT NULL,
    purchased_utc TEXT NOT NULL,
    consumed_utc TEXT,
    used_effect INTEGER
);
CREATE TABLE IF NOT EXISTS effect_events (
    effect_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    message_ref TEXT NOT NULL,
    use_ref TEXT NOT NULL UNIQUE,
    used_credit INTEGER NOT NULL,
    used_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class EffectsError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class EffectsFace:
    """Hall value-added effects face over one Ledger instance. Own
    connection and lock into the same DB file; every mutation runs
    inside BEGIN IMMEDIATE."""

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

    # -- writer faces --------------------------------------------------------

    def purchase(self, account_id, kind, token_price, ref):
        """Idempotent purchase face: one token spend (the only
        token-domain touch) buys one effect credit. A repeated
        purchase ref returns the existing credit with no second
        charge; a fresh ref spends once and binds its real tx."""
        if not account_id.startswith("usr:"):
            raise EffectsError(E_EFF_BAD_ACCOUNT, account_id)
        kind = str(kind or "").strip()
        if kind not in EFFECT_KINDS:
            raise EffectsError(E_EFF_BAD_KIND, kind)
        if (not isinstance(token_price, int) or isinstance(token_price, bool)
                or token_price <= 0):
            raise EffectsError(E_EFF_BAD_AMOUNT, str(token_price))
        ref = str(ref or "").strip()
        if not ref:
            raise EffectsError(E_EFF_BAD_REF, "purchase ref required")
        with self._lock:
            row = self._conn.execute(
                "SELECT credit_id, kind, token_price, bound_spend_tx,"
                " consumed_utc FROM effect_credits WHERE purchase_ref = ?",
                (ref,)).fetchone()
            if row is not None:
                return {"credit_id": int(row[0]), "kind": row[1],
                        "token_price": int(row[2]), "spend_tx": row[3],
                        "consumed": row[4] is not None,
                        "idempotent": True}
            self.led.ensure_account(account_id,
                                    census_avatar_id=account_id[4:])
            spend_tx = self.led.spend(account_id, token_price, ref, "order")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO effect_credits (account_id, kind,"
                    " purchase_ref, token_price, bound_spend_tx,"
                    " purchased_utc) VALUES (?,?,?,?,?,?)",
                    (account_id, kind, ref, token_price, spend_tx,
                     _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise EffectsError(E_EFF_BAD_REF, ref)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"credit_id": cur.lastrowid, "kind": kind,
                "token_price": token_price, "spend_tx": spend_tx,
                "consumed": False, "idempotent": False}

    def use(self, account_id, kind, message_ref, use_ref):
        """Consume exactly one unconsumed credit of the matching
        kind and emit one immutable effect row bound to the hall
        message. message_ref references an already-gated lobby
        message (the lobby ingress owns msgSecCheck); this module
        never re-runs a content channel on it. use_ref replay is
        idempotent: the same ref returns the existing effect row
        with no second consumption; a ref replayed by a different
        account or kind is rejected."""
        if not account_id.startswith("usr:"):
            raise EffectsError(E_EFF_BAD_ACCOUNT, account_id)
        kind = str(kind or "").strip()
        if kind not in EFFECT_KINDS:
            raise EffectsError(E_EFF_BAD_KIND, kind)
        message_ref = str(message_ref or "").strip()
        if not message_ref:
            raise EffectsError(E_EFF_BAD_MESSAGE, "message ref required")
        use_ref = str(use_ref or "").strip()
        if not use_ref:
            raise EffectsError(E_EFF_BAD_REF, "use ref required")
        self.led.ensure_account(account_id, census_avatar_id=account_id[4:])
        with self._lock:
            prior = self._conn.execute(
                "SELECT effect_id, account_id, kind, used_credit FROM"
                " effect_events WHERE use_ref = ?", (use_ref,)).fetchone()
            if prior is not None:
                if prior[1] != account_id or prior[2] != kind:
                    raise EffectsError(E_EFF_DUP_USE, use_ref)
                return {"effect_id": int(prior[0]), "kind": kind,
                        "message_ref": message_ref,
                        "used_credit": int(prior[3]), "idempotent": True}
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                row = self._conn.execute(
                    "SELECT credit_id FROM effect_credits"
                    " WHERE account_id = ? AND kind = ?"
                    " AND consumed_utc IS NULL"
                    " ORDER BY credit_id LIMIT 1",
                    (account_id, kind)).fetchone()
                if row is None:
                    self._conn.execute("ROLLBACK")
                    raise EffectsError(E_EFF_NO_CREDIT, kind)
                used_credit = int(row[0])
                cur = self._conn.execute(
                    "INSERT INTO effect_events (account_id, kind,"
                    " message_ref, use_ref, used_credit, used_utc)"
                    " VALUES (?,?,?,?,?,?)",
                    (account_id, kind, message_ref, use_ref, used_credit,
                     _now_utc()))
                hit = self._conn.execute(
                    "UPDATE effect_credits SET consumed_utc = ?,"
                    " used_effect = ? WHERE credit_id = ?"
                    " AND consumed_utc IS NULL",
                    (_now_utc(), cur.lastrowid, used_credit))
                if hit.rowcount != 1:
                    self._conn.execute("ROLLBACK")
                    raise EffectsError(E_EFF_NO_CREDIT, kind)
                self._conn.execute("COMMIT")
            except EffectsError:
                raise
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise EffectsError(E_EFF_DUP_USE, use_ref)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"effect_id": cur.lastrowid, "kind": kind,
                "message_ref": message_ref, "used_credit": used_credit,
                "idempotent": False}

    # -- read faces ----------------------------------------------------------

    def credits_view(self, account_id):
        """Per-account credit view: kind, purchase ref, bound spend
        tx and consumption state (with the effect row it paid for
        when consumed)."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT credit_id, kind, purchase_ref, token_price,"
                " bound_spend_tx, consumed_utc, used_effect"
                " FROM effect_credits WHERE account_id = ?"
                " ORDER BY credit_id", (account_id,)).fetchall()
        return {"account_id": account_id,
                "credits": [{"credit_id": int(r[0]), "kind": r[1],
                             "purchase_ref": r[2], "token_price": int(r[3]),
                             "spend_tx": r[4], "consumed": r[5] is not None,
                             "used_effect": r[6]} for r in rows]}

    def effects_view(self, account_id):
        """Per-account immutable effect audit view: every fired
        effect carries its kind, hall message ref, use ref and the
        credit that paid for it (spend-tx provenance via
        credits_view)."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT effect_id, kind, message_ref, use_ref, used_credit,"
                " used_utc FROM effect_events WHERE account_id = ?"
                " ORDER BY effect_id", (account_id,)).fetchall()
        return {"account_id": account_id,
                "effects": [{"effect_id": int(r[0]), "kind": r[1],
                             "message_ref": r[2], "use_ref": r[3],
                             "used_credit": int(r[4]), "used_utc": r[5]}
                            for r in rows]}
