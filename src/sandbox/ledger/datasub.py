"""City public dataset subscription face (BigDomain explore
queue, claimed R1764; canon = the "city public dataset
subscription" row: the reports one-time-purchase face R627 is the
seed - this adds periodic subscription windows with delivery,
reusing the member/observation monthly-window idempotency
judgement and the reports permission-gate + voucher delivery
judgement, reference not copy).

Design rulings (pre-registered AC-DSB1..AC-DSB7 in the R1764
explore-queue row before this code existed - honesty law):

  - carrier: DatasetSubscriptionFace, an INDEPENDENT sqlite file
    datasub.db next to the ledger db (single writer, WAL - the
    apimarket R1763 posture; zero ledger schema touch so the
    fingerprint sentinel stays CLEAN by construction)
  - window law: monthly datasets take YYYY-MM (01..12) windows,
    quarterly datasets take YYYY-Q1..Q4 windows; both regexes end
    in the hard end-anchor (the R1748 trailing-newline bad-arg
    lesson); a well-formed window of the WRONG period for the
    dataset is rejected E_DSB_BAD_WINDOW before any spend
  - subscription law (observation R623 judgement reuse): exactly
    ONE token spend per (account, dataset, window) bound to its
    spend tx; same-window resubscribe and same-ref replay are
    both rejected BEFORE the spend (zero charge); a different
    window is a separate legal spend
  - delivery law (reports R627 judgement reuse): the immutable
    subscription row is the permission gate; each deliver() with
    a distinct delivery_ref appends one immutable delivery row;
    duplicate delivery refs are rejected with zero double-write;
    delivery and every read face move zero tokens
  - structural de-identification (reports R627 law carried
    over): this module owns exactly three tables and performs
    zero SELECTs against any other table - a delivery bundle
    carries exactly the descriptor key set (title, period,
    window, sha256 dataset digest), so raw row data cannot leak
    through this face by construction

Non-advisory standing note (permanent): the delivered datasets
are descriptive aggregate city operational statistics, not
investment advice; the delivery bundle carries this disclaimer
as its first and last content line.

Platform-side posture: dataset registration and subscription
purchase contain zero resident free text, so there is no
msgSecCheck access point in this face (festival / ads /
showroom / apimarket-register precedent); any future
resident-text surface wires the SecGate pre-gate first.

AIGC label law: every dataset registry row persists its
ai_label 0/1 declaration (presented in every envelope); a direct
insert with ai_label=2 is rejected by the DB CHECK.

Gate posture: every reject (unknown dataset, bad window,
duplicate, not subscribed, bad arguments) fires before the
spend / before any row is written, so a rejected call never
charges and never grants. All three tables are append-only
(zero UPDATE statements exist in this module).

Window price points and the production catalog are
caller-supplied in the sandbox; real price points and launch
gating are a P1 item for CEO, approval-only ([needs-CEO]). No
config keys are added by this module.

Stdlib only. Encoding discipline: this module stays pure ASCII.
"""

import datetime
import hashlib
import os
import re
import sqlite3
import threading

E_DSB_UNKNOWN_DATASET = "E_DSB_UNKNOWN_DATASET"
E_DSB_DUP = "E_DSB_DUP"                    # ref / copy / window replay
E_DSB_BAD_WINDOW = "E_DSB_BAD_WINDOW"      # malformed or wrong period
E_DSB_NOT_SUBSCRIBED = "E_DSB_NOT_SUBSCRIBED"
E_DSB_NO_DISCLAIMER = "E_DSB_NO_DISCLAIMER"
E_DSB_BAD_ARGS = "E_DSB_BAD_ARGS"

PERIODS = ("monthly", "quarterly")

NON_ADVISORY = ("non-advisory notice: descriptive aggregate city"
                " operational statistics, not investment advice")

# \Z hard anchor (R1748 lesson: $ tolerates a trailing newline and
# would let "2026-10\n" through the gate onto an empty account).
_MONTHLY_RE = re.compile(r"\A[0-9]{4}-(0[1-9]|1[0-2])\Z")
_QUARTERLY_RE = re.compile(r"\A[0-9]{4}-Q[1-4]\Z")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS dataset_registry (
    dataset_key TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    period TEXT NOT NULL CHECK (period IN ('monthly', 'quarterly')),
    price_cent INTEGER NOT NULL CHECK (price_cent >= 1),
    dataset_digest TEXT NOT NULL,
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0, 1)),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dataset_subscriptions (
    sub_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account TEXT NOT NULL,
    dataset_key TEXT NOT NULL,
    period_window TEXT NOT NULL,
    purchase_ref TEXT NOT NULL UNIQUE,
    price_cent INTEGER NOT NULL,
    bound_spend_tx TEXT NOT NULL,
    subscribed_utc TEXT NOT NULL,
    UNIQUE (account, dataset_key, period_window)
);
CREATE TABLE IF NOT EXISTS dataset_deliveries (
    delivery_ref TEXT PRIMARY KEY,
    account TEXT NOT NULL,
    dataset_key TEXT NOT NULL,
    period_window TEXT NOT NULL,
    delivered_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return (isinstance(value, int) and not isinstance(value, bool))


def _account_ok(account):
    return (account.startswith("usr:") or account.startswith("ent:")) \
        and len(account) > 4


def _window_ok(period, window):
    if not isinstance(window, str):
        return False
    if period == "monthly":
        return _MONTHLY_RE.match(window) is not None
    return _QUARTERLY_RE.match(window) is not None


class DataSubError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class DatasetSubscriptionFace:
    """Periodic city-dataset subscription face over one Ledger
    instance. Own connection / lock / sqlite file for the three
    subscription tables; the only token touch is the ledger spend
    inside subscribe (the public ledger API)."""

    def __init__(self, ledger, disclaimer):
        text = str(disclaimer or "").strip()
        if not text:
            raise DataSubError(E_DSB_NO_DISCLAIMER,
                               "a resident disclaimer is required")
        self.disclaimer = text
        self.led = ledger
        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(ledger.db_path)),
            "datasub.db")
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- internal helpers ---------------------------------------------------

    def _registry_row(self, dataset_key):
        with self._lock:
            row = self._conn.execute(
                "SELECT title, period, price_cent, dataset_digest, ai_label"
                " FROM dataset_registry WHERE dataset_key = ?",
                (dataset_key,)).fetchone()
        return row

    def _sub_row(self, account, dataset_key, period_window):
        with self._lock:
            row = self._conn.execute(
                "SELECT sub_id, purchase_ref, price_cent, bound_spend_tx"
                " FROM dataset_subscriptions WHERE account = ?"
                " AND dataset_key = ? AND period_window = ?",
                (account, dataset_key, period_window)).fetchone()
        return row

    # -- writer faces -------------------------------------------------------

    def register_dataset(self, dataset_key, title, period, price_cent,
                         dataset_digest, ai_generated):
        """Mechanism registration of one published dataset (aggregate
        descriptors only - title, period, price, sha256 dataset
        digest). Re-registering the same key with identical
        parameters is idempotent; a conflicting re-register is
        rejected E_DSB_DUP (registry rows are immutable - no
        UPDATE exists). ai_label 0/1 persists on the row."""
        dataset_key = str(dataset_key or "").strip()
        title = str(title or "").strip()
        period = str(period or "").strip()
        digest = str(dataset_digest or "").strip()
        if isinstance(ai_generated, bool):
            ai_label = 1 if ai_generated else 0
        else:
            raise DataSubError(E_DSB_BAD_ARGS, "ai_generated must be bool")
        if not dataset_key or not title or not digest:
            raise DataSubError(E_DSB_BAD_ARGS,
                              "dataset_key/title/digest required")
        if period not in PERIODS:
            raise DataSubError(E_DSB_BAD_ARGS, "unknown period " + str(period))
        if not _is_int(price_cent) or price_cent < 1:
            raise DataSubError(E_DSB_BAD_ARGS,
                              "price_cent must be int >= 1")
        with self._lock:
            row = self._conn.execute(
                "SELECT title, period, price_cent, dataset_digest, ai_label"
                " FROM dataset_registry WHERE dataset_key = ?",
                (dataset_key,)).fetchone()
            if row is not None:
                if (row[0], row[1], int(row[2]), row[3], int(row[4])) \
                        == (title, period, price_cent, digest, ai_label):
                    return {"dataset_key": dataset_key,
                            "idempotent": True, "ai_label": ai_label,
                            "disclaimer": self.disclaimer}
                raise DataSubError(E_DSB_DUP, dataset_key)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO dataset_registry (dataset_key, title,"
                    " period, price_cent, dataset_digest, ai_label,"
                    " registered_utc) VALUES (?,?,?,?,?,?,?)",
                    (dataset_key, title, period, price_cent, digest,
                     ai_label, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise DataSubError(E_DSB_DUP, dataset_key)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"dataset_key": dataset_key, "idempotent": False,
                "ai_label": ai_label, "disclaimer": self.disclaimer}

    def subscribe(self, account, dataset_key, at_window, ref):
        """Subscribe one account to one dataset for one delivery
        window: exactly one token spend at the registered price,
        bound to its spend tx; the immutable subscription row is
        the delivery permission gate (the reports voucher
        judgement carried to windows). Window format must match
        the dataset period (E_DSB_BAD_WINDOW otherwise). Duplicate
        refs and duplicate account+dataset+window copies are both
        rejected before the spend (zero charge); a ledger balance
        reject leaves zero side effects (no row)."""
        account = str(account or "").strip()
        dataset_key = str(dataset_key or "").strip()
        if not _account_ok(account):
            raise DataSubError(E_DSB_BAD_ARGS,
                              "accounts are usr:* or ent:* only")
        if not dataset_key:
            raise DataSubError(E_DSB_BAD_ARGS, "dataset_key required")
        if not str(ref).strip():
            raise DataSubError(E_DSB_BAD_ARGS, "purchase ref required")
        cat = self._registry_row(dataset_key)
        if cat is None:
            raise DataSubError(E_DSB_UNKNOWN_DATASET, dataset_key)
        period = cat[1]
        if not _window_ok(period, at_window):
            raise DataSubError(E_DSB_BAD_WINDOW,
                               "%s dataset takes %s windows, got %r"
                               % (period,
                                  "YYYY-MM" if period == "monthly"
                                  else "YYYY-QN", at_window))
        price = int(cat[2])
        # pre-checks BEFORE the spend: a rejected replay never charges
        with self._lock:
            dup_ref = self._conn.execute(
                "SELECT 1 FROM dataset_subscriptions"
                " WHERE purchase_ref = ?", (str(ref),)).fetchone()
            dup_window = self._conn.execute(
                "SELECT 1 FROM dataset_subscriptions WHERE account = ?"
                " AND dataset_key = ? AND period_window = ?",
                (account, dataset_key, at_window)).fetchone()
        if dup_ref is not None or dup_window is not None:
            raise DataSubError(E_DSB_DUP,
                              str(ref) if dup_ref is not None
                              else account + "/" + dataset_key + "/"
                              + str(at_window))
        spend_tx = self.led.spend(account, price, str(ref), "order")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO dataset_subscriptions (account,"
                    " dataset_key, period_window, purchase_ref, price_cent,"
                    " bound_spend_tx, subscribed_utc)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (account, dataset_key, at_window, str(ref), price,
                     spend_tx, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise DataSubError(E_DSB_DUP, str(ref))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"dataset_key": dataset_key, "account": account,
                "period_window": at_window, "price_cent": price,
                "spend_tx": spend_tx, "disclaimer": self.disclaimer}

    def deliver(self, account, dataset_key, at_window, delivery_ref):
        """Deliver the window bundle through the permission gate:
        an immutable subscription row for (account, dataset,
        window) must exist (E_DSB_NOT_SUBSCRIBED otherwise - zero
        rows, zero tokens). The delivery is the descriptor bundle
        (aggregate metadata + dataset digest - structural
        de-identification, zero raw row data) with the
        non-advisory notice as first and last content line. One
        deliver = one immutable delivery row keyed by the
        caller's delivery_ref; duplicate refs are rejected with
        zero double-write; one window may re-download repeatedly
        with distinct refs. Zero token-ledger involvement."""
        account = str(account or "").strip()
        dataset_key = str(dataset_key or "").strip()
        if not _account_ok(account):
            raise DataSubError(E_DSB_BAD_ARGS,
                              "accounts are usr:* or ent:* only")
        if not dataset_key:
            raise DataSubError(E_DSB_BAD_ARGS, "dataset_key required")
        if not str(delivery_ref).strip():
            raise DataSubError(E_DSB_BAD_ARGS, "delivery ref required")
        cat = self._registry_row(dataset_key)
        if cat is None:
            raise DataSubError(E_DSB_UNKNOWN_DATASET, dataset_key)
        if not _window_ok(cat[1], at_window):
            raise DataSubError(E_DSB_BAD_WINDOW,
                               "%s dataset takes %s windows, got %r"
                               % (cat[1],
                                  "YYYY-MM" if cat[1] == "monthly"
                                  else "YYYY-QN", at_window))
        sub = self._sub_row(account, dataset_key, at_window)
        if sub is None:
            raise DataSubError(E_DSB_NOT_SUBSCRIBED,
                               account + "/" + dataset_key + "/"
                               + str(at_window))
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO dataset_deliveries (delivery_ref,"
                    " account, dataset_key, period_window,"
                    " delivered_utc) VALUES (?,?,?,?,?)",
                    (str(delivery_ref), account, dataset_key, at_window,
                     _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise DataSubError(E_DSB_DUP, str(delivery_ref))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return self.dataset_bundle(dataset_key, at_window)

    # -- read faces -----------------------------------------------------------

    def dataset_bundle(self, dataset_key, at_window):
        """The delivered bundle: aggregate descriptors + dataset
        digest, with the non-advisory standing notice as the first
        and last content line. The key set is exactly the
        descriptor set - raw row data cannot appear in a delivery.
        Read-only, zero token movement."""
        cat = self._registry_row(dataset_key)
        if cat is None:
            raise DataSubError(E_DSB_UNKNOWN_DATASET, dataset_key)
        return {"dataset_key": dataset_key,
                "title": cat[0],
                "period": cat[1],
                "period_window": at_window,
                "disclaimer_first": NON_ADVISORY,
                "disclaimer_last": NON_ADVISORY,
                "dataset_digest": cat[3],
                "ai_label": int(cat[4]),
                "disclaimer": self.disclaimer,
                "pricing_note": "window price published at sandbox"
                                " dock; production price points"
                                " = [needs-CEO] P1 approval-only"}

    def dataset_view(self, dataset_key):
        """Registry row + live subscriber and delivery counts for
        one dataset. Read-only, zero token movement."""
        cat = self._registry_row(dataset_key)
        if cat is None:
            raise DataSubError(E_DSB_UNKNOWN_DATASET, dataset_key)
        with self._lock:
            subs = self._conn.execute(
                "SELECT COUNT(*) FROM dataset_subscriptions"
                " WHERE dataset_key = ?", (dataset_key,)).fetchone()[0]
            dels = self._conn.execute(
                "SELECT COUNT(*) FROM dataset_deliveries"
                " WHERE dataset_key = ?", (dataset_key,)).fetchone()[0]
        return {"dataset_key": dataset_key, "title": cat[0],
                "period": cat[1], "price_cent": int(cat[2]),
                "dataset_digest": cat[3], "ai_label": int(cat[4]),
                "subscriber_count": int(subs),
                "delivery_count": int(dels),
                "disclaimer": self.disclaimer}

    def subscription_view(self, account):
        """One account's subscriptions with per-window delivery
        counts (the delivery permission gate is visible here).
        Read-only, zero token movement."""
        account = str(account or "").strip()
        if not _account_ok(account):
            raise DataSubError(E_DSB_BAD_ARGS,
                              "accounts are usr:* or ent:* only")
        with self._lock:
            rows = self._conn.execute(
                "SELECT dataset_key, period_window, price_cent,"
                " bound_spend_tx, subscribed_utc FROM"
                " dataset_subscriptions WHERE account = ?"
                " ORDER BY subscribed_utc, sub_id", (account,)).fetchall()
            subs = []
            for r in rows:
                cnt = self._conn.execute(
                    "SELECT COUNT(*) FROM dataset_deliveries"
                    " WHERE account = ? AND dataset_key = ?"
                    " AND period_window = ?",
                    (account, r[0], r[1])).fetchone()[0]
                subs.append({"dataset_key": r[0], "period_window": r[1],
                             "price_cent": int(r[2]), "spend_tx": r[3],
                             "subscribed_utc": r[4],
                             "deliveries": int(cnt)})
        return {"account": account, "subscriptions": subs,
                "disclaimer": self.disclaimer}

    def reconcile_dataset(self, dataset_key):
        """Dataset reconciliation read face: every subscription row
        must carry its bound spend tx, every delivery row must hang
        off a valid subscription of the same (account, dataset,
        window), and the billed total must equal the subscription
        price sum. Any drift (e.g. an injected orphan delivery
        row) flips the balanced verdict to False with the orphans
        named. Read-only, zero token movement."""
        cat = self._registry_row(dataset_key)
        if cat is None:
            raise DataSubError(E_DSB_UNKNOWN_DATASET, dataset_key)
        with self._lock:
            subs = self._conn.execute(
                "SELECT account, period_window, price_cent,"
                " bound_spend_tx FROM dataset_subscriptions"
                " WHERE dataset_key = ? ORDER BY sub_id",
                (dataset_key,)).fetchall()
            dels = self._conn.execute(
                "SELECT delivery_ref, account, period_window"
                " FROM dataset_deliveries WHERE dataset_key = ?"
                " ORDER BY delivered_utc, delivery_ref",
                (dataset_key,)).fetchall()
        sub_set = {(s[1], s[0]) for s in subs}
        orphans = [d[0] for d in dels if (d[2], d[1]) not in sub_set]
        missing_tx = [s[1] for s in subs if not s[3]]
        return {"dataset_key": dataset_key,
                "subscriptions": len(subs),
                "deliveries": len(dels),
                "orphan_deliveries": orphans,
                "missing_spend_tx": missing_tx,
                "balanced": (not orphans and not missing_tx),
                "billed_total_cent": sum(int(s[2]) for s in subs),
                "disclaimer": self.disclaimer}
