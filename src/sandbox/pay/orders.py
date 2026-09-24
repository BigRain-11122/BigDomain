"""Payment order domain sandbox core (BigDomain P-47-4b).

Implements the pre-registered criteria AC-Y1..AC-Y14 from
docs/spec/payment-integration-spec.md section 1 (criteria were
registered before this code existed; honesty law). Stdlib only: the real
payment channels are the one production touchpoint and stay blocked on
CEO account-domain physical items (merchant IDs / keys, never
self-served, keys only in .env), so the sandbox runs mock gateways
(adapters.py). No real payment API is called anywhere.

Docks (referenced products, not copies):
  - lobby sec_gate  : demand-text content gate (AC-Y8; E_GATE_OFFLINE
    serve refusal, fourth piece of the same-origin family:
    lobby AC-S4 / ledger AC-L8 / ugc AC-U2 / pay AC-Y8)
  - lobby EventStore: pay.success public stream (AC-Y14; six-field core
    + content-addressed evt_id, repo=domain/BigDomain, zone=pay)
  - ledger Ledger   : one-way fiat->token conversion bridge (AC-Y6/Y7;
    share entry ref=order_id ref_type='order', AC-LP1 dock face)

Fiat/token domain isolation (BLUEPRINT 5.4, double insurance): fiat
amounts exist ONLY in the pay tables; the ledger books token counts
only and carries no fiat field anywhere.

Callback processing order (spec section 2): receipt-level idempotency
first (an identical redelivery answers per upstream retry semantics,
AC-Y5 - this must precede the nonce freshness check or a legit retry
would look like a replay), then signature family (AC-Y4 bads 1-3),
nonce freshness (bad 4), state check, amount comparison, then the grant
transaction (AC-Y6), then the public event (AC-Y14), then the ack.

Cross-store atomicity note (honest record): status+entitlement+trigger
writes live in ONE SQLite transaction on the pay DB; the ledger share
entry is a separate single-writer store, so it is ordered INSIDE that
transaction before COMMIT - a ledger failure rolls the pay side back,
and the ledger's UNIQUE(ref, ref_type) idempotence heals the reverse
window on retry. The lobby event append is deterministic (ts =
granted_utc) so retries dedup onto one evt_id.

Encoding discipline: this script stays ASCII; all Chinese copy
(disclaimer, gate wordlists, product catalog) lives in config.json.

Run (readiness self-check = sandbox serve mode):
    python orders.py
    python orders.py --config config.json --db data/pay.db
"""

import argparse
import datetime
import hashlib
import json
import os
import sqlite3
import sys
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
_LOBBY = os.path.normpath(os.path.join(BASE, "..", "lobby"))
_LEDGER = os.path.normpath(os.path.join(BASE, "..", "ledger"))
for _p in (_LOBBY, _LEDGER, BASE):
    # deterministic order after the loop: BASE, _LEDGER, _LOBBY - pay's
    # own reconcile/orders/adapters win over same-named ledger modules,
    # while sec_gate/store still resolve to the lobby products
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

from sec_gate import ContentRejectedError, GateOfflineError, SecGate  # lobby product
import store as lobby_store                                          # lobby product
from ledger import Ledger, LedgerError, E_REF_DUPLICATE              # ledger product
import adapters

REPO = "domain/BigDomain"

# error codes (ASCII)
E_PRICE_TAINTED = "E_PRICE_TAINTED"          # AC-Y2
E_PRODUCT_UNKNOWN = "E_PRODUCT_UNKNOWN"      # AC-Y2
E_NO_BINDING = "E_NO_BINDING"                # AC-Y13 (same code family as ledger AC-L11)
E_CONTENT_REJECTED = "E_CONTENT_REJECTED"    # AC-Y8 (sec_gate same origin)
E_BAD_TRANSITION = "E_BAD_TRANSITION"        # AC-Y1 (trigger)
E_AMOUNT_LOCKED = "E_AMOUNT_LOCKED"          # AC-Y1 (trigger)
E_CALLBACK_REJECTED = "E_CALLBACK_REJECTED"  # AC-Y4
E_AMOUNT_MISMATCH = "E_AMOUNT_MISMATCH"      # AC-Y4 price-injection detect
E_UNKNOWN_ORDER = "E_UNKNOWN_ORDER"
E_BAD_STATE = "E_BAD_STATE"
E_RECEIPT_DUP = "E_RECEIPT_DUP"              # AC-Y5 authoritative-unique
E_BAD_CONFIG = "E_BAD_CONFIG"

_CHANNELS = ("virtual", "standard")
_STATUSES = ("created", "pending", "paid", "granted", "closed")
# legal status edges (spec section 2): main chain + timeout close
# (created/pending -> closed) + refund close (granted -> closed);
# closed is absorbing, granted only closes on refund.
_EDGES = (("created", "pending"), ("created", "closed"),
          ("pending", "paid"), ("pending", "closed"),
          ("paid", "granted"), ("granted", "closed"))


class PayError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_order_id(census_avatar_id, product_id, bucket):
    """Content-addressed order id (avatar + product + ordinal bucket,
    same construction idea as evt_id). Resubmission inside the active
    bucket replays onto one id (AC-Y3); a closed order re-buys into the
    next bucket."""
    canonical = "|".join((str(census_avatar_id), str(product_id), str(int(bucket))))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def compute_receipt_id(payload):
    canonical = "|".join(str(payload.get(k, "")) for k in
                         ("order_id", "amount_cent", "nonce", "ts_utc", "signer", "sig"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def compute_grant_id(order_id):
    return hashlib.sha256(("grant|" + str(order_id)).encode("utf-8")).hexdigest()[:16]


# Spec section 2 DDL. Documented implementation deltas beyond the spec:
#   pay_status_edges - legal-transition table driving trigger T1
_SCHEMA = """
CREATE TABLE IF NOT EXISTS pay_orders (
  order_id         TEXT PRIMARY KEY,
  channel          TEXT NOT NULL CHECK (channel IN ('virtual','standard')),
  census_avatar_id TEXT NOT NULL,
  product_id       TEXT NOT NULL,
  amount_cent      INTEGER NOT NULL CHECK (amount_cent > 0),
  demand_text      TEXT,
  status           TEXT NOT NULL DEFAULT 'created'
                   CHECK (status IN ('created','pending','paid','granted','closed')),
  ts_utc           TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pay_status_edges (
  from_status TEXT NOT NULL,
  to_status   TEXT NOT NULL,
  PRIMARY KEY (from_status, to_status)
);
CREATE TABLE IF NOT EXISTS pay_receipts (
  receipt_id   TEXT PRIMARY KEY,
  order_id     TEXT NOT NULL REFERENCES pay_orders(order_id),
  signer       TEXT NOT NULL,
  nonce        TEXT NOT NULL,
  amount_cent  INTEGER NOT NULL,
  sig_ok       INTEGER NOT NULL,
  verified_utc TEXT NOT NULL,
  UNIQUE (order_id, sig_ok)
);
CREATE TABLE IF NOT EXISTS pay_grants (
  grant_id         TEXT PRIMARY KEY,
  order_id         TEXT NOT NULL UNIQUE REFERENCES pay_orders(order_id),
  census_avatar_id TEXT NOT NULL,
  entitlement      TEXT NOT NULL,
  granted_utc      TEXT NOT NULL
);
"""

_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS trg_order_status
BEFORE UPDATE OF status ON pay_orders
WHEN NEW.status <> OLD.status
BEGIN
  SELECT RAISE(ABORT, 'E_BAD_TRANSITION')
   WHERE NOT EXISTS (SELECT 1 FROM pay_status_edges
                      WHERE from_status = OLD.status AND to_status = NEW.status);
END;
CREATE TRIGGER IF NOT EXISTS trg_order_amount_lock
BEFORE UPDATE OF amount_cent ON pay_orders
BEGIN
  SELECT RAISE(ABORT, 'E_AMOUNT_LOCKED');
END;
"""

_SEED_EDGES = "\n".join(
    "INSERT OR IGNORE INTO pay_status_edges (from_status, to_status) VALUES ('%s','%s');"
    % edge for edge in _EDGES)


class PayOrders:
    """Single-writer order domain: one connection guarded by one lock;
    every write opens with BEGIN IMMEDIATE (SQLite WAL discipline)."""

    def __init__(self, config, db_path, event_store, ledger):
        self._startup_checks(config, event_store, ledger)
        self.db_path = db_path
        parent = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(parent, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA + "\n" + _SEED_EDGES + "\n" + _TRIGGERS)
        self.event_store = event_store
        self.ledger = ledger
        self._adapters = adapters.from_config(config)

    def close(self):
        with self._lock:
            self._conn.close()

    # ---- startup self-checks (serve refusal family) -----------------------

    def _startup_checks(self, config, event_store, ledger):
        if not isinstance(config, dict):
            raise GateOfflineError("config not loaded")
        self.config = config
        self.gate = SecGate.from_config(config)  # AC-Y8: no gate = no serve
        bans = [str(w) for w in (config.get("copy_ban_words") or []) if str(w)]
        if not bans:
            raise GateOfflineError("copy_ban_words missing or empty (AC-Y11)")
        self.copy_ban_words = bans
        comp = config.get("compliance") or {}
        self.disclaimer = str(comp.get("disclaimer", ""))
        if not self.disclaimer:
            raise GateOfflineError("compliance.disclaimer missing (AC-Y10 resident face)")
        self.disclaimer_persistent = bool(comp.get("disclaimer_persistent", True))
        self.ai_service = 1  # fixed, server-authoritative (AC-Y9)
        order_cfg = config.get("order") or {}
        try:
            self.expire_minutes = float(order_cfg.get("expire_window_minutes", 15))
        except (TypeError, ValueError):
            raise GateOfflineError("order.expire_window_minutes invalid") from None
        if self.expire_minutes <= 0:
            raise GateOfflineError("order.expire_window_minutes must be > 0")
        conv = config.get("conversion") or {}
        self.conv_pool = str(conv.get("pool", "")).strip()
        self.conv_action = str(conv.get("action", "")).strip()
        if not self.conv_pool or not self.conv_action:
            raise GateOfflineError("conversion.pool/action missing (AC-Y6 bridge)")
        products = config.get("products")
        if not isinstance(products, dict) or not products:
            raise GateOfflineError("products price table missing or empty (AC-Y2)")
        self.products = {}
        for pid, spec in products.items():
            if not isinstance(spec, dict):
                raise GateOfflineError("product %s malformed" % pid)
            channel = str(spec.get("channel", ""))
            if channel not in _CHANNELS:
                raise GateOfflineError("product %s bad channel: %s" % (pid, channel))
            try:
                price_cent = int(spec.get("price_cent", 0))
                share_tokens = int(spec.get("share_tokens", 0))
            except (TypeError, ValueError):
                raise GateOfflineError("product %s bad numeric fields" % pid) from None
            if price_cent <= 0 or share_tokens < 0:
                raise GateOfflineError("product %s bad price/tokens" % pid)
            entitlement = str(spec.get("entitlement", "")).strip()
            if not entitlement:
                raise GateOfflineError("product %s entitlement missing" % pid)
            copy_text = str(spec.get("copy", ""))
            hit = next((w for w in self.copy_ban_words if w and w in copy_text), None)
            if hit is not None:
                # AC-Y11: banned marketing copy = config refused, product
                # never listed (fail closed before serve)
                raise GateOfflineError(
                    "product copy banned (AC-Y11): %s word=%s" % (pid, hit))
            self.products[str(pid)] = {
                "channel": channel, "price_cent": price_cent,
                "share_tokens": share_tokens, "entitlement": entitlement,
                "copy": copy_text,
            }
        if event_store is None or ledger is None:
            raise GateOfflineError(
                "public stream and ledger docks are mandatory (AC-Y6/AC-Y14)")

    @classmethod
    def startup_check(cls, config, db_path, event_store, ledger):
        probe = cls(config, db_path, event_store, ledger)
        probe.close()
        return True

    # ---- helpers -----------------------------------------------------------

    def _face(self, out):
        """Compliance faces: every response carries the fixed
        server-authoritative ai_service marker (AC-Y9) and the resident
        disclaimer (AC-Y10)."""
        out["ai_service"] = self.ai_service
        out["disclaimer"] = self.disclaimer
        out["persistent"] = self.disclaimer_persistent
        return out

    def _order_row(self, order_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT order_id, channel, census_avatar_id, product_id, amount_cent,"
                " demand_text, status, ts_utc FROM pay_orders WHERE order_id = ?",
                (order_id,)).fetchone()
        if row is None:
            return None
        keys = ("order_id", "channel", "census_avatar_id", "product_id",
                "amount_cent", "demand_text", "status", "ts_utc")
        return dict(zip(keys, row))

    # ---- order faces ---------------------------------------------------------

    def create_order(self, product_id, census_avatar_id, demand_text=None,
                     client_amount_cent=None, client_ai_service=None):
        """Create (or idempotently replay) one order. Client-supplied
        amount is refused outright (AC-Y2: the server price table is the
        only amount source, locked at creation); client ai_service hints
        are ignored (AC-Y9). Demand text, when carried, must pass the
        content gate before anything is accepted (AC-Y8)."""
        del client_ai_service  # server authority only (AC-Y9)
        if not str(census_avatar_id or "").strip():
            raise PayError(E_NO_BINDING, "census avatar binding required (AC-Y13)")
        if client_amount_cent is not None:
            raise PayError(E_PRICE_TAINTED, str(client_amount_cent))
        product = self.products.get(str(product_id))
        if product is None:
            raise PayError(E_PRODUCT_UNKNOWN, str(product_id))
        text = str(demand_text or "").strip()
        if text:
            try:
                self.gate.check_text(text)  # gate 1 + gate 2 (lobby product)
            except ContentRejectedError as exc:
                # gate hit = refused before any order row exists
                raise PayError(E_CONTENT_REJECTED,
                               "gate %d wordlist hit (AC-Y8)" % exc.gate) from None
        avatar = str(census_avatar_id).strip()
        with self._lock:
            closed = self._conn.execute(
                "SELECT COUNT(*) FROM pay_orders WHERE census_avatar_id = ?"
                " AND product_id = ? AND status = 'closed'",
                (avatar, str(product_id))).fetchone()[0]
        bucket = int(closed) + 1
        order_id = compute_order_id(avatar, str(product_id), bucket)
        replayed = False
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                existing = self._conn.execute(
                    "SELECT status FROM pay_orders WHERE order_id = ?",
                    (order_id,)).fetchone()
                if existing is None:
                    self._conn.execute(
                        "INSERT INTO pay_orders (order_id, channel, census_avatar_id,"
                        " product_id, amount_cent, demand_text, status, ts_utc)"
                        " VALUES (?,?,?,?,?,?,?,?)",
                        (order_id, product["channel"], avatar, str(product_id),
                         product["price_cent"], text or None, "created", now_utc()))
                else:
                    replayed = True
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                # cross-process create raced onto the same bucket: the
                # winner holds the order, replay is idempotent (AC-Y3)
                self._conn.execute("ROLLBACK")
                replayed = True
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        order = self._order_row(order_id)
        return self._face({
            "order_id": order_id, "product_id": str(product_id),
            "channel": order["channel"], "amount_cent": order["amount_cent"],
            "status": order["status"], "idempotent": replayed,
        })

    def place_order(self, order_id):
        """created -> pending via the channel adapter (mock prepay)."""
        order = self._order_row(order_id)
        if order is None:
            raise PayError(E_UNKNOWN_ORDER, str(order_id))
        if order["status"] != "created":
            raise PayError(E_BAD_STATE, "place needs created, got " + order["status"])
        adapter = self._adapters[order["channel"]]
        prepay = adapter.place(order_id, order["amount_cent"])
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "UPDATE pay_orders SET status = 'pending' WHERE order_id = ?",
                    (order_id,))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return self._face({"order_id": order_id, "status": "pending",
                           "prepay_id": prepay["prepay_id"],
                           "channel_signer": prepay["channel_signer"]})

    def sweep_expired(self, now=None):
        """created/pending orders past the expire window auto-close
        (legal edges created->closed / pending->closed; trigger T1
        validates). Closed orders re-buy under a new bucket."""
        reference = str(now or now_utc())
        cutoff = (datetime.datetime.strptime(reference, "%Y-%m-%dT%H:%M:%SZ")
                  - datetime.timedelta(minutes=self.expire_minutes)
                  ).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "UPDATE pay_orders SET status = 'closed'"
                    " WHERE status IN ('created','pending') AND ts_utc < ?",
                    (cutoff,))
                n = cur.rowcount
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return int(n)

    # ---- callback processing (AC-Y4/Y5/Y6) ---------------------------------

    def _record_bad_receipt(self, payload, reason):
        """Best-effort evidence row (sig_ok=0, four-bad audit trail).
        The schema caps one bad-receipt row per order
        (UNIQUE(order_id, sig_ok)); a cap hit only means the evidence
        already exists - the rejection itself always stands."""
        receipt_id = compute_receipt_id(payload)
        try:
            with self._lock:
                self._conn.execute("BEGIN IMMEDIATE")
                try:
                    self._conn.execute(
                        "INSERT INTO pay_receipts (receipt_id, order_id, signer, nonce,"
                        " amount_cent, sig_ok, verified_utc) VALUES (?,?,?,?,?,?,?)",
                        (receipt_id, str(payload.get("order_id", "")),
                         str(payload.get("signer", "")), str(payload.get("nonce", "")),
                         int(payload.get("amount_cent", 0)), 0, now_utc()))
                    self._conn.execute("COMMIT")
                except sqlite3.IntegrityError:
                    self._conn.execute("ROLLBACK")
                except BaseException:
                    self._conn.execute("ROLLBACK")
                    raise
        except (sqlite3.IntegrityError, sqlite3.OperationalError):
            pass  # unknown order has no FK target; rejection stands regardless
        return receipt_id

    def handle_callback(self, payload):
        """One gateway callback through the full constitutional order.
        Fresh valid callbacks: receipt + pending->paid (one tx), then the
        grant transaction, then the public event. Identical redeliveries
        answer per upstream retry semantics (AC-Y5)."""
        if not isinstance(payload, dict):
            raise PayError(E_CALLBACK_REJECTED, "payload not an object")
        order_id = str(payload.get("order_id", ""))
        order = self._order_row(order_id)
        if order is None:
            raise PayError(E_UNKNOWN_ORDER, order_id)
        receipt_id = compute_receipt_id(payload)
        with self._lock:
            seen = self._conn.execute(
                "SELECT sig_ok FROM pay_receipts WHERE receipt_id = ?",
                (receipt_id,)).fetchone()
        if seen is not None:
            if not seen[0]:
                raise PayError(E_CALLBACK_REJECTED, "evidence row: previously rejected")
            current = self._order_row(order_id)
            if current["status"] == "paid":
                self._grant(current)          # crash-window heal = retry entry
            elif current["status"] == "granted":
                self._emit_pay_success(order_id)  # deterministic ts -> dedup
            elif current["status"] not in ("paid", "granted"):
                raise PayError(E_BAD_STATE, "receipt exists but status=" + current["status"])
            return self._face({"receipt_id": receipt_id, "order_id": order_id,
                               "status": self._order_row(order_id)["status"],
                               "idempotent": True})
        # signature family (AC-Y4 bads 1-3)
        adapter = self._adapters[order["channel"]]
        try:
            adapter.verify(payload)
        except adapters.AdapterError as exc:
            self._record_bad_receipt(payload, exc.check)
            raise PayError(E_CALLBACK_REJECTED, exc.check) from None
        # nonce freshness (AC-Y4 bad 4)
        with self._lock:
            burned = self._conn.execute(
                "SELECT 1 FROM pay_receipts WHERE nonce = ?",
                (str(payload.get("nonce", "")),)).fetchone()
        if burned is not None:
            self._record_bad_receipt(payload, "nonce replay")
            raise PayError(E_CALLBACK_REJECTED, "nonce replay")
        # state check (no evidence row: a state anomaly, not a signature bad)
        if order["status"] != "pending":
            raise PayError(E_BAD_STATE,
                           "callback needs pending, got " + order["status"])
        # amount comparison (AC-Y4 price injection)
        if int(payload.get("amount_cent", 0)) != order["amount_cent"]:
            self._record_bad_receipt(payload, "amount mismatch")
            raise PayError(E_AMOUNT_MISMATCH, "%s != %d"
                           % (payload.get("amount_cent"), order["amount_cent"]))
        # receipt + pending->paid in one transaction
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO pay_receipts (receipt_id, order_id, signer, nonce,"
                    " amount_cent, sig_ok, verified_utc) VALUES (?,?,?,?,?,1,?)",
                    (receipt_id, order_id, str(payload.get("signer", "")),
                     str(payload.get("nonce", "")), int(payload["amount_cent"]),
                     now_utc()))
                self._conn.execute(
                    "UPDATE pay_orders SET status = 'paid' WHERE order_id = ?",
                    (order_id,))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError as exc:
                self._conn.execute("ROLLBACK")
                msg = str(exc)
                if "pay_receipts.receipt_id" in msg:
                    raise PayError(E_RECEIPT_DUP, "receipt raced") from None
                if "pay_receipts" in msg:
                    # UNIQUE(order_id, sig_ok=1): another valid receipt is the
                    # authority already (AC-Y5), zero re-grant zero re-migration
                    raise PayError(E_RECEIPT_DUP, "authoritative receipt exists") from None
                if "pay_orders" in msg:
                    raise PayError(E_BAD_TRANSITION, msg) from None
                raise
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        # grant transaction (AC-Y6)
        self._grant(self._order_row(order_id))
        return self._face({"receipt_id": receipt_id, "order_id": order_id,
                           "status": "granted"})

    # ---- grant + conversion bridge (AC-Y6/Y7) --------------------------------

    def _grant(self, order):
        """paid -> granted: entitlement row + status inside ONE pay-DB
        transaction; the ledger conversion share entry is ordered inside
        it (before COMMIT) so a ledger failure rolls the whole grant
        back - no 'paid but half-granted' window. The ledger's
        UNIQUE(ref, ref_type) heals the reverse window on retry."""
        product = self.products[order["product_id"]]
        share_tokens = int(product["share_tokens"])
        grant_id = compute_grant_id(order["order_id"])
        ts = now_utc()
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO pay_grants (grant_id, order_id, census_avatar_id,"
                    " entitlement, granted_utc) VALUES (?,?,?,?,?)",
                    (grant_id, order["order_id"], order["census_avatar_id"],
                     product["entitlement"], ts))
                self._conn.execute(
                    "UPDATE pay_orders SET status = 'granted' WHERE order_id = ?",
                    (order["order_id"],))
                if share_tokens > 0:
                    try:
                        self.ledger.share_from_pool(
                            self.conv_pool, "usr:" + order["census_avatar_id"],
                            share_tokens, order["order_id"], "order",
                            self.conv_action)
                    except LedgerError as exc:
                        if exc.code == E_REF_DUPLICATE:
                            pass  # prior attempt already booked this conversion
                        else:
                            raise
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        self._emit_pay_success(order["order_id"])

    def _emit_pay_success(self, order_id):
        """pay.success onto the public stream (AC-Y14): six-field core +
        content-addressed evt_id, zone=pay. ts comes from the stored
        granted_utc so retries dedup onto one evt_id."""
        order = self._order_row(order_id)
        if order is None or order["status"] != "granted":
            raise PayError(E_BAD_STATE, "emit needs granted order")
        with self._lock:
            row = self._conn.execute(
                "SELECT granted_utc FROM pay_grants WHERE order_id = ?",
                (order_id,)).fetchone()
        granted_utc = row[0]
        product = self.products[order["product_id"]]
        payload = {"order_id": order_id, "product_id": order["product_id"],
                   "channel": order["channel"],
                   "share_tokens": int(product["share_tokens"])}
        summary = "order %s granted: product=%s channel=%s" % (
            order_id, order["product_id"], order["channel"])
        evt_id = lobby_store.compute_evt_id(
            granted_utc, "pay.success", order["census_avatar_id"], REPO, "pay",
            summary, json.dumps(payload, ensure_ascii=False, sort_keys=True))
        try:
            self.event_store.append(granted_utc, "pay.success",
                                    order["census_avatar_id"], "pay", summary,
                                    payload)
        except sqlite3.IntegrityError:
            pass  # same evt_id already in the stream (idempotent heal)
        return evt_id

    # ---- read faces -----------------------------------------------------------

    def order_detail(self, order_id):
        order = self._order_row(order_id)
        if order is None:
            raise PayError(E_UNKNOWN_ORDER, str(order_id))
        return self._face(dict(order))

    def grant_row(self, grant_id):
        """Single-grant read face for the entitlement domain (member
        piece activation, AC-M2 source authenticity): the member store
        verifies every activation against this face; a forged grant id
        resolves to None. Additive read face, zero criteria change."""
        with self._lock:
            row = self._conn.execute(
                "SELECT grant_id, order_id, census_avatar_id, entitlement,"
                " granted_utc FROM pay_grants WHERE grant_id = ?",
                (str(grant_id or ""),)).fetchone()
        if row is None:
            return None
        return {"grant_id": row[0], "order_id": row[1],
                "census_avatar_id": row[2], "entitlement": row[3],
                "granted_utc": row[4]}

    def grants_for(self, census_avatar_id):
        """Grants query face: the lobby E_ENTRANCE_REQUIRED judgement
        source (birthright/any grant = entrance credential; enforcement
        lives in the lobby piece, referenced not copied). Items carry
        grant_id so the member activation face can address real grants
        (additive field, judgement semantics unchanged)."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT grant_id, order_id, entitlement, granted_utc"
                " FROM pay_grants"
                " WHERE census_avatar_id = ? ORDER BY granted_utc",
                (str(census_avatar_id),)).fetchall()
        return {"census_avatar_id": str(census_avatar_id),
                "items": [{"grant_id": r[0], "order_id": r[1],
                           "entitlement": r[2],
                           "granted_utc": r[3]} for r in rows]}


def main():
    parser = argparse.ArgumentParser(
        description="BigDomain sandbox pay order domain (P-47-4b) readiness self-check")
    parser.add_argument("--config", default=os.path.join(BASE, "config.json"))
    parser.add_argument("--db", default=os.path.join(BASE, "data", "pay.db"))
    parser.add_argument("--events-db", default=os.path.join(BASE, "data", "events.db"))
    parser.add_argument("--ledger-db", default=os.path.join(BASE, "data", "ledger.db"))
    parser.add_argument("--ledger-config",
                        default=os.path.join(_LEDGER, "config.json"))
    args = parser.parse_args()
    try:
        with open(args.config, encoding="utf-8") as handle:
            cfg = json.load(handle)
        with open(args.ledger_config, encoding="utf-8") as handle:
            led_cfg = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print("E_GATE_OFFLINE: config unreadable: %s" % exc, file=sys.stderr)
        return 2
    led = None
    pay = None
    events = None
    try:
        events = lobby_store.EventStore(args.events_db)
        led = Ledger(args.ledger_db, led_cfg)
        pay = PayOrders(cfg, args.db, events, led)
        print("pay orders ready: products=%d channels=virtual,standard gate=ok"
              " db=%s" % (len(pay.products), args.db), flush=True)
        return 0
    except (GateOfflineError, adapters.AdapterError) as exc:
        print(str(exc), file=sys.stderr)  # serve refusal, same family as lobby/ledger/ugc
        return 2
    finally:
        if pay is not None:
            pay.close()
        if led is not None:
            led.close()
        if events is not None:
            events.close()


if __name__ == "__main__":
    sys.exit(main())
