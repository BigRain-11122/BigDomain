"""Enterprise AI-compute verification API metering + billing face
over the token ledger sandbox (BigDomain R626; canon = BLUEPRINT
sec-4 B-side price row B5: enterprise SaaS interface for small teams
and studios, billed per metered call from the 0.5-CNY-per-call
anchor up; claimed from the explore-lane top open row).

Reference law (BigMoney engine, reference-not-double-build): this
module is the metering + billing spine only. The backtest /
visualization engine itself is BigMoney's; every metered call
carries the caller's engine_ref receipt (an opaque external engine
invocation record) stored verbatim, and the call rows carry zero
numeric-result columns - no backtest logic, no pnl, no return
figures live here. The production external API endpoint is a
bootstrap-time face: three-question gate + CEO authorization come
first; this sandbox module is pure local simulation, zero network.

Non-advisory standing note (canon row wording, permanent): the
API is a compute-and-visualization interface, not investment
advice; the client_contract read face carries this disclaimer as
its first and last line so every contract read is structurally
accompanied.

Two domains:

  - prepaid call packs : one pack purchase = exactly one token
                         spend (calls x unit_price) bound to its
                         spend tx; credits stack on re-purchase
  - metered calls      : one API call = exactly one credit
                         consumed, recorded as an immutable call
                         row keyed by the caller's call_ref

Counts-vs-tokens isolation law (props.py posture carried over):
pack purchase is the only token-domain touch in this module (the
ledger spend in buy_pack); metering, consumption and every read
face move zero tokens, and no verb anywhere turns credits back
into tokens or moves credits between clients. Fee reversal of any
kind is a P1 item for CEO, approval-only, not a mechanism here.

Gate posture: every reject (duplicate pack ref, duplicate call
ref, unregistered client, kind not enabled for the client, zero
credits, bad arguments) fires before the spend / before the
credit decrement, so a rejected call never charges and never
consumes. Pack rows and call rows are immutable once written (the
only counter that ever changes is the client credit balance).

Prices are caller-supplied in the sandbox; the production
per-call price points (0.5 CNY/call anchor and up) and any launch
gating are a P1 item for CEO, approval-only ([needs-CEO]). No
config keys are added by this module.

Pre-registered criteria AC-MT1..AC-MT7 live in the R626 backlog
row and were written before this code existed (honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: three extra tables in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import sqlite3
import threading

E_MT_UNKNOWN = "E_MT_UNKNOWN"          # client not registered
E_MT_DUP = "E_MT_DUP"                  # pack ref / call ref replay
E_MT_NO_CREDITS = "E_MT_NO_CREDITS"    # zero-balance fail-closed gate
E_MT_KIND_GATE = "E_MT_KIND_GATE"      # kind valid but not enabled
E_MT_BAD_ARGS = "E_MT_BAD_ARGS"

KINDS = ("backtest", "visualize")

NON_ADVISORY = ("non-advisory notice: compute + visualization"
                " interface only, not investment advice")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS metered_clients (
    client_id TEXT PRIMARY KEY,
    funding_account TEXT NOT NULL,
    enabled_kinds TEXT NOT NULL,
    call_credits INTEGER NOT NULL DEFAULT 0
                   CHECK (call_credits >= 0),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS metered_packs (
    pack_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT NOT NULL,
    purchase_ref TEXT NOT NULL UNIQUE,
    calls INTEGER NOT NULL CHECK (calls >= 1),
    unit_price INTEGER NOT NULL CHECK (unit_price >= 1),
    total_price INTEGER NOT NULL CHECK (total_price >= 1),
    bound_spend_tx TEXT NOT NULL,
    purchased_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS metered_calls (
    call_ref TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    engine_ref TEXT NOT NULL,
    consumed_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return (isinstance(value, int) and not isinstance(value, bool))


class MeteredError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class MeteredFace:
    """Per-call metering + billing face over one Ledger instance
    sharing the same DB file. Own connection and lock for the three
    metered tables; the only token touch is the ledger spend inside
    buy_pack (the public ledger API)."""

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

    # -- internal helpers -------------------------------------------------

    def _client_row(self, client_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT funding_account, enabled_kinds, call_credits"
                " FROM metered_clients WHERE client_id = ?",
                (client_id,)).fetchone()
        return row  # None or (funding_account, kinds_csv, credits)

    # -- writer faces -------------------------------------------------------

    def register_client(self, client_id, funding_account, kinds):
        """Mechanism registration of one enterprise client bound to one
        funding account with its enabled call kinds. Re-registering the
        same client with identical parameters is idempotent; a conflicting
        re-registration is rejected E_MT_DUP."""
        client_id = str(client_id or "").strip()
        funding_account = str(funding_account or "").strip()
        if not client_id.startswith("ent:"):
            raise MeteredError(E_MT_BAD_ARGS,
                               "client ids are ent:* only")
        if not funding_account.startswith("usr:"):
            raise MeteredError(E_MT_BAD_ARGS,
                               "funding accounts are usr:* only")
        if not kinds:
            raise MeteredError(E_MT_BAD_ARGS, "kinds required")
        kind_list = []
        for kind in kinds:
            if kind not in KINDS:
                raise MeteredError(E_MT_BAD_ARGS, "unknown kind " + str(kind))
            if kind not in kind_list:
                kind_list.append(kind)
        kinds_csv = ",".join(kind_list)
        with self._lock:
            row = self._conn.execute(
                "SELECT funding_account, enabled_kinds FROM metered_clients"
                " WHERE client_id = ?", (client_id,)).fetchone()
            if row is not None:
                if row[0] != funding_account or row[1] != kinds_csv:
                    raise MeteredError(E_MT_DUP, client_id)
                return {"client_id": client_id,
                        "funding_account": funding_account,
                        "enabled_kinds": kind_list, "idempotent": True}
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO metered_clients (client_id,"
                    " funding_account, enabled_kinds, call_credits,"
                    " registered_utc) VALUES (?,?,?,0,?)",
                    (client_id, funding_account, kinds_csv, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise MeteredError(E_MT_DUP, client_id)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"client_id": client_id, "funding_account": funding_account,
                "enabled_kinds": kind_list, "idempotent": False}

    def buy_pack(self, client_id, calls, unit_price, ref):
        """Prepaid call-pack purchase: exactly one token spend
        (calls x unit_price) from the client's funding account, then
        the immutable pack row + credit stack, both bound to that
        spend tx. A duplicate ref is rejected before the spend (zero
        charge); a ledger balance reject leaves zero side effects."""
        client_id = str(client_id or "").strip()
        if not _is_int(calls) or calls < 1:
            raise MeteredError(E_MT_BAD_ARGS, "calls must be int >= 1")
        if not _is_int(unit_price) or unit_price < 1:
            raise MeteredError(E_MT_BAD_ARGS, "unit_price must be int >= 1")
        if not str(ref).strip():
            raise MeteredError(E_MT_BAD_ARGS, "purchase ref required")
        row = self._client_row(client_id)
        if row is None:
            raise MeteredError(E_MT_UNKNOWN, client_id)
        total = calls * unit_price
        # pre-check BEFORE the spend: a rejected replay never charges
        with self._lock:
            dup = self._conn.execute(
                "SELECT 1 FROM metered_packs WHERE purchase_ref = ?",
                (str(ref),)).fetchone()
        if dup is not None:
            raise MeteredError(E_MT_DUP, str(ref))
        spend_tx = self.led.spend(row[0], total, str(ref), "order")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO metered_packs (client_id, purchase_ref,"
                    " calls, unit_price, total_price, bound_spend_tx,"
                    " purchased_utc) VALUES (?,?,?,?,?,?,?)",
                    (client_id, str(ref), calls, unit_price, total,
                     spend_tx, _now_utc()))
                self._conn.execute(
                    "UPDATE metered_clients"
                    " SET call_credits = call_credits + ?"
                    " WHERE client_id = ?", (calls, client_id))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise MeteredError(E_MT_DUP, str(ref))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"client_id": client_id, "calls": calls,
                "unit_price": unit_price, "total_price": total,
                "spend_tx": spend_tx}

    def meter_call(self, client_id, kind, call_ref, engine_ref):
        """Meter one API call: consume exactly one credit and record
        the immutable call row keyed by the caller's call_ref, with
        the external engine receipt stored verbatim (zero engine
        logic here). Duplicate call refs are rejected with zero
        double-charge; a zero-credit client is fail-closed
        E_MT_NO_CREDITS. Zero token-ledger involvement."""
        client_id = str(client_id or "").strip()
        kind = str(kind or "").strip()
        call_ref = str(call_ref or "").strip()
        engine_ref = str(engine_ref or "").strip()
        if kind not in KINDS:
            raise MeteredError(E_MT_BAD_ARGS, "unknown kind " + str(kind))
        if not call_ref:
            raise MeteredError(E_MT_BAD_ARGS, "call ref required")
        if not engine_ref:
            raise MeteredError(E_MT_BAD_ARGS, "engine ref required")
        with self._lock:
            row = self._conn.execute(
                "SELECT enabled_kinds, call_credits FROM metered_clients"
                " WHERE client_id = ?", (client_id,)).fetchone()
            if row is None:
                raise MeteredError(E_MT_UNKNOWN, client_id)
            enabled = row[0].split(",")
            if kind not in enabled:
                raise MeteredError(E_MT_KIND_GATE,
                                   "%s not enabled for %s" % (kind, client_id))
            if int(row[1]) < 1:
                raise MeteredError(E_MT_NO_CREDITS, client_id)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO metered_calls (call_ref, client_id, kind,"
                    " engine_ref, consumed_utc) VALUES (?,?,?,?,?)",
                    (call_ref, client_id, kind, engine_ref, _now_utc()))
                self._conn.execute(
                    "UPDATE metered_clients"
                    " SET call_credits = call_credits - 1"
                    " WHERE client_id = ?", (client_id,))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise MeteredError(E_MT_DUP, call_ref)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"call_ref": call_ref, "client_id": client_id, "kind": kind,
                "engine_ref": engine_ref}

    # -- read faces -----------------------------------------------------------

    def client_contract(self, client_id):
        """The client contract view. The non-advisory standing notice
        is the first and the last content line (canon permanent
        wording); per-call prices are caller-supplied in the sandbox
        and the production anchors stay [needs-CEO] P1
        approval-only. Read-only, zero token movement."""
        row = self._client_row(client_id)
        if row is None:
            raise MeteredError(E_MT_UNKNOWN, client_id)
        return {"client_id": client_id,
                "disclaimer_first": NON_ADVISORY,
                "disclaimer_last": NON_ADVISORY,
                "enabled_kinds": row[1].split(","),
                "call_credits": int(row[2]),
                "pricing_note": "per-call prices caller-supplied;"
                                " production 0.5-CNY/call anchor and up"
                                " = [needs-CEO] P1 approval-only"}

    def reconcile_client(self, client_id):
        """Metering reconciliation read face: purchased calls (sum of
        immutable pack rows) must equal consumed calls (count of
        immutable call rows) plus the remaining credit counter; any
        drift (e.g. counter tampering) flips the balanced verdict to
        False. Every pack row carries its spend tx so the billing
        side cross-checks against the token ledger. Read-only, zero
        token movement."""
        row = self._client_row(client_id)
        if row is None:
            raise MeteredError(E_MT_UNKNOWN, client_id)
        with self._lock:
            packs = self._conn.execute(
                "SELECT calls, total_price, bound_spend_tx"
                " FROM metered_packs WHERE client_id = ?"
                " ORDER BY pack_id", (client_id,)).fetchall()
            consumed = self._conn.execute(
                "SELECT COUNT(*) FROM metered_calls WHERE client_id = ?",
                (client_id,)).fetchone()[0]
        purchased = sum(int(p[0]) for p in packs)
        remaining = int(row[2])
        return {"client_id": client_id,
                "packs": len(packs),
                "purchased_calls": purchased,
                "consumed_calls": int(consumed),
                "remaining_credits": remaining,
                "balanced": purchased == int(consumed) + remaining,
                "spend_txs": [p[2] for p in packs],
                "billed_total": sum(int(p[1]) for p in packs)}

    def usage_log(self, client_id):
        """The client's metered-call log (immutable call rows with
        their external engine receipts). Read-only, zero token
        movement."""
        row = self._client_row(client_id)
        if row is None:
            raise MeteredError(E_MT_UNKNOWN, client_id)
        with self._lock:
            rows = self._conn.execute(
                "SELECT call_ref, kind, engine_ref, consumed_utc"
                " FROM metered_calls WHERE client_id = ?"
                " ORDER BY consumed_utc, call_ref",
                (client_id,)).fetchall()
        return {"client_id": client_id,
                "calls": [{"call_ref": r[0], "kind": r[1],
                           "engine_ref": r[2], "consumed_utc": r[3]}
                          for r in rows]}
