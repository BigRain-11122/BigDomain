"""Strategy co-creation paid observation face over the token
ledger sandbox (BigDomain R623; canon = BLUEPRINT sec-4
strategy-co-creation observation line: single-strategy permanent
observation / monthly unlimited pass, results-only view, no source
code; the observation-paid product is assigned to this company by
D-20260924-10 as a core revenue line; claimed from the canonical
price table after the explore lane ran out of claimable rows).

Two purchasable observation products ride on the P-47-2b token
ledger, each bound to exactly one token spend:

  grant_kind 'single': one account + one strategy = one permanent
                       observation entitlement (survives months)
  grant_kind 'pass'  : one account + one month window
                       (YYYY-MM) = unlimited observation of every
                       registered strategy inside that window

Mechanism (pre-registered criteria AC-OB1..AC-OB7 live in the
R623 backlog row and were written before this code existed;
honesty law):

  - registration gate: only registered strategies are purchasable
    or observable; unknown ids are rejected with zero charge
    (AC-OB1). A strategy is registered with a results summary
    payload ONLY - the registry has no source column and the
    register face has no source parameter at all, so the
    results-only boundary is structural, not advisory (AC-OB6).
  - single purchase: exactly one spend bound to its tx; a repeated
    purchase of the same (account, strategy) is rejected BEFORE the
    spend, so the balance never moves twice (AC-OB2/AC-OB3).
  - pass purchase: exactly one spend per (account, month); a
    repeated purchase of the same month is rejected before the
    spend (AC-OB4).
  - access gate is fail-closed: observing without an entitlement
    is rejected with zero charge; a single grant is permanent
    across months, a pass only covers its own month (AC-OB5).
  - observe() and can_observe() are pure reads: zero token
    movement, view keys are exactly {strategy_id, summary, kind,
    tx} (AC-OB6).
  - hard law (AC-OB7): bad args are all rejected with zero side
    effects, the module stays pure ASCII, grant rows are immutable
    (zero UPDATE surface) and config.json is never touched.

Creator economics: the creator share of observation fees (30%
token share per the sec-4 co-creation split) is NOT rebuilt here -
it is the allocation layer already covered by
docs/spec/incentive-agent-spec.md and the settlement face
(reference, no duplicate build).

Prices are caller-supplied in the sandbox; the production price
points (canon anchors 9.9 yuan single / 19.9 yuan monthly pass)
and any launch gating are a P1 item for CEO, approval-only
([needs-CEO]).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: two extra tables in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import json
import re
import sqlite3
import threading

E_OBS_BAD_ACCOUNT = "E_OBS_BAD_ACCOUNT"    # AC-OB7
E_OBS_BAD_ARGS = "E_OBS_BAD_ARGS"          # AC-OB1 / AC-OB7
E_OBS_BAD_PRICE = "E_OBS_BAD_PRICE"        # AC-OB7
E_OBS_BAD_MONTH = "E_OBS_BAD_MONTH"        # AC-OB7
E_OBS_UNKNOWN = "E_OBS_UNKNOWN"            # AC-OB1
E_OBS_EXISTS = "E_OBS_EXISTS"              # AC-OB1
E_OBS_DUP = "E_OBS_DUP"                    # AC-OB3
E_OBS_PASS_DUP = "E_OBS_PASS_DUP"          # AC-OB4
E_OBS_DENIED = "E_OBS_DENIED"             # AC-OB5

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS obs_strategies (
    strategy_id TEXT PRIMARY KEY,
    creator_account TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS obs_grants (
    grant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    grant_kind TEXT NOT NULL CHECK (grant_kind IN ('single','pass')),
    strategy_id TEXT,
    pass_month TEXT,
    token_price INTEGER NOT NULL CHECK (token_price > 0),
    bound_spend_tx TEXT NOT NULL,
    granted_utc TEXT NOT NULL,
    UNIQUE (account_id, grant_kind, strategy_id),
    UNIQUE (account_id, grant_kind, pass_month)
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class ObservationError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class ObservationFace:
    """Paid-observation face over one Ledger instance. Own
    connection and lock into the same DB file; every mutation runs
    inside BEGIN IMMEDIATE. Grant rows are immutable once written
    (zero UPDATE surface)."""

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

    def register_strategy(self, strategy_id, creator_account, summary):
        """Results-only registry face. Accepts a strategy id, the
        creator account and a results summary payload; there is no
        source parameter at all. A repeated id is rejected with
        E_OBS_EXISTS and zero rows."""
        sid = str(strategy_id or "").strip()
        if not sid:
            raise ObservationError(E_OBS_BAD_ARGS, "strategy id required")
        creator = str(creator_account or "").strip()
        if not creator.startswith("usr:"):
            raise ObservationError(E_OBS_BAD_ACCOUNT, creator)
        if not isinstance(summary, (dict, list)) or not summary:
            raise ObservationError(E_OBS_BAD_ARGS,
                                   "results summary payload required")
        payload = json.dumps(summary, sort_keys=True)
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM obs_strategies WHERE strategy_id = ?",
                (sid,)).fetchone()
            if row is not None:
                raise ObservationError(E_OBS_EXISTS, sid)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO obs_strategies (strategy_id,"
                    " creator_account, summary_json, registered_utc)"
                    " VALUES (?,?,?,?)",
                    (sid, creator, payload, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ObservationError(E_OBS_EXISTS, sid)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"strategy_id": sid, "creator_account": creator,
                "registered": True}

    def _require_strategy(self, strategy_id):
        sid = str(strategy_id or "").strip()
        if not sid:
            raise ObservationError(E_OBS_BAD_ARGS, "strategy id required")
        row = self._conn.execute(
            "SELECT 1 FROM obs_strategies WHERE strategy_id = ?",
            (sid,)).fetchone()
        if row is None:
            raise ObservationError(E_OBS_UNKNOWN, sid)
        return sid

    @staticmethod
    def _check_price(token_price):
        if (not isinstance(token_price, int) or isinstance(token_price, bool)
                or token_price <= 0):
            raise ObservationError(E_OBS_BAD_PRICE, str(token_price))

    def _spend_and_grant(self, account_id, grant_kind, strategy_id,
                         pass_month, token_price, ref, dup_code):
        """Shared purchase core: the duplicate check runs BEFORE the
        spend, so a rejected repurchase never moves the balance; the
        grant insert is the only row written and it is immutable."""
        self._check_price(token_price)
        ref = str(ref or "").strip()
        if not ref:
            raise ObservationError(E_OBS_BAD_ARGS, "purchase ref required")
        with self._lock:
            row = self._conn.execute(
                "SELECT grant_id FROM obs_grants WHERE account_id = ?"
                " AND grant_kind = ? AND strategy_id IS ?"
                " AND pass_month IS ?",
                (account_id, grant_kind, strategy_id, pass_month)).fetchone()
            if row is not None:
                raise ObservationError(dup_code,
                                       "%s/%s" % (grant_kind, ref))
            self.led.ensure_account(account_id,
                                    census_avatar_id=account_id[4:])
            spend_tx = self.led.spend(account_id, token_price, ref, "order")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO obs_grants (account_id, grant_kind,"
                    " strategy_id, pass_month, token_price, bound_spend_tx,"
                    " granted_utc) VALUES (?,?,?,?,?,?,?)",
                    (account_id, grant_kind, strategy_id, pass_month,
                     token_price, spend_tx, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ObservationError(dup_code,
                                       "%s/%s" % (grant_kind, ref))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"grant_id": cur.lastrowid, "grant_kind": grant_kind,
                "strategy_id": strategy_id, "pass_month": pass_month,
                "token_price": token_price, "spend_tx": spend_tx}

    def buy_single(self, account_id, strategy_id, token_price, ref):
        """Single-strategy permanent observation: exactly one spend
        bound to its tx; a repeated purchase of the same
        (account, strategy) is rejected before the spend."""
        if not str(account_id or "").startswith("usr:"):
            raise ObservationError(E_OBS_BAD_ACCOUNT, account_id)
        with self._lock:
            sid = self._require_strategy(strategy_id)
        return self._spend_and_grant(account_id, "single", sid, None,
                                     token_price, ref, E_OBS_DUP)

    def buy_pass(self, account_id, pass_month, token_price, ref):
        """Monthly unlimited-observation pass for one YYYY-MM window:
        exactly one spend per (account, month); a repeated purchase
        of the same month is rejected before the spend; another
        month is a separate legal purchase."""
        if not str(account_id or "").startswith("usr:"):
            raise ObservationError(E_OBS_BAD_ACCOUNT, account_id)
        month = str(pass_month or "").strip()
        if not _MONTH_RE.match(month):
            raise ObservationError(E_OBS_BAD_MONTH, month)
        return self._spend_and_grant(account_id, "pass", None, month,
                                      token_price, ref, E_OBS_PASS_DUP)

    # -- read faces -----------------------------------------------------------

    def can_observe(self, account_id, strategy_id, at_month):
        """Pure-read access gate: a permanent single grant covers any
        month; a pass covers exactly its own month. No token
        movement, no rows written."""
        sid = str(strategy_id or "").strip()
        if not sid:
            raise ObservationError(E_OBS_BAD_ARGS, "strategy id required")
        month = str(at_month or "").strip()
        if not _MONTH_RE.match(month):
            raise ObservationError(E_OBS_BAD_MONTH, month)
        with self._lock:
            if self._conn.execute(
                    "SELECT 1 FROM obs_strategies WHERE strategy_id = ?",
                    (sid,)).fetchone() is None:
                raise ObservationError(E_OBS_UNKNOWN, sid)
            single = self._conn.execute(
                "SELECT bound_spend_tx FROM obs_grants"
                " WHERE account_id = ? AND grant_kind = 'single'"
                " AND strategy_id = ?",
                (account_id, sid)).fetchone()
            if single is not None:
                return {"allowed": True, "kind": "single",
                        "tx": single[0]}
            pass_row = self._conn.execute(
                "SELECT bound_spend_tx FROM obs_grants"
                " WHERE account_id = ? AND grant_kind = 'pass'"
                " AND pass_month = ?",
                (account_id, month)).fetchone()
            if pass_row is not None:
                return {"allowed": True, "kind": "pass", "tx": pass_row[0]}
        return {"allowed": False, "kind": None, "tx": None}

    def observe(self, account_id, strategy_id, at_month):
        """Results-only observation view. Fail-closed: without an
        entitlement the call is rejected with zero charge. The view
        key set is exactly {strategy_id, summary, kind, tx} - the
        registry has no source column, so no source can leak."""
        gate = self.can_observe(account_id, strategy_id, at_month)
        if not gate["allowed"]:
            raise ObservationError(E_OBS_DENIED,
                                   "%s on %s" % (account_id, strategy_id))
        with self._lock:
            row = self._conn.execute(
                "SELECT summary_json FROM obs_strategies"
                " WHERE strategy_id = ?", (strategy_id,)).fetchone()
        return {"strategy_id": strategy_id,
                "summary": json.loads(row[0]),
                "kind": gate["kind"], "tx": gate["tx"]}

    def entitlements_view(self, account_id):
        """Per-account grant view: kind, target, price, bound spend
        tx (provenance) - grant rows are immutable."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT grant_id, grant_kind, strategy_id, pass_month,"
                " token_price, bound_spend_tx FROM obs_grants"
                " WHERE account_id = ? ORDER BY grant_id",
                (account_id,)).fetchall()
        return {"account_id": account_id,
                "grants": [{"grant_id": int(r[0]), "kind": r[1],
                            "strategy_id": r[2], "pass_month": r[3],
                            "token_price": int(r[4]), "spend_tx": r[5]}
                           for r in rows]}

    def strategy_view(self, strategy_id):
        """Registry read view: id, creator, results summary. No
        source field exists in the registry."""
        sid = str(strategy_id or "").strip()
        if not sid:
            raise ObservationError(E_OBS_BAD_ARGS, "strategy id required")
        with self._lock:
            row = self._conn.execute(
                "SELECT creator_account, summary_json, registered_utc"
                " FROM obs_strategies WHERE strategy_id = ?",
                (sid,)).fetchone()
        if row is None:
            raise ObservationError(E_OBS_UNKNOWN, sid)
        return {"strategy_id": sid, "creator_account": row[0],
                "summary": json.loads(row[1]), "registered_utc": row[2]}
