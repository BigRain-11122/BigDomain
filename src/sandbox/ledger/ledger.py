"""Token double-entry ledger sandbox core (BigDomain P-47-2b).

Implements the pre-registered acceptance criteria AC-L1..AC-L11 from
docs/spec/token-ledger-spec.md section 1 (criteria were registered before
this code existed; honesty law). Stdlib only: no external dependency, no
external API touchpoint (three-question gate: not needed, nothing local
is missing, no CEO authorization).

Structural bans (BLUEPRINT section 5.4, double insurance): there is no
withdraw, no transfer-out, no fiat currency field, and no exchange/out
verb anywhere in this schema or this API. Tokens are pure in-loop
consumption credits; fiat settlement belongs to BigCompute only.

Encoding discipline: this script stays ASCII; all Chinese copy (risk
disclaimer, AI label, gate wordlists) lives in config.json.

Storage discipline: one SQLite DB in this repo (WAL), single writer,
same pattern as the lobby event store.
"""

import datetime
import hashlib
import json
import os
import sqlite3
import sys
import threading

REPO = "domain/BigDomain"

_HERE = os.path.dirname(os.path.abspath(__file__))
_LOBBY = os.path.normpath(os.path.join(_HERE, "..", "lobby"))
if _LOBBY not in sys.path:
    sys.path.insert(0, _LOBBY)

from sec_gate import SecGate  # lobby gate pipeline product: referenced, not copied

AUTH_ACCOUNT = "equity:auth"
POOL_ACCOUNTS = ("pool:reserve", "pool:reward", "pool:share")
TX_TYPES = ("mint", "spend", "share", "adjust")
REF_TYPES = ("event", "order", "settlement", "manual")

# error codes (ASCII)
E_TX_IMBALANCE = "E_TX_IMBALANCE"          # AC-L1
E_TX_MIN_ENTRIES = "E_TX_MIN_ENTRIES"      # AC-L1
E_TX_CLOSED = "E_TX_CLOSED"
E_TX_IMMUTABLE = "E_TX_IMMUTABLE"
E_TX_DUPLICATE = "E_TX_DUPLICATE"          # AC-L3
E_REF_DUPLICATE = "E_REF_DUPLICATE"        # AC-L4
E_NEGATIVE_BALANCE = "E_NEGATIVE_BALANCE"  # AC-L2
E_TOKEN_CAP = "E_TOKEN_CAP"                # AC-L7
E_GATE_REF = "E_GATE_REF"                  # AC-L8
E_NO_BINDING = "E_NO_BINDING"              # AC-L11
E_UNKNOWN_ACCOUNT = "E_UNKNOWN_ACCOUNT"
E_BAD_ACCOUNT = "E_BAD_ACCOUNT"
E_BAD_AMOUNT = "E_BAD_AMOUNT"
E_BAD_TYPE = "E_BAD_TYPE"
E_BAD_ACTION = "E_BAD_ACTION"
E_ADJUST_MEMO = "E_ADJUST_MEMO"

_TRIGGER_CODES = (E_NEGATIVE_BALANCE, E_TX_IMBALANCE, E_TX_MIN_ENTRIES,
                  E_TX_CLOSED, E_TX_IMMUTABLE)


class LedgerError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_tx_id(ts_utc, tx_type, action, ref, ref_type, entries):
    """Content-addressed tx id: sha256 over the six-field core plus an
    entries digest (same construction idea as the lobby evt_id dialect)."""
    digest = hashlib.sha256(json.dumps(
        [[account_id, direction, int(amount)] for account_id, direction, amount in entries],
        separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()[:16]
    canonical = "|".join((ts_utc, tx_type, action, REPO, str(ref), ref_type, digest))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class Ledger:
    """Single-writer double-entry ledger: one connection guarded by one
    lock; every tx writes inside BEGIN IMMEDIATE (SQLite WAL discipline)."""

    def __init__(self, db_path, config):
        self.db_path = db_path
        self.config = config or {}
        parent = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(parent, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        with open(os.path.join(_HERE, "schema.sql"), encoding="utf-8") as handle:
            self._conn.executescript(handle.read())
        self._gate = None

    def close(self):
        with self._lock:
            self._conn.close()

    # -- serve gate ---------------------------------------------------------

    def serve_check(self):
        """AC-L8: an unwired content gate means serve mode refuses to work
        at all (same origin as lobby AC-S4 E_GATE_OFFLINE)."""
        if self._gate is None:
            self._gate = SecGate.from_config(self.config)
        return self._gate

    # -- accounts -----------------------------------------------------------

    def ensure_account(self, account_id, census_avatar_id=None):
        """Create an account on first use. usr:* accounts must carry a
        census avatar binding (AC-L11); binding is a usr:* exclusive.
        Existing accounts pass through: their binding was enforced at
        creation time and cannot be re-pointed from here."""
        with self._lock:
            row = self._conn.execute(
                "SELECT census_avatar_id FROM ledger_accounts WHERE account_id = ?",
                (account_id,)).fetchone()
        if row is not None:
            return account_id
        if account_id.startswith("usr:"):
            if not census_avatar_id:
                raise LedgerError(E_NO_BINDING, account_id)
        else:
            census_avatar_id = None
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO ledger_accounts (account_id, census_avatar_id, created_utc)"
                    " VALUES (?,?,?)", (account_id, census_avatar_id, now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return account_id

    def record_gate_pass(self, evt_id):
        """Sandbox stand-in for the lobby gate pipeline product: mark an
        event as content-gate passed (AC-L8 source registry)."""
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT OR IGNORE INTO gate_events (evt_id, gate, checked_utc)"
                    " VALUES (?,?,?)", (str(evt_id), "pass", now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return evt_id

    # -- core writer --------------------------------------------------------

    def _write_tx(self, tx_type, action, ref, ref_type, source_ai, entries,
                  memo=None, ts_utc=None):
        """Validate, then book one tx (header + entries + close) atomically.
        App validates first; schema triggers are the fallback gate."""
        if tx_type not in TX_TYPES:
            raise LedgerError(E_BAD_TYPE, tx_type)
        if ref_type not in REF_TYPES or not str(ref).strip():
            raise LedgerError(E_BAD_TYPE, "ref/ref_type")
        if tx_type == "adjust" and not (memo and str(memo).strip()):
            raise LedgerError(E_ADJUST_MEMO, "adjust requires an approval memo")
        if len(entries) < 2:
            raise LedgerError(E_TX_MIN_ENTRIES, str(len(entries)))
        for account_id, direction, amount in entries:
            if direction not in ("debit", "credit"):
                raise LedgerError(E_BAD_TYPE, direction)
            if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
                raise LedgerError(E_BAD_AMOUNT, str(amount))
            with self._lock:
                known = self._conn.execute(
                    "SELECT 1 FROM ledger_accounts WHERE account_id = ?",
                    (account_id,)).fetchone()
            if not known:
                raise LedgerError(E_UNKNOWN_ACCOUNT, account_id)
        total_debit = sum(a for _, d, a in entries if d == "debit")
        total_credit = sum(a for _, d, a in entries if d == "credit")
        if total_debit != total_credit or total_debit <= 0:
            raise LedgerError(E_TX_IMBALANCE, "debit=%d credit=%d" % (total_debit, total_credit))
        ts = ts_utc or now_utc()
        tx_id = compute_tx_id(ts, tx_type, action, ref, ref_type, entries)
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO ledger_tx (tx_id, type, action, ref, ref_type, source_ai,"
                    " memo, ts_utc) VALUES (?,?,?,?,?,?,?,?)",
                    (tx_id, tx_type, action, str(ref), ref_type, 1 if source_ai else 0,
                     memo, ts))
                for account_id, direction, amount in entries:
                    self._conn.execute(
                        "INSERT INTO ledger_entries (tx_id, account_id, direction, amount,"
                        " ts_utc) VALUES (?,?,?,?,?)",
                        (tx_id, account_id, direction, int(amount), ts))
                self._conn.execute("UPDATE ledger_tx SET closed = 1 WHERE tx_id = ?", (tx_id,))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError as exc:
                self._conn.execute("ROLLBACK")
                msg = str(exc)
                for code in _TRIGGER_CODES:
                    if code in msg:
                        raise LedgerError(code, msg) from None
                if "ledger_tx.tx_id" in msg:
                    raise LedgerError(E_TX_DUPLICATE, msg) from None    # AC-L3
                if "ledger_tx.ref" in msg:
                    raise LedgerError(E_REF_DUPLICATE, msg) from None   # AC-L4
                if "FOREIGN KEY" in msg:
                    raise LedgerError(E_UNKNOWN_ACCOUNT, msg) from None
                raise
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return tx_id

    # -- book operations ----------------------------------------------------

    def mint_to_pool(self, pool_id, amount, ref, ref_type="settlement",
                     source_ai=False, memo=None):
        """Authorized mint: equity:auth debit -> pool credit. The auth
        account stays negative by construction (zero-sum identity AC-L6);
        the mint counterparty proves every issued token has an authorizer."""
        if pool_id not in POOL_ACCOUNTS:
            raise LedgerError(E_BAD_ACCOUNT, pool_id)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise LedgerError(E_BAD_AMOUNT, str(amount))
        self.ensure_account(pool_id)
        self.ensure_account(AUTH_ACCOUNT)
        entries = [(AUTH_ACCOUNT, "debit", amount), (pool_id, "credit", amount)]
        return self._write_tx("mint", "mint", ref, ref_type, source_ai, entries, memo)

    def grant_reward(self, account_id, action, ref, ref_type="event"):
        """Reward payout from a pool (tx type 'share' per the spec
        paradigm): behavior mining + co-creation shares. Enforces AC-L7
        daily cap, AC-L8 content gate, AC-L9 server-side source_ai, AC-L11
        avatar binding."""
        self.serve_check()
        if not account_id.startswith("usr:"):
            raise LedgerError(E_BAD_ACCOUNT, "rewards go to usr:* accounts only")
        spec = (self.config.get("actions") or {}).get(action)
        if not isinstance(spec, dict):
            raise LedgerError(E_BAD_ACTION, action)
        amount = int(spec.get("score", 0))
        pool_id = str(spec.get("pool", "pool:reward"))
        source_ai = bool(spec.get("ai_adjudicated", False))  # AC-L9: server authority
        cap = int(spec.get("daily_cap", 0) or 0)
        self.ensure_account(account_id)
        if spec.get("content_gate"):
            if ref_type != "event":
                raise LedgerError(E_GATE_REF, "content rewards must reference events")
            with self._lock:
                passed = self._conn.execute(
                    "SELECT 1 FROM gate_events WHERE evt_id = ? AND gate = 'pass'",
                    (str(ref),)).fetchone()
            if not passed:
                raise LedgerError(E_GATE_REF, str(ref))
        day = now_utc()[:10]
        with self._lock:
            used = self._conn.execute(
                "SELECT COALESCE(SUM(e.amount), 0) FROM ledger_entries e"
                " JOIN ledger_tx t ON t.tx_id = e.tx_id"
                " WHERE e.account_id = ? AND e.direction = 'credit' AND t.action = ?"
                " AND substr(t.ts_utc, 1, 10) = ?",
                (account_id, action, day)).fetchone()[0]
        if cap > 0 and used + amount > cap:
            raise LedgerError(E_TOKEN_CAP, "action=%s used=%d amount=%d cap=%d"
                              % (action, used, amount, cap))
        entries = [(pool_id, "debit", amount), (account_id, "credit", amount)]
        return self._write_tx("share", action, ref, ref_type, source_ai, entries)

    def share_from_pool(self, pool_id, account_id, amount, ref,
                        ref_type="order", action="pay_conversion", source_ai=False):
        """AC-LP1 dock face (P-47-4 pay piece): order-receipt-triggered
        share entry, the one-way fiat->token conversion bridge. The
        token count comes from the pay price table (server-side); this
        ledger books token counts only - fiat amounts have no field
        anywhere here (BLUEPRINT 5.4 double insurance). Same serve-gate
        requirement as every other payout."""
        self.serve_check()
        if pool_id not in POOL_ACCOUNTS:
            raise LedgerError(E_BAD_ACCOUNT, pool_id)
        if not account_id.startswith("usr:"):
            raise LedgerError(E_BAD_ACCOUNT, account_id)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise LedgerError(E_BAD_AMOUNT, str(amount))
        self.ensure_account(pool_id)
        self.ensure_account(account_id, census_avatar_id=account_id[4:])
        entries = [(pool_id, "debit", amount), (account_id, "credit", amount)]
        return self._write_tx("share", action, ref, ref_type, source_ai, entries)

    def spend(self, account_id, amount, ref, ref_type="order", memo=None):
        """Privilege consumption: usr debit -> pool:reserve credit. Tokens
        never leave the loop (BLUEPRINT 5.4); re-issuance stays bound by
        the reserve balance."""
        if not account_id.startswith("usr:"):
            raise LedgerError(E_BAD_ACCOUNT, account_id)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise LedgerError(E_BAD_AMOUNT, str(amount))
        self.ensure_account("pool:reserve")
        entries = [(account_id, "debit", amount), ("pool:reserve", "credit", amount)]
        return self._write_tx("spend", "spend", ref, ref_type, False, entries, memo)

    def adjust(self, entries, ref, memo, ref_type="manual", source_ai=False):
        """Manual correction tx: approval memo mandatory; the reconcile
        script names every adjust line (spec section 3, check 8)."""
        return self._write_tx("adjust", "adjust", ref, ref_type, source_ai, entries, memo)

    # -- read faces (API: ledger.balance / ledger.bill) ----------------------

    def disclaimer_payload(self):
        tok = self.config.get("token") or {}
        return {
            "disclaimer": str(tok.get("disclaimer", "")),      # AC-L10
            "persistent": bool(tok.get("disclaimer_persistent", True)),
        }

    def balance(self, account_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT balance FROM ledger_accounts WHERE account_id = ?",
                (account_id,)).fetchone()
        if not row:
            raise LedgerError(E_UNKNOWN_ACCOUNT, account_id)
        out = {"account_id": account_id, "balance": int(row[0])}
        out.update(self.disclaimer_payload())
        return out

    def bill(self, account_id, limit=100):
        ai_label = str((self.config.get("token") or {}).get("ai_label_text", ""))
        with self._lock:
            rows = self._conn.execute(
                "SELECT t.tx_id, t.type, t.action, t.ref, t.ref_type, t.source_ai, t.memo,"
                " t.ts_utc, e.direction, e.amount"
                " FROM ledger_entries e JOIN ledger_tx t ON t.tx_id = e.tx_id"
                " WHERE e.account_id = ? ORDER BY t.ts_utc DESC, e.entry_id DESC LIMIT ?",
                (account_id, int(limit))).fetchall()
        items = []
        for r in rows:
            item = {
                "tx_id": r[0], "type": r[1], "action": r[2], "ref": r[3], "ref_type": r[4],
                "source_ai": bool(r[5]), "memo": r[6], "ts_utc": r[7],
                "direction": r[8], "amount": int(r[9]),
            }
            if r[5]:
                item["ai_label"] = ai_label  # AC-L9 bill-face presentation label
            items.append(item)
        out = {"account_id": account_id, "items": items}
        out.update(self.disclaimer_payload())
        return out

    # -- sandbox mock entrance (API: token.grant_sandbox) --------------------

    def grant_sandbox(self, request):
        """Sandbox stub for the mock entrance token.grant_sandbox (spec
        section 2 API face). Production trigger sources replace this whole
        entry point when P-47-4 lands (AC-LP1). A client-supplied
        'source_ai' key is deliberately ignored: the server alone decides
        the AI-adjudication marker (AC-L9)."""
        req = dict(request or {})
        op = str(req.pop("op", ""))
        if op == "mint":
            return self.mint_to_pool(str(req["pool_id"]), int(req["amount"]),
                                     str(req["ref"]), str(req.get("ref_type", "settlement")))
        if op == "reward":
            req.pop("source_ai", None)  # ignored on purpose (AC-L9)
            return self.grant_reward(str(req["account_id"]), str(req["action"]),
                                     str(req["ref"]), str(req.get("ref_type", "event")))
        if op == "spend":
            return self.spend(str(req["account_id"]), int(req["amount"]),
                              str(req["ref"]), str(req.get("ref_type", "order")))
        raise LedgerError(E_BAD_TYPE, "op=" + op)
